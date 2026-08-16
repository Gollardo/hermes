"""add default account preference

Revision ID: 0010_default_account
Revises: 0009_scheduled_fund_allocation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_default_account"
down_revision: str | None = "0009_scheduled_fund_allocation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "application_settings",
        sa.Column("default_account_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_application_settings_default_account",
        "application_settings",
        "accounts",
        ["default_account_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_application_settings_default_account",
        "application_settings",
        type_="foreignkey",
    )
    op.drop_column("application_settings", "default_account_id")
