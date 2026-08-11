# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project intends to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Virtual fund definitions, per-account ledger positions and coverage summary.
- Exact allocation preview with manual correction and documented round-down
  remainder policy.
- Atomic fund-aware expenses/transfers, virtual redistribution and complete
  fund movement history.
- Migration `0005_virtual_funds` plus upgrade/downgrade, rollback, concurrency,
  integration and frontend coverage for the alpha.4 invariants.
- Financial posting model ADR with explicit alpha assumptions and invariants.
- Atomic income, expense, transfer and balance-adjustment CRUD.
- Filtered, paginated operation journal with details and responsive Angular UI.
- Migration `0004_financial_operations`, optimistic operation versions and
  clean/existing-database PostgreSQL coverage.
- Account creation, list, derived balance, edit, archive/restore and safe deletion.
- Exact initial balances posted as atomic `balance_adjustment` operations.
- Income and expense category trees with subcategories, editing and archival.
- Authenticated Angular screens for accounts and categories.
- Migration `0003_accounts_categories` and PostgreSQL/unit/frontend coverage.

### Changed

- Account balances now include all ordinary journal movements; the conservative
  alpha policy rejects mutations that would leave an affected account negative.
- Base currency now locks on the first account write; categories remain currency-independent.
- Financial JSON values use decimal strings and reject binary floating-point input.
- Balance correction now accepts the expected balance in the UI and posts an
  exact calculated ledger delta with current/difference preview.
- Calendar defaults and migration use the configured application timezone.
- Historical category types and concurrent account deletion are protected by
  operation-aware lifecycle checks and shared locking conventions.
- Journal rows show transfer direction, retain existing archived references and
  preserve visible rows while another page loads.

## [0.1.0-alpha.1] - 2026-08-02

### Added

- One-time first-run setup for master password, base currency and timezone.
- Argon2id owner credential, persistent login throttling and revocable server-side sessions.
- HttpOnly session cookies plus double-submit CSRF protection for state-changing requests.
- Authenticated settings UI for preferences, password changes and session termination.
- Initial access/settings schema plus an initialized-data hardening migration.
- PostgreSQL integration coverage for migration, session expiry and concurrent
  throttle/currency-lock invariants.

### Security

- Production-like Compose binds to loopback until the owner deliberately exposes
  an initialized instance.
- Successful authenticated responses and cookies are sent only after database
  commit; currency locking is serialized against concurrent settings updates.
