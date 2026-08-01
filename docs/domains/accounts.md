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

## Boundary

Accounts owns account identity, lifecycle and type rules. Operations owns posted
movements. Accounts may expose a balance read contract, but it must not allow a
caller to overwrite the derived balance.

## Open questions

- Currency model and permitted precision per currency.
- Whether negative physical balances or debit overdrafts are allowed.
- Account archive/close behavior when the ledger or fund allocations exist.
- Treatment of pending bank transactions, which are not in current scope.
