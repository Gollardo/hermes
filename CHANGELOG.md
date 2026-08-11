# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project intends to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Recurring income, expense and transfer rules with daily, weekly, monthly and
  yearly frequencies, inclusive date bounds and optimistic editing.
- One-calendar-year idempotent occurrence materialization with persistent
  pending, postponed, cancelled and confirmed states.
- Monthly calendar, account/type filters, upcoming and overdue list, plus quick
  confirm, postpone and cancel actions.
- Atomic occurrence confirmation through the Operations posting contract and a
  durable link to the actual financial operation.
- Migration `0006_recurring_operations`, ADR 0003 and unit/integration/frontend
  coverage for recurrence, rule synchronization, concurrency and rollback.
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

- Calendar month reads now consume every bounded API page, while the limited
  upcoming list exposes its complete result count.
- Confirmed calendar items open their exact posted operation; narrow layouts
  show the action list first and keep all current navigation destinations visible.
- Scheduling and Operations now use explicit public posting/ledger contracts,
  deterministic concurrent lock ordering and constraint-specific delete errors.
- Common exact-money validation moved to `app.core` so Accounts, Operations,
  Funds and Scheduling share one no-float input contract.
- Account deletion and category type changes now preserve recurring-rule and
  expected-occurrence references.
- Posted operations linked to confirmed expected occurrences cannot be deleted
  independently.
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
