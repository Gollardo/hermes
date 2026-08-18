# Reports

Reports is a read-only module. It owns response composition, not financial
facts, and consumes exact Operations and Categories public read contracts.

The report developed on the intermediate `0.2.0` line and is recorded under
`0.3.0` in the current changelog. It selects one inclusive calendar period and
exactly one operation type (`income` or `expense`). It groups posted facts by their
operation category, preserves the root-category context, lists the source
operations and calculates exact totals with `Decimal`. Percent shares are
display metadata rounded to two decimal places; monetary API values remain
four-place decimal strings. Reports cannot post, edit or silently reclassify an
operation, and archived categories remain readable as history.

Month selection is a UI convenience over the same inclusive custom-date API.
The second requested perspective, future fund balances, remains in Forecasting
because it is a plan rather than a report over posted facts.
