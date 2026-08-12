from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.exc import IntegrityError
from starlette.responses import Response as StarletteResponse
from starlette.types import Message

from app.core.database import DatabaseSession
from app.modules.auth.dependencies import AuthenticatedSession, get_runtime_settings
from app.modules.auth.service import (
    LoginStatus,
    logout_other_sessions,
    reauthenticate_owner,
)
from app.modules.backup.schemas import (
    BackupDocument,
    BackupPreviewResponse,
    RestoreRequest,
    RestoreResponse,
)
from app.modules.backup.service import (
    RESTORE_CONFIRMATION,
    BackupIntegrityError,
    BackupInvariantError,
    create_backup,
    preview_backup,
    restore_backup,
)

MAX_BACKUP_BYTES = 50 * 1024 * 1024


class BackupBodyLimitRoute(APIRoute):
    """Reject oversized backup bodies before FastAPI buffers and parses JSON."""

    def get_route_handler(
        self,
    ) -> Callable[[Request], Coroutine[Any, Any, StarletteResponse]]:
        original_handler = super().get_route_handler()

        async def limited_handler(request: Request) -> StarletteResponse:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    declared_size = int(content_length)
                except ValueError:
                    declared_size = MAX_BACKUP_BYTES + 1
                if declared_size > MAX_BACKUP_BYTES:
                    raise _backup_too_large()

            received = 0
            original_receive = request.receive

            async def limited_receive() -> Message:
                nonlocal received
                message = await original_receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > MAX_BACKUP_BYTES:
                        raise _backup_too_large()
                return message

            return await original_handler(Request(request.scope, limited_receive))

        return limited_handler


def _backup_too_large() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_413_CONTENT_TOO_LARGE,
        detail={
            "code": "backup_too_large",
            "message": "Backup exceeds the 50 MiB request limit",
        },
    )


read_router = APIRouter(prefix="/backup", tags=["backup"])
write_router = APIRouter(
    prefix="/backup",
    tags=["backup"],
    route_class=BackupBodyLimitRoute,
)


def _invalid_backup(error: ValueError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={"code": "invalid_backup", "message": str(error)},
    )


@read_router.get("/export", response_model=BackupDocument)
def export_backup(session: DatabaseSession, response: Response) -> BackupDocument:
    response.headers["Content-Disposition"] = 'attachment; filename="hermes-backup.json"'
    response.headers["Cache-Control"] = "no-store"
    return create_backup(session)


@write_router.post("/preview", response_model=BackupPreviewResponse)
def preview(payload: BackupDocument) -> BackupPreviewResponse:
    try:
        return preview_backup(payload)
    except (BackupIntegrityError, BackupInvariantError, ValueError) as error:
        raise _invalid_backup(error) from error


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
    reauthentication = reauthenticate_owner(
        session,
        get_runtime_settings(request),
        payload.master_password.get_secret_value(),
    )
    if reauthentication.status is LoginStatus.INVALID:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": {
                    "code": "current_password_invalid",
                    "message": "Current password is invalid",
                }
            },
        )
    if reauthentication.status is LoginStatus.BLOCKED:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(reauthentication.retry_after_seconds or 1)},
            content={
                "detail": {
                    "code": "login_rate_limited",
                    "message": "Too many failed password attempts",
                }
            },
        )
    try:
        result = restore_backup(session, payload.backup)
        logout_other_sessions(session, auth_session)
        return result
    except (BackupIntegrityError, BackupInvariantError, ValueError) as error:
        raise _invalid_backup(error) from error
    except IntegrityError as error:
        raise _invalid_backup(ValueError("Backup violates a database domain constraint")) from error
