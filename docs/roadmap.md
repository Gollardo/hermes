# Roadmap

This document describes the proposed development sequence and the boundaries of
future releases.

The roadmap is not a fixed calendar plan. The scope and order of milestones may
change as the project gains experience from real-world use.

The current implementation state is documented in
[project-status.md](./project-status.md). The engineering documentation map is
in [index.md](./index.md). The actual version history is in
[CHANGELOG.md](../CHANGELOG.md): the roadmap must not assign an already-used
version number to a new future scope.

Versions through `0.4.6` are the owner's internal development milestones, not
published GitHub Releases. The first public tag starts the normal release
process; its version is selected separately after the current release gate is
closed.

## Development principles

The project evolves through vertical user scenarios.

Whenever possible, each completed scenario should include:

- database migrations;
- backend;
- frontend;
- validation;
- error handling;
- automated tests;
- engineering documentation updates;
- production build verification.

New functionality should not exist only at the database or API level without a
way to verify its primary user scenario.

Project priorities:

1. Correctness of the financial model.
2. Data safety and portability.
3. Simplicity of daily operation entry.
4. Simplicity of self-hosted deployment.
5. Interface usability.
6. Expansion of analytics and integrations.

## Item statuses

- `[ ]` — not started.
- `[~]` — in progress or partially implemented.
- `[x]` — implemented and passed the required checks.
- `[?]` — requires a product or architectural decision.

---

# 0.0.x — project foundation

The milestone goal was to create a reproducible environment and engineering
foundation without complete financial business logic.

## 0.0.1 — initial structure

- [x] Git repository initialization.
- [x] Python and FastAPI backend skeleton.
- [x] Angular frontend skeleton.
- [x] PostgreSQL and Docker Compose.
- [x] Initial migration configuration.
- [x] Application health check.
- [x] Testing and static-analysis tooling.
- [x] Initial architecture documentation.
- [x] `AGENTS.md`.
- [x] AGPL-3.0-or-later license.
- [x] Local development and deployment documentation.

## Milestone completion criteria

- The project can be deployed by following its documentation.
- Backend, frontend, and PostgreSQL start in the local environment.
- Available tests, lint, type checks, and the production build pass.
- The repository contains no secrets or local artifacts.
- Architectural boundaries are described under `docs/`.

This milestone remained an internal development milestone and was not published
as a user release or git tag.

---

# 0.1.0-alpha.1 — first run and application access

The release goal was a protected single-user application with basic settings.

**Status: completed on 2026-08-02.** The user scenario was verified in a
production-like Compose environment on a clean PostgreSQL volume. The upgrade
from `0001_first_run_access` to `0002_harden_access_invariants` was verified on
an initialized database while preserving credentials, settings, and sessions.

## First run

- [x] Detect an uninitialized application.
- [x] Initial setup screen.
- [x] Master password creation.
- [x] Base currency selection.
- [x] Timezone selection.
- [x] Prevent repeated initial setup after initialization.

## Authentication

- [x] Password hashing with Argon2id.
- [x] Sign in with the master password.
- [x] Server-side sessions.
- [x] HttpOnly cookie.
- [x] End the current session.
- [x] End all active sessions.
- [x] Protect every API except setup, login, and health check.
- [x] Rate-limit frequent failed login attempts.

## Settings

- [x] View application settings.
- [x] Change timezone.
- [x] Change the base currency before financial data exists.
- [x] Change the master password.

## Release criteria

- [x] A new user can deploy the application and complete initial setup.
- [x] An unauthenticated user cannot access financial data or protected APIs.
- [x] Sessions are created, validated, and ended correctly.
- [x] Startup was verified on a clean database.
- [x] Migration of an initialized database was verified.

---

# 0.1.0-alpha.2 — accounts and categories

The release goal was to prepare the core financial reference data.

