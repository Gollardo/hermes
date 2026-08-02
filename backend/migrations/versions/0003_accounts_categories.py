"""Add account, category, and initial-balance ledger foundations.

Revision ID: 0003_accounts_categories
Revises: 0002_harden_access_invariants
Create Date: 2026-08-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_accounts_categories"
down_revision: str | None = "0002_harden_access_invariants"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    account_type_ddl = postgresql.ENUM("cash", "debit", "savings", name="account_type")
    category_type_ddl = postgresql.ENUM("income", "expense", name="category_type")
    operation_type_ddl = postgresql.ENUM("balance_adjustment", name="financial_operation_type")
    account_type_ddl.create(op.get_bind(), checkfirst=True)
    category_type_ddl.create(op.get_bind(), checkfirst=True)
    operation_type_ddl.create(op.get_bind(), checkfirst=True)
    account_type = postgresql.ENUM(
        "cash", "debit", "savings", name="account_type", create_type=False
    )
    category_type = postgresql.ENUM("income", "expense", name="category_type", create_type=False)
    operation_type = postgresql.ENUM(
        "balance_adjustment", name="financial_operation_type", create_type=False
    )

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", account_type, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_accounts_name_not_blank"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", category_type, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(btrim(name)) > 0", name="ck_categories_name_not_blank"),
        sa.CheckConstraint(
            "parent_id IS NULL OR parent_id <> id", name="ck_categories_not_own_parent"
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_parent_id", "categories", ["parent_id"])
    op.create_table(
        "financial_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", operation_type, nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "account_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(precision=20, scale=4), nullable=False),
        sa.CheckConstraint("amount <> 0", name="ck_account_movements_amount_nonzero"),
        sa.ForeignKeyConstraint(["operation_id"], ["financial_operations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_account_movements_operation_id", "account_movements", ["operation_id"])
    op.create_index("ix_account_movements_account_id", "account_movements", ["account_id"])


def downgrade() -> None:
    op.drop_index("ix_account_movements_account_id", table_name="account_movements")
    op.drop_index("ix_account_movements_operation_id", table_name="account_movements")
    op.drop_table("account_movements")
    op.drop_table("financial_operations")
    op.drop_index("ix_categories_parent_id", table_name="categories")
    op.drop_table("categories")
    op.drop_table("accounts")
    postgresql.ENUM(name="financial_operation_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="category_type").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="account_type").drop(op.get_bind(), checkfirst=True)
