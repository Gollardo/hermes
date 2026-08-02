from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.categories.models import Category, CategoryType
from app.modules.categories.service import lock_category_tree, update_category
from app.modules.operations.contracts import category_has_history


def update_category_preserving_history(
    session: Session,
    category_id: UUID,
    *,
    type: CategoryType,
    name: str,
    description: str | None,
    parent_id: UUID | None,
) -> Category:
    """Coordinate category lifecycle with operation-owned classification history."""
    lock_category_tree(session)
    return update_category(
        session,
        category_id,
        type=type,
        name=name,
        description=description,
        parent_id=parent_id,
        has_financial_history=category_has_history(session, category_id),
    )
