# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project intends to follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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
