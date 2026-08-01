# Local development

## Prerequisites

- Python 3.13;
- Node.js 22.22.3+ within the Node 22 release line and npm 10+;
- Docker 29+ with Docker Compose v2-compatible CLI;
- GNU or BSD `make` and Git.

The versions above match the initialized environment. Angular's exact packages
are locked in `frontend/package-lock.json`; Python packages are hash-locked in
`backend/requirements*.lock`.

## Initial setup

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD before any non-local deployment.
make setup
```

`make setup` creates `.venv`, installs hash-verified backend development
dependencies and runs `npm ci`. Environment-file creation stays explicit so the
developer reviews the example before using its placeholder password.

## Development servers

```bash
make dev
```

This starts PostgreSQL, the FastAPI reload server at `http://localhost:8000`,
and Angular at `http://localhost:4200`. The Angular proxy forwards `/api` to the
backend, so application code uses a same-origin relative API base URL.
The proxy target defaults to host `localhost:8000`; development Compose sets
`HERMES_PROXY_TARGET=http://backend:8000` for container-to-container routing.

## Command interface

| Command | Effect |
| --- | --- |
| `make setup` | create local environment and install locked dependencies |
| `make dev` | foreground development Compose stack |
| `make up` | build/start production-like stack in background |
| `make down` | stop production and development stacks |
| `make logs` | follow production app/PostgreSQL logs |
| `make test` | all backend and frontend tests |
| `make test-backend` | pytest with coverage |
| `make test-frontend` | Angular/Vitest unit tests once |
| `make lint` | Ruff, formatting, ESLint, Prettier and docs links/fences |
| `make format` | apply Ruff and Prettier formatting |
| `make typecheck` | strict mypy and TypeScript checks |
| `make migrate` | apply Alembic revisions |
| `make migration name="..."` | autogenerate a reviewable revision |
| `make build` | build the production Compose image |

## Changing dependencies

Edit `backend/pyproject.toml`, then regenerate both lock files from a temporary or
existing environment containing `pip-tools`:

```bash
.venv/bin/pip-compile --generate-hashes --strip-extras \
  --output-file backend/requirements.lock backend/pyproject.toml
.venv/bin/pip-compile --generate-hashes --strip-extras --extra dev \
  --output-file backend/requirements-dev.lock backend/pyproject.toml
```

For frontend dependencies, use npm and commit both `package.json` and
`package-lock.json`. Use `npm ci`, not an unlocked install, in verification and
containers. The `overrides` for MCP SDK and Hono address a development-only
Angular CLI advisory and must be rechecked during Angular upgrades.

## Migrations

Run Alembic from `backend` through the Make targets. The foundation intentionally
has no revision because it defines no tables. Do not generate an empty migration.
Once a revision ships publicly, correct it with a later revision rather than
rewriting history.
