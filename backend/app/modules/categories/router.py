from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.database import DatabaseSession
from app.modules.categories.models import Category
from app.modules.categories.schemas import (
    CategoryCreateRequest,
    CategoryResponse,
    CategoryUpdateRequest,
)
from app.modules.categories.service import (
    CategoryHasChildrenError,
    CategoryNotFoundError,
    InvalidCategoryParentError,
    create_category,
    list_categories,
    set_category_archived,
    update_category,
)

read_router = APIRouter(prefix="/categories", tags=["categories"])
write_router = APIRouter(prefix="/categories", tags=["categories"])


def _response(category: Category) -> CategoryResponse:
    return CategoryResponse(
        id=category.id,
        type=category.type,
        name=category.name,
        description=category.description,
        parent_id=category.parent_id,
        archived=category.archived_at is not None,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def _not_found(error: CategoryNotFoundError) -> HTTPException:
    return HTTPException(
        status_code=404, detail={"code": "category_not_found", "message": "Category not found"}
    )


def _invalid_parent(error: InvalidCategoryParentError) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={"code": "invalid_category_parent", "message": "Invalid category parent"},
    )


@read_router.get("", response_model=list[CategoryResponse])
def read_categories(
    session: DatabaseSession, include_archived: bool = Query(default=True)
) -> list[CategoryResponse]:
    return [
        _response(category)
        for category in list_categories(session, include_archived=include_archived)
    ]


@write_router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def add_category(payload: CategoryCreateRequest, session: DatabaseSession) -> CategoryResponse:
    try:
        return _response(create_category(session, **payload.model_dump()))
    except InvalidCategoryParentError as error:
        raise _invalid_parent(error) from error


@write_router.put("/{category_id}", response_model=CategoryResponse)
def replace_category(
    category_id: UUID, payload: CategoryUpdateRequest, session: DatabaseSession
) -> CategoryResponse:
    try:
        return _response(update_category(session, category_id, **payload.model_dump()))
    except CategoryNotFoundError as error:
        raise _not_found(error) from error
    except InvalidCategoryParentError as error:
        raise _invalid_parent(error) from error


@write_router.post("/{category_id}/archive", response_model=CategoryResponse)
def archive_category(category_id: UUID, session: DatabaseSession) -> CategoryResponse:
    try:
        return _response(set_category_archived(session, category_id, archived=True))
    except CategoryNotFoundError as error:
        raise _not_found(error) from error
    except CategoryHasChildrenError as error:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "category_has_active_children",
                "message": "Archive active subcategories first",
            },
        ) from error


@write_router.post("/{category_id}/restore", response_model=CategoryResponse)
def restore_category(category_id: UUID, session: DatabaseSession) -> CategoryResponse:
    try:
        return _response(set_category_archived(session, category_id, archived=False))
    except CategoryNotFoundError as error:
        raise _not_found(error) from error
    except InvalidCategoryParentError as error:
        raise _invalid_parent(error) from error
