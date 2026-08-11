"""Add virtual funds and their ledger.

Revision ID: 0005_virtual_funds
Revises: 0004_financial_operations
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_virtual_funds"
down_revision: str | None = "0004_financial_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    fund_event_type = sa.Enum("allocation", "redistribution", name="fund_event_type")
    op.create_table(
        "funds",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("allocation_percentage", sa.Numeric(7, 4), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_funds_name_not_blank"),
        sa.CheckConstraint(
            "allocation_percentage >= 0 AND allocation_percentage <= 100",
            name="ck_funds_allocation_percentage_range",
        ),
        sa.CheckConstraint("version > 0", name="ck_funds_version_positive"),
    )
    op.create_table(
        "fund_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("type", fund_event_type, nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "fund_movements",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "fund_id",
            sa.UUID(),
            sa.ForeignKey("funds.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "account_id",
            sa.UUID(),
            sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "operation_id",
            sa.UUID(),
            sa.ForeignKey("financial_operations.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "event_id",
            sa.UUID(),
            sa.ForeignKey("fund_events.id", ondelete="CASCADE"),
        ),
        sa.Column("amount", sa.Numeric(20, 4), nullable=False),
        sa.CheckConstraint("amount <> 0", name="ck_fund_movements_amount_nonzero"),
        sa.CheckConstraint(
            "(operation_id IS NOT NULL)::int + (event_id IS NOT NULL)::int = 1",
            name="ck_fund_movements_one_source",
        ),
        sa.UniqueConstraint(
            "operation_id", "fund_id", "account_id", name="uq_fund_movements_operation_position"
        ),
        sa.UniqueConstraint(
            "event_id", "fund_id", "account_id", name="uq_fund_movements_event_position"
        ),
    )
    op.create_index("ix_fund_movements_fund_id", "fund_movements", ["fund_id"])
    op.create_index("ix_fund_movements_account_id", "fund_movements", ["account_id"])
    op.create_index("ix_fund_movements_operation_id", "fund_movements", ["operation_id"])
    op.create_index("ix_fund_movements_event_id", "fund_movements", ["event_id"])
    op.create_index(
        "ix_fund_events_history_order", "fund_events", ["occurred_on", "created_at", "id"]
    )


def downgrade() -> None:
    op.drop_index("ix_fund_events_history_order", table_name="fund_events")
    op.drop_table("fund_movements")
    op.drop_table("fund_events")
    op.drop_table("funds")
    sa.Enum(name="fund_event_type").drop(op.get_bind())
