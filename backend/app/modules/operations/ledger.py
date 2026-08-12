"""Operations-owned ledger queries shared by service and public contracts."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.operations.models import AccountMovement


def account_balance(session: Session, account_id: UUID) -> Decimal:
    value = session.scalar(
        select(func.coalesce(func.sum(AccountMovement.amount), 0)).where(
            AccountMovement.account_id == account_id
        )
    )
    return Decimal(0) if value is None else Decimal(value)


def account_balances(session: Session, account_ids: set[UUID]) -> dict[UUID, Decimal]:
    """Return exact ledger-derived balances, including zero-balance accounts."""
    if not account_ids:
        return {}
    rows = session.execute(
        select(AccountMovement.account_id, func.sum(AccountMovement.amount))
        .where(AccountMovement.account_id.in_(account_ids))
        .group_by(AccountMovement.account_id)
    ).all()
    balances = {account_id: Decimal(0) for account_id in account_ids}
    balances.update({account_id: Decimal(amount) for account_id, amount in rows})
    return balances
