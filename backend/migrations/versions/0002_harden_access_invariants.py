"""Harden persisted access and settings invariants.

Revision ID: 0002_harden_access_invariants
Revises: 0001_first_run_access
Create Date: 2026-08-02
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_harden_access_invariants"
down_revision: str | None = "0001_first_run_access"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_auth_session_positive_lifetime",
        "auth_sessions",
        "expires_at > created_at",
    )
    op.create_check_constraint(
        "ck_auth_login_throttle_failed_count",
        "auth_login_throttle",
        "failed_count >= 0",
    )
    op.create_check_constraint(
        "ck_application_settings_base_currency",
        "application_settings",
        "base_currency ~ '^[A-Z]{3}$'",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_application_settings_base_currency",
        "application_settings",
        type_="check",
    )
    op.drop_constraint(
        "ck_auth_login_throttle_failed_count",
        "auth_login_throttle",
        type_="check",
    )
    op.drop_constraint(
        "ck_auth_session_positive_lifetime",
        "auth_sessions",
        type_="check",
    )
