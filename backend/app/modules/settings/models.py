from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ApplicationSettings(Base):
    __tablename__ = "application_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="ck_application_settings_singleton"),
        CheckConstraint(
            "base_currency ~ '^[A-Z]{3}$'",
            name="ck_application_settings_base_currency",
        ),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False)
    default_account_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
    )
    base_currency_locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
