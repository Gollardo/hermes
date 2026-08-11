from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.accounts.contracts import (
    AccountType,
    create_account_identity,
    delete_account_identity,
    lock_account_identity,
)
from app.modules.funds.contracts import account_has_fund_history
from app.modules.operations.contracts import account_has_history, post_initial_balance
from app.modules.settings.contracts import application_timezone, lock_base_currency


class AccountHasHistoryError(RuntimeError):
    pass


def calendar_date_at(instant: datetime, timezone: str) -> date:
    """Resolve a financial calendar date in the configured application timezone."""
    return instant.astimezone(ZoneInfo(timezone)).date()


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
    occurred_on = calendar_date_at(datetime.now(UTC), application_timezone(session))
    account_id = create_account_identity(session, type=type, name=name, description=description)
    post_initial_balance(
        session, account_id=account_id, amount=initial_balance, occurred_on=occurred_on
    )
    return account_id


def delete_account_without_history(session: Session, account_id: UUID) -> None:
    lock_account_identity(session, account_id)
    if account_has_history(session, account_id) or account_has_fund_history(session, account_id):
        raise AccountHasHistoryError
    delete_account_identity(session, account_id)
