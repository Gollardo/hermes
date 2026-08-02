from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.categories.models import Category, CategoryType
from app.modules.categories.service import lock_category_tree


class CategoryReferenceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CategoryReference:
    id: UUID
    type: CategoryType
    archived: bool


def validate_category_reference(
    session: Session,
    category_id: UUID,
    *,
    expected_type: CategoryType,
    allow_archived: bool = False,
) -> CategoryReference:
    """Public operation-facing validation; history may explicitly allow archived nodes."""
    lock_category_tree(session)
    category = session.get(Category, category_id)
    if category is None or category.type != expected_type:
        raise CategoryReferenceError
    if category.archived_at is not None and not allow_archived:
        raise CategoryReferenceError
    return CategoryReference(
        id=category.id,
        type=category.type,
        archived=category.archived_at is not None,
    )
