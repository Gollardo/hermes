from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.operations.models import AccountMovement, FinancialOperation, OperationType


def post_initial_balance(session: Session, *, account_id: UUID, amount: Decimal) -> None:
    """Post the immutable initial-balance fact inside the caller's transaction."""
    if amount == 0:
        return
    now = datetime.now(UTC)
    operation = FinancialOperation(
        type=OperationType.BALANCE_ADJUSTMENT,
        description="Initial balance",
        occurred_at=now,
        created_at=now,
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
