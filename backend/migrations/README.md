# Database migrations

Alembic owns schema evolution. Revision `0001_first_run_access` creates the
single-owner credential, server sessions, persistent login throttle and base
application settings used by release `0.1.0-alpha.1`. Revision
`0002_harden_access_invariants` adds database checks for session lifetime,
throttle counters and normalized currency while preserving initialized data.
