# Architecture Decision Records

ADR records a durable decision with meaningful alternatives and consequences.
Create one when a choice changes architecture, data semantics, deployment or a
cross-module contract. Do not manufacture past meetings or mark a proposal as
accepted without an explicit project-owner decision.

## Release implementation decisions

- [ADR 0001: Financial posting model for 0.1.0-alpha.3](0001-financial-posting-model.md)
  records the posting model and the owner-confirmed non-negative balance policy
  for the current release; overdraft remains a separate future design.
- [ADR 0002: Virtual fund ledger and allocation policy](0002-virtual-fund-ledger.md)
  records the owner-confirmed virtual posting, coverage, rounding and archive
  model for the current release.
- [ADR 0003: Recurring rules and expected occurrences](0003-recurring-rules-and-occurrences.md)
  records the owner-confirmed recurrence limits, materialization, rule-edit and
  confirmation policies for the current release.
- [ADR 0004: Encrypted Hermes backup envelope](0004-encrypted-backup-envelope.md)
  records the owner-confirmed two-level key architecture, protected V1 format,
  legacy JSON compatibility and untrusted-file limits.

## Template for a future ADR

```markdown
# ADR-NNN: Short decision title

- Status: proposed | accepted | superseded | rejected
- Date: YYYY-MM-DD
- Decision owners: names or roles that actually participated

## Context

What forces and constraints require a decision? Separate confirmed facts from
assumptions.

## Decision

What is chosen and what is explicitly not chosen?

## Alternatives considered

List credible alternatives and why they were not selected.

## Consequences

Positive, negative, operational and migration consequences.

## Open questions

Anything intentionally deferred.
```

## Candidate register

The entries below are candidates, not retroactively accepted ADRs. Unless a
candidate is explicitly linked to an implementation decision below, its status
is `proposed` even where the owner has supplied a strong direction; formal
consequences and unresolved details still require review.
Candidates ADR-003, ADR-004 and ADR-006 predate the numbered implementation
decisions above. They are retained as discovery history, but ADR 0001, 0002 and
0003 are the authoritative records of the implemented baselines.

### ADR-001 Modular monolith

- **Status:** proposed
- **Context:** a self-hosted single-owner application has many finance domains
  but one deployment lifecycle; distributed operations would add unjustified
  failure modes and administration.
- **Proposed choice:** one modular monolith with explicit public module
  boundaries and one transactional PostgreSQL database.
- **Known alternatives:** unstructured monolith; microservices; separate worker
  services.
- **Questions:** enforcement mechanism for private boundaries; which
  cross-module read contracts remain stable; criteria for ever revisiting the
  deployment boundary.

### ADR-002 PostgreSQL as the only supported database

- **Status:** proposed
- **Context:** financial invariants require reliable transactions and a single
  support target. Supporting divergent SQL dialects would multiply schema and
  locking behavior.
- **Proposed choice:** PostgreSQL is the sole production and test database; do
  not add SQLite compatibility.
- **Known alternatives:** SQLite for local use; MySQL/MariaDB; a database
  abstraction supporting several engines.
- **Questions:** first supported PostgreSQL major versions; extension policy;
  transaction isolation and locking conventions.

### ADR-003 Ledger-derived account balances

- **Status:** implemented baseline recorded by ADR 0001; immutable change
  history is explicitly not required for the current product
- **Context:** freely editable balance fields can drift from operation history.
  The owner confirmed operation history as source of truth and initial balance
  as an adjustment operation.
- **Proposed choice:** derive physical account balance from posted money
  movements; never expose direct balance mutation.
- **Known alternatives:** mutable balance column; cached balance projection with
  reconciliation; full accounting double-entry ledger.
- **Questions:** whether and how to cache; future reconciliation requirements
  if the product scope changes.

### ADR-004 Virtual fund allocation model

- **Status:** accepted current-release policy recorded by ADR 0002
- **Context:** funds earmark real account money, can span accounts and must move
  atomically with relevant physical operations.
- **Proposed choice:** represent per-account virtual fund movements and derive
  fund positions; enforce percentage and physical-coverage invariants.
- **Known alternatives:** funds as accounts; a mutable allocation snapshot;
  envelope-only totals without account placement.
