# Hermes engineering documentation

This documentation records durable architectural knowledge, domain language,
invariants and operating procedures. It intentionally avoids speculative API,
DTO and table catalogues.

## Planning and current state

- [Project status](project-status.md) records the factual, currently verified
  state, active milestone, known limitations, risks and next recommended action.
- [Roadmap](roadmap.md) records the intended sequence and scope of milestones. It
  is not a calendar commitment or a substitute for detailed domain design.

Start development work by comparing the requested change with both documents.
When a meaningful change alters implemented capabilities, verification results,
risks or the next action, update the project status in the same change. Update
the roadmap only when milestone scope, order or completion changes, and mark an
item complete only after its stated user scenario and checks are complete.

Architecture and domain documents remain authoritative for confirmed decisions
and invariants. A planned roadmap item does not override them or resolve an open
question by itself.

## Architecture

- [Overview](architecture/overview.md)
- [Module boundaries](architecture/module-boundaries.md)
- [Data flows](architecture/data-flow.md)
- [Deployment](architecture/deployment.md)

## Domains

- [Authentication](domains/authentication.md)
- [Application settings](domains/settings.md)
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
