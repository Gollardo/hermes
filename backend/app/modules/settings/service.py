from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.settings.models import ApplicationSettings


class SettingsNotInitializedError(RuntimeError):
    pass


class BaseCurrencyLockedError(RuntimeError):
    pass


def initialize_settings(session: Session, *, base_currency: str, timezone: str) -> None:
    if session.get(ApplicationSettings, 1) is not None:
        raise RuntimeError("Application settings already exist")
    now = datetime.now(UTC)
    session.add(
        ApplicationSettings(
            id=1,
            base_currency=base_currency,
            timezone=timezone,
            base_currency_locked_at=None,
            created_at=now,
            updated_at=now,
        )
    )


def get_application_settings(session: Session) -> ApplicationSettings:
    settings = session.get(ApplicationSettings, 1)
    if settings is None:
        raise SettingsNotInitializedError
    return settings


def update_application_settings(
    session: Session, *, base_currency: str, timezone: str
) -> ApplicationSettings:
    settings = session.scalar(
        select(ApplicationSettings).where(ApplicationSettings.id == 1).with_for_update()
    )
    if settings is None:
        raise SettingsNotInitializedError
    if settings.base_currency_locked_at is not None and base_currency != settings.base_currency:
        raise BaseCurrencyLockedError
    settings.base_currency = base_currency
    settings.timezone = timezone
    settings.updated_at = datetime.now(UTC)
    return settings


def lock_base_currency(session: Session) -> None:
    """Public contract for the first financial-data write transaction."""
    settings = session.scalar(
        select(ApplicationSettings).where(ApplicationSettings.id == 1).with_for_update()
    )
    if settings is None:
        raise SettingsNotInitializedError
    if settings.base_currency_locked_at is None:
        now = datetime.now(UTC)
        settings.base_currency_locked_at = now
        settings.updated_at = now
