# Module boundaries

## Ownership map

| Module | Owns | Collaborates through |
| --- | --- | --- |
| `auth` | owner credential, password hash, sessions, login throttle | authentication dependency and settings setup contract |
| `settings` | persisted preferences and base-currency lock | explicit settings queries/commands |
| `accounts` | account identity and account rules | account references and balance read contract |
| `categories` | category tree | category reference validation |
| `operations` | posted operations and physical money movements | atomic posting commands and ledger reads |
| `funds` | fund definitions, percentages, virtual movements | fund posting contracts and application coordination with physical ledger reads |
| `scheduling` | recurrence rules and expected occurrences | confirmation command into operations |
| `forecasting` | future-balance calculations | read contracts from ledger, funds and plans |
| `liabilities` | credits and installment plans | planned/payment integration contracts |
| `debts` | `i_owe` and `owed_to_me` obligations | repayment posting contract |
| `reports` | reporting read models | public read contracts only |
| `imports` | parse, map, preview, duplicate candidates | owning modules' validation/write commands |
| `backup` | versioned export and restore orchestration | module-owned export/import contracts |

`app.core` owns technical configuration and database lifecycle, not business
rules. `app.api` composes HTTP routes and cross-cutting concerns. Cross-module
commands that share a transaction belong to `app.application`; it owns no tables
and calls only public module contracts.

## Dependency direction

Arrows below mean “uses a public contract of”, not direct access to private
tables.

```mermaid
flowchart TB
    API["API composition"] --> Auth
    API --> Settings
    API --> Application["Application use cases"]
    Application --> Auth
    Application --> Settings
    Application --> Accounts
    Application --> Operations
    Application --> Funds
    Application --> Scheduling
    Auth --> Settings
    API --> Operations
    API --> Funds
    API --> Scheduling
    API --> Reports
    Operations --> Accounts
    Operations --> Categories
    Operations --> Funds
    Funds --> Accounts
    Scheduling --> Operations
    Scheduling --> Accounts
    Scheduling --> Categories
    Scheduling --> Settings
    Liabilities --> Scheduling
    Liabilities --> Operations
    Debts --> Scheduling
    Debts --> Operations
    Forecasting --> Accounts
    Forecasting --> Operations
    Forecasting --> Funds
    Forecasting --> Scheduling
    Forecasting --> Liabilities
    Forecasting --> Debts
    Reports --> Operations
    Reports --> Funds
    Imports --> Operations
    Imports --> Accounts
    Backup --> Modules["All module export/restore contracts"]
```

Authentication guards every API except setup status, fresh setup, first-run
setup restore, login and health. It does not own financial data. Backup may
orchestrate all modules, but must not duplicate their validation rules.

For schema-level round trips, every owning module exposes a narrow `backup.py`
persistence surface. It is separate from ordinary runtime contracts: only
Backup uses it, and the versioned validator enforces the same documented
invariants before any rows are replaced.

Scheduling validates account/category snapshots and the application timezone
through those modules' public contracts. It posts confirmed occurrences only
through the Operations contract and never writes the physical ledger directly.

The application setup use case calls Auth, Categories and Backup only through
their public contracts. Fresh setup commits credential, preferences, optional
category templates and the first session atomically. First-run restore validates
the document and replaces the new settings/data in that same transaction, so a
failed restore cannot leave a partially initialized instance. A future module
creating the first financial record must call settings' public currency-lock
command in that write transaction.
These Python-level commands and validators are exported by
`app.modules.settings.contracts`; HTTP authentication and CSRF dependencies are
composed by `app.api`, so the settings module does not depend on auth internals.

## Boundary rules

- A module owns writes to its state and defines any public commands or reads.
- Cross-module changes that must stay consistent share one database transaction.
- Cross-module orchestration normally belongs to `app.application`. A module
  that owns a source record's lifecycle may call another module's explicit
  public posting contract when the dependency remains one-way; operation-owned
  fund movements use this narrower rule.
- Read-oriented modules may query purpose-built public read models; this does not
  authorize writes around the owner module.
- Avoid generic repository or service abstractions until repeated behaviour
  proves a real need.
- Moving code between modules requires updating this map and related domain docs.

## Open questions

- Whether liabilities and debts remain separate modules once detailed lifecycle
  use cases are designed.
- Which stable public read contracts reporting and forecasting need.
