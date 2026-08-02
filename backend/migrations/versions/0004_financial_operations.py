"""Add the general financial operation journal.

Revision ID: 0004_financial_operations
Revises: 0003_accounts_categories
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_financial_operations"
down_revision: str | None = "0003_accounts_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE financial_operation_type ADD VALUE IF NOT EXISTS 'income'")
    op.execute("ALTER TYPE financial_operation_type ADD VALUE IF NOT EXISTS 'expense'")
    op.execute("ALTER TYPE financial_operation_type ADD VALUE IF NOT EXISTS 'transfer'")

    op.add_column("financial_operations", sa.Column("occurred_on", sa.Date(), nullable=True))
    op.execute(
        "UPDATE financial_operations "
        "SET occurred_on = (occurred_at AT TIME ZONE COALESCE("
        "(SELECT timezone FROM application_settings WHERE id = 1), 'UTC'))::date"
    )
    op.alter_column("financial_operations", "occurred_on", nullable=False)
    op.drop_column("financial_operations", "occurred_at")
    op.alter_column("financial_operations", "description", existing_type=sa.Text(), nullable=True)
    op.add_column("financial_operations", sa.Column("reason", sa.Text(), nullable=True))
    op.execute(
        "UPDATE financial_operations SET reason = description WHERE type = 'balance_adjustment'"
    )
    op.add_column(
        "financial_operations",
        sa.Column("category_id", sa.UUID(), nullable=True),
    )
    op.add_column("financial_operations", sa.Column("updated_at", sa.DateTime(timezone=True)))
    op.execute("UPDATE financial_operations SET updated_at = created_at")
    op.alter_column("financial_operations", "updated_at", nullable=False)
    op.add_column(
        "financial_operations",
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
    )
    op.create_check_constraint(
        "ck_financial_operations_version_positive", "financial_operations", "version > 0"
    )
    op.create_check_constraint(
        "ck_financial_operations_reason_not_blank",
        "financial_operations",
        "reason IS NULL OR length(btrim(reason)) > 0",
    )
    op.create_foreign_key(
        "fk_financial_operations_category_id",
        "financial_operations",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_financial_operations_category_id", "financial_operations", ["category_id"])
    op.create_index(
        "ix_financial_operations_journal_order",
        "financial_operations",
        ["occurred_on", "created_at", "id"],
    )
    op.create_unique_constraint(
        "uq_account_movements_operation_account",
        "account_movements",
        ["operation_id", "account_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_account_movements_operation_account", "account_movements", type_="unique"
    )
    op.drop_index("ix_financial_operations_journal_order", table_name="financial_operations")
    op.drop_index("ix_financial_operations_category_id", table_name="financial_operations")
    op.drop_constraint(
        "fk_financial_operations_category_id", "financial_operations", type_="foreignkey"
    )
    op.drop_constraint(
        "ck_financial_operations_reason_not_blank", "financial_operations", type_="check"
    )
    op.drop_constraint(
        "ck_financial_operations_version_positive", "financial_operations", type_="check"
    )
    op.drop_column("financial_operations", "version")
    op.drop_column("financial_operations", "updated_at")
    op.drop_column("financial_operations", "category_id")
    op.execute(
        "UPDATE financial_operations SET description = COALESCE("
        "description, reason, 'Legacy ' || replace(type::text, '_', ' '))"
    )
    op.drop_column("financial_operations", "reason")
    op.alter_column("financial_operations", "description", existing_type=sa.Text(), nullable=False)
    op.add_column(
        "financial_operations", sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.execute(
        "UPDATE financial_operations SET occurred_at = occurred_on::timestamp AT TIME ZONE 'UTC'"
    )
    op.alter_column("financial_operations", "occurred_at", nullable=False)
    op.drop_column("financial_operations", "occurred_on")
    # PostgreSQL enum values are intentionally retained on development downgrade.
