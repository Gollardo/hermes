# Import, export and restore

## Owner-confirmed import direction

Future import supports CSV and Excel with column mapping, preview, account
selection, likely-duplicate detection and explicit confirmation before writes.
Parsing or previewing cannot mutate domain data. Confirmation delegates writes
to the owning modules and uses appropriate transaction boundaries.

Duplicate detection is advisory: “likely” matches must remain reviewable rather
than being silently discarded.

## Owner-confirmed backup direction

A full JSON export contains all data and is versioned. Its envelope includes at
least:

```text
format
schema_version
app_version
exported_at
```

Restore is transactional: either the complete validated backup becomes the
restored state or no restored changes remain. See the operational
[backup and restore runbook](../operations/backup-and-restore.md).

Money in JSON should use decimal strings when needed to avoid loss of precision.

## JSON backup format (schema 1)

`0.1.0-rc.1` implements `hermes-json-backup`, schema version `1`. The envelope
contains `format`, `schema_version`, `app_version`, `exported_at`, `data` and an
`integrity` object with a SHA-256 digest of canonical envelope content excluding
the integrity object itself. Money and percentages are JSON strings with no
binary floating-point conversion.

The digest detects accidental corruption; it is not a digital signature and
does not authenticate the file's author. Restore therefore treats every JSON
file as untrusted, applies strict size/schema/domain validation and still
requires destination-owner re-authentication.

The data section contains application settings, accounts, categories, financial
operation headers and physical movements, funds, fund events and virtual
movements, recurring rules and expected occurrences. Stable identifiers,
calendar dates, timestamps, archive state and optimistic versions are retained.
Optional fund targets and recurrence interval/weekday fields are included.
Schema 1 readers supply compatible defaults for backups written before these
fields existed. Fund-event validation preserves the distinct shapes of an
allocation into one account, redistribution of one fund between accounts, and
a transfer between two funds within one account.

Owner credential, password hash, login throttle and sessions are deliberately
excluded: they are security state of the destination instance, not portable
financial data. An initialized target re-authenticates its current owner through
the shared password throttle and ends other active sessions after restore. An
uninitialized target may instead use first-run restore: the destination owner
chooses a new master password, and the new credential/session plus restored
settings and financial data commit atomically. Excluding source authentication
state is the security-first MVP assumption pending owner review; importing it
remains outside scope.

Only schema 1 is accepted. Compatibility translation between backup schemas is
not implicit: a future version must add an explicit, tested reader before it
claims support.

## Boundaries

Imports owns staging and mapping, not accounts or ledger tables. Backup owns the
versioned envelope and validator and orchestrates narrow module-owned backup
persistence surfaces. Neither may bypass current domain invariants merely
because data came from a file.

## Open questions

- CSV dialects, date formats and locale-aware decimal parsing.
- Excel formats; JSON backup requests are currently limited to 50 MiB.
- Duplicate fingerprint and conflict-review UX.
- Forward/backward schema compatibility beyond exact schema 1 and encryption at rest.
