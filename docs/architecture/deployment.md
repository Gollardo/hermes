# Deployment architecture

## Production-like Compose

```mermaid
flowchart LR
    Browser["Desktop or mobile browser"] -->|"HTTP :8000"| App["app container\nFastAPI + Angular build"]
    App -->|"private Compose network :5432"| Postgres[("postgres container")]
    Postgres --> Volume["named PostgreSQL volume"]
```

The multi-stage Dockerfile compiles Angular, installs hash-locked Python
dependencies and produces one non-root application image. At startup the app
runs `alembic upgrade head` before Uvicorn. Only the app port is published;
PostgreSQL has no host port.

Compose health checks PostgreSQL with `pg_isready` and the application through
`GET /api/v1/health`. The current HTTP endpoint reports process readiness; the
dependency order and PostgreSQL health check cover startup database readiness.

## Development Compose

```mermaid
flowchart LR
    Browser -->|":4200"| Frontend["Angular dev server"]
    Frontend -->|"proxy /api"| Backend["FastAPI reload server :8000"]
    Backend --> Postgres[("PostgreSQL")]
    Source["bind-mounted source"] --> Frontend
    Source --> Backend
```

Development publishes frontend and backend on loopback, bind-mounts source and
uses separate named volumes for PostgreSQL and frontend dependencies.

## Security boundary

The owner-confirmed current-release boundary is a protected environment. For
remote access, put the single app entrypoint behind a VPN or HTTPS reverse
proxy; direct public-internet exposure is unsupported. Never publish PostgreSQL merely
for convenience; use an explicit local override and loopback binding if an
administrator genuinely needs host database access.

Production defaults session and CSRF cookies to `Secure`. Plain-HTTP loopback
testing can explicitly set `HERMES_COOKIE_SECURE=false`; do not use that override
for LAN or remote access. State-changing requests rely on same-origin Angular
delivery plus the per-session CSRF cookie/header pair.

Production-like Compose binds to loopback by default. Initial setup must complete
over that trusted local path before an operator deliberately publishes the app
through a LAN, VPN or HTTPS reverse proxy; otherwise another network client could
claim the single owner credential first.

## Open questions

- Supported reverse proxies and forwarded-header configuration.
- Container image publishing, signing and supported CPU architectures.
- Migration failure recovery and rollback policy for the pre-1.0 release line.
- Whether health should later expose separate liveness and database-readiness
  endpoints without leaking operational detail.
