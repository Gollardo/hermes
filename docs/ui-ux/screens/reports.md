# Reports screen

The owner-confirmed 0.2.0 navigation exposes a top-level «Отчёты» destination.
Its first report answers how income or expense is distributed over a selected
month or custom inclusive date range.

The category chart is the visual centre. Exact period total and operation count
stay adjacent to it; below, category groups are collapsed by default and reveal
exact operation amounts, dates and visible links back to the corresponding
journal detail. Income and expense are explicit mutually exclusive choices;
period mode remains secondary. Empty, loading and error states must not present
partial data as a complete report. Money uses the project currency symbol and
text dates use «20 января 2025». Child categories use the leaf name as the main
label and show the root category as secondary context. Category disclosure uses
the same compact chevron pattern as the operation journal and shows the number
of source operations before expansion.
