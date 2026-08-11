"""Public scheduling references used by cross-module application use cases."""

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.scheduling.models import ExpectedOccurrence, RecurringRule


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
    "account_has_schedule_reference",
    "category_has_schedule_reference",
    "has_schedule_data",
]
