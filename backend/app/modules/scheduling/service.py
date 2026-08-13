from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.modules.accounts.contracts import account_names, lock_account_references
from app.modules.categories.contracts import (
    CategoryType,
    category_name,
    validate_category_reference,
)
from app.modules.operations.contracts import (
    OperationType,
    ScheduledOperationDraft,
    post_scheduled_operation,
)
from app.modules.scheduling.models import (
    ExpectedOccurrence,
    OccurrenceStatus,
    RecurrenceFrequency,
    RecurringRule,
)
from app.modules.scheduling.schemas import (
    ExpectedOccurrenceResponse,
    MaterializationResponse,
    OccurrencePageResponse,
    RecurringRuleCreateRequest,
    RecurringRuleResponse,
    RecurringRuleUpdateRequest,
    format_money,
)
from app.modules.settings.contracts import application_timezone, lock_application_timezone


class RecurringRuleNotFoundError(RuntimeError):
    pass


class SchedulingConflictError(RuntimeError):
    pass


class ExpectedOccurrenceNotFoundError(RuntimeError):
    pass


class InvalidOccurrenceTransitionError(RuntimeError):
    pass


@dataclass(slots=True)
class _MaterializationCounts:
    created: int = 0
    updated: int = 0
    cancelled: int = 0

    def add(self, other: "_MaterializationCounts") -> None:
        self.created += other.created
        self.updated += other.updated
        self.cancelled += other.cancelled


def calendar_year_later(value: date) -> date:
    try:
        return value.replace(year=value.year + 1)
    except ValueError:
        return value.replace(year=value.year + 1, day=28)


