# Virtual funds

## Meaning and ownership

A fund is a virtual purpose assigned to real money, never a bank account. One
fund may span physical accounts. Funds owns definitions, percentages, events
and per-account virtual movements; Operations owns physical movements. The
posting model is recorded in [ADR 0002](../decisions/0002-virtual-fund-ledger.md).

## Implemented model in 0.1.0-alpha.4

- A fund has a name, optional description, exact allocation percentage,
  lifecycle state and optimistic version.
- Active percentages total at most 100%. Changing a percentage never moves
  existing money.
- Fund totals and positions are sums of `NUMERIC(20,4)` movements; there is no
  mutable authoritative balance.
- Account coverage is `physical = reserved + free`, with
  `0 <= reserved <= physical` and non-negative individual fund positions.
- Explicit allocation reserves a selected part of one account's free balance;
  the remainder stays free.
- An expense may consume one fund completely or use free money. A transfer may
  carry one virtual part no greater than its physical amount.
- Virtual redistribution moves one fund between accounts without physical
  movements. Both transfer forms preserve the total fund balance.
- Create, edit and delete of fund-linked financial operations replace both
  ledgers atomically and recheck the resulting state.
- History includes allocations, redistributions, fund expenses and transfers.
- New actions use active physical accounts; operation entry exposes a fund only
  when it has a positive position on the selected source account.

## Rounding policy

For every active fund independently:

```text
allocation = round_down(amount * percentage / 100, 4 decimal places)
```

Fund order cannot affect the result. Percentage, rounding and manual
remainders stay free. Manual values must be non-negative, unique per fund and
total no more than both the selected amount and current free balance. Binary
floating point is rejected at API boundaries.

## Concurrency and lifecycle

Account rows and then fund rows are locked in UUID order before
coverage-dependent writes. Concurrent commands cannot overreserve one account
or fund position. Definition writes share a transaction advisory lock, so the
percentage limit also holds under concurrency.

The alpha archive policy permits archive only at zero total balance. Restore is
explicit, version-checked and rechecks the percentage limit. Editing or deleting
an older linked operation cannot make an archived fund non-zero. Reserved money
is never silently released or moved.

## Deliberately outside alpha.4

- automatic allocation while posting income;
- splitting one expense or transfer across several funds;
- target amount/date, icons, colours or gamification;
- batch allocation across multiple accounts;
- edit/delete lifecycle for explicit allocation and redistribution facts;
- immutable audit history and bulk actions;
- currency-specific precision and exchange rates.
