from fastapi import APIRouter, HTTPException, status

from app.application.settings import (
    TimezoneLockedByScheduleError,
    replace_application_settings,
)
from app.core.database import DatabaseSession
from app.modules.settings.contracts import ApplicationSettings
from app.modules.settings.schemas import SettingsResponse, SettingsUpdateRequest
from app.modules.settings.service import BaseCurrencyLockedError, get_application_settings

read_router = APIRouter(prefix="/settings", tags=["settings"])
write_router = APIRouter(prefix="/settings", tags=["settings"])


def _response(settings: ApplicationSettings) -> SettingsResponse:
    return SettingsResponse(
        base_currency=settings.base_currency,
        timezone=settings.timezone,
        base_currency_locked=settings.base_currency_locked_at is not None,
        updated_at=settings.updated_at,
    )


@read_router.get("", response_model=SettingsResponse)
def read_settings(session: DatabaseSession) -> SettingsResponse:
    return _response(get_application_settings(session))


@write_router.put("", response_model=SettingsResponse)
def replace_settings(
    payload: SettingsUpdateRequest,
    session: DatabaseSession,
) -> SettingsResponse:
    try:
        settings = replace_application_settings(
            session,
            base_currency=payload.base_currency,
            timezone=payload.timezone,
        )
    except BaseCurrencyLockedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "base_currency_locked",
                "message": "Base currency cannot change after financial data exists",
            },
        ) from error
    except TimezoneLockedByScheduleError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "timezone_locked_by_schedule",
                "message": "Timezone cannot change after recurring rules exist",
            },
        ) from error
    return _response(settings)
