# Forecasting

Owns read-side calculations that combine actual balances with expected future
movements. It does not post or mutate financial operations.

`service.calculate_forecast` is the deterministic pure calculation boundary.
`service.build_forecast` composes public contracts from Accounts, Operations and
Scheduling. The module owns no tables: projections are calculated on request and
returned as exact decimal strings.
