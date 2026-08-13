from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.auth.contracts import IssuedSession, setup_owner
from app.modules.backup.contracts import BackupDocument, preview_backup, restore_backup
from app.modules.categories.contracts import OnboardingExpenseGroup, create_onboarding_categories


def initialize_fresh_application(
    session: Session,
    settings: Settings,
    *,
    master_password: str,
    base_currency: str,
    timezone: str,
    create_default_categories: bool,
    onboarding_expense_groups: list[OnboardingExpenseGroup],
) -> IssuedSession:
    """Create access state and optional owner-selected directories in one transaction."""
    issued = setup_owner(
        session,
        settings,
        master_password=master_password,
        base_currency=base_currency,
        timezone=timezone,
    )
    if create_default_categories:
        create_onboarding_categories(session, onboarding_expense_groups)
    return issued


def initialize_application_from_backup(
    session: Session,
    settings: Settings,
    *,
    master_password: str,
    backup: BackupDocument,
) -> IssuedSession:
    """Validate and restore a fresh instance without committing a partial setup."""
    preview_backup(backup)
    issued = setup_owner(
        session,
        settings,
        master_password=master_password,
        base_currency=backup.data.settings.base_currency,
        timezone=backup.data.settings.timezone,
    )
    restore_backup(session, backup)
    return issued
