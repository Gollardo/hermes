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
    Tx --> Session["Hashed server session and CSRF tokens"]
    Session --> Cookie["HttpOnly session cookie"]
    Cookie --> Guard["Protected API guard"]
    Guard --> CSRF["CSRF check for writes"]
    CSRF --> UseCase["Authenticated use case"]
```

After credential commit, setup can only report a conflict. Login throttling is
locked and updated in the same database transaction as password verification
and session issuance, preventing parallel attempts from bypassing the counter.
Database request dependencies close at FastAPI function scope, so a successful
HTTP response and authentication cookies are sent only after transaction commit.

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

In `0.1.0-alpha.3`, affected account identities are locked in deterministic
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

The fund part cannot exceed the physical transfer amount without an explicitly
designed alternative rule; this is currently an assumption, not an
owner-confirmed invariant.

## Expected occurrence to actual operation

```mermaid
flowchart LR
    Rule["Recurrence rule"] --> Generate["Materialize expected occurrence"]
    Generate --> Pending["pending"]
    Pending -->|postpone| Postponed["postponed with new date"]
    Postponed -->|due again| Pending
    Pending -->|cancel| Cancelled["cancelled"]
    Pending -->|confirm| Tx["Operations transaction"]
    Tx --> Actual["Posted financial operation"]
    Actual --> Confirmed["confirmed and linked"]
```

Generating, postponing or cancelling an occurrence never changes the actual
balance. Confirmation creates one actual operation and must be idempotent.
Idempotency is a technical requirement inferred from safe retries and still
needs a concrete design.

## Forecast calculation

```mermaid
flowchart LR
    Ledger["Current ledger-derived balance"] --> Timeline["Ordered future timeline"]
    Expected["Pending expected income, expense and transfers"] --> Timeline
    Loans["Planned loan and installment payments"] --> Timeline
    Debts["Planned debt repayments"] --> Timeline
    Timeline --> Scope["Filter: one account or all accounts"]
    Scope --> Projection["Apply movements through selected horizon"]
    Projection --> Series["Projected balances and influencing operations"]
    Series --> Minimum["Minimum future balance"]
    Series --> Negative["First possible negative date"]
```

Supported horizons are week, month, quarter, half-year and year. Forecasting is
a read calculation and cannot silently post expected data.
