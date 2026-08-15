"""Track authenticated-session activity for idle expiry.

Revision ID: 0008_session_idle_timeout
Revises: 0007_fund_targets_recurrence
Create Date: 2026-08-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_session_idle_timeout"
down_revision: str | None = "0007_fund_targets_recurrence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("auth_sessions", sa.Column("last_activity_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE auth_sessions SET last_activity_at = created_at")
    op.alter_column("auth_sessions", "last_activity_at", nullable=False)
    op.create_check_constraint(
        "ck_auth_session_activity_within_lifetime",
        "auth_sessions",
        "last_activity_at >= created_at AND last_activity_at < expires_at",
    )


def downgrade() -> None:
    op.drop_constraint("ck_auth_session_activity_within_lifetime", "auth_sessions", type_="check")
    op.drop_column("auth_sessions", "last_activity_at")
