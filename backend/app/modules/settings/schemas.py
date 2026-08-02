from datetime import datetime

from pydantic import BaseModel, field_validator

from app.modules.settings.validation import normalize_currency, normalize_timezone


class SettingsResponse(BaseModel):
    base_currency: str
    timezone: str
    base_currency_locked: bool
    updated_at: datetime


class SettingsUpdateRequest(BaseModel):
    base_currency: str
    timezone: str

    @field_validator("base_currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        return normalize_timezone(value)
