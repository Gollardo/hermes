# Backup and restore

## Current status

The owner-confirmed target is a full, versioned JSON export with transactional
restore. That application feature is **not implemented** in the foundation. Its
required envelope and open format questions are documented in
[import and export](../domains/import-export.md).

Until then, a PostgreSQL dump is the only complete technical backup. It is
database-version dependent and is not the promised portable JSON format.

## Interim PostgreSQL backup

Choose a protected host directory with enough space, then run:

```bash
docker compose exec -T postgres sh -c \
  'pg_dump --format=custom --create --clean --if-exists \
  --username="$POSTGRES_USER" "$POSTGRES_DB"' > hermes.dump
```

Protect `hermes.dump` like the live financial database. Record the app commit or
version, PostgreSQL image version and backup time. Copy it to separate protected
storage and test restoration periodically.

## Interim PostgreSQL restore

Restore **overwrites the database named in the dump**. Verify the target Compose
project and backup file first, take another backup if possible, and stop the app:

```bash
docker compose stop app
docker compose exec -T postgres sh -c \
  'pg_restore --clean --if-exists --create --dbname=postgres \
  --username="$POSTGRES_USER"' < hermes.dump
docker compose start app
```

Then inspect logs and verify `/api/v1/health`. A successful health response does
not prove financial correctness; future restore verification must include schema
version and domain-level counts/invariants.

## Required future JSON restore behavior

1. Read and validate `format`, `schema_version`, `app_version` and `exported_at`.
2. Reject unsupported or malformed input before mutation.
3. Validate all module data and exact decimal representations.
4. Restore all module state inside one database transaction.
5. Recheck cross-module invariants and commit once; roll back everything on any
   failure.
6. Invalidate restored sessions unless a later explicit decision says otherwise.

Step 6 is a security assumption, not yet an owner-approved backup rule.
