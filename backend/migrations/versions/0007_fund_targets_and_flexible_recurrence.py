"""Add fund targets and flexible recurrence parameters.

Revision ID: 0007_fund_targets_recurrence
Revises: 0006_recurring_operations
Create Date: 2026-08-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_fund_targets_recurrence"
down_revision: str | None = "0006_recurring_operations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE fund_event_type ADD VALUE IF NOT EXISTS 'fund_transfer'")
    op.add_column("funds", sa.Column("target_amount", sa.Numeric(20, 4)))
    op.create_check_constraint(
        "ck_funds_target_amount_positive", "funds", "target_amount IS NULL OR target_amount > 0"
    )
    op.add_column(
        "recurring_rules",
        sa.Column("interval", sa.SmallInteger(), server_default="1", nullable=False),
    )
    op.add_column(
        "recurring_rules",
        sa.Column("weekdays", postgresql.ARRAY(sa.SmallInteger()), nullable=True),
    )
    op.execute(
        "UPDATE recurring_rules SET weekdays = ARRAY[extract(isodow from start_on)::smallint] "
        "WHERE frequency = 'weekly'"
    )
    op.create_check_constraint(
        "ck_recurring_rules_interval", "recurring_rules", "interval BETWEEN 1 AND 3"
    )
    op.create_check_constraint(
        "ck_recurring_rules_interval_frequency",
        "recurring_rules",
        "frequency IN ('weekly', 'monthly') OR interval = 1",
    )
    op.create_check_constraint(
        "ck_recurring_rules_weekdays",
        "recurring_rules",
        "(frequency = 'weekly' AND weekdays IS NOT NULL AND cardinality(weekdays) BETWEEN 1 AND 7 "
        "AND weekdays <@ ARRAY[1,2,3,4,5,6,7]::smallint[]) OR "
        "(frequency <> 'weekly' AND weekdays IS NULL)",
    )
    op.create_check_constraint(
        "ck_recurring_rules_weekdays_unique",
        "recurring_rules",
        "weekdays IS NULL OR cardinality(weekdays) = "
        "(CASE WHEN 1 = ANY(weekdays) THEN 1 ELSE 0 END + "
        "CASE WHEN 2 = ANY(weekdays) THEN 1 ELSE 0 END + "
        "CASE WHEN 3 = ANY(weekdays) THEN 1 ELSE 0 END + "
        "CASE WHEN 4 = ANY(weekdays) THEN 1 ELSE 0 END + "
        "CASE WHEN 5 = ANY(weekdays) THEN 1 ELSE 0 END + "
        "CASE WHEN 6 = ANY(weekdays) THEN 1 ELSE 0 END + "
        "CASE WHEN 7 = ANY(weekdays) THEN 1 ELSE 0 END)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_recurring_rules_weekdays_unique", "recurring_rules", type_="check")
    op.drop_constraint("ck_recurring_rules_weekdays", "recurring_rules", type_="check")
    op.drop_constraint("ck_recurring_rules_interval_frequency", "recurring_rules", type_="check")
    op.drop_constraint("ck_recurring_rules_interval", "recurring_rules", type_="check")
    op.drop_column("recurring_rules", "weekdays")
    op.drop_column("recurring_rules", "interval")
    op.drop_constraint("ck_funds_target_amount_positive", "funds", type_="check")
    op.drop_column("funds", "target_amount")
    # PostgreSQL enum values cannot be removed safely in-place. The historical
    # value remains unused after downgrade, matching earlier enum migrations.
