"""add dynamic fund allocation mode

Revision ID: 0011_dynamic_fund_allocation
Revises: 0010_default_account
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011_dynamic_fund_allocation"
down_revision: str | None = "0010_default_account"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "application_settings",
        sa.Column(
            "fund_allocation_mode",
            sa.String(length=16),
            server_default="manual",
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_application_settings_fund_allocation_mode",
        "application_settings",
        "fund_allocation_mode IN ('manual', 'dynamic')",
    )
    op.alter_column("application_settings", "fund_allocation_mode", server_default=None)


def downgrade() -> None:
    op.drop_constraint(
        "ck_application_settings_fund_allocation_mode",
        "application_settings",
        type_="check",
    )
    op.drop_column("application_settings", "fund_allocation_mode")
