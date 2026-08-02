from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from app.modules.accounts.models import AccountType


def parse_money(value: object) -> Decimal:
    if isinstance(value, float):
        raise ValueError("binary floating-point money is not accepted")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError("invalid monetary value") from error
    exponent = amount.as_tuple().exponent
    if not amount.is_finite() or not isinstance(exponent, int) or exponent < -4:
        raise ValueError("money must be finite with at most 4 decimal places")
    if abs(amount) > Decimal("9999999999999999.9999"):
        raise ValueError("money is outside the supported range")
    return amount


Money = Annotated[Decimal, BeforeValidator(parse_money)]


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
