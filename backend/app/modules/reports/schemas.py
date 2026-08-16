from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class IncomeExpenseReportType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class ReportOperationResponse(BaseModel):
    id: UUID
    occurred_on: date
    description: str | None
    amount: str


class ReportCategoryResponse(BaseModel):
    category_id: UUID
    category_name: str
    root_category_id: UUID
    root_category_name: str
    amount: str
    share: str
    operations: list[ReportOperationResponse]


class IncomeExpenseReportResponse(BaseModel):
    type: IncomeExpenseReportType
    from_on: date
    through_on: date
    total_amount: str
    operation_count: int
    categories: list[ReportCategoryResponse]
