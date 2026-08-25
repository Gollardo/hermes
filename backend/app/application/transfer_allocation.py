from sqlalchemy.orm import Session

from app.modules.funds.contracts import (
    AllocationCreateRequest,
    AllocationItem,
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
    """Move physical money, then reserve percentage shares or one selected fund atomically."""
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
    if payload.fund_id is None:
        preview = locked_percentage_allocation_preview_with_free_balance(
            session, payload.destination_account_id, payload.amount, free
        )
        positive_allocations = [item for item in preview.allocations if item.amount > 0]
    else:
        positive_allocations = [AllocationItem(fund_id=payload.fund_id, amount=payload.amount)]
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
        caused_by_operation_id=operation_id,
    )
    return TransferAllocationResponse(
        operation_id=operation_id,
        allocation=event_response(session, event),
    )
