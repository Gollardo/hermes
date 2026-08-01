# Deployment runbook

This is a production-like foundation, not a security-hardening guarantee or a
released upgrade contract.

## Prepare

1. Install Docker and Compose on the target host.
2. Copy `.env.example` to `.env` and replace `POSTGRES_PASSWORD` with a long,
   unique value. Restrict file permissions on the host.
3. Choose `APP_BIND_ADDRESS`. `0.0.0.0` permits LAN access; loopback is safer
   behind a local reverse proxy.
4. Arrange a VPN or HTTPS reverse proxy for any remote access.

Validate and start:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

Verify both API and Angular through the same port:

```bash
curl --fail http://localhost:8000/api/v1/health
curl --fail http://localhost:8000/
```

Inspect logs with `make logs`. The app waits for healthy PostgreSQL, applies
Alembic upgrades and then starts as a non-root user. PostgreSQL is not published
to the host.

## Stop and restart

```bash
docker compose stop
docker compose start
```

`docker compose down` removes containers/network but retains the named database
volume. Do not add `--volumes` unless intentionally destroying persistent data
after a verified backup.

## Upgrade outline

Before a future upgrade: read release notes, create and test a backup, pull or
checkout the intended version, then run `docker compose up -d --build`. Automatic
Alembic upgrade runs before the new process. A formal rollback guarantee does
not exist until releases and schema migrations exist.

See [backup and restore](backup-and-restore.md) and the
[security policy](../../SECURITY.md).