**Status: the primary slice was implemented on 2026-08-02.** Scenarios were
verified on PostgreSQL 17 with both a clean migration and an upgrade of existing
data from `0001_first_run_access` to head. Verification of a real operation with
an archived category remained partial until categorized operations arrived in
`alpha.3`.

## Accounts

- [x] Create an account.
- [x] Account types: `cash`, `debit`, and `savings`.
- [x] Account name and description.
- [x] Initial balance through a financial adjustment operation.
- [x] View the account list.
- [x] View the current balance.
- [x] Edit an account.
- [x] Archive and restore an account.
- [x] Prevent invalid deletion of an account with operation history.

## Categories

- [x] Create a category.
- [x] Income categories.
- [x] Expense categories.
- [x] Subcategories.
- [x] Edit categories.
- [x] Archive categories.
- [~] The archived-category contract is ready; the real operation scenario
  awaited `alpha.3`.

## Release criteria

- [x] The user can create an account and category structure.
- [x] Initial balance is not stored as an arbitrarily mutable field.
- [x] Account and category history is preserved in real categorized operations.
- [x] Monetary values do not use `float`.

---

# 0.1.0-alpha.3 — financial core

The release goal was to implement the operation journal and calculation of
actual balances.

**Status: the vertical slice was implemented and verified on 2026-08-02.** The
posting model is recorded separately in ADR 0001. The owner confirmed that
negative balances are prohibited for the current release; overdraft and
multi-currency behavior require separate future models.

The financial posting model had to be reviewed and documented separately before
implementation.

## Operation model

- [x] Financial operation header.
- [x] Account movement records.
- [x] Atomic posting of an operation.
- [x] Derive an account balance from the movement journal.
- [x] Validate financial invariants.
- [x] Prevent partially saved operations.

## Income

- [x] Create income.
- [x] Select an account.
- [x] Select a category.
- [x] Date, amount, and description.
- [x] Edit income.
- [x] Delete income.

## Expenses

- [x] Create an expense.
- [x] Select an account.
- [x] Select a category.
- [x] Date, amount, and description.
- [x] Edit an expense.
- [x] Delete an expense.
- [x] Enforce the approved insufficient-balance policy.

## Transfers

- [x] Transfer between two accounts.
- [x] Represent a transfer as one operation.
- [x] Atomic debit and credit.
- [x] Edit a transfer.
- [x] Delete a transfer.

## Balance adjustment

- [x] Create an adjustment.
- [x] Enter the expected balance and calculate the exact journal movement.
- [x] Display the adjustment reason.
- [x] Save the adjustment in the operation journal.

## Operation journal

- [x] Operation list.
- [x] Filter by period.
- [x] Filter by account.
- [x] Filter by type and category.
- [x] View operation details.
- [x] Pagination.
- [x] Transfer direction, active filters, and the total for the full selection.

## Release criteria

- Every account balance can be fully reconstructed from the journal.
- Creating, editing, and deleting an operation is transactional.
- A transfer cannot be saved partially.
- Core invariants are covered by unit and integration tests.
- Migrations are verified on clean and existing databases.

The regression suite additionally verifies concurrent debits and account
deletion, rollback after saving the header and first movement, immutability of a
historical category type, and timezone-boundary upgrade and downgrade of
`alpha.3` data.

---

# 0.1.0-alpha.4 — virtual funds

The release goal was to implement the application's primary differentiating
feature: virtual allocation of money to purposes.

**Status: the primary vertical slice was implemented and verified on
2026-08-11.** The virtual posting, rounding, coverage, and archiving models are
recorded separately in ADR 0002.

## Fund management

- [x] Create a fund.
- [x] Fund name and description.
- [x] Allocation percentage.
- [x] Edit a fund.
- [x] Archive a fund.
- [x] Ensure active-fund percentages total no more than 100%.
- [x] Optional target amount and progress.

## Fund balances

- [x] Total fund balance.
- [x] Fund breakdown by physical account.
- [x] Free balance of each account.
- [x] Reserved balance of each account.
- [x] Fund movement history.

