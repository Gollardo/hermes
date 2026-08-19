"""add recurring series shift policy

Revision ID: 0012_recurring_series_shift
Revises: 0011_dynamic_fund_allocation
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012_recurring_series_shift"
down_revision: str | None = "0011_dynamic_fund_allocation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recurring_rules",
        sa.Column(
            "shift_future_on_postpone",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.add_column(
        "recurring_rules",
        sa.Column("series_shift_days", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "expected_occurrences",
        sa.Column("series_shift_days", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "expected_occurrences",
        sa.Column(
            "preserve_from_series_shift",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_expected_occurrences_series_shift_preservation",
        "expected_occurrences",
        "NOT preserve_from_series_shift OR (status = 'cancelled' AND NOT manually_modified)",
    )
    op.create_index(
        "ix_expected_occurrences_series_shift_candidates",
        "expected_occurrences",
        ["rule_id", "scheduled_on", "id"],
        postgresql_where=sa.text(
            "status = 'pending' OR "
            "(status = 'cancelled' AND NOT manually_modified "
            "AND NOT preserve_from_series_shift)"
        ),
    )
    op.drop_constraint("ck_expected_occurrences_due_date", "expected_occurrences", type_="check")
    op.create_check_constraint(
        "ck_expected_occurrences_due_date",
        "expected_occurrences",
        "status IN ('postponed', 'confirmed') OR due_on = scheduled_on + series_shift_days",
    )
    op.alter_column("recurring_rules", "shift_future_on_postpone", server_default=None)
    op.alter_column("recurring_rules", "series_shift_days", server_default=None)
    op.alter_column("expected_occurrences", "series_shift_days", server_default=None)
    op.alter_column("expected_occurrences", "preserve_from_series_shift", server_default=None)


def downgrade() -> None:
    op.drop_index(
        "ix_expected_occurrences_series_shift_candidates",
        table_name="expected_occurrences",
    )
    op.drop_constraint(
        "ck_expected_occurrences_series_shift_preservation",
        "expected_occurrences",
        type_="check",
    )
    op.drop_constraint("ck_expected_occurrences_due_date", "expected_occurrences", type_="check")
    op.execute(
        "UPDATE expected_occurrences SET due_on = scheduled_on "
        "WHERE status NOT IN ('postponed', 'confirmed')"
    )
    op.create_check_constraint(
        "ck_expected_occurrences_due_date",
        "expected_occurrences",
        "status IN ('postponed', 'confirmed') OR due_on = scheduled_on",
    )
    op.drop_column("expected_occurrences", "series_shift_days")
    op.drop_column("expected_occurrences", "preserve_from_series_shift")
    op.drop_column("recurring_rules", "series_shift_days")
    op.drop_column("recurring_rules", "shift_future_on_postpone")
