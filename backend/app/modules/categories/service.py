from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.categories.models import Category, CategoryType

CATEGORY_TREE_LOCK_ID = 0x4845524D45534341


class CategoryNotFoundError(RuntimeError):
    pass


class InvalidCategoryParentError(RuntimeError):
    pass


class CategoryHasChildrenError(RuntimeError):
    pass


def lock_category_tree(session: Session) -> None:
    """Serialize tree reads that guard mutations and new operation references."""
    session.execute(select(func.pg_advisory_xact_lock(CATEGORY_TREE_LOCK_ID)))


def list_categories(session: Session, *, include_archived: bool) -> list[Category]:
    query = select(Category).order_by(Category.type, Category.name, Category.id)
    if not include_archived:
        query = query.where(Category.archived_at.is_(None))
    return list(session.scalars(query))


def get_category(session: Session, category_id: UUID) -> Category:
    category = session.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError
    return category


def _validate_parent(
    session: Session,
    *,
    category_id: UUID | None,
    parent_id: UUID | None,
    type: CategoryType,
) -> None:
    if parent_id is None:
        return
    parent = session.get(Category, parent_id)
    if (
        parent is None
        or parent.archived_at is not None
        or parent.type != type
        or parent.parent_id is not None
        or parent.id == category_id
    ):
        raise InvalidCategoryParentError


def create_category(
    session: Session,
    *,
    type: CategoryType,
    name: str,
    description: str | None,
    parent_id: UUID | None,
) -> Category:
    lock_category_tree(session)
    _validate_parent(session, category_id=None, parent_id=parent_id, type=type)
    now = datetime.now(UTC)
    category = Category(
        type=type,
        name=name,
        description=description,
        parent_id=parent_id,
        created_at=now,
        updated_at=now,
    )
    session.add(category)
    session.flush()
    return category


def update_category(
    session: Session,
    category_id: UUID,
    *,
    type: CategoryType,
    name: str,
    description: str | None,
    parent_id: UUID | None,
) -> Category:
    lock_category_tree(session)
    category = get_category(session, category_id)
    children = session.scalars(select(Category).where(Category.parent_id == category_id)).all()
    if parent_id is not None and children:
        raise InvalidCategoryParentError
    _validate_parent(session, category_id=category_id, parent_id=parent_id, type=type)
    if any(child.type != type for child in children):
        raise InvalidCategoryParentError
    category.type = type
    category.name = name
    category.description = description
    category.parent_id = parent_id
    category.updated_at = datetime.now(UTC)
    return category


def set_category_archived(session: Session, category_id: UUID, *, archived: bool) -> Category:
    lock_category_tree(session)
    category = get_category(session, category_id)
    if archived:
        active_child = session.scalar(
            select(Category.id)
            .where(Category.parent_id == category_id, Category.archived_at.is_(None))
            .limit(1)
        )
        if active_child is not None:
            raise CategoryHasChildrenError
    elif category.parent_id is not None:
        parent = get_category(session, category.parent_id)
        if parent.archived_at is not None:
            raise InvalidCategoryParentError
    category.archived_at = datetime.now(UTC) if archived else None
    category.updated_at = datetime.now(UTC)
    return category
