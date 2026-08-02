from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings
from app.core.database import DatabaseSession
from app.modules.auth.models import AuthSession
from app.modules.auth.security import CSRF_HEADER_NAME
from app.modules.auth.service import csrf_is_valid, find_authenticated_session


def get_runtime_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def require_authenticated_session(request: Request, session: DatabaseSession) -> AuthSession:
    settings = get_runtime_settings(request)
    token = request.cookies.get(settings.session_cookie_name)
    auth_session = find_authenticated_session(session, token) if token else None
    if auth_session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "authentication_required", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Session"},
        )
    return auth_session


AuthenticatedSession = Annotated[AuthSession, Depends(require_authenticated_session)]


def require_csrf_session(request: Request, auth_session: AuthenticatedSession) -> AuthSession:
    csrf_token = request.headers.get(CSRF_HEADER_NAME)
    if csrf_token is None or not csrf_is_valid(auth_session, csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "csrf_failed", "message": "CSRF validation failed"},
        )
    return auth_session


CsrfSession = Annotated[AuthSession, Depends(require_csrf_session)]
