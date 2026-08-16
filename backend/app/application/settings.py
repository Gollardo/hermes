"""Cross-module application-settings use cases."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.accounts.contracts import lock_account_references
from app.modules.scheduling.contracts import has_schedule_data
from app.modules.settings.contracts import (
    ApplicationSettings,
    lock_application_timezone,
    update_application_settings,
)


class TimezoneLockedByScheduleError(RuntimeError):
    pass


def replace_application_settings(
    session: Session,
    *,
    base_currency: str,
    timezone: str,
    default_account_id: UUID | None = None,
) -> ApplicationSettings:
    current_timezone = lock_application_timezone(session)
    if default_account_id is not None:
        lock_account_references(session, {default_account_id})
    if timezone != current_timezone and has_schedule_data(session):
        raise TimezoneLockedByScheduleError
    return update_application_settings(
        session,
        base_currency=base_currency,
        timezone=timezone,
        default_account_id=default_account_id,
    )