## Allocation

- [x] Allocate an arbitrary amount by percentages.
- [x] Allocation preview.
- [x] Manually adjust the allocation.
- [x] Atomically allocate an amount directly to the fund being created.
- [x] Leave the unallocated amount free.
- [x] Fixed rounding policy.

## Fund operations

- [x] Spend from a selected fund.
- [x] Spend without a fund.
- [x] Transfer money and a virtual fund portion between accounts.
- [x] Redistribute a fund between accounts without changing its total.
- [x] Edit operations associated with a fund.
- [x] Delete operations associated with a fund.
- [x] Restore invariants after changing an operation.
- [x] Transfer a virtual amount between funds on one account.

## Release criteria

- Funds reserved on an account do not exceed its physical balance under the
  approved policy.
- Spending from a fund reduces both the account and the fund.
- Transferring a fund between accounts does not change the fund total.
- Percentage allocation is reproducible and covered by tests.
- Rounding rules are documented.

The regression suite verifies exact independent rounding, concurrent allocation
and fund consumption, rollback of both journals after an injected failure,
prevention of coverage violations through physical-operation changes, the
archive invariant, and migrations on clean and existing `alpha.3` databases.

---

# 0.1.0-beta.1 — recurring operations and calendar

The release goal was to add planned financial events.

## Recurrence rules

- [x] Create recurring income.
- [x] Create a recurring expense.
- [x] Create a recurring transfer.
- [x] Recurrence frequency.
- [x] Weekdays and a 1–3 week interval for weekly recurrence; a 1–3 month
  interval for monthly recurrence.
- [x] Start date.
- [x] Optional end date.
- [x] Account, category, amount, and description.
- [x] Edit and disable a rule.

## Expected occurrences

- [x] Materialize future occurrences.
- [x] Prevent duplicate materialization.
- [x] Statuses `pending`, `confirmed`, `postponed`, and `cancelled`.
- [x] Confirm an expected operation.
- [x] Adjust the amount of an individual occurrence during confirmation.
- [x] Atomic planned transfer with percentage-based fund allocation.
- [x] Postpone an individual occurrence.
- [x] Cancel an individual occurrence.
- [x] Link a confirmed occurrence to the actual operation.

## Calendar

- [x] Monthly view.
- [x] Upcoming-operation list.
- [x] Filter by accounts and types.
- [x] Highlight overdue expected operations.
- [x] Quick confirmation, postponement, and cancellation.

## Resolved decisions

- [x] Editing a rule synchronizes or automatically cancels only untouched
  current and future occurrences; confirmed and manually edited occurrences
  remain unchanged.
- [x] Occurrences are materialized from the current date through one calendar
  year ahead, inclusive.
- [x] Nonexistent dates are prohibited: monthly recurrence is limited to days
  1–28, and yearly recurrence does not accept February 29.
- [x] All values are calendar dates. The occurrence timezone is considered
  stable after initial setup; schedules are not migrated automatically.

## Release criteria

- An expected operation does not change the actual balance.
- Only confirmation creates an actual operation.
- Repeated materialization does not create duplicates.
- Postponing an occurrence does not change its rule without an explicit user
  action.

The regression suite verifies exact generation, repeated and concurrent
materialization, protection of manually edited occurrences, preservation of
overdue items, idempotent confirmation, concurrent confirmation and rule edits,
the authentication and CSRF boundary, rollback of the actual operation and link
after an injected failure, upgrade of an existing `alpha.4` database, and
downgrade of the `beta.1` schema. Frontend checks cover full month pagination,
an honest upcoming-event limit, archived references when editing a rule, and a
direct link to the actual operation. `alembic check` confirms that head has no
model/schema drift.

---

# 0.1.0-beta.2 — balance forecasting

The release goal was to show future balances including expected operations.

