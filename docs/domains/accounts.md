# Accounts

## Owner-confirmed rules

The first account types are `cash`, `debit` and `savings`. An account balance is
not an ordinary editable field: the journal of financial operations and related
money movements is the source of truth. An initial balance is posted as a
`balance_adjustment` operation.

For a concrete account, the sum of virtual funds assigned to it must not exceed
its available physical balance.

## Terms and invariants

- **Physical balance**: sum of posted physical money movements for an account.
- **Available physical balance**: physical amount eligible to cover funds; its
  exact overdraft/pending definition remains open.
- **Free money**: available physical balance not virtually assigned to funds.

Balances are calculated with exact decimal values: Python `Decimal`, PostgreSQL
`NUMERIC`, and decimal strings at JSON boundaries where numeric parsing could
lose precision. Binary `float` is forbidden.

## Release 0.1.0-alpha.2 behavior

- Accounts contain type, trimmed name, optional description and lifecycle timestamps.
- The supported amount envelope is `NUMERIC(20,4)`; JSON writes and reads use decimal strings.
- Creating the first account locks the singleton base currency in the same transaction.
- A non-zero initial balance creates one `balance_adjustment` and one account movement.
- A zero initial balance creates no synthetic zero movement.
- Initial balances are non-negative until overdraft semantics are explicitly designed.
- Edit does not accept a balance field. Balance is always the sum of movements.
- Archive and restore preserve ledger history. Physical deletion is allowed only without movements.
- Physical deletion locks the account before checking history, so a concurrent
  posting either observes a deleted account or commits first and makes deletion
  return the normal history conflict.
- Initial-balance dates use the configured application timezone, not the host or
  database-session timezone.

## Boundary

Accounts owns account identity, lifecycle and type rules. Operations owns posted
movements. Accounts may expose a balance read contract, but it must not allow a
caller to overwrite the derived balance.

## Open questions

- Currency-specific precision and rounding beyond the alpha-wide four-decimal envelope.
- Whether later operations may produce negative physical balances or debit overdrafts.
- Account archive/close behavior when the ledger or fund allocations exist.
- Treatment of pending bank transactions, which are not in current scope.
