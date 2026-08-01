# Virtual funds

## Meaning

A fund is a virtual purpose assigned to some real money, not a bank account. One
fund may be spread across several physical accounts—for example, `20 000.00` on
a debit account plus `80 000.00` on savings means `100 000.00` in the fund.

## Owner-confirmed rules and invariants

- An expense may identify the fund consumed on a specific account.
- A transfer may move a virtual portion of a fund between the source and target
  accounts without changing the fund total.
- Arbitrary incoming amounts can be allocated among funds. Each active fund may
  have a user-defined percentage, changeable at any time.
- The sum of active allocation percentages is at most 100%. Any remainder stays
  free money.
- On each account, total virtual fund value cannot exceed available physical
  balance.
- Spending from a fund decreases both physical account balance and that fund's
  virtual balance on the account.
- Moving a fund between accounts decreases/increases physical source/target and
  virtual source/target respectively, while total fund value is unchanged.

Percentages and money require exact decimal arithmetic, never `float`.

## Boundary

Funds owns definitions, allocation percentages and virtual movements. Operations
owns physical movements. Any command affecting both must use one database
transaction and verify post-change invariants before commit. See the
[expense and transfer diagrams](../architecture/data-flow.md).

## Assumptions requiring confirmation

- The virtual fund amount moved with a physical transfer cannot exceed that
  transfer's amount.
- Percentage allocation is applied only on an explicit user action or selected
  eligible incoming amount, not retroactively when percentages change.
- A fund can be archived only after choosing how to handle its remaining amount.

## Open questions

- Scale and rounding/remainder distribution for percentages.
- Which operation types are eligible for automatic allocation.
- Concurrency/locking strategy when simultaneous operations consume the same
  account and fund balances.
- Whether negative fund balances are always forbidden.