**Status: the vertical slice was implemented and verified on 2026-08-12.** The
read-only model adds no stored entities, so no new migration is required;
migration checks confirm compatibility with the existing schema.

## Calculation engine

- [x] Forecast for one account.
- [x] Aggregate forecast for all accounts.
- [x] Horizons: two weeks, one month, one quarter, six months, and one year.
- [x] Include expected income.
- [x] Include expected expenses.
- [x] Include planned transfers.
- [x] Calculate the minimum future balance.
- [x] Identify the date of a possible negative balance.
- [x] Explain the events affecting every forecast point.

## Interface

- [x] Forecast balance chart.
- [x] Period selector.
- [x] Account selector.
- [x] Aggregate forecast.
- [x] Insufficient-funds warnings.
- [x] View operations that changed the forecast.

## Release criteria

- The calculation engine is tested separately from the visualization.
- Identical source data produces an identical forecast.
- Transfers do not distort the total balance across all accounts.
- The user can understand why the forecast changed.

The pure unit suite fixes calendar horizons, `Decimal` determinism, daily close,
minimum and negative balance, scope filtering, and transfer neutrality. The
PostgreSQL integration scenario confirms that a confirmed event moves only into
the actual starting state, a postponed event changes the planned date, and the
API is unavailable without a session. UI tests cover selectors, risk, and
explanations.

---

# 0.1.0-rc.1 — backup and MVP stabilization

The release goal was to prepare the application for real daily use.

## JSON export

- [x] Full data export.
- [x] Versioned format.
- [x] Fields `format`, `schema_version`, `app_version`, and `exported_at`.
- [x] Export settings.
- [x] Export accounts, categories, operations, and funds.
- [x] Export recurrence rules and expected occurrences.
- [x] Validate the generated backup's integrity.

## Restore

- [x] Upload a JSON file.
- [x] Validate format and version.
- [x] Preview a content summary.
- [x] Explicitly confirm data replacement.
- [x] Transactional restore.
- [x] Validate domain invariants after restore.
- [x] Clear error messages.
- [x] Restore test on a clean database.

## Stabilization

- [x] Verify upgrades from all previous prerelease versions.
- [x] Verify deployment on a clean server.
- [x] Update documentation.
- [x] Backup documentation.
- [x] Verify the production Docker image.
- [x] Fix critical UX issues.
- [x] Fix critical financial-core defects.
- [x] Verify that monetary calculations do not use `float`.
- [x] Review authentication and session security.

---

# 0.1.2 — stabilized MVP slice

**Status: the code slice was completed on 2026-08-15.** The version number is
recorded in the changelog but does not by itself confirm publication of the
first public tag. Real-use and publication criteria move to the current release
gate.

## Release capabilities

- Single-user authentication.
- Accounts.
- Categories and subcategories.
- Income and expenses.
- Transfers.
- Balance adjustments.
- Operation journal.
- Virtual funds.
- Percentage-based allocation.
- Expenses and transfers involving funds.
- Recurring expected operations.
- Calendar.
- Balance forecast.
- JSON export and restore.
- Docker Compose deployment.
- End an inactive session after 30 minutes.
- Free funds as the primary forecast mode, with an explicit switch to total
  physical balance.
- Consistent textual dates, currency symbols, and thousands grouping in
  monetary fields.

## Public release criteria

- No known defects can silently corrupt financial data.
- All key financial invariants are covered by tests.
- Full restore from backup is verified.
- Migrations from the previous version are verified.
- Documentation matches actual behavior.
- Installation and upgrade instructions are clear.
- The production image builds reproducibly.
- The application has completed a period of real personal use.

---

# 0.3.0 — reports and everyday usability

**Status: completed on 2026-08-17.** The intermediate development version
`0.2.0` has no separate section in the current changelog; its implemented scope
is consolidated under `0.3.0`. Unimplemented items from the former plan were
moved to an unversioned backlog.

