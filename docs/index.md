# Hermes engineering documentation

This documentation records durable architectural knowledge, domain language,
invariants and operating procedures. It intentionally avoids speculative API,
DTO and table catalogues.

## Architecture

- [Overview](architecture/overview.md)
- [Module boundaries](architecture/module-boundaries.md)
- [Data flows](architecture/data-flow.md)
- [Deployment](architecture/deployment.md)

## Domains

- [Authentication](domains/authentication.md)
- [Accounts](domains/accounts.md)
- [Operations](domains/operations.md)
- [Categories](domains/categories.md)
- [Virtual funds](domains/funds.md)
- [Scheduling](domains/scheduling.md)
- [Forecasting](domains/forecasting.md)
- [Liabilities and debts](domains/liabilities-and-debts.md)
- [Import and export](domains/import-export.md)

## Decisions and operations

- [ADR registry and candidates](decisions/README.md)
- [Local development](operations/local-development.md)
- [Deployment runbook](operations/deployment.md)
- [Backup and restore](operations/backup-and-restore.md)

Each document distinguishes owner-confirmed rules, initialization decisions,
assumptions, open questions and future work where those categories apply.
