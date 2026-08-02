from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OperationType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    BALANCE_ADJUSTMENT = "balance_adjustment"


class FinancialOperation(Base):
    __tablename__ = "financial_operations"
    __table_args__ = (
        CheckConstraint("version > 0", name="ck_financial_operations_version_positive"),
        CheckConstraint(
            "reason IS NULL OR length(btrim(reason)) > 0",
            name="ck_financial_operations_reason_not_blank",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    type: Mapped[OperationType] = mapped_column(
        Enum(
            OperationType,
            name="financial_operation_type",
            values_callable=lambda values: [v.value for v in values],
        )
    )
    description: Mapped[str | None] = mapped_column(Text)
    reason: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
    )
    occurred_on: Mapped[date]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(default=1)


class AccountMovement(Base):
    __tablename__ = "account_movements"
    __table_args__ = (CheckConstraint("amount <> 0", name="ck_account_movements_amount_nonzero"),)

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    operation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("financial_operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
