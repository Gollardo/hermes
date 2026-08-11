from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.application.funds import (
    allocate_funds,
    fund_history,
    fund_summary,
    preview_allocation,
    redistribute_fund,
)
from app.core.database import DatabaseSession
from app.modules.accounts.contracts import AccountReferenceError
from app.modules.funds.schemas import (
    AllocationCreateRequest,
    AllocationPreviewRequest,
    AllocationPreviewResponse,
    FundCreateRequest,
    FundEventResponse,
    FundHistoryResponse,
    FundLifecycleRequest,
    FundResponse,
    FundSummaryResponse,
    FundUpdateRequest,
    RedistributionCreateRequest,
)
from app.modules.funds.service import (
    FundArchiveBalanceError,
    FundBalanceError,
    FundConflictError,
    FundCoverageError,
    FundNotFoundError,
    FundPercentageLimitError,
    archive_fund,
    create_fund,
    get_fund_response,
    list_funds,
    update_fund,
)

read_router = APIRouter(prefix="/funds", tags=["funds"])
write_router = APIRouter(prefix="/funds", tags=["funds"])


def _raise_domain_error(error: RuntimeError) -> None:
    mapping: list[tuple[type[RuntimeError], int, str, str]] = [
        (FundNotFoundError, 404, "fund_not_found", "Fund is unavailable"),
        (FundConflictError, 409, "fund_conflict", "Fund was changed"),
        (FundPercentageLimitError, 409, "fund_percentage_limit", "Active percentages exceed 100"),
        (
            FundArchiveBalanceError,
            409,
            "fund_has_balance",
            "Fund must have zero balance before archive",
        ),
        (FundBalanceError, 409, "insufficient_fund_balance", "Insufficient fund balance"),
        (
            FundCoverageError,
            409,
            "insufficient_free_balance",
            "Fund reservations exceed physical balance",
        ),
        (AccountReferenceError, 409, "invalid_account_reference", "Account is unavailable"),
    ]
    for error_type, status_code, code, message in mapping:
        if isinstance(error, error_type):
            raise HTTPException(status_code, detail={"code": code, "message": message})
    raise error


@read_router.get("", response_model=list[FundResponse])
def read_funds(session: DatabaseSession, include_archived: bool = True) -> list[FundResponse]:
    return list_funds(session, include_archived=include_archived)


@read_router.get("/summary", response_model=FundSummaryResponse)
def read_summary(session: DatabaseSession) -> FundSummaryResponse:
    return fund_summary(session)


@read_router.get("/history", response_model=FundHistoryResponse)
def read_history(
    session: DatabaseSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    fund_id: UUID | None = None,
    account_id: UUID | None = None,
) -> FundHistoryResponse:
    return fund_history(
        session, page=page, page_size=page_size, fund_id=fund_id, account_id=account_id
    )


@write_router.post("", response_model=FundResponse, status_code=status.HTTP_201_CREATED)
def add_fund(payload: FundCreateRequest, session: DatabaseSession) -> FundResponse:
    try:
        fund = create_fund(
            session,
            name=payload.name,
            description=payload.description,
            percentage=payload.allocation_percentage,
        )
        return get_fund_response(session, fund.id)
    except FundPercentageLimitError as error:
        _raise_domain_error(error)
        raise AssertionError from error


@write_router.put("/{fund_id}", response_model=FundResponse)
def replace_fund(
    fund_id: UUID, payload: FundUpdateRequest, session: DatabaseSession
) -> FundResponse:
    try:
        return get_fund_response(session, update_fund(session, fund_id, payload).id)
    except (FundNotFoundError, FundConflictError, FundPercentageLimitError) as error:
        _raise_domain_error(error)
        raise AssertionError from error


@write_router.post("/{fund_id}/archive", response_model=FundResponse)
def archive(fund_id: UUID, payload: FundLifecycleRequest, session: DatabaseSession) -> FundResponse:
    try:
        fund = archive_fund(session, fund_id, restore=False, expected_version=payload.version)
        return get_fund_response(session, fund.id)
    except (FundNotFoundError, FundConflictError, FundArchiveBalanceError) as error:
        _raise_domain_error(error)
        raise AssertionError from error


@write_router.post("/{fund_id}/restore", response_model=FundResponse)
def restore(fund_id: UUID, payload: FundLifecycleRequest, session: DatabaseSession) -> FundResponse:
    try:
        fund = archive_fund(session, fund_id, restore=True, expected_version=payload.version)
        return get_fund_response(session, fund.id)
    except (FundNotFoundError, FundConflictError, FundPercentageLimitError) as error:
        _raise_domain_error(error)
        raise AssertionError from error


@write_router.post("/allocation-preview", response_model=AllocationPreviewResponse)
def preview(
    payload: AllocationPreviewRequest, session: DatabaseSession
) -> AllocationPreviewResponse:
    try:
        return preview_allocation(session, payload.account_id, payload.amount)
    except AccountReferenceError as error:
        _raise_domain_error(error)
        raise AssertionError from error


@write_router.post(
    "/allocations", response_model=FundEventResponse, status_code=status.HTTP_201_CREATED
)
def allocate(payload: AllocationCreateRequest, session: DatabaseSession) -> FundEventResponse:
    try:
        return allocate_funds(session, payload)
    except (AccountReferenceError, FundNotFoundError, FundCoverageError, FundBalanceError) as error:
        _raise_domain_error(error)
        raise AssertionError from error


@write_router.post(
    "/redistributions", response_model=FundEventResponse, status_code=status.HTTP_201_CREATED
)
def redistribute(
    payload: RedistributionCreateRequest, session: DatabaseSession
) -> FundEventResponse:
    try:
        return redistribute_fund(session, payload)
    except (AccountReferenceError, FundNotFoundError, FundCoverageError, FundBalanceError) as error:
        _raise_domain_error(error)
        raise AssertionError from error
