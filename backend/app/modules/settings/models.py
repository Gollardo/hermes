from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FundAllocationMode(StrEnum):
    MANUAL = "manual"
    DYNAMIC = "dynamic"


class ApplicationSettings(Base):
    __tablename__ = "application_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_application_settings_singleton"),
        CheckConstraint(
            "base_currency ~ '^[A-Z]{3}$'",
            name="ck_application_settings_base_currency",
        ),
        CheckConstraint(
            "fund_allocation_mode IN ('manual', 'dynamic')",
            name="ck_application_settings_fund_allocation_mode",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    fund_allocation_mode: Mapped[FundAllocationMode] = mapped_column(
        String(16), nullable=False, default=FundAllocationMode.MANUAL
    )
    default_account_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
    )
    base_currency_locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