- [x] Income and expenses for a month or arbitrary period.
- [x] Expenses and income by category with operation lists.
- [x] Fund outlook based on planned percentage allocations.
- [x] Quick-create dropdown with operation-type selection.
- [x] Optional active default account for new income and expenses.
- [x] Redesign the application in the approved light, neutral visual direction.
- [x] Free-balance forecasting includes future percentage allocations from
  transfers, while total forecasting preserves the physical neutrality of
  internal transfers.

---

# 0.4.0 — dynamic fund allocation

**Status: implementation and automated checks were completed on 2026-08-17;
owner acceptance on real data and the public-tag decision remain the release
gate.**

- [x] Switch between manual and dynamic modes in settings.
- [x] Calculate the initial dynamic percentages from each absolute remaining
  amount to target while guaranteeing a base share.
- [x] Exclude completed and archived funds, and include restored funds again.
- [x] Recalculate after actual and sequential planned allocations.
- [x] Preserve currently calculated percentages when returning to manual mode.
- [x] Migration, backup compatibility, API/UI, and automated checks.
- [x] Format every UI amount and percentage consistently as `100 000,00` and
  `12,50%`, accept comma and period decimal separators in numeric inputs, and
  cover the contract with frontend tests. Server-side precision is unchanged.

---

# 0.4.5 — amount expressions and recurring-series shifts

**Status: implemented on 2026-08-19; owner acceptance on real data remains.**

- [x] Evaluate addition and subtraction exactly in monetary operation and
  scheduling inputs without binary floating point.
- [x] Add an opt-in rule policy that propagates a postpone delta to untouched
  later occurrences while preserving confirmed and manual decisions.
- [x] Persist the policy and accumulated offset through migration and backups.
- [x] Model automatically cancelled dated exceptions with an explicit
  series-shift preservation marker instead of an offset comparison.
- [x] Narrow series-shift row locks to the selected occurrence and mutable later
  candidates without weakening atomicity or preserved-exception semantics.
- [x] Decompose Scheduling's scoped calendar and action styles so its owned CSS
  stays within the component-style budget without changing established UX.
- [x] Cover validation, API/UI behavior, domain invariants and error paths.
- [x] Advance the internal application version to `0.4.5`.

---

# 0.4.6 — relative fund progress and scheduling control alignment

**Status: implemented on 2026-08-20; owner acceptance on real data remains.**

- [x] Weight dynamic fund percentages by relative unfilled target progress so
  equal completion levels receive equal shares regardless of target size.
- [x] Preserve the existing equal guaranteed-base behavior when 20 or more
  funds are active and document that relative progress cannot differentiate
  shares once that base consumes the complete percentage.
- [x] Reuse the same exact calculator for previews, committed transfer
  allocations, manual-mode snapshots and sequential forecast projections.
- [x] Preserve the existing base share, exact largest-remainder closure,
  filled/archive eligibility, reactivation and target-overshoot behavior.
- [x] Correct long recurring-rule checkbox alignment without changing the
  series-shift workflow or adding a new interface pattern.
- [x] Cover the new policy and layout contract with unit, integration and
  frontend tests, and update current product documentation.
- [x] Advance the internal application version to `0.4.6`.
- [x] Confirm that no database migration is required because the dynamic
  percentages are derived and the persisted schema is unchanged.

---

# Proposed global plan after 0.4.6

This plan is a product hypothesis for discussion, not an approved detailed
design or calendar commitment. A version number marks a convenient boundary of
user value; each version's scope is confirmed separately before implementation.
An unfinished item is never moved silently into the next release.

## Sequencing principles

1. First publish and strengthen a reliable self-hosted core.
2. Add the i18n foundation early, while the amount of unmigrated copy is small.
3. Build the deterministic What if? engine before shortening its input path
   with local AI.
4. Import high-quality source data before history-informed analytics.
5. Implement debts and budgeting as independent domains, without mixing them
   with funds or ordinary operations.
