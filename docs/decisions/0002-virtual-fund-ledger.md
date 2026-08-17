# ADR 0002: Virtual fund ledger and allocation policy

- Status: accepted alpha implementation decision
- Date: 2026-08-11
- Decision owner: implementation scope requested by the project owner; detailed
  policies below remain alpha assumptions pending usage review

## Context

Physical money is reconstructed from account movements owned by Operations. A
virtual fund is a purpose assigned to part of that money and may span accounts.
Fund state must be reconstructable without turning a fund into another physical
account or duplicating physical balances.

## Decision

Funds owns `funds`, `fund_events` and `fund_movements`. A fund balance is always
the sum of its movements; a fund/account balance is that sum restricted to one
account. No cached balance is authoritative.

Each fund movement belongs to exactly one source: a financial operation for an
expense or physical transfer, or a fund event for an explicit allocation,
virtual redistribution or transfer between funds.

An expense may consume one fund on its physical account. Its virtual movement
equals the complete expense amount and is negative. An expense without a fund
changes only physical money. A physical transfer may move zero or one fund
portion. The virtual portion must be positive and no greater than the physical
transfer amount. Equal opposite movements are written on source and destination,
so the fund total is unchanged. A virtual redistribution is a separate fund
event with equal opposite movements and does not change physical money.
A fund-to-fund transfer is another virtual event: it decreases one fund and
increases another on the same physical account. It preserves that account's
reserved total and all physical balances.

A fund definition may carry an optional positive target amount. The target and
its exact progress ratio are planning metadata; neither is a balance source and
progress may legitimately exceed 100%. Creating a definition may include one
explicit positive allocation from one account to that new fund only. Definition
and movement commit together or both roll back; percentage distribution is not
invoked by this command.

Creating, replacing or deleting a financial operation replaces its associated
physical and virtual movements in one database transaction. Affected accounts
are locked in UUID order before affected funds are locked and balances are
checked. Definition creation with an initial allocation follows the same
account-before-fund order before taking the definition advisory lock. The resulting state must
satisfy, for every affected account:

```text
0 <= reserved = sum(fund movements) <= physical balance
free = physical balance - reserved
```

Every individual fund/account balance must also remain non-negative. This keeps
one fund from temporarily borrowing another fund's reservation.

Manual allocation percentages are exact `NUMERIC(7,4)` values in 0..100. Their
sum may not exceed 100. Fund definition writes are serialized with one
transaction-level advisory lock. Changing percentages does not move money.

The global application setting selects manual or dynamic allocation. Dynamic
percentages are derived, not persisted: incomplete non-archived funds receive a
base `min(5%, 100% / N)` plus a share of the remaining pool proportional to the
absolute amount still missing from their target. Exact four-decimal percentages
sum to 100 through deterministic largest-remainder allocation. Filled and
archived funds receive zero. Switching back to manual snapshots those effective
values atomically; switching to dynamic is rejected while any non-archived fund
lacks a positive target.

Percentage preview computes each active fund independently as
`amount * percentage / 100`, rounded down to four decimal places. The sum of
rounded allocations is reserved; percentage and rounding remainders remain
free. Fund order cannot affect the result. A manual preview is valid when each
amount is non-negative, refers once to an active fund, and the total does not
exceed the requested amount or the account's free balance. A committed
allocation must contain at least one positive movement; empty and all-zero
events are rejected.

A fund may be archived only with a zero total balance. Restoration is explicit.
Archived funds remain visible in history and may be retained while editing an
existing financial operation only when the resulting archived-fund total stays
zero. They cannot receive new allocations or be chosen for a new operation.
They do not participate in dynamic percentage calculation; restoring a fund
returns it to the next calculation when its balance is below its target.
Definition edit, archive and restore commands carry an optimistic version.
Allocation and redistribution events are immutable ledger facts in this alpha;
editing and deletion apply to fund-linked financial operations, not these
explicit events.

Cross-ledger allocation reads, summary and history composition live in the
application layer and call public Accounts, Operations and Funds contracts.
Operation posting remains a one-way dependency on the Funds posting contract,
so Funds never imports Operations and the modular graph stays acyclic.

## Consequences

- Physical and virtual ledgers remain independently explainable.
- Allocation is reproducible and exposes its remainder.
- Cross-module writes share the request transaction through public contracts.
- One expense or transfer can use at most one fund in this alpha release.
- Allocation/redistribution/fund-transfer events have no premature mutable lifecycle or
  unused event version; immutable revision history for editable financial
  operations remains deferred.
