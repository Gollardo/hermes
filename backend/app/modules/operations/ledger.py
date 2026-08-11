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
