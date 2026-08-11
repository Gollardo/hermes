from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import Money
from app.modules.accounts.models import AccountType


class AccountCreateRequest(BaseModel):
    type: AccountType
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    initial_balance: Money = Decimal("0")

    @field_validator("name")
    @classmethod
    def normalized_name(cls, value: str) -> str:
        if not (name := value.strip()):
            raise ValueError("name must not be blank")
        return name

    @field_validator("initial_balance")
    @classmethod
    def non_negative_initial_balance(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("initial balance cannot be negative")
        return value


class AccountUpdateRequest(BaseModel):
    type: AccountType
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def normalized_name(cls, value: str) -> str:
        if not (name := value.strip()):
            raise ValueError("name must not be blank")
        return name


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: AccountType
    name: str
    description: str | None
    balance: str
    archived: bool
    created_at: datetime
    updated_at: datetime
