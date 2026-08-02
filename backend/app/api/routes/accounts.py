from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.application.accounts import (
    AccountHasHistoryError,
    create_account_with_initial_balance,
    delete_account_without_history,
)
from app.core.database import DatabaseSession
from app.modules.accounts.models import Account
from app.modules.accounts.schemas import AccountCreateRequest, AccountResponse, AccountUpdateRequest
from app.modules.accounts.service import (
    AccountNotFoundError,
    get_account,
    list_accounts,
    set_account_archived,
    update_account,
)
from app.modules.operations.contracts import account_balance

read_router = APIRouter(prefix="/accounts", tags=["accounts"])
write_router = APIRouter(prefix="/accounts", tags=["accounts"])


def _response(session: DatabaseSession, account: Account) -> AccountResponse:
    return AccountResponse(
        id=account.id,
        type=account.type,
        name=account.name,
        description=account.description,
        balance=format(account_balance(session, account.id), "f"),
        archived=account.archived_at is not None,
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


def _not_found(error: AccountNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=404, detail={"code": "account_not_found", "message": "Account not found"}
    )


@read_router.get("", response_model=list[AccountResponse])
def read_accounts(
    session: DatabaseSession, include_archived: bool = Query(default=True)
) -> list[AccountResponse]:
    return [
        _response(session, account)
        for account in list_accounts(session, include_archived=include_archived)
    ]


@read_router.get("/{account_id}", response_model=AccountResponse)
def read_account(account_id: UUID, session: DatabaseSession) -> AccountResponse:
    try:
        return _response(session, get_account(session, account_id))
    except AccountNotFoundError as error:
        raise _not_found(error) from error


@write_router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
def add_account(payload: AccountCreateRequest, session: DatabaseSession) -> AccountResponse:
    account_id = create_account_with_initial_balance(session, **payload.model_dump())
    return _response(session, get_account(session, account_id))


@write_router.put("/{account_id}", response_model=AccountResponse)
def replace_account(
    account_id: UUID, payload: AccountUpdateRequest, session: DatabaseSession
) -> AccountResponse:
    try:
        return _response(session, update_account(session, account_id, **payload.model_dump()))
    except AccountNotFoundError as error:
        raise _not_found(error) from error


@write_router.post("/{account_id}/archive", response_model=AccountResponse)
def archive_account(account_id: UUID, session: DatabaseSession) -> AccountResponse:
    try:
        return _response(session, set_account_archived(session, account_id, archived=True))
    except AccountNotFoundError as error:
        raise _not_found(error) from error


@write_router.post("/{account_id}/restore", response_model=AccountResponse)
def restore_account(account_id: UUID, session: DatabaseSession) -> AccountResponse:
    try:
        return _response(session, set_account_archived(session, account_id, archived=False))
    except AccountNotFoundError as error:
        raise _not_found(error) from error


@write_router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_account(account_id: UUID, session: DatabaseSession) -> Response:
    try:
        delete_account_without_history(session, account_id)
    except AccountNotFoundError as error:
        raise _not_found(error) from error
    except AccountHasHistoryError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "account_has_history",
                "message": "An account with financial history cannot be deleted",
            },
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