6. Build explainable deterministic analytics first, then use a local model only
   as an optional assistant over the same facts.
7. Multi-currency support must precede full investment accounting.
8. A public online platform is a separate architectural program and does not
   automatically expand the trusted single-owner model.

## Before 1.0.0 — trial use and stable self-hosted core preparation

- [ ] Perform owner acceptance of `0.4.6` on a restored copy of real data.
- [x] Add protected `.hermes` V1 export/restore while retaining explicit legacy
  plaintext JSON export/import.
- [ ] Define supported PostgreSQL, Python, Node, Docker, and browser versions.
- [ ] Verify upgrades and backup/restore between public versions.
- [ ] Add automated local backups, validation, and limited rotation.
- [ ] Publish a multi-architecture image and document upgrades, rollback,
  reverse proxy, VPN, and HTTPS.
- [ ] Resolve known critical defects and complete the release/security
  checklist.
- [ ] Release `1.0.0` only after a separate explicit owner decision; completing
  the technical items does not assign a date or open the release by itself.

## 1.1.0 — multilingual foundation

- [ ] Move user-facing copy out of components and define an i18n contract.
- [ ] Support Russian and English interfaces with an explicit fallback
  language.
- [ ] Localize dates, numbers, currencies, validation, and API errors without
  changing exact domain payloads.
- [ ] Verify interface overflow, keyboard navigation, and screen-reader labels
  in both languages.
- [ ] Document how to add a community translation without changing business
  code.

## 2.0.0 — Oracle: deterministic What if? mode

- [ ] Create a temporary purchase, income, amount-change, or date-shift scenario
  without changing the ledger or confirmed plan.
- [ ] Provide an ordinary structured form that does not depend on AI.
- [ ] Calculate baseline and alternative forecasts from one snapshot, scope,
  and horizon.
- [ ] Answer “what changes” before showing a chart: delta in free money,
  minimum, date, stress window, and affected funds or events.
- [ ] Support a user-defined stop-loss and a separate, explainable risk boundary
  suggested by the system.
- [ ] Expose assumptions and sources, and distinguish facts, plans, scenarios,
  and estimates.
- [ ] Discard a scenario by default; saving it or creating a plan draft are
  separate explicit actions.
- [ ] Cover scenario calculation with exact-decimal, snapshot-consistency, and
  no-side-effect tests.

## 2.1.0 — save and compare scenarios

- [ ] Named scenarios that do not become confirmed plans.
- [ ] Compare several amount, date, or decision-set alternatives.
- [ ] Detect a stale baseline and recalculate explicitly from new facts.
- [ ] Transfer reviewed fields only into the plan-draft composer.
- [ ] Define a backup/restore policy for saved scenarios without conversation
  history.

## 2.2.0 — local conversational input for Oracle

- [ ] An optional local-model adapter converts text into a structured scenario
  draft.
- [ ] Unknown material parameters trigger a short clarification instead of a
  hidden default.
- [ ] The user reviews the recognized amount, date, scope, and action before
  calculation or saving.
- [ ] The model explains the completed deterministic result but does not
  calculate authoritative balances.
- [ ] Chat does not create operations or plans directly, and conversations are
  not stored by default.
- [ ] Provide a complete non-AI fallback and deletion of local model artifacts.

## 3.0.0 — receivable and payable debts

- [ ] Directions `owed_to_me` and `i_owe`, counterparty, dates, description,
  and status.
- [ ] Initial amount and current balance derived from loans, receipts, and
  repayments without allowing drift.
- [ ] Partial repayment and adjustment through an explicit financial fact.
- [ ] Atomic relationship between the debt lifecycle and physical operations.
- [ ] Due date, overdue state, calendar, baseline forecast, Oracle, and reports.
- [ ] Backup/restore and migration compatibility.

## 3.1.0 — loans and installment plans

