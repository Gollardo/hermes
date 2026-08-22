"""add one-off expected-operation plans

Revision ID: 0014_one_off_plans
Revises: 0013_fund_reserve
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_one_off_plans"
down_revision: str | None = "0013_fund_reserve"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    source_kind = sa.Enum("recurring", "one_off", name="expected_occurrence_source_kind")
    source_kind.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "expected_occurrences",
        sa.Column(
            "source_kind",
            source_kind,
            nullable=False,
            server_default="recurring",
        ),
    )
    op.alter_column("expected_occurrences", "rule_id", nullable=True)
    op.drop_constraint("uq_expected_occurrences_rule_date", "expected_occurrences", type_="unique")
    op.create_check_constraint(
        "ck_expected_occurrences_source_rule",
        "expected_occurrences",
        "(source_kind = 'recurring' AND rule_id IS NOT NULL) OR "
        "(source_kind = 'one_off' AND rule_id IS NULL)",
    )
    op.create_index(
        "uq_expected_occurrences_recurring_rule_date",
        "expected_occurrences",
        ["rule_id", "scheduled_on"],
        unique=True,
        postgresql_where=sa.text("source_kind = 'recurring'"),
    )
    op.drop_constraint(
        "ck_expected_occurrences_postponed_manual", "expected_occurrences", type_="check"
    )
    op.create_check_constraint(
        "ck_expected_occurrences_postponed_manual",
        "expected_occurrences",
        "source_kind = 'one_off' OR status <> 'postponed' OR manually_modified",
    )
    op.drop_constraint(
        "ck_expected_occurrences_pending_automatic", "expected_occurrences", type_="check"
    )
    op.create_check_constraint(
        "ck_expected_occurrences_pending_automatic",
        "expected_occurrences",
        "source_kind = 'one_off' OR NOT (status = 'pending' AND manually_modified)",
    )
    op.drop_constraint("ck_expected_occurrences_due_date", "expected_occurrences", type_="check")
    op.create_check_constraint(
        "ck_expected_occurrences_due_date",
        "expected_occurrences",
        "source_kind = 'one_off' OR status IN ('postponed', 'confirmed') "
        "OR due_on = scheduled_on + series_shift_days",
    )
    op.drop_constraint(
        "ck_expected_occurrences_series_shift_preservation",
        "expected_occurrences",
        type_="check",
    )
    op.create_check_constraint(
        "ck_expected_occurrences_series_shift_preservation",
        "expected_occurrences",
        "source_kind = 'one_off' OR NOT preserve_from_series_shift "
        "OR (status = 'cancelled' AND NOT manually_modified)",
    )
    op.alter_column("expected_occurrences", "source_kind", server_default=None)


def downgrade() -> None:
    has_one_off_plans = op.get_bind().scalar(
        sa.text("SELECT EXISTS (SELECT 1 FROM expected_occurrences WHERE source_kind = 'one_off')")
    )
    if has_one_off_plans:
        raise RuntimeError(
            "Cannot downgrade 0014_one_off_plans while one-off plans exist; "
            "remove or restore them before downgrading."
        )
    op.drop_index("uq_expected_occurrences_recurring_rule_date", table_name="expected_occurrences")
    op.drop_constraint("ck_expected_occurrences_source_rule", "expected_occurrences", type_="check")
    op.drop_constraint(
        "ck_expected_occurrences_series_shift_preservation",
        "expected_occurrences",
        type_="check",
    )
    op.create_check_constraint(
        "ck_expected_occurrences_series_shift_preservation",
        "expected_occurrences",
        "NOT preserve_from_series_shift OR (status = 'cancelled' AND NOT manually_modified)",
    )
    op.drop_constraint("ck_expected_occurrences_due_date", "expected_occurrences", type_="check")
    op.create_check_constraint(
        "ck_expected_occurrences_due_date",
        "expected_occurrences",
        "status IN ('postponed', 'confirmed') OR due_on = scheduled_on + series_shift_days",
    )
    op.drop_constraint(
        "ck_expected_occurrences_pending_automatic", "expected_occurrences", type_="check"
    )
    op.create_check_constraint(
        "ck_expected_occurrences_pending_automatic",
        "expected_occurrences",
        "NOT (status = 'pending' AND manually_modified)",
    )
    op.drop_constraint(
        "ck_expected_occurrences_postponed_manual", "expected_occurrences", type_="check"
    )
    op.create_check_constraint(
        "ck_expected_occurrences_postponed_manual",
        "expected_occurrences",
        "status <> 'postponed' OR manually_modified",
    )
    op.create_unique_constraint(
        "uq_expected_occurrences_rule_date",
        "expected_occurrences",
        ["rule_id", "scheduled_on"],
    )
    op.alter_column("expected_occurrences", "rule_id", nullable=False)
    op.drop_column("expected_occurrences", "source_kind")
    sa.Enum(name="expected_occurrence_source_kind").drop(op.get_bind(), checkfirst=True)
