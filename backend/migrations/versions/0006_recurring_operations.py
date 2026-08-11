"""Add recurring rules and expected operation occurrences.

Revision ID: 0006_recurring_operations
Revises: 0005_virtual_funds
Create Date: 2026-08-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_recurring_operations"
down_revision: str | None = "0005_virtual_funds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    frequency = sa.Enum("daily", "weekly", "monthly", "yearly", name="recurrence_frequency")
    occurrence_status = sa.Enum(
        "pending",
        "confirmed",
        "postponed",
        "cancelled",
        name="expected_occurrence_status",
    )
    operation_type = postgresql.ENUM(
        "income",
        "expense",
        "transfer",
        "balance_adjustment",
        name="financial_operation_type",
        create_type=False,
    )
    op.create_table(
        "recurring_rules",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("type", operation_type, nullable=False),
        sa.Column("frequency", frequency, nullable=False),
        sa.Column("start_on", sa.Date(), nullable=False),
        sa.Column("end_on", sa.Date()),
        sa.Column("amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "account_id",
            sa.UUID(),
            sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "destination_account_id",
            sa.UUID(),
            sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "category_id",
            sa.UUID(),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
        ),
        sa.Column("active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_recurring_rules_amount_positive"),
        sa.CheckConstraint("version > 0", name="ck_recurring_rules_version_positive"),
        sa.CheckConstraint("end_on IS NULL OR end_on >= start_on", name="ck_recurring_rules_dates"),
        sa.CheckConstraint(
            "frequency <> 'monthly' OR extract(day from start_on) <= 28",
            name="ck_recurring_rules_monthly_day",
        ),
        sa.CheckConstraint(
            "frequency <> 'yearly' OR extract(month from start_on) <> 2 "
            "OR extract(day from start_on) <> 29",
            name="ck_recurring_rules_yearly_day",
        ),
        sa.CheckConstraint(
            "(type IN ('income', 'expense') AND category_id IS NOT NULL "
            "AND destination_account_id IS NULL) OR "
            "(type = 'transfer' AND category_id IS NULL "
            "AND destination_account_id IS NOT NULL "
            "AND destination_account_id <> account_id)",
            name="ck_recurring_rules_operation_shape",
        ),
    )
    op.create_index("ix_recurring_rules_account_id", "recurring_rules", ["account_id"])
    op.create_index(
        "ix_recurring_rules_destination_account_id",
        "recurring_rules",
        ["destination_account_id"],
    )
    op.create_index("ix_recurring_rules_category_id", "recurring_rules", ["category_id"])

    op.create_table(
        "expected_occurrences",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "rule_id",
            sa.UUID(),
            sa.ForeignKey("recurring_rules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("scheduled_on", sa.Date(), nullable=False),
        sa.Column("due_on", sa.Date(), nullable=False),
        sa.Column("status", occurrence_status, nullable=False),
        sa.Column("manually_modified", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("type", operation_type, nullable=False),
        sa.Column("amount", sa.Numeric(20, 4), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "account_id",
            sa.UUID(),
            sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "destination_account_id",
            sa.UUID(),
            sa.ForeignKey("accounts.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "category_id",
            sa.UUID(),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "actual_operation_id",
            sa.UUID(),
            sa.ForeignKey(
                "financial_operations.id",
                ondelete="RESTRICT",
                name="fk_expected_occurrences_actual_operation",
            ),
            unique=True,
        ),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_expected_occurrences_amount_positive"),
        sa.CheckConstraint("version > 0", name="ck_expected_occurrences_version_positive"),
        sa.CheckConstraint(
            "(type IN ('income', 'expense') AND category_id IS NOT NULL "
            "AND destination_account_id IS NULL) OR "
            "(type = 'transfer' AND category_id IS NULL "
            "AND destination_account_id IS NOT NULL "
            "AND destination_account_id <> account_id)",
            name="ck_expected_occurrences_operation_shape",
        ),
        sa.CheckConstraint(
            "(status = 'confirmed' AND actual_operation_id IS NOT NULL) OR "
            "(status <> 'confirmed' AND actual_operation_id IS NULL)",
            name="ck_expected_occurrences_confirmation_link",
        ),
        sa.CheckConstraint(
            "status <> 'postponed' OR manually_modified",
            name="ck_expected_occurrences_postponed_manual",
        ),
        sa.CheckConstraint(
            "NOT (status = 'pending' AND manually_modified)",
            name="ck_expected_occurrences_pending_automatic",
        ),
        sa.CheckConstraint(
            "status IN ('postponed', 'confirmed') OR due_on = scheduled_on",
            name="ck_expected_occurrences_due_date",
        ),
        sa.UniqueConstraint("rule_id", "scheduled_on", name="uq_expected_occurrences_rule_date"),
    )
    op.create_index("ix_expected_occurrences_rule_id", "expected_occurrences", ["rule_id"])
    op.create_index("ix_expected_occurrences_account_id", "expected_occurrences", ["account_id"])
    op.create_index(
        "ix_expected_occurrences_destination_account_id",
        "expected_occurrences",
        ["destination_account_id"],
    )
    op.create_index("ix_expected_occurrences_category_id", "expected_occurrences", ["category_id"])
    op.create_index(
        "ix_expected_occurrences_calendar",
        "expected_occurrences",
        ["due_on", "status", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_expected_occurrences_calendar", table_name="expected_occurrences")
    op.drop_table("expected_occurrences")
    op.drop_table("recurring_rules")
    sa.Enum(name="expected_occurrence_status").drop(op.get_bind())
    sa.Enum(name="recurrence_frequency").drop(op.get_bind())
