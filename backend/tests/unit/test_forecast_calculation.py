from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest

from app.modules.accounts.contracts import AccountReferenceError
from app.modules.forecasting.schemas import ForecastHorizon, ForecastResponse
from app.modules.forecasting.service import ForecastInputEvent, calculate_forecast, horizon_end
from app.modules.operations.contracts import OperationType
from app.modules.scheduling.contracts import OccurrenceStatus

TODAY = date(2026, 8, 12)
SOURCE = UUID("10000000-0000-0000-0000-000000000001")
TARGET = UUID("10000000-0000-0000-0000-000000000002")
RULE = UUID("20000000-0000-0000-0000-000000000001")


def event(
    suffix: int,
    *,
    due_on: date,
    type: OperationType,
    amount: str,
    account_id: UUID = SOURCE,
    destination_account_id: UUID | None = None,
    status: OccurrenceStatus = OccurrenceStatus.PENDING,
) -> ForecastInputEvent:
    return ForecastInputEvent(
        occurrence_id=UUID(f"30000000-0000-0000-0000-{suffix:012d}"),
        rule_id=RULE,
        due_on=due_on,
        type=type,
        status=status,
        description=f"event {suffix}",
        account_id=account_id,
        destination_account_id=destination_account_id,
        amount=Decimal(amount),
    )


def test_horizons_are_calendar_bounded() -> None:
    assert horizon_end(TODAY, ForecastHorizon.WEEK) == date(2026, 8, 19)
    assert horizon_end(date(2026, 1, 31), ForecastHorizon.MONTH) == date(2026, 2, 28)
    assert horizon_end(TODAY, ForecastHorizon.QUARTER) == date(2026, 11, 12)
    assert horizon_end(TODAY, ForecastHorizon.HALF_YEAR) == date(2027, 2, 12)
    assert horizon_end(TODAY, ForecastHorizon.YEAR) == date(2027, 8, 12)


def test_account_forecast_is_exact_deterministic_and_explained() -> None:
    events = [
        event(2, due_on=date(2026, 8, 13), type=OperationType.EXPENSE, amount="40.0000"),
        event(1, due_on=date(2026, 8, 13), type=OperationType.INCOME, amount="10.0000"),
        event(3, due_on=date(2026, 8, 14), type=OperationType.EXPENSE, amount="80.0000"),
    ]

    def calculate(items: list[ForecastInputEvent]) -> ForecastResponse:
        return calculate_forecast(
            today=TODAY,
            through_on=date(2026, 8, 19),
            balances={SOURCE: Decimal("100.0000")},
            account_name_by_id={SOURCE: "Main"},
            events=items,
            account_id=SOURCE,
            horizon=ForecastHorizon.WEEK,
        )

    first = calculate(events)
    second = calculate(list(reversed(events)))

    assert first == second
    assert first.starting_balance == "100.0000"
    assert first.ending_balance == "-10.0000"
    assert first.minimum_balance == "-10.0000"
    assert first.minimum_on == date(2026, 8, 14)
    assert first.first_negative_on == date(2026, 8, 14)
    assert first.first_negative_balance == "-10.0000"
    assert first.expected_income == "10.0000"
    assert first.expected_expense == "120.0000"
    assert first.granularity == "day"
    assert len(first.points) == 8
    assert [point.on for point in first.points[:3]] == [
        date(2026, 8, 12),
        date(2026, 8, 13),
        date(2026, 8, 14),
    ]
    assert first.points[1].opening_balance == "100.0000"
    assert first.points[1].change == "-30.0000"
    assert [item.effect for item in first.points[1].events] == ["10.0000", "-40.0000"]


def test_transfer_is_neutral_for_all_accounts_and_directional_for_one() -> None:
    transfer = event(
        1,
        due_on=date(2026, 8, 13),
        type=OperationType.TRANSFER,
        amount="25.0000",
        destination_account_id=TARGET,
    )

    def calculate(account_id: UUID | None) -> ForecastResponse:
        return calculate_forecast(
            today=TODAY,
            through_on=date(2026, 8, 19),
            balances={SOURCE: Decimal("100.0000"), TARGET: Decimal("20.0000")},
            account_name_by_id={SOURCE: "Main", TARGET: "Savings"},
            events=[transfer],
            account_id=account_id,
            horizon=ForecastHorizon.WEEK,
        )

    combined = calculate(None)
    source = calculate(SOURCE)
    target = calculate(TARGET)

    assert combined.starting_balance == combined.ending_balance == "120.0000"
    assert combined.points[1].events[0].effect == "0"
    assert combined.expected_income == combined.expected_expense == "0"
    assert combined.first_negative_on is None
    assert combined.first_negative_balance is None
    assert source.ending_balance == "75.0000"
    assert target.ending_balance == "45.0000"


