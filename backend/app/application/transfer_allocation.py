from sqlalchemy.orm import Session

from app.modules.funds.contracts import (
    AllocationCreateRequest,
    FundAllocationUnavailableError,
    TransferAllocationCreateRequest,
    TransferAllocationResponse,
    create_allocation_with_free_balance,
    event_response,
    locked_percentage_allocation_preview_with_free_balance,
    reserved_balance,
)
from app.modules.operations.contracts import (
    PhysicalTransferDraft,
    account_balance,
    post_physical_transfer,
)


def transfer_and_allocate(
    session: Session, payload: TransferAllocationCreateRequest
) -> TransferAllocationResponse:
    """Move physical money, then reserve its locked percentage shares atomically."""
    operation_id = post_physical_transfer(
        session,
        PhysicalTransferDraft(
            occurred_on=payload.occurred_on,
            amount=payload.amount,
            description=payload.description,
            source_account_id=payload.source_account_id,
            destination_account_id=payload.destination_account_id,
        ),
    )
    free = account_balance(session, payload.destination_account_id) - reserved_balance(
        session, payload.destination_account_id
    )
    preview = locked_percentage_allocation_preview_with_free_balance(
        session, payload.destination_account_id, payload.amount, free
    )
    positive_allocations = [item for item in preview.allocations if item.amount > 0]
    if not positive_allocations:
        raise FundAllocationUnavailableError
    event = create_allocation_with_free_balance(
        session,
        AllocationCreateRequest(
            account_id=payload.destination_account_id,
            amount=payload.amount,
            occurred_on=payload.occurred_on,
            description=payload.description,
            allocations=positive_allocations,
        ),
        free,
    )
    return TransferAllocationResponse(
        operation_id=operation_id,
        allocation=event_response(session, event),
    )
