from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.modules.settings.models import FundAllocationMode
from app.modules.settings.validation import normalize_currency, normalize_timezone


class SettingsResponse(BaseModel):
    base_currency: str
    timezone: str
    default_account_id: UUID | None
    fund_allocation_mode: FundAllocationMode
    base_currency_locked: bool
    updated_at: datetime
    application_today: date


class SettingsUpdateRequest(BaseModel):
    base_currency: str
    timezone: str
    default_account_id: UUID | None = None

    @field_validator("base_currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        return normalize_timezone(value)


class FundAllocationModeUpdateRequest(BaseModel):
    mode: FundAllocationMode