- [ ] Creditor, initial and current amounts, start date, and expected end date.
- [ ] Regular payment, frequency, and next payment date.
- [ ] A simplified user-facing schedule that does not attempt to reproduce bank
  mathematics for interest, fees, and early repayment.
- [ ] Confirming a payment atomically creates a financial operation and reduces
  the outstanding liability.
- [ ] Partial, missed, and modified payments have explicit states.
- [ ] Calendar, forecast, scenarios, dashboard, reports, and backup/restore.

Loans do not belong in the first debt release merely because both use the word
“liability”: loans have a different lifecycle, a recurring payment, and a
creditor.

## 4.0.0 — universal bank-statement import

“Universal” means a shared configurable pipeline, not a promise to understand
every bank file automatically without configuration.

- [ ] CSV with encoding, delimiter, numeric locale, and date-format detection.
- [ ] XLSX with worksheet selection; evaluate OFX and QIF as additional formats.
- [ ] Column mapping, saved format profiles, and a write-free preview.
- [ ] Account selection, normalization of operation sign and type, and category
  suggestions.
- [ ] Explainable duplicate candidates and manual conflict resolution.
- [ ] Explicit confirmation, atomic writes through owning modules' public
  contracts, and a result report.
- [ ] Bank-specific profiles build on the shared pipeline and receive no direct
  ledger access.

Additional formats, ready-made bank profiles, and reconciliation improvements
may ship as `4.x` minor versions without changing import ownership.

## 5.0.0 — budgeting policy, goals, and plan versus actual

- [ ] Periodic income and expense limits by category.
- [ ] Explicit policy for carrying remaining amounts between periods.
- [ ] Plan, actual, available through period end, and explainable variances.
- [ ] Warnings that neither prohibit a legitimate operation nor change the
  ledger.
- [ ] Independence of budgets from funds: a budget plans flow over a period,
  while a fund assigns money already held.
- [ ] Budget templates, backup/restore, and reports.
- [ ] Fund target date, required savings pace, and expected completion date.
- [ ] Budgets and goals become explicit inputs to baseline and What if?
  scenarios.

## 6.0.0 — history-informed forecasting and explainable analytics

- [ ] Improved search, saved filters, and bulk categorization.
- [ ] Trends in balances, expenses, income, funds, debts, and budget execution.
- [ ] Configurable dashboard and period comparison.
- [ ] Deterministic forecast baselines with backtesting and error metrics.
- [ ] Machine-readable local analytical read model that does not bypass domain
  owners.
- [ ] Explainable comparison of the user's plan with actual history, without
  replacing the plan automatically.
- [ ] Financial horizon, resilience runway, and stress windows with a disclosed
  methodology.

## 6.1.0 — history-informed Oracle

- [ ] Optional local execution without sending financial data to an external AI
  service.
- [ ] Category suggestions, anomaly detection, and trend explanations.
- [ ] A forecast as a probabilistic scenario beside the deterministic baseline,
  not a replacement for the exact financial model.
- [ ] Show data source, confidence, horizon, and quality from historical
  backtesting.
- [ ] No recommendation creates or changes a financial operation without
  explicit user confirmation.
- [ ] Allow the model to be disabled completely and its local artifacts deleted.
- [ ] Conversational analytics questions use grounded tools and read models,
  not unconstrained model guesses.

## 7.0.0 — multi-currency support and capital model

- [ ] Account currency and base reporting currency.
- [ ] Explicit exchange rate recorded on a financial operation.
- [ ] Rate source, date, and missing-rate policy.
- [ ] Separate representation of actual value and revaluation.
- [ ] Currency-specific precision, cross-currency transfers, reports, and
  backup.
- [ ] Basic asset, liability, and net-worth model suitable for a later
  investment scope.

## 7.1.0 — investments and advanced asset accounting

- [ ] Begin with a manual asset and liability register and net-worth
  calculation.
- [ ] Separate a cash account from an investment account, a position from an
  instrument, and a trade from a market-price change.