def test_account_forecast_omits_events_for_other_accounts() -> None:
    other_account_event = event(
        3,
        due_on=date(2026, 8, 13),
        type=OperationType.EXPENSE,
        amount="10.0000",
        account_id=TARGET,
    )

    result = calculate_forecast(
        today=TODAY,
        through_on=date(2026, 8, 19),
        balances={SOURCE: Decimal("100.0000"), TARGET: Decimal("50.0000")},
        account_name_by_id={SOURCE: "Main", TARGET: "Other"},
        events=[other_account_event],
        account_id=SOURCE,
        horizon=ForecastHorizon.WEEK,
    )

    assert result.ending_balance == "100.0000"
    assert all(not point.events for point in result.points)


def test_non_actionable_events_are_defensively_excluded() -> None:
    result = calculate_forecast(
        today=TODAY,
        through_on=date(2026, 8, 19),
        balances={SOURCE: Decimal("100.0000")},
        account_name_by_id={SOURCE: "Main"},
        events=[
            event(
                4,
                due_on=date(2026, 8, 13),
                type=OperationType.INCOME,
                amount="50.0000",
                status=OccurrenceStatus.CONFIRMED,
            ),
            event(
                5,
                due_on=date(2026, 8, 14),
                type=OperationType.EXPENSE,
                amount="25.0000",
                status=OccurrenceStatus.CANCELLED,
            ),
        ],
        account_id=SOURCE,
        horizon=ForecastHorizon.WEEK,
    )

    assert result.starting_balance == result.ending_balance == "100.0000"
    assert all(not point.events for point in result.points)


def test_invalid_account_scope_is_rejected() -> None:
    with pytest.raises(AccountReferenceError):
        calculate_forecast(
            today=TODAY,
            through_on=date(2026, 8, 19),
            balances={SOURCE: Decimal("0")},
            account_name_by_id={SOURCE: "Main"},
            events=[],
            account_id=TARGET,
            horizon=ForecastHorizon.WEEK,
        )


def test_year_forecast_uses_monthly_periods_and_keeps_event_details() -> None:
    result = calculate_forecast(
        today=TODAY,
        through_on=date(2027, 8, 12),
        balances={SOURCE: Decimal("100.0000")},
        account_name_by_id={SOURCE: "Main"},
        events=[
            event(1, due_on=date(2026, 8, 13), type=OperationType.INCOME, amount="20.0000"),
            event(2, due_on=date(2026, 8, 20), type=OperationType.EXPENSE, amount="5.0000"),
            event(3, due_on=date(2026, 9, 1), type=OperationType.EXPENSE, amount="10.0000"),
        ],
        account_id=SOURCE,
        horizon=ForecastHorizon.YEAR,
    )

    assert result.granularity == "month"
    assert len(result.points) == 13
    assert result.points[0].period_from == TODAY
    assert result.points[0].on == date(2026, 8, 31)
    assert result.points[0].change == "15.0000"
    assert len(result.points[0].events) == 2
    assert result.points[1].period_from == date(2026, 9, 1)
    assert result.points[1].on == date(2026, 9, 30)
    assert result.points[-1].on == date(2027, 8, 12)


def test_first_negative_balance_keeps_daily_precision_for_year_view() -> None:
    result = calculate_forecast(
        today=TODAY,
        through_on=date(2027, 8, 12),
        balances={SOURCE: Decimal("20.0000")},
        account_name_by_id={SOURCE: "Main"},
        events=[
            event(1, due_on=date(2026, 8, 13), type=OperationType.EXPENSE, amount="22.0000"),
            event(2, due_on=date(2026, 8, 20), type=OperationType.INCOME, amount="10.0000"),
        ],
        account_id=SOURCE,
        horizon=ForecastHorizon.YEAR,
    )

    assert result.first_negative_on == date(2026, 8, 13)
    assert result.first_negative_balance == "-2.0000"
    assert result.points[0].closing_balance == "8.0000"


def test_starting_deficit_keeps_the_current_balance_as_first_negative() -> None:
    result = calculate_forecast(
        today=TODAY,
        through_on=date(2026, 8, 19),
        balances={SOURCE: Decimal("-7.5000")},
        account_name_by_id={SOURCE: "Main"},
        events=[
            event(1, due_on=TODAY, type=OperationType.INCOME, amount="20.0000"),
        ],
        account_id=SOURCE,
        horizon=ForecastHorizon.WEEK,
    )

    assert result.first_negative_on == TODAY
    assert result.first_negative_balance == "-7.5000"
    assert result.points[0].closing_balance == "12.5000"