def recurrence_dates(
    *,
    frequency: RecurrenceFrequency,
    interval: int = 1,
    weekdays: list[int] | None = None,
    anchor: date,
    range_from: date,
    range_to: date,
    end_on: date | None,
) -> list[date]:
    """Return deterministic recurrence dates within an inclusive bounded range."""
    upper = min(range_to, end_on) if end_on is not None else range_to
    lower = max(range_from, anchor)
    if upper < lower:
        return []
    if frequency == RecurrenceFrequency.DAILY:
        step = 1
        elapsed = (lower - anchor).days
        skipped = (elapsed + step - 1) // step
        current = anchor + timedelta(days=skipped * step)
        result: list[date] = []
        while current <= upper:
            result.append(current)
            current += timedelta(days=step)
        return result
    if frequency == RecurrenceFrequency.WEEKLY:
        selected = sorted(weekdays or [anchor.isoweekday()])
        anchor_week = anchor - timedelta(days=anchor.isoweekday() - 1)
        current_week = lower - timedelta(days=lower.isoweekday() - 1)
        elapsed_weeks = (current_week - anchor_week).days // 7
        if elapsed_weeks % interval:
            current_week += timedelta(weeks=interval - elapsed_weeks % interval)
        result = []
        while current_week <= upper:
            for weekday in selected:
                current = current_week + timedelta(days=weekday - 1)
                if current >= anchor and lower <= current <= upper:
                    result.append(current)
            current_week += timedelta(weeks=interval)
        return result
    if frequency == RecurrenceFrequency.MONTHLY:
        start_index = anchor.year * 12 + anchor.month - 1
        lower_index = lower.year * 12 + lower.month - 1
        index = max(start_index, lower_index)
        remainder = (index - start_index) % interval
        if remainder:
            index += interval - remainder
        current = date(index // 12, index % 12 + 1, anchor.day)
        if current < lower:
            index += interval
        result = []
        while True:
            current = date(index // 12, index % 12 + 1, anchor.day)
            if current > upper:
                return result
            result.append(current)
            index += interval
    year = max(anchor.year, lower.year)
    current = date(year, anchor.month, anchor.day)
    if current < lower:
        year += interval
    result = []
    while True:
        current = date(year, anchor.month, anchor.day)
        if current > upper:
            return result
        result.append(current)
        year += interval


def _today(session: Session) -> date:
    return datetime.now(UTC).astimezone(ZoneInfo(application_timezone(session))).date()


def _validate_rule_references(
    session: Session, payload: RecurringRuleCreateRequest, *, require_active: bool
) -> None:
    if payload.category_id is not None:
        expected_type = (
            CategoryType.INCOME if payload.type == OperationType.INCOME else CategoryType.EXPENSE
        )
        validate_category_reference(
            session,
            payload.category_id,
            expected_type=expected_type,
            allow_archived=not require_active,
        )
    account_ids = {payload.account_id}
    if payload.destination_account_id is not None:
        account_ids.add(payload.destination_account_id)
    lock_account_references(
        session,
        account_ids,
        allow_archived_ids=set() if require_active else account_ids,
    )


def _get_rule(session: Session, rule_id: UUID, *, lock: bool) -> RecurringRule:
    query = select(RecurringRule).where(RecurringRule.id == rule_id)
    if lock:
        query = query.with_for_update()
    rule = session.scalar(query)
    if rule is None:
        raise RecurringRuleNotFoundError
    return rule


def _get_occurrence(session: Session, occurrence_id: UUID, *, lock: bool) -> ExpectedOccurrence:
    query = select(ExpectedOccurrence).where(ExpectedOccurrence.id == occurrence_id)
    if lock:
        query = query.with_for_update()
    occurrence = session.scalar(query)
    if occurrence is None:
        raise ExpectedOccurrenceNotFoundError
    return occurrence


def _copy_snapshot(rule: RecurringRule, occurrence: ExpectedOccurrence) -> bool:
    changed = False
    values: dict[str, object] = {
        "type": rule.type,
        "amount": rule.amount,
        "description": rule.description,
        "account_id": rule.account_id,
        "destination_account_id": rule.destination_account_id,
        "category_id": rule.category_id,
    }
    for name, value in values.items():
        if getattr(occurrence, name) != value:
            setattr(occurrence, name, value)
            changed = True
    return changed


def _new_occurrence(rule: RecurringRule, scheduled_on: date, now: datetime) -> ExpectedOccurrence:
    return ExpectedOccurrence(
        rule_id=rule.id,
        scheduled_on=scheduled_on,
        due_on=scheduled_on,
        status=OccurrenceStatus.PENDING,
        manually_modified=False,
        type=rule.type,
        amount=rule.amount,
        description=rule.description,
        account_id=rule.account_id,
        destination_account_id=rule.destination_account_id,
        category_id=rule.category_id,
        actual_operation_id=None,
        version=1,
        created_at=now,
        updated_at=now,
    )


def _lock_rule_occurrences(session: Session, rule_id: UUID) -> dict[date, ExpectedOccurrence]:
    return {
        occurrence.scheduled_on: occurrence
        for occurrence in session.scalars(
            select(ExpectedOccurrence)
            .where(ExpectedOccurrence.rule_id == rule_id)
            .order_by(ExpectedOccurrence.scheduled_on, ExpectedOccurrence.id)
            .with_for_update()
        ).all()
    }


def _synchronize_rule(
    session: Session,
    rule: RecurringRule,
    *,
    horizon_from: date,
    horizon_to: date,
    existing: dict[date, ExpectedOccurrence] | None = None,
) -> _MaterializationCounts:
    if existing is None:
        existing = _lock_rule_occurrences(session, rule.id)
    target_dates = (
        set(
            recurrence_dates(
                frequency=rule.frequency,
                interval=rule.interval,
                weekdays=rule.weekdays,
                anchor=rule.start_on,
                range_from=horizon_from,
                range_to=horizon_to,
                end_on=rule.end_on,
            )
        )
        if rule.active
        else set()
    )
    now = datetime.now(UTC)
    counts = _MaterializationCounts()
    for scheduled_on, occurrence in existing.items():
        if scheduled_on < horizon_from:
            continue
        if occurrence.status == OccurrenceStatus.CONFIRMED or occurrence.manually_modified:
            continue
        changed = False
        if scheduled_on in target_dates:
            if occurrence.status != OccurrenceStatus.PENDING:
                occurrence.status = OccurrenceStatus.PENDING
                changed = True
            if occurrence.due_on != scheduled_on:
                occurrence.due_on = scheduled_on
                changed = True
            changed = _copy_snapshot(rule, occurrence) or changed
        elif occurrence.status != OccurrenceStatus.CANCELLED:
            occurrence.status = OccurrenceStatus.CANCELLED
            occurrence.due_on = scheduled_on
            changed = True
            counts.cancelled += 1
        if changed:
            occurrence.version += 1
            occurrence.updated_at = now
            counts.updated += 1
    for scheduled_on in sorted(target_dates - existing.keys()):
        session.add(_new_occurrence(rule, scheduled_on, now))
        counts.created += 1
    session.flush()
    return counts


def create_rule(
    session: Session, payload: RecurringRuleCreateRequest, *, today: date | None = None
) -> RecurringRule:
    lock_application_timezone(session)
    _validate_rule_references(session, payload, require_active=True)
    now = datetime.now(UTC)
    rule = RecurringRule(
        **payload.model_dump(), active=True, version=1, created_at=now, updated_at=now
    )
    session.add(rule)
    session.flush()
    horizon_from = today or _today(session)
    _synchronize_rule(
        session,
        rule,
        horizon_from=horizon_from,
        horizon_to=calendar_year_later(horizon_from),
    )
    return rule


def update_rule(
    session: Session,
    rule_id: UUID,
    payload: RecurringRuleUpdateRequest,
    *,
    today: date | None = None,
) -> RecurringRule:
    rule = _get_rule(session, rule_id, lock=True)
    if rule.version != payload.version:
        raise SchedulingConflictError
    existing = _lock_rule_occurrences(session, rule.id)
    _validate_rule_references(session, payload, require_active=payload.active)
    for name, value in payload.model_dump(exclude={"version"}).items():
        setattr(rule, name, value)
    rule.version += 1
    rule.updated_at = datetime.now(UTC)
    horizon_from = today or _today(session)
    _synchronize_rule(
        session,
        rule,
        horizon_from=horizon_from,
        horizon_to=calendar_year_later(horizon_from),
        existing=existing,
    )
    return rule


def materialize_all(session: Session, *, today: date | None = None) -> MaterializationResponse:
    horizon_from = today or _today(session)
    horizon_to = calendar_year_later(horizon_from)
    counts = _MaterializationCounts()
    rules = session.scalars(
        select(RecurringRule).order_by(RecurringRule.id).with_for_update()
    ).all()
    for rule in rules:
        counts.add(
            _synchronize_rule(session, rule, horizon_from=horizon_from, horizon_to=horizon_to)
        )
    return MaterializationResponse(
        horizon_from=horizon_from,
        horizon_to=horizon_to,
        created=counts.created,
        updated=counts.updated,
        cancelled=counts.cancelled,
    )


def _rule_response(session: Session, rule: RecurringRule) -> RecurringRuleResponse:
    ids = {rule.account_id}
    if rule.destination_account_id is not None:
        ids.add(rule.destination_account_id)
    names = account_names(session, ids)
    return RecurringRuleResponse(
        id=rule.id,
        type=rule.type,
        frequency=rule.frequency,
        interval=rule.interval,
        weekdays=rule.weekdays,
        start_on=rule.start_on,
        end_on=rule.end_on,
        amount=format_money(Decimal(rule.amount)),
        description=rule.description,
        account_id=rule.account_id,
        account_name=names[rule.account_id],
        destination_account_id=rule.destination_account_id,
        destination_account_name=(
            names[rule.destination_account_id] if rule.destination_account_id is not None else None
        ),
        category_id=rule.category_id,
        category_name=(category_name(session, rule.category_id) if rule.category_id else None),
        active=rule.active,
        version=rule.version,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


def list_rule_responses(session: Session) -> list[RecurringRuleResponse]:
    return [
        _rule_response(session, rule)
        for rule in session.scalars(
            select(RecurringRule).order_by(
                RecurringRule.active.desc(), RecurringRule.start_on, RecurringRule.id
            )
        ).all()
    ]


def get_rule_response(session: Session, rule_id: UUID) -> RecurringRuleResponse:
    return _rule_response(session, _get_rule(session, rule_id, lock=False))


def _occurrence_response(
    session: Session, occurrence: ExpectedOccurrence, *, today: date
) -> ExpectedOccurrenceResponse:
    ids = {occurrence.account_id}
    if occurrence.destination_account_id is not None:
        ids.add(occurrence.destination_account_id)
    names = account_names(session, ids)
    return ExpectedOccurrenceResponse(
        id=occurrence.id,
        rule_id=occurrence.rule_id,
        scheduled_on=occurrence.scheduled_on,
        due_on=occurrence.due_on,
        status=occurrence.status,
        manually_modified=occurrence.manually_modified,
        overdue=(
            occurrence.status in {OccurrenceStatus.PENDING, OccurrenceStatus.POSTPONED}
            and occurrence.due_on < today
        ),
        type=occurrence.type,
        amount=format_money(Decimal(occurrence.amount)),
        description=occurrence.description,
        account_id=occurrence.account_id,
        account_name=names[occurrence.account_id],
        destination_account_id=occurrence.destination_account_id,
        destination_account_name=(
            names[occurrence.destination_account_id]
            if occurrence.destination_account_id is not None
            else None
        ),
        category_id=occurrence.category_id,
        category_name=(
            category_name(session, occurrence.category_id) if occurrence.category_id else None
        ),
        actual_operation_id=occurrence.actual_operation_id,
        version=occurrence.version,
        created_at=occurrence.created_at,
        updated_at=occurrence.updated_at,
    )


def list_occurrence_responses(
    session: Session,
    *,
    page: int,
    page_size: int,
    due_from: date | None,
    due_to: date | None,
    account_id: UUID | None,
    operation_type: OperationType | None,
    statuses: set[OccurrenceStatus] | None,
    today: date | None = None,
) -> OccurrencePageResponse:
    conditions: list[ColumnElement[bool]] = []
    if due_from is not None:
        conditions.append(ExpectedOccurrence.due_on >= due_from)
    if due_to is not None:
        conditions.append(ExpectedOccurrence.due_on <= due_to)
    if account_id is not None:
        conditions.append(
            or_(
                ExpectedOccurrence.account_id == account_id,
                ExpectedOccurrence.destination_account_id == account_id,
            )
        )
    if operation_type is not None:
        conditions.append(ExpectedOccurrence.type == operation_type)
    if statuses:
        conditions.append(ExpectedOccurrence.status.in_(statuses))
    total = session.scalar(select(func.count()).select_from(ExpectedOccurrence).where(*conditions))
    occurrences = session.scalars(
        select(ExpectedOccurrence)
        .where(*conditions)
        .order_by(ExpectedOccurrence.due_on, ExpectedOccurrence.created_at, ExpectedOccurrence.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    resolved_today = today or _today(session)
    return OccurrencePageResponse(
        items=[
            _occurrence_response(session, occurrence, today=resolved_today)
            for occurrence in occurrences
        ],
        page=page,
        page_size=page_size,
        total=int(total or 0),
    )


def confirm_occurrence(
    session: Session, occurrence_id: UUID, *, expected_version: int, today: date | None = None
) -> ExpectedOccurrenceResponse:
    occurrence = _get_occurrence(session, occurrence_id, lock=True)
    resolved_today = today or _today(session)
    if occurrence.status == OccurrenceStatus.CONFIRMED:
        return _occurrence_response(session, occurrence, today=resolved_today)
    if occurrence.version != expected_version:
        raise SchedulingConflictError
    if occurrence.status not in {OccurrenceStatus.PENDING, OccurrenceStatus.POSTPONED}:
        raise InvalidOccurrenceTransitionError
    operation_id = post_scheduled_operation(
        session,
        ScheduledOperationDraft(
            type=occurrence.type,
            occurred_on=occurrence.due_on,
            amount=Decimal(occurrence.amount),
            description=occurrence.description,
            account_id=occurrence.account_id,
            destination_account_id=occurrence.destination_account_id,
            category_id=occurrence.category_id,
        ),
    )

    _link_confirmed_operation(occurrence, operation_id)
    session.flush()
    return _occurrence_response(session, occurrence, today=resolved_today)


def _link_confirmed_operation(occurrence: ExpectedOccurrence, operation_id: UUID) -> None:
    occurrence.status = OccurrenceStatus.CONFIRMED
    occurrence.actual_operation_id = operation_id
    occurrence.version += 1
    occurrence.updated_at = datetime.now(UTC)


def postpone_occurrence(
    session: Session,
    occurrence_id: UUID,
    *,
    due_on: date,
    expected_version: int,
    today: date | None = None,
) -> ExpectedOccurrenceResponse:
    occurrence = _get_occurrence(session, occurrence_id, lock=True)
    if occurrence.version != expected_version:
        raise SchedulingConflictError
    if (
        occurrence.status not in {OccurrenceStatus.PENDING, OccurrenceStatus.POSTPONED}
        or occurrence.due_on == due_on
    ):
        raise InvalidOccurrenceTransitionError
    occurrence.due_on = due_on
    occurrence.status = OccurrenceStatus.POSTPONED
    occurrence.manually_modified = True
    occurrence.version += 1
    occurrence.updated_at = datetime.now(UTC)
    session.flush()
    return _occurrence_response(session, occurrence, today=today or _today(session))


def cancel_occurrence(
    session: Session, occurrence_id: UUID, *, expected_version: int, today: date | None = None
) -> ExpectedOccurrenceResponse:
    occurrence = _get_occurrence(session, occurrence_id, lock=True)
    resolved_today = today or _today(session)
    if occurrence.status == OccurrenceStatus.CANCELLED and occurrence.manually_modified:
        return _occurrence_response(session, occurrence, today=resolved_today)
    if occurrence.version != expected_version:
        raise SchedulingConflictError
    if occurrence.status not in {OccurrenceStatus.PENDING, OccurrenceStatus.POSTPONED}:
        raise InvalidOccurrenceTransitionError
    occurrence.status = OccurrenceStatus.CANCELLED
    occurrence.due_on = occurrence.scheduled_on
    occurrence.manually_modified = True
    occurrence.version += 1
    occurrence.updated_at = datetime.now(UTC)
    session.flush()
    return _occurrence_response(session, occurrence, today=resolved_today)
