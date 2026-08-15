from datetime import date
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.modules.operations.contracts import OperationType
from app.modules.scheduling.contracts import OccurrenceStatus


class ForecastScope(StrEnum):
    ALL = "all"
    ACCOUNT = "account"


class ForecastHorizon(StrEnum):
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    HALF_YEAR = "half_year"
    YEAR = "year"


class ForecastGranularity(StrEnum):
    DAY = "day"
    MONTH = "month"


class ForecastBalanceMode(StrEnum):
    FREE = "free"
    TOTAL = "total"


class ForecastEventResponse(BaseModel):
    occurrence_id: UUID
    rule_id: UUID
    due_on: date
    type: OperationType
    status: OccurrenceStatus
    description: str | None
    account_id: UUID
    account_name: str
    destination_account_id: UUID | None
    destination_account_name: str | None
    amount: str
    effect: str


class ForecastPointResponse(BaseModel):
    period_from: date
    on: date
    opening_balance: str
    change: str
    closing_balance: str
    events: list[ForecastEventResponse]


class ForecastResponse(BaseModel):
    balance_mode: ForecastBalanceMode
    scope: ForecastScope
    account_id: UUID | None
    account_name: str | None
    horizon: ForecastHorizon
    granularity: ForecastGranularity
    from_on: date
    through_on: date
    starting_balance: str
    ending_balance: str
    minimum_balance: str
    minimum_on: date
    first_negative_on: date | None
    expected_income: str
    expected_expense: str
    overdue_excluded_count: int
    points: list[ForecastPointResponse]
