"""add the dynamic fund reserve ledger

Revision ID: 0013_fund_reserve
Revises: 0012_recurring_series_shift
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_fund_reserve"
down_revision: str | None = "0012_recurring_series_shift"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE fund_event_type ADD VALUE IF NOT EXISTS 'reserve_distribution'")
    op.execute("ALTER TYPE fund_event_type ADD VALUE IF NOT EXISTS 'reserve_release'")
    op.add_column(
        "fund_events",
        sa.Column("caused_by_operation_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_fund_events_caused_by_operation",
        "fund_events",
        "financial_operations",
        ["caused_by_operation_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_fund_events_caused_by_operation_id",
        "fund_events",
        ["caused_by_operation_id"],
    )
    op.create_table(
        "fund_reserve_movements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(20, 4), nullable=False),
        sa.CheckConstraint("amount <> 0", name="ck_fund_reserve_movements_amount_nonzero"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["event_id"], ["fund_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "event_id", "account_id", name="uq_fund_reserve_movements_event_position"
        ),
    )
    op.create_index(
        "ix_fund_reserve_movements_account_id",
        "fund_reserve_movements",
        ["account_id"],
    )
    op.create_index(
        "ix_fund_reserve_movements_event_id",
        "fund_reserve_movements",
        ["event_id"],
    )


def downgrade() -> None:
    op.drop_table("fund_reserve_movements")
    op.drop_index("ix_fund_events_caused_by_operation_id", table_name="fund_events")
    op.drop_constraint("fk_fund_events_caused_by_operation", "fund_events", type_="foreignkey")
    op.drop_column("fund_events", "caused_by_operation_id")
    # PostgreSQL enum values intentionally remain: removing values is unsafe when
    # older application processes may still hold the enum type in prepared plans.
