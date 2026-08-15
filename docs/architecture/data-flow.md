# Data flows

The diagrams describe confirmed semantic flows. Names such as “transaction
boundary” are architectural concepts, not promised endpoint, class or table
names.

## First-run setup and authenticated requests

```mermaid
flowchart LR
    Status["Public setup status"] --> Setup["Validated one-time setup"]
    Setup --> Tx["One database transaction"]
    Tx --> Credential["Argon2id owner credential"]
    Tx --> Preferences["Currency and timezone"]
    Tx --> Categories["Optional category templates"]
    Tx --> Session["Hashed server session and CSRF tokens"]
    Session --> Cookie["HttpOnly session cookie"]
    Cookie --> Guard["Protected API guard"]
    Guard --> Idle["Absolute and 30-minute idle checks"]
    Idle --> CSRF["CSRF check for writes"]
    CSRF --> UseCase["Authenticated use case"]
```

First-run backup restore is an alternative branch of the same setup
transaction: validate backup integrity and domain invariants, create the new
destination credential/session, replace settings and financial data, run
post-write checks, then commit. Any validation or insertion failure rolls back
the credential as well as restored data.

After credential commit, setup can only report a conflict. Login throttling is
locked and updated in the same database transaction as password verification
and session issuance, preventing parallel attempts from bypassing the counter.
Database request dependencies close at FastAPI function scope, so a successful
HTTP response and authentication cookies are sent only after transaction commit.
The Angular shell also tracks keyboard, pointer, touch and scroll activity. It
ends the visible session at 30 minutes and sends a throttled authenticated
heartbeat while the owner remains active, so a long form edit does not expire
merely because it has not yet produced a business request. Activity is shared
between tabs of the same origin; the backend remains authoritative.

## Posting an ordinary operation

```mermaid
flowchart LR
    Request["Validated owner request"] --> UseCase["Operations use case"]
    UseCase --> Validate["Validate account and category references"]
    Validate --> Tx["Begin database transaction"]
    Tx --> Header["Record financial operation"]
    Header --> Movements["Record complete physical money movements"]
    Movements --> Commit["Commit"]
    Commit --> Balance["Balances derived from ledger"]
```

Editing or deleting follows the same transaction boundary: replace or remove all
parts of the operation atomically, then derive balances from the resulting
ledger. A balance adjustment is itself an operation, including initial balance.

Since `0.1.0-alpha.3`, affected account identities are locked in deterministic
order and their prospective ledger balances are checked before commit. Transfer
movements net to zero; income and expense cross the boundary of modelled
accounts and therefore do not.

Category mutation and posting share the category-tree advisory lock. A type
change consults the operations-owned history contract and is rejected after the
first reference. Account deletion locks the account before checking movement
history, using the same account-row ordering convention as posting.

An application-layer use case coordinates account identity,
base-currency lock, optional non-zero adjustment and its movement in one
transaction. Neither Accounts nor Operations depends on the other's private
implementation. The initial adjustment date is resolved in the application
timezone.

## Expense from a virtual fund

```mermaid
flowchart LR
    Expense["Expense naming account and fund"] --> Tx["One transaction"]
    Tx --> CheckPhysical["Check physical availability"]
    Tx --> CheckFund["Check fund allocation on account"]
    CheckPhysical --> Physical["Post physical expense movement"]
    CheckFund --> Virtual["Post virtual fund decrease"]
    Physical --> Invariants["Recheck account and fund invariants"]
    Virtual --> Invariants
    Invariants --> Commit["Commit together"]
```

## Transfer with a virtual fund movement

```mermaid
flowchart LR
    Transfer["Transfer amount plus optional fund amount"] --> Tx["One transaction"]
    Tx --> SourceMoney["Decrease source physical balance"]
    Tx --> TargetMoney["Increase target physical balance"]
    Tx --> SourceFund["Decrease fund on source account"]
    Tx --> TargetFund["Increase fund on target account"]
    SourceMoney --> Verify["Verify per-account coverage"]
    TargetMoney --> Verify
    SourceFund --> Verify
    TargetFund --> Verify
    Verify --> SameTotal["Fund total unchanged"]
    SameTotal --> Commit["Commit"]
```

