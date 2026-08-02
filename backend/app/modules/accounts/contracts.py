"""Public account commands used by cross-module application use cases."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.accounts.models import AccountType
from app.modules.accounts.service import create_account, get_account


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


__all__ = ["AccountType", "create_account_identity", "delete_account_identity"]
