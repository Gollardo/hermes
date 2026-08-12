# Backup and restore

## Application JSON backup

Open **Настройки → Экспорт и восстановление** and select **Скачать проверенный
backup**. Store the JSON file outside the Hermes host, protect it as financial
data and periodically test it on a separately initialized instance. The file is
not encrypted by Hermes.

To restore, initialize the destination instance, sign in, choose the JSON file
and review the count/currency/timezone summary. Type `ЗАМЕНИТЬ ВСЕ ДАННЫЕ`, enter
the destination instance's current master password and confirm. Current
financial and planning data is replaced; the current owner credential and
current session are retained, while other sessions are ended. A checksum,
strict schema and references are checked
before mutation. Table locks, one database transaction and post-write domain
checks guarantee that a failed restore leaves the old data intact.
The UI and API reject JSON backup payloads larger than 50 MiB before parsing.
The SHA-256 digest detects accidental corruption but is not an authenticity
signature, so only restore files from a trusted source.

Schema 1 restore accepts only `hermes-json-backup`. Keep an old application
image available when retaining older backup formats; no compatibility beyond
schema 1 is currently promised.

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

## Implemented JSON restore behavior

1. Read and validate `format`, `schema_version`, `app_version` and `exported_at`.
2. Reject unsupported or malformed input before mutation.
3. Validate all module data and exact decimal representations.
4. Restore all module state inside one database transaction.
5. Recheck cross-module invariants and commit once; roll back everything on any
   failure.
6. Preserve the destination credential and current session, import no
   authentication state and end other sessions after successful replacement.
