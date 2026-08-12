"""Public scheduling references used by cross-module read/application use cases."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.operations.contracts import OperationType
from app.modules.scheduling.models import ExpectedOccurrence, OccurrenceStatus, RecurringRule


@dataclass(frozen=True, slots=True)
class PlannedOccurrence:
    id: UUID
    rule_id: UUID
    due_on: date
    type: OperationType
    amount: Decimal
    description: str | None
    account_id: UUID
    destination_account_id: UUID | None
    status: OccurrenceStatus


@dataclass(frozen=True, slots=True)
class ForecastScheduleSnapshot:
    occurrences: list[PlannedOccurrence]
    overdue_count: int


def forecast_schedule_snapshot(
    session: Session,
    *,
    today: date,
    due_to: date,
    account_id: UUID | None,
) -> ForecastScheduleSnapshot:
    """Lock and return one consistent actionable schedule snapshot.

    The shared row locks serialize confirmation, cancellation and postponement
    until the caller has read the ledger balance in the same transaction. This
    prevents a confirming occurrence from appearing in both actual and planned
    money in one forecast.
    """
    conditions = [
        ExpectedOccurrence.due_on <= due_to,
        ExpectedOccurrence.status.in_({OccurrenceStatus.PENDING, OccurrenceStatus.POSTPONED}),
    ]
    if account_id is not None:
        conditions.append(
            or_(
                ExpectedOccurrence.account_id == account_id,
                ExpectedOccurrence.destination_account_id == account_id,
            )
        )
    occurrences = session.scalars(
        select(ExpectedOccurrence)
        .where(*conditions)
        .order_by(
            ExpectedOccurrence.rule_id,
            ExpectedOccurrence.scheduled_on,
            ExpectedOccurrence.id,
        )
        .with_for_update(read=True)
    ).all()
    planned = sorted(
        [
            PlannedOccurrence(
                id=item.id,
                rule_id=item.rule_id,
                due_on=item.due_on,
                type=item.type,
                amount=Decimal(item.amount),
                description=item.description,
                account_id=item.account_id,
                destination_account_id=item.destination_account_id,
                status=item.status,
            )
            for item in occurrences
            if item.due_on >= today
        ],
        key=lambda item: (item.due_on, item.id),
    )
    return ForecastScheduleSnapshot(
        occurrences=planned,
        overdue_count=sum(item.due_on < today for item in occurrences),
    )


def account_has_schedule_reference(session: Session, account_id: UUID) -> bool:
    return (
        session.scalar(
            select(RecurringRule.id)
            .where(
                or_(
                    RecurringRule.account_id == account_id,
                    RecurringRule.destination_account_id == account_id,
                )
            )
            .limit(1)
        )
        is not None
        or session.scalar(
            select(ExpectedOccurrence.id)
            .where(
                or_(
                    ExpectedOccurrence.account_id == account_id,
                    ExpectedOccurrence.destination_account_id == account_id,
                )
            )
            .limit(1)
        )
        is not None
    )


def category_has_schedule_reference(session: Session, category_id: UUID) -> bool:
    return (
        session.scalar(
            select(RecurringRule.id).where(RecurringRule.category_id == category_id).limit(1)
        )
        is not None
        or session.scalar(
            select(ExpectedOccurrence.id)
            .where(ExpectedOccurrence.category_id == category_id)
            .limit(1)
        )
        is not None
    )


def has_schedule_data(session: Session) -> bool:
    """Return whether calendar-date semantics have become persistent."""
    return session.scalar(select(RecurringRule.id).limit(1)) is not None


__all__ = [
    "ForecastScheduleSnapshot",
    "OccurrenceStatus",
    "PlannedOccurrence",
    "account_has_schedule_reference",
    "category_has_schedule_reference",
    "forecast_schedule_snapshot",
    "has_schedule_data",
]
