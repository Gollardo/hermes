from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class AppEnvironment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Runtime settings populated from `HERMES_*` environment variables."""

    model_config = SettingsConfigDict(env_prefix="HERMES_", extra="ignore")

    app_name: str = "Hermes"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    api_prefix: str = "/api/v1"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "hermes"
    database_user: str = "hermes"
    database_password: SecretStr = SecretStr("")
    database_echo: bool = False
    static_dir: Path | None = None
    session_cookie_name: str = "hermes_session"
    cookie_secure: bool | None = None
    session_lifetime_days: int = Field(default=7, ge=1, le=90)
    session_idle_minutes: int = Field(default=30, ge=1, le=1440)
    login_failure_limit: int = Field(default=5, ge=1, le=100)
    login_failure_window_minutes: int = Field(default=15, ge=1, le=1440)
    login_block_minutes: int = Field(default=15, ge=1, le=1440)

    @property
    def secure_cookies(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.app_env is AppEnvironment.PRODUCTION

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.database_user,
            password=self.database_password.get_secret_value() or None,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
