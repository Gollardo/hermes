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

## Boundaries

Imports owns staging and mapping, not accounts or ledger tables. Backup
orchestrates module-owned versioned representations. Neither may bypass current
domain invariants merely because data came from a file.

## Open questions

- CSV dialects, date formats and locale-aware decimal parsing.
- Excel formats and maximum safe upload size.
- Duplicate fingerprint and conflict-review UX.
- Whether backups include owner credential/session data; sessions should likely
  be excluded, but this is not confirmed.
- Forward/backward schema compatibility, migrations and encryption at rest.
