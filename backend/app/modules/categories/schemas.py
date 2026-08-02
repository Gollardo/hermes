from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.modules.categories.models import CategoryType


class CategoryCreateRequest(BaseModel):
    type: CategoryType
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    parent_id: UUID | None = None

    @field_validator("name")
    @classmethod
    def normalized_name(cls, value: str) -> str:
        if not (name := value.strip()):
            raise ValueError("name must not be blank")
        return name


class CategoryUpdateRequest(CategoryCreateRequest):
    pass


class CategoryResponse(BaseModel):
    id: UUID
    type: CategoryType
    name: str
    description: str | None
    parent_id: UUID | None
    archived: bool
    created_at: datetime
    updated_at: datetime
