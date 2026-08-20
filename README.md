# Hermes

Hermes is an early-stage, single-owner, self-hosted web application for personal
finance. It is intended for a home server or local computer and keeps its data
independent of external cloud services.

Its long-term north star is decision-first planning: not only showing where
money went, but helping the owner understand what will happen if they make a
financial decision. The future **Oracle · What if?** capability will compare
hypothetical scenarios with the deterministic baseline forecast; it is planned,
not part of the current release.

> **Current internal version:** `0.4.6` balances dynamic fund allocations by
> relative target progress and corrects long recurring-rule checkbox alignment.
> Versions through `0.4.6` are development milestones; no public GitHub release
> has been published yet.

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
- income/expense category trees with archive-safe lifecycle rules;
- income, expense, transfer and balance-adjustment CRUD with exact movements;
- collapsible journal filters, details and pagination with optimistic edit protection;
- virtual funds, physical/free coverage, manual or target-aware dynamic
  percentage allocation, redistribution between accounts and funds, and progress;
- recurring income, expense and transfer rules with selectable weekly weekdays,
  weekly/monthly intervals, exact dated snapshots and optional series shifting;
- exact addition and subtraction directly in operation and scheduling amount
  fields, with comma and dot decimal separators;
- monthly calendar, upcoming/overdue list and confirm/postpone/cancel actions;
- idempotent confirmation that atomically links one posted financial operation;
- per-account and combined balance forecasts with five horizons, risk warnings
  and exact explanations for every changing date;
- income/expense reports for a month or custom period, with category drill-down;
- an optional default account for new income and expense operations;
- protected `.hermes` and explicit plaintext JSON export, preview and
  transactional restore.

## Planned directions

- deterministic “What if?” decision scenarios with optional local-language
  assistance that never replaces exact financial calculation;
- simplified loans, installment plans and two-way debts;
- staged CSV/Excel import with preview and duplicate review;
- operation templates, improved search and saved filters;
- automatic and rotated local backups;
- release hardening for upgrades, reverse proxies and published container images.

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

Review and replace the example database password in `.env`. For a loopback-only
plain-HTTP run, also set `HERMES_COOKIE_SECURE=false`; keep it `true` when the
browser reaches Hermes through HTTPS. Then run:

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
