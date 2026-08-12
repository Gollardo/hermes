from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.operations.ledger import account_balance, account_balances
from app.modules.operations.models import AccountMovement, FinancialOperation, OperationType
from app.modules.operations.schemas import OperationCreateRequest
from app.modules.operations.service import InsufficientBalanceError, create_operation


@dataclass(frozen=True, slots=True)
class OperationHistoryReference:
    id: UUID
    type: OperationType
    occurred_on: date
    description: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ScheduledOperationDraft:
    type: OperationType
    occurred_on: date
    amount: Decimal
    description: str | None
    account_id: UUID
    destination_account_id: UUID | None
    category_id: UUID | None


@dataclass(frozen=True, slots=True)
class PhysicalTransferDraft:
    occurred_on: date
    amount: Decimal
    description: str | None
    source_account_id: UUID
    destination_account_id: UUID


def post_physical_transfer(session: Session, draft: PhysicalTransferDraft) -> UUID:
    """Post one transfer inside the caller's transaction and return its identity."""
    operation = create_operation(
        session,
        OperationCreateRequest(
            type=OperationType.TRANSFER,
            occurred_on=draft.occurred_on,
            amount=draft.amount,
            description=draft.description,
            account_id=draft.source_account_id,
            destination_account_id=draft.destination_account_id,
        ),
    )
    return operation.id


def post_scheduled_operation(session: Session, draft: ScheduledOperationDraft) -> UUID:
    """Post one occurrence through Operations inside the caller's transaction."""
    operation = create_operation(
        session,
        OperationCreateRequest(
            type=draft.type,
            occurred_on=draft.occurred_on,
            amount=draft.amount,
            description=draft.description,
            account_id=draft.account_id,
            destination_account_id=draft.destination_account_id,
            category_id=draft.category_id,
        ),
    )
    return operation.id


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


__all__ = [
    "InsufficientBalanceError",
    "OperationHistoryReference",
    "OperationType",
    "PhysicalTransferDraft",
    "ScheduledOperationDraft",
    "account_balance",
    "account_balances",
    "account_has_history",
    "category_has_history",
    "operation_history_references",
    "post_initial_balance",
    "post_physical_transfer",
    "post_scheduled_operation",
]