The alpha.4 fund part cannot exceed the physical transfer amount. Accounts and
then funds are locked in deterministic UUID order; physical and virtual
movements are replaced together before coverage is verified.

## Explicit fund allocation

```mermaid
flowchart LR
    Amount["Selected account and amount"] --> Preview["Exact percentage preview"]
    Preview --> Manual["Optional manual correction"]
    Manual --> Tx["One transaction"]
    Tx --> Locks["Lock account then funds"]
    Locks --> Virtual["Post event and virtual movements"]
    Virtual --> Coverage["Verify reserved does not exceed physical"]
    Coverage --> Free["Remainder stays free"]
```

Virtual redistribution uses the same lock and coverage order but posts equal
opposite fund movements and no account movement.

Creating a fund with an initial amount locks the selected account before the
fund definition lock, calculates its free balance, then writes the definition
and one explicit allocation only to that new fund. A coverage or reference
failure rolls back the definition as well as the virtual movement.

A transfer between funds locks the physical account and then both fund
definitions in deterministic order. Equal opposite virtual movements stay on
that account, so physical balance, account reserved total and the total across
all funds are unchanged.

## Transfer and percentage allocation

The UI may compose a physical transfer and an explicit percentage allocation
as one command. The application layer first posts one Operations-owned transfer,
then calculates the exact Funds-owned allocation on the destination account and
creates its virtual event before the request transaction commits. A failure in
either part rolls back both ledgers; this does not turn a fund into a transfer
destination or introduce automatic income allocation.

## Expected occurrence to actual operation

```mermaid
flowchart LR
    Rule["Recurrence rule"] --> Generate["Materialize expected occurrence"]
    Generate --> Pending["pending"]
    Pending -->|postpone| Postponed["postponed with new date"]
    Pending -->|cancel| Cancelled["cancelled"]
    Postponed -->|cancel| Cancelled
    Pending -->|confirm, optional amount override| Tx["Application transaction"]
    Postponed -->|confirm, optional amount override| Tx
    Tx --> Actual["Posted financial operation"]
    Tx -->|transfer option| Allocation["Percentage fund allocation"]
    Actual --> Confirmed["confirmed and linked"]
```

Materialization locks each rule and uses unique `(rule_id, scheduled_on)`
identity for a one-calendar-year window. Generating, postponing or cancelling
an occurrence never changes the actual balance. Confirmation locks the
occurrence, creates one actual operation through the Operations public contract
and records its link in the same transaction. A retry returns that link instead
of posting again. Sliding the window preserves overdue untouched occurrences.
Rule replacement locks the rule and all of its occurrences before validating
the category and deterministically ordered accounts. Confirmation already owns
the occurrence before taking those same reference locks, so concurrent rule
editing and posting serialize without a reverse lock dependency.
Rules without an end date keep advancing that bounded window on later runs.
For a transfer marked for fund allocation, the application layer also invokes
the Funds workflow before linking confirmation; every effect shares the request
transaction. Funds protects the percentage snapshot from concurrent definition
changes until that transaction finishes.

## Forecast calculation

```mermaid
flowchart LR
    Ledger["Current ledger-derived physical balance"] --> BalanceMode["Free or total mode"]
    Funds["Current Funds-owned reserves"] --> BalanceMode
    BalanceMode --> Timeline["Ordered future timeline"]
    Expected["Pending expected income, expense and transfers"] --> Timeline
    Timeline --> Scope["Filter: one account or all accounts"]
    Scope --> Projection["Apply movements through selected horizon"]
    Projection --> Series["Projected balances and influencing operations"]
    Series --> Minimum["Minimum future balance"]
    Series --> Negative["First possible negative date"]
```

Supported horizons are two weeks, month, quarter, half-year and year. Forecasting is
a read calculation and cannot silently post expected data. Beta.2 reads the
Operations ledger and actionable Scheduling occurrences through their public
contracts; liabilities and debts remain future sources until their domains
exist. Events are grouped into deterministic daily closing points. Overdue
occurrences are excluded explicitly and reported, while an internal transfer is
neutral only in the combined scope. Free mode subtracts the current Funds-owned
per-account reserves from the starting physical balances through a batch public
read contract; total mode leaves physical balances unchanged.
