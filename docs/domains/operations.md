# Financial operations

## Owner-confirmed types

`income`, `expense`, `transfer`, `balance_adjustment`, `loan_disbursement`,
`loan_payment`, `debt_issuance` and `debt_repayment`.

Operations may be freely edited and deleted. Every change to one financial
operation—including its physical and virtual consequences—must complete
atomically in one database transaction.

## Ledger semantics

An operation is the user-meaningful fact; associated money movements are its
effect on accounts. Account balances are derived from those posted movements.
Transfers decrease one physical account and increase another. An adjustment is
explicit history, including initial balance, rather than direct balance mutation.

If a fund participates, its virtual movement shares the operation transaction.
The ordinary posting flow is documented in [data flows](../architecture/data-flow.md).

## Boundary and consistency

Operations owns the journal and posted physical movements. It validates public
references to accounts and categories. Other modules request posting through an
operations-owned command or shared use case; they do not insert ledger rows
directly.

The ability to edit/delete is owner-confirmed, but the audit representation is
not. Soft deletion, immutable revision history and direct replacement are still
alternatives.

## Open questions

- Exact movement model and balancing rule for income/expense versus transfers.
- Date/time, timezone, booking date and ordering semantics.
- How concurrent edits detect lost updates.
- Whether reconciliation or an optional audit trail is required.
- Rounding policy once currency precision is chosen.