- **Questions:** future lifecycle of explicit allocation events beyond the
  accepted rounding, remainder, ownership and coverage rules.

### ADR-005 Single-user server-side authentication

- **Status:** proposed
- **Context:** the deployment has one local owner and no need for identity
  federation, registration, roles or tenants.
- **Proposed choice:** first-run Argon2id credential plus revocable server-side
  sessions identified by HttpOnly cookies.
- **Known alternatives:** JWT bearer tokens; HTTP Basic authentication; reverse
  proxy authentication; multi-user identity model.
- **Implemented alpha baseline:** seven-day database sessions, hashed opaque
  tokens, SameSite cookies, double-submit CSRF, 30-minute idle expiry and
  persistent instance-wide throttling. These are documented release
  assumptions, not a retroactively accepted ADR.
- **Questions:** recovery flow, reverse-proxy cookie behavior and whether the
  current lifetime/idle/throttle defaults should become long-term policy.

### ADR-006 Expected occurrence materialization

- **Status:** accepted current-release policy recorded by ADR 0003
- **Context:** recurring intent must be visible and adjustable without changing
  actual balances until confirmation.
- **Proposed choice:** materialize dated expected occurrences with lifecycle
  states; confirmation atomically creates and links one posted operation.
- **Known alternatives:** calculate recurrences only on read; post future
  operations immediately; use an external scheduler/queue.
- **Questions:** future richer recurrence expressions, background
  materialization and timezone migration.

### ADR-007 Angular production build delivery

- **Status:** proposed
- **Context:** users should access one port while development benefits from the
  Angular dev server.
- **Proposed choice:** multi-stage build copies Angular browser assets into the
  FastAPI application image, which serves them after `/api` routes.
- **Known alternatives:** Nginx/Caddy sidecar; separately exposed frontend;
  server-side rendering.

### ADR-008 Deterministic what-if scenario boundary

- **Status:** proposed candidate; product direction confirmed, detailed design
  not accepted
- **Context:** Hermes should compare the consequences of a hypothetical
  financial decision without changing actual facts or confirmed plans.
- **Proposed choice:** apply structured hypothetical changes to the same coherent
  snapshot and exact projection rules as the baseline; keep scenarios read-only
  and require a separate explicit plan-draft flow.
- **Known alternatives:** mutate and roll back a temporary plan; clone financial
  tables; let an AI model calculate the answer.
- **Questions:** initial command set, snapshot/version strategy, persistence and
  the exact Forecasting/Scenarios ownership split.

### ADR-009 Optional local assistant boundary

- **Status:** proposed candidate; owner-confirmed safety and fallback direction
- **Context:** natural language can simplify scenario construction, but model
  output is probabilistic and personal financial data should remain local.
- **Proposed choice:** an optional local adapter produces a reviewable structured
  draft and grounded explanation; deterministic services calculate outcomes,
  and the complete workflow remains available without AI.
- **Known alternatives:** mandatory bundled model; external AI API; direct
  model-to-ledger tools; structured UI only.
- **Questions:** runtime and model packaging, resource budget, update policy,
  evaluation corpus and whether semantic retrieval is justified.
- **Questions:** cache headers and compression; reverse-proxy guidance; CSP;
  whether FastAPI static serving remains adequate under measured load.

### ADR-010 Versioned JSON backup format

- **Status:** proposed
- **Context:** owners need cloud-independent, portable full export and atomic
  restore across evolving schemas.
- **Proposed choice:** module-coordinated JSON document with `format`,
  `schema_version`, `app_version`, `exported_at`, exact decimal strings and a
  transactional restore.
- **Implemented baseline:** `hermes-json-backup` schema 1, canonical SHA-256
  integrity, a 50 MiB pre-parse limit, destination-owner re-authentication and
  transactional restore through module-owned persistence contracts.
- **Known alternatives:** PostgreSQL-only dumps; per-domain files; unversioned
  JSON; archive containing JSON plus attachments.
- **Implemented extension:** ADR 0004 adds the encrypted `hermes` V1 envelope
  while retaining explicit plaintext JSON export/import.
- **Questions:** compatibility beyond payload schema 1, authenticity/signing
  and large-dataset streaming.
