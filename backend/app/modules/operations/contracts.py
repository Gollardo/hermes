from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.operations.models import AccountMovement, FinancialOperation, OperationType


@dataclass(frozen=True, slots=True)
class OperationHistoryReference:
    id: UUID
    type: OperationType
    occurred_on: date
    description: str | None
    created_at: datetime


def post_initial_balance(
    session: Session, *, account_id: UUID, amount: Decimal, occurred_on: date
) -> None:
    """Post the immutable initial-balance fact inside the caller's transaction."""
    if amount == 0:
        return
    now = datetime.now(UTC)
    operation = FinancialOperation(
        type=OperationType.BALANCE_ADJUSTMENT,
        description=None,
        reason="Initial balance",
        occurred_on=occurred_on,
        created_at=now,
        updated_at=now,
        version=1,
    )
    session.add(operation)
    session.flush()
    session.add(AccountMovement(operation_id=operation.id, account_id=account_id, amount=amount))


def account_balance(session: Session, account_id: UUID) -> Decimal:
    value = session.scalar(
        select(func.coalesce(func.sum(AccountMovement.amount), 0)).where(
            AccountMovement.account_id == account_id
        )
    )
    return Decimal(0) if value is None else Decimal(value)


def account_has_history(session: Session, account_id: UUID) -> bool:
    return (
        session.scalar(
            select(AccountMovement.id).where(AccountMovement.account_id == account_id).limit(1)
        )
        is not None
    )


def category_has_history(session: Session, category_id: UUID) -> bool:
    return (
        session.scalar(
            select(FinancialOperation.id)
            .where(FinancialOperation.category_id == category_id)
            .limit(1)
        )
        is not None
    )


def operation_history_references(
    session: Session, operation_ids: set[UUID]
) -> dict[UUID, OperationHistoryReference]:
    return {
        operation.id: OperationHistoryReference(
            id=operation.id,
            type=operation.type,
            occurred_on=operation.occurred_on,
            description=operation.description,
            created_at=operation.created_at,
        )
        for operation in session.scalars(
            select(FinancialOperation).where(FinancialOperation.id.in_(operation_ids))
        ).all()
    }
