# Deployment runbook

This is the deployment path for the alpha release, not a complete
security-hardening guarantee.

## Prepare

1. Install Docker and Compose on the target host.
2. Copy `.env.example` to `.env` and replace `POSTGRES_PASSWORD` with a long,
   unique value. Restrict file permissions on the host.
3. Keep `APP_BIND_ADDRESS=127.0.0.1` through the one-time setup. A fresh
   instance has no owner credential yet, so publishing it on a LAN would let
   another network client claim the first setup.
4. Arrange a VPN or HTTPS reverse proxy for any remote access.
5. Keep `HERMES_COOKIE_SECURE=true` whenever the browser uses HTTPS. For a
   loopback-only plain-HTTP check, explicitly set it to `false`; never combine
   that override with a LAN-facing bind address.

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

On a clean database, opening the Angular URL presents the one-time setup screen.
After setup, subsequent browsers see the master-password login screen. The app
container applies all migrations through the current Alembic head
automatically before serving traffic.

Complete setup from the host over loopback before changing `APP_BIND_ADDRESS`.
Only after setup may an operator deliberately use `0.0.0.0` for LAN access, and
then only behind the VPN or HTTPS controls described above. Restoring an empty
database reopens setup and requires repeating this trusted-loopback procedure.

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

Before an upgrade: read release notes, create and test a backup, pull or checkout
the intended version, then run `docker compose up -d --build`. Automatic Alembic
upgrade runs before the new process. Downgrading application code after a schema
upgrade is not guaranteed; restore the verified pre-upgrade backup if rollback
is required.

See [backup and restore](backup-and-restore.md) and the
[security policy](../../SECURITY.md).
