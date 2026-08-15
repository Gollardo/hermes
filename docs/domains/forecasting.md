# Balance forecasting

## Owner-confirmed behavior

Forecast horizons are week, month, quarter, half-year and year. A forecast can
target one account or all accounts combined and includes:

- current actual balance;
- expected income and expense;
- planned transfers;
- credit/installment payments;
- debt repayments.

It reports the future balance series, minimum future balance, a possible first
negative-balance date, and the operations influencing changes.

The default series represents free money: current physical balances minus
amounts reserved in virtual funds. The owner can explicitly switch to all money,
including reserved amounts. This view choice does not change allocations.
The reserve snapshot comes from the Funds public batch read after Forecasting
has taken shared account locks, preserving the Accounts → Funds lock order used
by coverage-dependent writes.

Scheduling occurrences do not currently select a virtual fund. Free mode
therefore starts from today's free balance and applies planned physical effects
without guessing which future expense may consume a reserve or which income may
later be allocated. The UI states this limitation next to the series.

## Boundary and flow

Forecasting is a read-side calculation. It combines ledger-derived current
balances with public planned-occurrence and obligation contracts, orders their
effects on a timeline and applies exact decimal arithmetic. It cannot confirm or
post expected operations. See the [forecast diagram](../architecture/data-flow.md).

## Implemented beta.2 policy

- The series starts with today's ledger-derived actual balance. It includes
  actionable `pending` and `postponed` occurrences from today through the
  inclusive horizon end; `confirmed` and `cancelled` occurrences are excluded.
- Overdue actionable occurrences are not silently moved to today. Their count is
  reported for the selected scope so the user can resolve them in the calendar.
- Events are ordered by `(due_on, occurrence_id)`, grouped by date, and applied
  as one deterministic daily closing balance. The minimum and first negative
  date use these closing balances, not an invented intraday order.
- Week, month, quarter and half-year responses contain one closing point for
  every calendar date in the inclusive horizon, including dates without
  events. A year response uses monthly intervals: the first and last may be
  partial months, while intermediate points close on calendar month-end.
- Monthly display aggregation does not reduce risk accuracy: minimum balance
  and first negative date are still calculated from ordered daily event
  closings before the response is grouped into month points. Every source event
  remains attached to its monthly interval for explanation.
- A single-account transfer is outgoing on its source and incoming on its
  destination. An internal transfer has zero effect on the all-accounts balance,
  but remains in the explanation for that date.
- Week ends at `today + 7 days`; month, quarter, half-year and year preserve the
  day of month where possible and clamp to the target month's last day.
- All current account identities, including archived accounts, participate in
  the combined balance because their ledger history still contains physical
  money. A selected archived account can still be inspected.
- Money is calculated with `Decimal`; API money fields are exact decimal strings.
- The current account model has one locked base currency and no per-account
  currency, so all-account aggregation is compatible by construction.
- The calculation is read-only and persists no projection or snapshot. Beta.2
  therefore adds no schema migration.
- One request takes shared locks on the selected actionable occurrences and
  account identities before reading ledger movements. Confirmation and posting
  use the corresponding exclusive locks in the same Scheduling-to-Accounts
  order, so one forecast cannot count an occurrence in both actual and planned
  money during a concurrent confirmation.
- The application screen materializes Scheduling's rolling one-year window
  before reading the forecast. The forecast GET itself remains side-effect free;
  API clients that bypass the screen must synchronize the schedule explicitly.

## Open questions

- Performance and snapshot strategy once data volume is measurable.
- The consistent read currently holds shared locks for the request and returns
  every explaining event plus up to one point per day for a half-year horizon.
  Large schedules may require a versioned read projection or another snapshot
  strategy that preserves explanations.
- Whether future multi-currency accounts require separate series or explicit FX
  scenarios; implicit conversion remains prohibited.
- Whether liabilities and debts join the projection after those domains exist.
