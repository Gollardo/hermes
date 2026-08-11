from datetime import date, datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.validation import Money
from app.modules.operations.contracts import OperationType
from app.modules.scheduling.models import OccurrenceStatus, RecurrenceFrequency


class RecurringRuleCreateRequest(BaseModel):
    type: OperationType
    frequency: RecurrenceFrequency
    start_on: date
    end_on: date | None = None
    amount: Money
    description: str | None = Field(default=None, max_length=2000)
    account_id: UUID
    destination_account_id: UUID | None = None
    category_id: UUID | None = None

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        if self.type == OperationType.BALANCE_ADJUSTMENT:
            raise ValueError("balance adjustments cannot recur")
        if self.amount <= 0:
            raise ValueError("amount must be positive")
        if self.end_on is not None and self.end_on < self.start_on:
            raise ValueError("end date must not precede start date")
        if self.frequency == RecurrenceFrequency.MONTHLY and self.start_on.day > 28:
            raise ValueError("monthly rules must start on day 1 through 28")
        if self.frequency == RecurrenceFrequency.YEARLY and (
            self.start_on.month == 2 and self.start_on.day == 29
        ):
            raise ValueError("yearly rules cannot start on February 29")
        if self.type in {OperationType.INCOME, OperationType.EXPENSE}:
            if self.category_id is None or self.destination_account_id is not None:
                raise ValueError("income and expense require category and one account")
        elif (
            self.category_id is not None
            or self.destination_account_id is None
            or self.destination_account_id == self.account_id
        ):
            raise ValueError("transfer requires two different accounts and no category")
        return self


class RecurringRuleUpdateRequest(RecurringRuleCreateRequest):
    active: bool
    version: int = Field(ge=1)


class RecurringRuleResponse(BaseModel):
    id: UUID
    type: OperationType
    frequency: RecurrenceFrequency
    start_on: date
    end_on: date | None
    amount: str
    description: str | None
    account_id: UUID
    account_name: str
    destination_account_id: UUID | None
    destination_account_name: str | None
    category_id: UUID | None
    category_name: str | None
    active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class ExpectedOccurrenceResponse(BaseModel):
    id: UUID
    rule_id: UUID
    scheduled_on: date
    due_on: date
    status: OccurrenceStatus
    manually_modified: bool
    overdue: bool
    type: OperationType
    amount: str
    description: str | None
    account_id: UUID
    account_name: str
    destination_account_id: UUID | None
    destination_account_name: str | None
    category_id: UUID | None
    category_name: str | None
    actual_operation_id: UUID | None
    version: int
    created_at: datetime
    updated_at: datetime


class OccurrencePageResponse(BaseModel):
    items: list[ExpectedOccurrenceResponse]
    page: int
    page_size: int
    total: int


class MaterializationResponse(BaseModel):
    horizon_from: date
    horizon_to: date
    created: int
    updated: int
    cancelled: int


class OccurrenceVersionRequest(BaseModel):
    version: int = Field(ge=1)


class OccurrencePostponeRequest(OccurrenceVersionRequest):
    due_on: date


def format_money(value: Decimal) -> str:
    return format(value, "f")
