"""add scheduled transfer fund allocation snapshot

Revision ID: 0009_scheduled_fund_allocation
Revises: 0008_session_idle_timeout
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_scheduled_fund_allocation"
down_revision: str | None = "0008_session_idle_timeout"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in ("recurring_rules", "expected_occurrences"):
        op.add_column(
            table,
            sa.Column("allocate_to_funds", sa.Boolean(), server_default=sa.false(), nullable=False),
        )
        op.create_check_constraint(
            f"ck_{table}_fund_allocation_transfer",
            table,
            "NOT allocate_to_funds OR type = 'transfer'",
        )
        op.alter_column(table, "allocate_to_funds", server_default=None)


def downgrade() -> None:
    for table in ("expected_occurrences", "recurring_rules"):
        op.drop_constraint(f"ck_{table}_fund_allocation_transfer", table, type_="check")
        op.drop_column(table, "allocate_to_funds")
