"""Public virtual-fund contracts used by cross-module financial use cases."""

from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.funds.schemas import (
    AllocationCreateRequest,
    AllocationItem,
    AllocationPreviewResponse,
    FundCreateRequest,
    FundEventResponse,
    FundHistoryResponse,
    FundMovementResponse,
    FundResponse,
    FundSummaryResponse,
    FundTransferCreateRequest,
    RedistributionCreateRequest,
    TransferAllocationCreateRequest,
    TransferAllocationResponse,
)
from app.modules.funds.service import (
    FundAllocationUnavailableError,
    FundArchivedMutationError,
    FundBalanceError,
    FundCoverageError,
    FundNotFoundError,
    account_has_fund_history,
    allocation_preview_with_free_balance,
    create_allocation_with_free_balance,
    create_fund,
    create_fund_transfer,
    create_redistribution_with_physical_balances,
    event_response,
    event_responses,
    fund_names,
    get_fund_response,
    history_source_ids,
    locked_percentage_allocation_preview_with_free_balance,
    operation_fund_movements,
    replace_operation_movements,
    reserved_balance,
    reserved_balances,
    summary_with_physical_balances,
    validate_account_coverage,
)


def create_fund_definition(
    session: Session,
    *,
    name: str,
    description: str | None,
    percentage: Decimal,
    target_amount: Decimal | None,
) -> UUID:
    """Create a Funds-owned definition without exposing its private model."""
    return create_fund(
        session,
        name=name,
        description=description,
        percentage=percentage,
        target_amount=target_amount,
    ).id


def fund_response(session: Session, fund_id: UUID) -> FundResponse:
    return get_fund_response(session, fund_id)


__all__ = [
    "FundBalanceError",
    "FundArchivedMutationError",
    "FundAllocationUnavailableError",
    "FundCoverageError",
    "FundNotFoundError",
    "AllocationCreateRequest",
    "AllocationItem",
    "AllocationPreviewResponse",
    "FundEventResponse",
    "FundCreateRequest",
    "FundTransferCreateRequest",
    "FundHistoryResponse",
    "FundMovementResponse",
    "FundResponse",
    "FundSummaryResponse",
    "RedistributionCreateRequest",
    "TransferAllocationCreateRequest",
    "TransferAllocationResponse",
    "account_has_fund_history",
    "allocation_preview_with_free_balance",
    "create_allocation_with_free_balance",
    "create_fund_definition",
    "create_fund_transfer",
    "create_redistribution_with_physical_balances",
    "event_response",
    "event_responses",
    "operation_fund_movements",
    "fund_names",
    "fund_response",
    "history_source_ids",
    "locked_percentage_allocation_preview_with_free_balance",
    "replace_operation_movements",
    "reserved_balance",
    "reserved_balances",
    "summary_with_physical_balances",
    "validate_account_coverage",
]
