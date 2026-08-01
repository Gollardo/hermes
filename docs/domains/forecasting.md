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

## Boundary and flow

Forecasting is a read-side calculation. It combines ledger-derived current
balances with public planned-occurrence and obligation contracts, orders their
effects on a timeline and applies exact decimal arithmetic. It cannot confirm or
post expected operations. See the [forecast diagram](../architecture/data-flow.md).

## Assumptions requiring confirmation

- “All accounts” sums only values in a compatible currency; cross-currency
  aggregation is undefined until a currency model exists.
- Cancelled and confirmed expected occurrences are excluded as future planned
  effects; the confirmed actual operation is already in the ledger.
- Multiple movements on one date use deterministic ordering but daily end
  balance may be more meaningful than an arbitrary intraday sequence.

## Open questions

- Date/time granularity and ordering for same-day operations.
- Treatment of postponed, overdue and uncertain expected occurrences.
- Whether inactive/archived accounts participate.
- Performance and snapshot strategy once data volume is measurable.
