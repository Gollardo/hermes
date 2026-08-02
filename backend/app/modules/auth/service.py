from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from math import ceil

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.auth.models import AuthSession, LoginThrottle, OwnerCredential
from app.modules.auth.security import (
    hash_password,
    hash_token,
    new_opaque_token,
    password_hash_needs_upgrade,
    tokens_match,
    verify_password,
)
from app.modules.settings.contracts import initialize_settings


class AlreadyInitializedError(RuntimeError):
    pass


class CurrentPasswordInvalidError(RuntimeError):
    pass


class LoginStatus(StrEnum):
    SUCCESS = "success"
    INVALID = "invalid"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class IssuedSession:
    row: AuthSession
    session_token: str
    csrf_token: str


@dataclass(frozen=True)
class LoginResult:
    status: LoginStatus
    issued_session: IssuedSession | None = None
    retry_after_seconds: int | None = None


def is_initialized(session: Session) -> bool:
    return session.scalar(select(OwnerCredential.id).limit(1)) is not None


def _issue_session(session: Session, settings: Settings) -> IssuedSession:
    now = datetime.now(UTC)
    session_token = new_opaque_token()
    csrf_token = new_opaque_token()
    row = AuthSession(
        token_hash=hash_token(session_token),
        owner_id=1,
        csrf_token_hash=hash_token(csrf_token),
        created_at=now,
        expires_at=now + timedelta(days=settings.session_lifetime_days),
    )
    session.add(row)
    return IssuedSession(row=row, session_token=session_token, csrf_token=csrf_token)


def setup_owner(
    session: Session,
    settings: Settings,
    *,
    master_password: str,
    base_currency: str,
    timezone: str,
) -> IssuedSession:
    if is_initialized(session):
        raise AlreadyInitializedError
    now = datetime.now(UTC)
    session.add(
        OwnerCredential(
            id=1,
            password_hash=hash_password(master_password),
            created_at=now,
            password_changed_at=now,
        )
    )
    throttle = session.get(LoginThrottle, 1)
    if throttle is None:
        session.add(LoginThrottle(id=1, failed_count=0))
    else:
        throttle.failed_count = 0
        throttle.window_started_at = None
        throttle.blocked_until = None
    initialize_settings(session, base_currency=base_currency, timezone=timezone)
    issued = _issue_session(session, settings)
    try:
        session.flush()
    except IntegrityError as error:
        raise AlreadyInitializedError from error
    return issued


def _get_locked_throttle(session: Session) -> LoginThrottle:
    throttle = session.get(LoginThrottle, 1, with_for_update=True)
    if throttle is None:
        throttle = LoginThrottle(id=1, failed_count=0)
        session.add(throttle)
        session.flush()
    return throttle


def _blocked_seconds(throttle: LoginThrottle, now: datetime) -> int | None:
    if throttle.blocked_until is None or throttle.blocked_until <= now:
        return None
    return max(1, ceil((throttle.blocked_until - now).total_seconds()))


def _record_failed_login(throttle: LoginThrottle, now: datetime, settings: Settings) -> None:
    window = timedelta(minutes=settings.login_failure_window_minutes)
    if throttle.window_started_at is None or now - throttle.window_started_at >= window:
        throttle.failed_count = 1
        throttle.window_started_at = now
    else:
        throttle.failed_count += 1
    if throttle.failed_count >= settings.login_failure_limit:
        throttle.blocked_until = now + timedelta(minutes=settings.login_block_minutes)


def login(session: Session, settings: Settings, *, master_password: str) -> LoginResult:
    now = datetime.now(UTC)
    throttle = _get_locked_throttle(session)
    blocked_seconds = _blocked_seconds(throttle, now)
    if blocked_seconds is not None:
        return LoginResult(LoginStatus.BLOCKED, retry_after_seconds=blocked_seconds)

    owner = session.get(OwnerCredential, 1)
    if owner is None or not verify_password(owner.password_hash, master_password):
        _record_failed_login(throttle, now, settings)
        blocked_seconds = _blocked_seconds(throttle, now)
        if blocked_seconds is not None:
            return LoginResult(LoginStatus.BLOCKED, retry_after_seconds=blocked_seconds)
        return LoginResult(LoginStatus.INVALID)

    throttle.failed_count = 0
    throttle.window_started_at = None
    throttle.blocked_until = None
    if password_hash_needs_upgrade(owner.password_hash):
        owner.password_hash = hash_password(master_password)
    session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
    return LoginResult(LoginStatus.SUCCESS, issued_session=_issue_session(session, settings))


def find_authenticated_session(session: Session, token: str) -> AuthSession | None:
    now = datetime.now(UTC)
    return session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == hash_token(token), AuthSession.expires_at > now
        )
    )


def csrf_is_valid(auth_session: AuthSession, csrf_token: str) -> bool:
    return tokens_match(auth_session.csrf_token_hash, csrf_token)


def logout_current(session: Session, auth_session: AuthSession) -> None:
    session.delete(auth_session)


def logout_all(session: Session) -> None:
    session.execute(delete(AuthSession))


def change_master_password(
    session: Session,
    auth_session: AuthSession,
    *,
    current_password: str,
    new_master_password: str,
) -> None:
    owner = session.get(OwnerCredential, 1)
    if owner is None or not verify_password(owner.password_hash, current_password):
        raise CurrentPasswordInvalidError
    owner.password_hash = hash_password(new_master_password)
    owner.password_changed_at = datetime.now(UTC)
    session.execute(delete(AuthSession).where(AuthSession.token_hash != auth_session.token_hash))
