# Hermes

Hermes is an early-stage, single-owner, self-hosted web application for personal
finance. It is intended for a home server or local computer and keeps its data
independent of external cloud services.

> **Early development:** only the project foundation and a health-check UI
> exist. Financial workflows, authentication and stable data schemas are not
> implemented yet.

## Planned capabilities

- accounts backed by a financial-operation ledger;
- categories and subcategories;
- income, expenses, transfers and balance adjustments;
- virtual funds distributed across physical accounts;
- expected and recurring operations, calendar and balance forecasts;
- simplified loans, installment plans and two-way debts;
- reports, staged CSV/Excel import and versioned JSON backup/restore;
- one local owner authenticated by an Argon2id password and server-side session.

## Stack

- Python 3.13, FastAPI, SQLAlchemy 2, Alembic, Pydantic and PostgreSQL;
- Angular 22 with standalone components and strict TypeScript;
- pytest, Ruff, mypy, ESLint, Prettier and Vitest;
- Docker and Docker Compose; modular-monolith architecture.

## Quick start for development

Requirements: Python 3.13, Node.js 22.22.3 or newer within the Angular-supported
Node 22 line, npm and Docker Compose.

```bash
cp .env.example .env
make setup
make dev
```

Open `http://localhost:4200`. The frontend dev server proxies `/api` to the
backend on `http://localhost:8000`.

## Production-like Compose run

Review and replace the example database password in `.env`, then run:

```bash
make up
```

Open `http://localhost:8000`. Angular and the API share that one entrypoint.
PostgreSQL is available only inside the Compose network. Stop services with
`make down`.

## Documentation

- [Current project status](docs/project-status.md)
- [Development roadmap](docs/roadmap.md)
- [Documentation map](docs/index.md)
- [Architecture overview](docs/architecture/overview.md)
- [Local development](docs/operations/local-development.md)
- [Contribution guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## License

Copyright holders license Hermes under
[GNU Affero General Public License v3.0 or later](LICENSE), SPDX identifier
`AGPL-3.0-or-later`.
