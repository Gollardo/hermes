# Operations

Owns posted financial operations and their money movements. Creating, editing
or deleting one operation is one database transaction.

Release `0.1.0-alpha.3` implements income, expense, transfer and signed ledger
adjustment commands, journal reads, full-selection net totals and pagination.
The UI derives an adjustment delta from the expected balance. Affected accounts are locked
before a mutation, non-negative alpha balances are checked against the
ledger-derived result, and an optimistic integer version rejects lost edits and
deletes. Posting details and assumptions are recorded in ADR 0001.

Release `0.1.0-alpha.4` optionally attaches one fund to an expense or transfer.
Operations owns the physical movements, Funds owns virtual movements, and both
are replaced atomically through public contracts. See ADR 0002.
