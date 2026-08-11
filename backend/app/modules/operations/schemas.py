from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field, field_validator, model_validator

from app.modules.operations.models import OperationType


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


class OperationCreateRequest(BaseModel):
    type: OperationType
    occurred_on: date
    amount: Money
    description: str | None = Field(default=None, max_length=2000)
    reason: str | None = Field(default=None, max_length=2000)
    account_id: UUID
    destination_account_id: UUID | None = None
    category_id: UUID | None = None
    fund_id: UUID | None = None
    fund_amount: Money | None = None

    @field_validator("description", "reason")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        if self.type == OperationType.BALANCE_ADJUSTMENT:
            if self.amount == 0 or self.reason is None:
                raise ValueError("adjustment requires a non-zero amount and reason")
            if (
                self.category_id is not None
                or self.destination_account_id is not None
                or self.fund_id is not None
                or self.fund_amount is not None
            ):
                raise ValueError("adjustment cannot have category, destination account or fund")
            return self
        if self.amount <= 0:
            raise ValueError("ordinary operation amount must be positive")
        if self.type in {OperationType.INCOME, OperationType.EXPENSE}:
            if self.category_id is None or self.destination_account_id is not None:
                raise ValueError("income and expense require category and one account")
            if self.type == OperationType.INCOME and (
                self.fund_id is not None or self.fund_amount is not None
            ):
                raise ValueError("income allocation is an explicit fund action")
            if self.type == OperationType.EXPENSE and self.fund_amount is not None:
                raise ValueError("fund expense consumes the complete expense amount")
        elif self.type == OperationType.TRANSFER and (
            self.category_id is not None
            or self.destination_account_id is None
            or self.destination_account_id == self.account_id
        ):
            raise ValueError("transfer requires two different accounts and no category")
        if self.type == OperationType.TRANSFER:
            if (self.fund_id is None) != (self.fund_amount is None):
                raise ValueError("fund transfer requires fund and virtual amount together")
            if self.fund_amount is not None and (
                self.fund_amount <= 0 or self.fund_amount > self.amount
            ):
                raise ValueError("virtual amount must be positive and no greater than transfer")
        return self


class OperationUpdateRequest(OperationCreateRequest):
    version: int = Field(ge=1)


class MovementResponse(BaseModel):
    account_id: UUID
    account_name: str
    amount: str


class OperationFundMovementResponse(BaseModel):
    fund_id: UUID
    fund_name: str
    account_id: UUID
    account_name: str
    amount: str


class OperationResponse(BaseModel):
    id: UUID
    type: OperationType
    occurred_on: date
    amount: str
    description: str | None
    reason: str | None
    category_id: UUID | None
    category_name: str | None
    account_id: UUID
    destination_account_id: UUID | None
    movements: list[MovementResponse]
    fund_id: UUID | None
    fund_amount: str | None
    fund_movements: list[OperationFundMovementResponse]
    version: int
    created_at: datetime
    updated_at: datetime


class OperationPageResponse(BaseModel):
    items: list[OperationResponse]
    page: int
    page_size: int
    total: int
    total_amount: str
