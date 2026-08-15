from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.accounts.contracts import (
    AccountReferenceError,
    account_names,
    list_account_identities,
)
from app.modules.forecasting.schemas import (
    ForecastBalanceMode,
    ForecastEventResponse,
    ForecastGranularity,
    ForecastHorizon,
    ForecastPointResponse,
    ForecastResponse,
    ForecastScope,
)
from app.modules.funds.contracts import reserved_balances
from app.modules.operations.contracts import OperationType, account_balances
from app.modules.scheduling.contracts import (
    OccurrenceStatus,
    PlannedOccurrence,
    forecast_schedule_snapshot,
)


@dataclass(frozen=True, slots=True)
class ForecastInputEvent:
    occurrence_id: UUID
    rule_id: UUID
    due_on: date
    type: OperationType
    status: OccurrenceStatus
    description: str | None
    account_id: UUID
    destination_account_id: UUID | None
    amount: Decimal


def horizon_end(today: date, horizon: ForecastHorizon) -> date:
    if horizon == ForecastHorizon.TWO_WEEKS:
        return today + timedelta(days=14)
    if horizon == ForecastHorizon.MONTH:
        return _add_months(today, 1)
    if horizon == ForecastHorizon.QUARTER:
        return _add_months(today, 3)
    if horizon == ForecastHorizon.HALF_YEAR:
        return _add_months(today, 6)
    return _add_months(today, 12)


def _add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(index, 12)
    month = month_index + 1
    next_index = index + 1
    next_year, next_month_index = divmod(next_index, 12)
    last_day = (date(next_year, next_month_index + 1, 1) - timedelta(days=1)).day
    return date(year, month, min(value.day, last_day))


def calculate_forecast(
    *,
    today: date,
    through_on: date,
    balances: dict[UUID, Decimal],
    account_name_by_id: dict[UUID, str],
    events: list[ForecastInputEvent],
    account_id: UUID | None,
    horizon: ForecastHorizon,
    overdue_excluded_count: int = 0,
    balance_mode: ForecastBalanceMode = ForecastBalanceMode.TOTAL,
) -> ForecastResponse:
    if through_on < today:
        raise ValueError("forecast end must not precede today")
    if account_id is not None and account_id not in balances:
        raise AccountReferenceError
    starting = (
        balances[account_id] if account_id is not None else sum(balances.values(), Decimal(0))
    )
    grouped: dict[date, list[tuple[ForecastInputEvent, Decimal]]] = defaultdict(list)
    income = Decimal(0)
    expense = Decimal(0)
    for event in sorted(events, key=lambda item: (item.due_on, item.occurrence_id)):
        if event.status not in {OccurrenceStatus.PENDING, OccurrenceStatus.POSTPONED}:
            continue
        if event.due_on < today or event.due_on > through_on:
            continue
        if account_id is not None and account_id not in {
            event.account_id,
            event.destination_account_id,
        }:
            continue
        effect = _scope_effect(event, account_id)
        grouped[event.due_on].append((event, effect))
        if event.type == OperationType.INCOME and effect > 0:
            income += effect
        elif event.type == OperationType.EXPENSE and effect < 0:
            expense += -effect

    granularity = (
        ForecastGranularity.MONTH if horizon == ForecastHorizon.YEAR else ForecastGranularity.DAY
    )
    minimum = starting
    minimum_on = today
    first_negative: date | None = today if starting < 0 else None
    first_negative_balance: Decimal | None = starting if starting < 0 else None
    risk_balance = starting
    for on in sorted(grouped):
        risk_balance += sum((effect for _, effect in grouped[on]), Decimal(0))
        if risk_balance < minimum:
            minimum = risk_balance
            minimum_on = on
        if first_negative is None and risk_balance < 0:
            first_negative = on
            first_negative_balance = risk_balance

    current = starting
    points: list[ForecastPointResponse] = []
    for period_from, on in _forecast_periods(today, through_on, granularity):
        opening = current
        period_events = [
            item
            for event_on in sorted(grouped)
            if period_from <= event_on <= on
            for item in grouped[event_on]
        ]
        change = sum((effect for _, effect in period_events), Decimal(0))
        current += change
        points.append(
            ForecastPointResponse(
                period_from=period_from,
                on=on,
                opening_balance=_money(opening),
                change=_money(change),
                closing_balance=_money(current),
                events=[
                    _event_response(event, effect, account_name_by_id)
                    for event, effect in period_events
                ],
            )
        )
    return ForecastResponse(
        balance_mode=balance_mode,
        scope=ForecastScope.ACCOUNT if account_id is not None else ForecastScope.ALL,
        account_id=account_id,
        account_name=account_name_by_id.get(account_id) if account_id is not None else None,
        horizon=horizon,
        granularity=granularity,
        from_on=today,
        through_on=through_on,
        starting_balance=_money(starting),
        ending_balance=_money(current),
        minimum_balance=_money(minimum),
        minimum_on=minimum_on,
        first_negative_on=first_negative,
        first_negative_balance=(
            _money(first_negative_balance) if first_negative_balance is not None else None
        ),
        expected_income=_money(income),
        expected_expense=_money(expense),
        overdue_excluded_count=overdue_excluded_count,
        points=points,
    )


