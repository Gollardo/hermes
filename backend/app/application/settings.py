"""Cross-module application-settings use cases."""

from sqlalchemy.orm import Session

from app.modules.scheduling.contracts import has_schedule_data
from app.modules.settings.contracts import (
    ApplicationSettings,
    lock_application_timezone,
    update_application_settings,
)


class TimezoneLockedByScheduleError(RuntimeError):
    pass


def replace_application_settings(
    session: Session, *, base_currency: str, timezone: str
) -> ApplicationSettings:
    current_timezone = lock_application_timezone(session)
    if timezone != current_timezone and has_schedule_data(session):
        raise TimezoneLockedByScheduleError
    return update_application_settings(session, base_currency=base_currency, timezone=timezone)
