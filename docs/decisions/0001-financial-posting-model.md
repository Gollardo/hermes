# ADR 0001: Financial posting model for 0.1.0-alpha.3

- **Status:** accepted for the current release
- **Date:** 2026-08-02; owner confirmation 2026-08-18
- **Decision owner:** project owner

## Context

Hermes needs a user-facing operation journal whose account balances can be
reconstructed without a mutable balance column. Income and expense cross the
boundary of the model, while a transfer moves money only between modelled
accounts. The model must support free edit and delete while preventing a
partially saved transfer or a concurrent lost update.

## Decision

A `financial_operation` is the user-meaningful header. Its
`account_movements` are the complete physical effect on accounts. Amounts use
`NUMERIC(20,4)`/`Decimal` and decimal strings at JSON boundaries.

| Operation | Required references | Movements | Sum across modelled accounts |
| --- | --- | --- | --- |
| income | one active account, one active income category | `+amount` to account | `+amount` |
| expense | one active account, one active expense category | `-amount` from account | `-amount` |
| transfer | two different active accounts | `-amount` from source, `+amount` to target | `0` |
| balance adjustment | one active account, non-blank reason | one signed delta | signed delta |

Income, expense and transfer accept a strictly positive amount. An adjustment
accepts a non-zero signed delta. A zero movement is never persisted. A category
is absent for transfer and adjustment.

The adjustment composer does not ask the user to reason about that signed delta.
It shows the current ledger-derived balance, accepts the new expected balance,
calculates the difference with exact four-decimal integer arithmetic and posts
the resulting delta.

The calendar fact is stored as `occurred_on` without time. Journal ordering is
stable by `occurred_on DESC`, then `created_at DESC`, then identifier. Creation
time is metadata and does not alter the financial date.
Existing timestamped initial adjustments and new date defaults are interpreted
in the configured application timezone.

Create, edit and delete lock all affected account rows in UUID order and change
the header and its complete movement set in one database transaction. Edit and
delete require the current integer `version`; a mismatch is a conflict. This
prevents a silent lost update. The database owns referential integrity and
cascades movement deletion with the header; the operations service owns the
cross-row shape rules that SQL row checks cannot express safely.

For the current release, every account type has the same availability
policy: the ledger-derived balance may not become negative after a create, edit
or delete. The check is performed while affected accounts are locked. This is
an owner-confirmed current policy rather than a promise that overdraft will
never exist; overdrafts require a separate account-level policy and UI before
they can be enabled.

Historical reads retain archived account and category names. New references
must be active. An edit may retain its existing archived references, but cannot
switch to another archived reference.

A category type is immutable while any operation references it. This preserves
the income/expense meaning of existing operations; rename,
reparenting and archival remain separate lifecycle changes.

## Verification examples

- Income `100` followed by expense `30` reconstructs balance `70`.
- Transfer `25` from an account with `70` to one with `10` reconstructs `45`
  and `35`, while total physical money remains `80`.
- Replacing that transfer with `40` atomically reconstructs `30` and `50`.
- Deleting the income is rejected while its removal would make the source
  account negative; no header or movement is changed.
- A failure in a transfer request rolls back its header and both movements; a
  committed transfer always has both sides.

## Consequences

Balances need no mutable cache and are fully recoverable from movements.
Income/expense are intentionally not double-entry accounting because their
external counterparty is outside the current account universe. The current
single-owner product intentionally replaces movements in place and records only
the current version; the owner confirmed that a separate immutable change
history is not required for this scope.
