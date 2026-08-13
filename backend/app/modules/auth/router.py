from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from app.core.database import DatabaseSession
from app.modules.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.modules.auth.dependencies import (
    AuthenticatedSession,
    CsrfSession,
    get_runtime_settings,
)
from app.modules.auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    SessionResponse,
)
from app.modules.auth.service import (
    CurrentPasswordInvalidError,
    LoginStatus,
    change_master_password,
    login,
    logout_all,
    logout_current,
)

public_router = APIRouter()
protected_router = APIRouter()


@public_router.post("/auth/login", tags=["authentication"])
def login_route(payload: LoginRequest, request: Request, session: DatabaseSession) -> Response:
    settings = get_runtime_settings(request)
    result = login(
        session,
        settings,
        master_password=payload.master_password.get_secret_value(),
    )
    if result.status is LoginStatus.INVALID:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": {"code": "invalid_credentials", "message": "Invalid password"}},
        )
    if result.status is LoginStatus.BLOCKED:
        retry_after = result.retry_after_seconds or 1
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": str(retry_after)},
            content={
                "detail": {
                    "code": "login_rate_limited",
                    "message": "Too many failed login attempts",
                }
            },
        )
    assert result.issued_session is not None
    body = SessionResponse(expires_at=result.issued_session.row.expires_at)
    success = JSONResponse(content=body.model_dump(mode="json"))
    set_auth_cookies(success, settings, result.issued_session)
    return success


@protected_router.get("/auth/session", response_model=SessionResponse, tags=["authentication"])
def current_session(auth_session: AuthenticatedSession) -> SessionResponse:
    return SessionResponse(expires_at=auth_session.expires_at)


@protected_router.post(
    "/auth/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["authentication"]
)
def logout_route(
    request: Request, session: DatabaseSession, auth_session: CsrfSession, response: Response
) -> Response:
    logout_current(session, auth_session)
    settings = get_runtime_settings(request)
    clear_auth_cookies(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@protected_router.post(
    "/auth/logout-all", status_code=status.HTTP_204_NO_CONTENT, tags=["authentication"]
)
def logout_all_route(
    request: Request, session: DatabaseSession, auth_session: CsrfSession, response: Response
) -> Response:
    del auth_session
    logout_all(session)
    settings = get_runtime_settings(request)
    clear_auth_cookies(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@protected_router.post(
    "/auth/password", status_code=status.HTTP_204_NO_CONTENT, tags=["authentication"]
)
def password_change_route(
    payload: PasswordChangeRequest,
    session: DatabaseSession,
    auth_session: CsrfSession,
) -> Response:
    try:
        change_master_password(
            session,
            auth_session,
            current_password=payload.current_password.get_secret_value(),
            new_master_password=payload.new_master_password.get_secret_value(),
        )
    except CurrentPasswordInvalidError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "current_password_invalid", "message": "Current password is invalid"},
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
