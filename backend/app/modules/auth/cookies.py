from datetime import UTC, datetime

from fastapi import Response

from app.core.config import Settings
from app.modules.auth.security import CSRF_COOKIE_NAME
from app.modules.auth.service import IssuedSession


def set_auth_cookies(response: Response, settings: Settings, issued: IssuedSession) -> None:
    max_age = max(0, int((issued.row.expires_at - datetime.now(UTC)).total_seconds()))
    response.set_cookie(
        settings.session_cookie_name,
        issued.session_token,
        max_age=max_age,
        expires=issued.row.expires_at,
        path=settings.api_prefix,
        secure=settings.secure_cookies,
        httponly=True,
        samesite="lax",
    )
    response.set_cookie(
        CSRF_COOKIE_NAME,
        issued.csrf_token,
        max_age=max_age,
        expires=issued.row.expires_at,
        # The Angular page must be able to read this non-secret double-submit token.
        path="/",
        secure=settings.secure_cookies,
        httponly=False,
        samesite="lax",
    )


def clear_auth_cookies(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        path=settings.api_prefix,
        secure=settings.secure_cookies,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        CSRF_COOKIE_NAME,
        path="/",
        secure=settings.secure_cookies,
        httponly=False,
        samesite="lax",
    )


__all__ = ["clear_auth_cookies", "set_auth_cookies"]