def _forecast_periods(
    from_on: date, through_on: date, granularity: ForecastGranularity
) -> list[tuple[date, date]]:
    if granularity == ForecastGranularity.DAY:
        return [
            (from_on + timedelta(days=offset), from_on + timedelta(days=offset))
            for offset in range((through_on - from_on).days + 1)
        ]
    periods: list[tuple[date, date]] = []
    cursor = from_on
    while cursor <= through_on:
        month_end = _add_months(cursor.replace(day=1), 1) - timedelta(days=1)
        period_end = min(month_end, through_on)
        periods.append((cursor, period_end))
        cursor = period_end + timedelta(days=1)
    return periods


def build_forecast(
    session: Session,
    *,
    today: date,
    horizon: ForecastHorizon,
    account_id: UUID | None,
    balance_mode: ForecastBalanceMode = ForecastBalanceMode.FREE,
) -> ForecastResponse:
    through_on = horizon_end(today, horizon)
    schedule = forecast_schedule_snapshot(
        session,
        today=today,
        due_to=through_on,
        account_id=account_id,
    )
    # Preserve the Scheduling -> Accounts lock order used by confirmation and
    # rule replacement. Shared locks keep both the plan and actual ledger at one
    # coherent transaction point without introducing a reverse lock dependency.
    accounts = list_account_identities(session, shared_lock=True)
    account_ids = {account.id for account in accounts}
    if account_id is not None and account_id not in account_ids:
        raise AccountReferenceError
    names = account_names(session, account_ids)
    balances = account_balances(session, account_ids)
    if balance_mode == ForecastBalanceMode.FREE:
        reserved_by_account = reserved_balances(session, account_ids)
        balances = {
            identity: balance - reserved_by_account[identity]
            for identity, balance in balances.items()
        }
    return calculate_forecast(
        today=today,
        through_on=through_on,
        balances=balances,
        account_name_by_id=names,
        events=[_input_event(item) for item in schedule.occurrences],
        account_id=account_id,
        horizon=horizon,
        overdue_excluded_count=schedule.overdue_count,
        balance_mode=balance_mode,
    )


def _scope_effect(event: ForecastInputEvent, account_id: UUID | None) -> Decimal:
    if event.type == OperationType.INCOME:
        return event.amount if account_id in {None, event.account_id} else Decimal(0)
    if event.type == OperationType.EXPENSE:
        return -event.amount if account_id in {None, event.account_id} else Decimal(0)
    if account_id is None:
        return Decimal(0)
    if account_id == event.account_id:
        return -event.amount
    if account_id == event.destination_account_id:
        return event.amount
    return Decimal(0)


def _input_event(item: PlannedOccurrence) -> ForecastInputEvent:
    return ForecastInputEvent(
        occurrence_id=item.id,
        rule_id=item.rule_id,
        due_on=item.due_on,
        type=item.type,
        status=item.status,
        description=item.description,
        account_id=item.account_id,
        destination_account_id=item.destination_account_id,
        amount=item.amount,
    )


def _event_response(
    event: ForecastInputEvent, effect: Decimal, names: dict[UUID, str]
) -> ForecastEventResponse:
    return ForecastEventResponse(
        occurrence_id=event.occurrence_id,
        rule_id=event.rule_id,
        due_on=event.due_on,
        type=event.type,
        status=event.status,
        description=event.description,
        account_id=event.account_id,
        account_name=names[event.account_id],
        destination_account_id=event.destination_account_id,
        destination_account_name=(
            names[event.destination_account_id]
            if event.destination_account_id is not None
            else None
        ),
        amount=_money(event.amount),
        effect=_money(effect),
    )


def _money(value: Decimal) -> str:
    return format(value, "f")
