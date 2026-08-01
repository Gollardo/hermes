from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
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
