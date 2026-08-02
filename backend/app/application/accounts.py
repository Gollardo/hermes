from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.accounts.contracts import (
    AccountType,
    create_account_identity,
    delete_account_identity,
)
from app.modules.operations.contracts import account_has_history, post_initial_balance
from app.modules.settings.contracts import lock_base_currency


class AccountHasHistoryError(RuntimeError):
    pass


def create_account_with_initial_balance(
    session: Session,
    *,
    type: AccountType,
    name: str,
    description: str | None,
    initial_balance: Decimal,
) -> UUID:
    """Coordinate the first account and its ledger fact in one transaction."""
    lock_base_currency(session)
    account_id = create_account_identity(session, type=type, name=name, description=description)
    post_initial_balance(session, account_id=account_id, amount=initial_balance)
    return account_id


def delete_account_without_history(session: Session, account_id: UUID) -> None:
    if account_has_history(session, account_id):
        raise AccountHasHistoryError
    delete_account_identity(session, account_id)
