from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models import Account, AccountType


class AccountNotFoundError(RuntimeError):
    pass


def list_accounts(session: Session, *, include_archived: bool) -> list[Account]:
    query = select(Account).order_by(Account.archived_at.nulls_first(), Account.name, Account.id)
    if not include_archived:
        query = query.where(Account.archived_at.is_(None))
    return list(session.scalars(query))


def get_account(session: Session, account_id: UUID) -> Account:
    account = session.get(Account, account_id)
    if account is None:
        raise AccountNotFoundError
    return account


def create_account(
    session: Session,
    *,
    type: AccountType,
    name: str,
    description: str | None,
) -> Account:
    now = datetime.now(UTC)
    account = Account(type=type, name=name, description=description, created_at=now, updated_at=now)
    session.add(account)
    session.flush()
    return account


def update_account(
    session: Session, account_id: UUID, *, type: AccountType, name: str, description: str | None
) -> Account:
    account = get_account(session, account_id)
    account.type = type
    account.name = name
    account.description = description
    account.updated_at = datetime.now(UTC)
    return account


def set_account_archived(session: Session, account_id: UUID, *, archived: bool) -> Account:
    account = get_account(session, account_id)
    account.archived_at = datetime.now(UTC) if archived else None
    account.updated_at = datetime.now(UTC)
    return account
