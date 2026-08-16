# Hermes

Hermes is an early-stage, single-owner, self-hosted web application for personal
finance. It is intended for a home server or local computer and keeps its data
independent of external cloud services.

> **Current version:** `0.2.0` adds faster operation entry, a default account,
> income/expense reports and fund-balance planning alongside safer idle sessions
> and owner-confirmed presentation conventions for dates, currencies and planning balances.

## Project priorities and contributions

Hermes is first and foremost a personal project. Its direction and development
priorities follow the maintainer's own needs and use of the application.

Issues and pull requests are welcome, but there is no guaranteed response time,
review schedule or commitment to implement requested features. Contributions
and suggestions may be considered when they align with the project's direction
and the maintainer's available time.

## Current capabilities

- one-time setup with atomic JSON restore or a fresh start with optional expense
  category templates, a master password, base currency and IANA timezone;
- Argon2id password storage and revocable server-side browser sessions;
- protected API and application shell, login throttling and session termination;
- base settings and master-password changes;
- cash, debit and savings accounts with derived balances and archive/restore;
- exact initial-balance adjustments stored in the operation ledger;
- income/expense category trees with archive-safe lifecycle rules.
- income, expense, transfer and balance-adjustment CRUD with exact movements;
- collapsible journal filters, details and pagination with optimistic edit protection.
- virtual funds, physical/free coverage, explicit percentage allocation and
  virtual redistribution between accounts and funds, optional targets and progress.
- recurring income, expense and transfer rules with selectable weekly weekdays,
  weekly/monthly intervals and exact dated snapshots;
- monthly calendar, upcoming/overdue list and confirm/postpone/cancel actions;
- idempotent confirmation that atomically links one posted financial operation.
- per-account and combined balance forecasts with five horizons, risk warnings
  and exact explanations for every changing date.
- full versioned JSON export, preview and transactional restore.

## Planned financial capabilities

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
