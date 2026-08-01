# Architecture Decision Records

ADR records a durable decision with meaningful alternatives and consequences.
Create one when a choice changes architecture, data semantics, deployment or a
cross-module contract. Do not manufacture past meetings or mark a proposal as
accepted without an explicit project-owner decision.

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

The entries below are candidates, not retroactively accepted ADRs. Their status
is `proposed` even where the owner has already supplied a strong direction;
formal consequences and unresolved details still require review.

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

- **Status:** proposed
- **Context:** freely editable balance fields can drift from operation history.
  The owner confirmed operation history as source of truth and initial balance
  as an adjustment operation.
- **Proposed choice:** derive physical account balance from posted money
  movements; never expose direct balance mutation.
- **Known alternatives:** mutable balance column; cached balance projection with
  reconciliation; full accounting double-entry ledger.
- **Questions:** exact movement/balancing model; whether and how to cache; audit
  semantics for freely edited/deleted operations; concurrency controls.

### ADR-004 Virtual fund allocation model

- **Status:** proposed
- **Context:** funds earmark real account money, can span accounts and must move
  atomically with relevant physical operations.
- **Proposed choice:** represent per-account virtual fund movements and derive
  fund positions; enforce percentage and physical-coverage invariants.
- **Known alternatives:** funds as accounts; a mutable allocation snapshot;
  envelope-only totals without account placement.
- **Questions:** rounding and remainder rules; fund-transfer command ownership;
  negative balances; concurrent invariant enforcement.

### ADR-005 Single-user server-side authentication

- **Status:** proposed
- **Context:** the deployment has one local owner and no need for identity
  federation, registration, roles or tenants.
- **Proposed choice:** first-run Argon2id credential plus revocable server-side
  sessions identified by HttpOnly cookies.
- **Known alternatives:** JWT bearer tokens; HTTP Basic authentication; reverse
  proxy authentication; multi-user identity model.
- **Questions:** session persistence/expiry, CSRF defense, recovery flow, cookie
  policy and brute-force protection.

### ADR-006 Expected occurrence materialization

- **Status:** proposed
- **Context:** recurring intent must be visible and adjustable without changing
  actual balances until confirmation.
- **Proposed choice:** materialize dated expected occurrences with lifecycle
  states; confirmation atomically creates and links one posted operation.
- **Known alternatives:** calculate recurrences only on read; post future
  operations immediately; use an external scheduler/queue.
- **Questions:** generation horizon and trigger, recurrence expression, timezones,
  idempotency key and rule-edit behavior.

### ADR-007 Angular production build delivery

- **Status:** proposed
- **Context:** users should access one port while development benefits from the
  Angular dev server.
- **Proposed choice:** multi-stage build copies Angular browser assets into the
  FastAPI application image, which serves them after `/api` routes.
- **Known alternatives:** Nginx/Caddy sidecar; separately exposed frontend;
  server-side rendering.
- **Questions:** cache headers and compression; reverse-proxy guidance; CSP;
  whether FastAPI static serving remains adequate under measured load.

### ADR-008 Versioned JSON backup format

- **Status:** proposed
- **Context:** owners need cloud-independent, portable full export and atomic
  restore across evolving schemas.
- **Proposed choice:** module-coordinated JSON document with `format`,
  `schema_version`, `app_version`, `exported_at`, exact decimal strings and a
  transactional restore.
- **Known alternatives:** PostgreSQL-only dumps; per-domain files; unversioned
  JSON; archive containing JSON plus attachments.
- **Questions:** credential inclusion, compatibility window, validation schema,
  archive/encryption support and large-dataset streaming.