- [ ] Purchases, sales, fees, dividends, and realized and unrealized results.
- [ ] Manual quotes as the baseline; an external market-data provider requires
  a separate ADR, cache, provenance, and degradation policy.
- [ ] Real estate, vehicles, and other non-market assets use periodic valuations
  rather than fictitious financial operations.
- [ ] Broker import and crypto assets are considered after the base model is
  stable and are not automatically part of the first investment release.

## Parallel everyday-work backlog

These improvements may be included in the nearest thematically appropriate
release if they do not dilute its acceptance criteria:

- operation templates and duplication;
- a more convenient calendar and further mobile adaptation;
- additional export formats;
- PWA and limited offline mode;
- extended backup diagnostics and password-only protected-backup rewrap.

---

# Hermes Online strategic program

A potential free online platform—with a subscription, without one, or supported
by voluntary donations—is not an ordinary continuation of the self-hosted
deployment. Before assigning it a version, the project needs a separate
feasibility milestone and an ADR covering these decisions:

- whether self-hosted Hermes remains the primary product and whether a hosted
  edition can exist without a closed functional fork;
- identity, password recovery, email verification, roles, tenant isolation,
  account deletion, and data export;
- encryption, secret management, rate limiting, abuse prevention,
  observability, incident response, vulnerability disclosure, and privacy
  policy;
- background-job isolation, per-tenant backup, disaster recovery, and restore
  verification;
- costs for PostgreSQL, files, email, model inference, and support;
- subscription, donations, or a fully free model, as well as taxes and the
  payment provider;
- AGPL licensing, contribution rules, and a transparent division between
  shared and hosted components.

Until these questions are resolved, the current guarantee remains unchanged:
one owner in a protected environment. Code for new domains must not depend
prematurely on multi-tenant or cloud infrastructure.

---

# Version and release policy

- The entire `0.x` series is for internal trial use. Versions `0.1.0`–`0.4.6`
  and subsequent numbers before a separate owner decision are not stable public
  releases.
- The first stable public release will be `1.0.0`. The owner announces its
  readiness and release date separately; the roadmap cannot do so
  automatically.
- Major product generations use `2.0.0`, `3.0.0`, and so on. Functional
  improvements within a generation ship as minor `N.x.0` versions, while
  compatible fixes ship as patches `N.x.y`.
- After `1.0.0`, every public major, minor, and patch receives an annotated git
  tag, a GitHub Release, a changelog entry, and any required migration and
  backup notes. A distributed container image uses the same version.
- Whenever possible, an incompatible change after `1.0.0` waits for the next
  major version and always has an explicit migration path. A minor version must
  not silently break the API, backups, or stored data.
- `N.x.0-rc.1` prereleases may verify a real upgrade; a prerelease does not
  replace a stable backup/restore test.
- Published migrations are never rewritten after the first public release.

---

# 1.0.0 — stable release

Version `1.0.0` must not be released merely because many features have been
implemented.

Proposed criteria:

- The application is used reliably with real data.
- The financial model is considered stable.
- Operation and fund formats do not require destructive redesign.
- Backup and restore are verified across different versions.
- A compatibility policy is documented.
- Migrations between public versions are reliable.
- A vulnerability-handling process exists.
- The update release process is clear.
- No known critical defects remain.
- Core user scenarios require no manual database intervention.
- A person who did not participate in development can install and upgrade the
  project by following the documentation.

Until these conditions are met, the project may remain in the `0.x` series even
if it is already fully usable.

---

# Rules for changing the roadmap

When changing the roadmap:

1. Check consistency with the architecture documentation.
2. Do not mark an item complete solely because backend code exists.
3. Move unfinished functionality between releases explicitly.
4. Do not add infrastructure without architectural justification.
5. Update [project-status.md](./project-status.md) when the current phase
   changes.
6. Do not use the roadmap as a log of every commit.
7. Do not specify calendar deadlines without an explicit owner decision.
