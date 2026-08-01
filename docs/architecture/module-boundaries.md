# Module boundaries

## Ownership map

| Module | Owns | Collaborates through |
| --- | --- | --- |
| `auth` | owner setup, password hash, sessions | authentication dependency at API boundary |
| `settings` | persisted preferences | explicit settings queries/commands |
| `accounts` | account identity and account rules | account references and balance read contract |
| `categories` | category tree | category reference validation |
| `operations` | posted operations and physical money movements | atomic posting commands and ledger reads |
| `funds` | fund definitions, percentages, virtual movements | atomic coordination with operations/accounts |
| `scheduling` | recurrence rules and expected occurrences | confirmation command into operations |
| `forecasting` | future-balance calculations | read contracts from ledger and plans |
| `liabilities` | credits and installment plans | planned/payment integration contracts |
| `debts` | `i_owe` and `owed_to_me` obligations | repayment posting contract |
| `reports` | reporting read models | public read contracts only |
| `imports` | parse, map, preview, duplicate candidates | owning modules' validation/write commands |
| `backup` | versioned export and restore orchestration | module-owned export/import contracts |

`app.core` owns technical configuration and database lifecycle, not business
rules. `app.api` composes module routers and cross-cutting HTTP concerns, not
domain use cases.

## Dependency direction

Arrows below mean “uses a public contract of”, not direct access to private
tables.

```mermaid
flowchart TB
    API["API composition"] --> Auth
    API --> Operations
    API --> Scheduling
    API --> Reports
    Operations --> Accounts
    Operations --> Categories
    Funds --> Operations
    Funds --> Accounts
    Scheduling --> Operations
    Liabilities --> Scheduling
    Liabilities --> Operations
    Debts --> Scheduling
    Debts --> Operations
    Forecasting --> Accounts
    Forecasting --> Operations
    Forecasting --> Scheduling
    Forecasting --> Liabilities
    Forecasting --> Debts
    Reports --> Operations
    Reports --> Funds
    Imports --> Operations
    Imports --> Accounts
    Backup --> Modules["All module export/restore contracts"]
```

Authentication guards every API except setup, login and health. It does not own
financial data. Backup may orchestrate all modules, but must not duplicate their
validation rules.

## Boundary rules

- A module owns writes to its state and defines any public commands or reads.
- Cross-module changes that must stay consistent share one database transaction.
- Read-oriented modules may query purpose-built public read models; this does not
  authorize writes around the owner module.
- Avoid generic repository or service abstractions until repeated behaviour
  proves a real need.
- Moving code between modules requires updating this map and related domain docs.

## Open questions

- Whether liabilities and debts remain separate modules once detailed lifecycle
  use cases are designed.
- Whether fund transfer should be an operation-owned composite command or a
  fund-owned orchestrator sharing the operations transaction boundary.
- Which stable public read contracts reporting and forecasting need.
