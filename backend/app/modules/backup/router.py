from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.database import DatabaseSession
from app.core.http_limits import BackupBodyLimitRoute
from app.modules.auth.dependencies import AuthenticatedSession, get_runtime_settings
from app.modules.auth.service import LoginStatus, logout_other_sessions, reauthenticate_owner
from app.modules.backup.errors import (
    BackupAuthenticationFailed,
    BackupTooLarge,
    InvalidBackupPayload,
    InvalidHermesFile,
    InvalidKdfParameters,
    UnsupportedHermesVersion,
)
from app.modules.backup.schemas import (
    BackupDocument,
    BackupPreviewRequest,
    BackupPreviewResponse,
    HermesBackup,
    HermesExportRequest,
    RestoreRequest,
    RestoreResponse,
)
from app.modules.backup.service import (
    RESTORE_CONFIRMATION,
    BackupIntegrityError,
    BackupInvariantError,
    create_backup,
    create_hermes_backup,
    preview_backup_envelope,
    restore_backup_envelope,
)

read_router = APIRouter(prefix="/backup", tags=["backup"])
write_router = APIRouter(
    prefix="/backup",
    tags=["backup"],
    route_class=BackupBodyLimitRoute,
)


def _backup_error(error: ValueError) -> HTTPException:
    if isinstance(error, BackupTooLarge):
        return HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={"code": "backup_too_large", "message": str(error)},
        )
    if isinstance(error, BackupAuthenticationFailed):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "backup_authentication_failed", "message": str(error)},
        )
    codes = {
        UnsupportedHermesVersion: "unsupported_hermes_version",
        InvalidKdfParameters: "invalid_kdf_parameters",
        InvalidBackupPayload: "invalid_backup_payload",
        InvalidHermesFile: "invalid_hermes_file",
    }
    for error_type, code in codes.items():
        if isinstance(error, error_type):
            return HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail={"code": code, "message": str(error)},
            )
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_backup", "message": str(error)},
    )


def _reauthenticate_or_response(
    request: Request, session: DatabaseSession, master_password: str
) -> Response | None:
    result = reauthenticate_owner(session, get_runtime_settings(request), master_password)
    if result.status is LoginStatus.INVALID:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": {
                    "code": "current_password_invalid",
                    "message": "Current password is invalid",
                }
            },
        )
    if result.status is LoginStatus.BLOCKED:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(result.retry_after_seconds or 1)},
            content={
                "detail": {
                    "code": "login_rate_limited",
                    "message": "Too many failed password attempts",
                }
            },
        )
    return None


@read_router.get("/export", response_model=BackupDocument)
def export_backup(session: DatabaseSession, response: Response) -> BackupDocument:
    response.headers["Content-Disposition"] = 'attachment; filename="hermes-backup.json"'
    response.headers["Cache-Control"] = "no-store"
    return create_backup(session)


@write_router.post("/export/hermes", response_model=HermesBackup)
def export_hermes_backup(
    payload: HermesExportRequest,
    request: Request,
    session: DatabaseSession,
    response: Response,
) -> HermesBackup | Response:
    password = payload.master_password.get_secret_value()
    rejection = _reauthenticate_or_response(request, session, password)
    if rejection is not None:
        return rejection
    response.headers["Content-Disposition"] = 'attachment; filename="hermes-backup.hermes"'
    response.headers["Cache-Control"] = "no-store"
    try:
        return create_hermes_backup(session, password)
    except ValueError as error:
        raise _backup_error(error) from error


@write_router.post("/preview", response_model=BackupPreviewResponse)
def preview(payload: dict[str, Any]) -> BackupPreviewResponse:
    try:
        request_payload = (
            BackupPreviewRequest.model_validate(payload)
            if "backup" in payload
            else BackupPreviewRequest(backup=payload)
        )
        password = (
            request_payload.backup_password.get_secret_value()
            if request_payload.backup_password is not None
            else None
        )
        return preview_backup_envelope(request_payload.backup, password)
    except (BackupIntegrityError, BackupInvariantError, ValueError) as error:
        raise _backup_error(error) from error


@write_router.post("/restore", response_model=RestoreResponse)
def restore(
    payload: RestoreRequest,
    request: Request,
    session: DatabaseSession,
    auth_session: AuthenticatedSession,
) -> RestoreResponse | Response:
    if payload.confirmation != RESTORE_CONFIRMATION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "confirmation_invalid",
                "message": "Restore confirmation does not match",
            },
        )
    rejection = _reauthenticate_or_response(
        request, session, payload.master_password.get_secret_value()
    )
    if rejection is not None:
        return rejection
    try:
        backup_password = (
            payload.backup_password.get_secret_value()
            if payload.backup_password is not None
            else None
        )
        result = restore_backup_envelope(session, payload.backup, backup_password)
        logout_other_sessions(session, auth_session)
        return result
    except (BackupIntegrityError, BackupInvariantError, ValueError) as error:
        raise _backup_error(error) from error
    except IntegrityError as error:
        raise _backup_error(ValueError("Backup violates a database domain constraint")) from error
