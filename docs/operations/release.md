# Release lifecycle

## 1.0.0 baseline

Hermes `1.0.0` is the first public stable release. It is a single-owner,
self-hosted application supported in a protected environment: loopback or a
trusted network, with a VPN or maintained HTTPS reverse proxy for remote
access. Direct public-internet exposure is unsupported.

The published release consists of an annotated git tag, GitHub Release notes,
and the source tree required to build the application with Docker Compose. The
release does not promise managed hosting, multi-user access, public exposure,
or an externally audited security posture.

## Supported baseline

The checked release environment uses Python 3.13, Node.js 22.23.1, npm 10.9.8,
PostgreSQL 17, Docker Engine 29, and Docker Compose v2. Development requires
Python 3.13 and a supported Node 22 release; deployment uses the pinned
PostgreSQL 17 and Node/Python image bases in the repository.

## Install, upgrade, and rollback

Follow the [deployment runbook](deployment.md) for a new installation. Before
an upgrade, read the GitHub Release notes and make a protected `.hermes` backup.
Confirm the backup can be opened before replacing the running application, then
checkout the intended annotated tag and run:

```bash
docker compose up -d --build
docker compose ps
curl --fail http://localhost:8000/api/v1/health
```

Alembic upgrades the schema before the application serves traffic. Do not roll
back application code after a schema upgrade. If rollback is needed, restore
the verified pre-upgrade backup as described in the
[backup-and-restore guide](backup-and-restore.md).

## Compatibility policy

Within `1.x`, compatible fixes use patch versions and additive, compatible
features use minor versions. A release must retain the ability to open backups
from earlier public `1.x` versions or explicitly document an upgrade path.
Published database migrations are never rewritten. Breaking changes wait for
the next major version and require explicit migration and backup guidance.

## Release checks

Before creating a public tag, run:

```bash
make test
make lint
make typecheck
make build
git diff --check
```

Run the PostgreSQL integration suite against a disposable PostgreSQL 17
instance, verify a production-like Compose startup, and record any checks that
could not be performed. Complete the owner acceptance on restored real data for
major releases.

Create an annotated tag only after these checks and publish the same commit to
GitHub. Attach concise release notes that include user-visible changes,
migrations, backup compatibility, verification, and known limits.
