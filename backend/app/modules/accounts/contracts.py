"""Public account commands and references used by cross-module use cases."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.accounts.models import Account, AccountType
from app.modules.accounts.service import AccountNotFoundError, create_account, get_account


class AccountReferenceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AccountReference:
    id: UUID
    archived: bool


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    id: UUID
    name: str
    archived: bool


def create_account_identity(
    session: Session,
    *,
    type: AccountType,
    name: str,
    description: str | None,
) -> UUID:
    return create_account(session, type=type, name=name, description=description).id


def delete_account_identity(session: Session, account_id: UUID) -> None:
    session.delete(get_account(session, account_id))


def lock_account_identity(session: Session, account_id: UUID) -> AccountReference:
    """Lock one account before a lifecycle decision that depends on ledger history."""
    account = session.scalar(select(Account).where(Account.id == account_id).with_for_update())
    if account is None:
        raise AccountNotFoundError
    return AccountReference(account.id, account.archived_at is not None)


def lock_account_references(
    session: Session,
    account_ids: set[UUID],
    *,
    allow_archived_ids: set[UUID] | None = None,
) -> dict[UUID, AccountReference]:
    """Lock account identities in deterministic order and validate operation use."""
    allowed = allow_archived_ids or set()
    accounts = session.scalars(
        select(Account).where(Account.id.in_(account_ids)).order_by(Account.id).with_for_update()
    ).all()
    if len(accounts) != len(account_ids):
        raise AccountReferenceError
    references = {
        account.id: AccountReference(account.id, account.archived_at is not None)
        for account in accounts
    }
    if any(reference.archived and reference.id not in allowed for reference in references.values()):
        raise AccountReferenceError
    return references


def account_names(session: Session, account_ids: set[UUID]) -> dict[UUID, str]:
    rows = session.execute(
        select(Account.id, Account.name).where(Account.id.in_(account_ids))
    ).all()
    return {account_id: name for account_id, name in rows}


def list_account_identities(session: Session) -> list[AccountIdentity]:
    return [
        AccountIdentity(account.id, account.name, account.archived_at is not None)
        for account in session.scalars(
            select(Account).order_by(Account.archived_at.nulls_first(), Account.name, Account.id)
        ).all()
    ]


__all__ = [
    "AccountReferenceError",
    "AccountType",
    "account_names",
    "list_account_identities",
    "create_account_identity",
    "delete_account_identity",
    "lock_account_identity",
    "lock_account_references",
]
