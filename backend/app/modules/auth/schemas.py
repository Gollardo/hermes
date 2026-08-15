from datetime import datetime

from pydantic import BaseModel, ConfigDict, SecretStr, field_validator

from app.modules.settings.contracts import normalize_currency, normalize_timezone

MIN_PASSWORD_LENGTH = 12
MAX_PASSWORD_LENGTH = 1024


def _validate_password(value: SecretStr, *, enforce_minimum: bool) -> SecretStr:
    password = value.get_secret_value()
    if enforce_minimum and len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must contain at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must contain at most {MAX_PASSWORD_LENGTH} characters")
    return value


def validate_new_master_password(value: SecretStr) -> SecretStr:
    return _validate_password(value, enforce_minimum=True)


class SetupRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=False)

    master_password: SecretStr
    base_currency: str
    timezone: str

    @field_validator("master_password")
    @classmethod
    def valid_master_password(cls, value: SecretStr) -> SecretStr:
        return validate_new_master_password(value)

    @field_validator("base_currency")
    @classmethod
    def valid_currency(cls, value: str) -> str:
        return normalize_currency(value)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        return normalize_timezone(value)


class LoginRequest(BaseModel):
    master_password: SecretStr

    @field_validator("master_password")
    @classmethod
    def bounded_password(cls, value: SecretStr) -> SecretStr:
        return _validate_password(value, enforce_minimum=False)


class PasswordChangeRequest(BaseModel):
    current_password: SecretStr
    new_master_password: SecretStr

    @field_validator("current_password")
    @classmethod
    def bounded_current_password(cls, value: SecretStr) -> SecretStr:
        return _validate_password(value, enforce_minimum=False)

    @field_validator("new_master_password")
    @classmethod
    def valid_new_password(cls, value: SecretStr) -> SecretStr:
        return validate_new_master_password(value)


class SessionResponse(BaseModel):
    authenticated: bool = True
    expires_at: datetime
    idle_timeout_seconds: int
