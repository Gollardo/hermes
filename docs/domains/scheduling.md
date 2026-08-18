# Recurring and expected operations

## Owner-confirmed lifecycle

A recurring rule does not affect actual balance. It materializes expected
occurrences. A user may `confirm`, `postpone` or `cancel` an occurrence. Internal
status candidates are `pending`, `confirmed`, `postponed` and `cancelled`.

Only confirmation creates an actual financial operation that affects balance.
Postponing one occurrence need not modify its source recurrence rule.

## Terms and boundary

- **Recurrence rule** describes a repeating intent.
- **Expected occurrence** is a dated, mutable plan generated from the rule.
- **Actual operation** is a posted operations-module fact linked after
  confirmation.

Scheduling owns rules and occurrences; operations owns posting. Confirmation is
a transactional cross-module use case. The flow appears in
[data-flow.md](../architecture/data-flow.md).

## Confirmed recurrence and materialization policy

In plain language, the first-release recurrence editor intentionally supports a
small predictable subset: every day; selected weekdays every one to three
weeks; the same date every one to three months, limited to dates 1–28; or once
per year except 29 February. It prepares instances only one year ahead when the
calendar/materialization command runs, not through a background service. An
unbounded rule itself continues beyond that stored one-year window.

- Supported frequencies are `daily`, `weekly`, `monthly` and `yearly`.
- Weekly rules select one or more ISO weekdays and repeat every 1–3 weeks.
  Monthly rules repeat every 1–3 months on the `start_on` day. Yearly rules
  repeat on the month and day of `start_on`; its year advances automatically.
- `start_on` anchors the recurrence; `end_on` is optional and inclusive.
- Monthly starts are limited to days 1–28. Yearly rules cannot start on
  29 February. A nonexistent occurrence date is never silently shifted.
- Materialization includes today through the same calendar date one year ahead,
  evaluated in the configured application timezone.
- A rule without `end_on` has no implicit one-year end. Each materialization
  advances the physical occurrence window to one year from its current date.
- The first recurring rule locks the application timezone. There is no implicit
  reinterpretation of persisted calendar dates.
- `(rule_id, scheduled_on)` is the deterministic identity. Repeated and
  concurrent materialization cannot create duplicates.
- `scheduled_on` remains the source identity. Postponing changes only `due_on`
  and keeps persistent status `postponed`.

## Rule editing policy

An occurrence is protected from implicit rule updates after confirmation or any
manual postponement/cancellation. Other generated occurrences are synchronized:

- matching dates receive the current rule snapshot;
- dates no longer produced are automatically cancelled;
- newly produced dates are materialized;
- disabling a rule automatically cancels its untouched future occurrences.

Past pending occurrences are preserved as overdue and require an explicit
confirm, postpone or cancel action.

Re-enabling or another edit may restore an automatically cancelled occurrence,
but never one cancelled manually.

In practical terms, changing a rule updates only untouched current and future
instances. Anything already confirmed, postponed or manually cancelled keeps
the exact decision the owner made.

## Financial invariants

- Rules and expected occurrences never create account or fund movements.
- Confirmation posts exactly one actual operation and links it atomically.
- Confirmation may override the amount of that occurrence. The confirmed
  snapshot records the actual amount and future siblings keep the rule amount.
- A transfer snapshot may request percentage allocation on the destination
  account. Its physical transfer, fund allocation and confirmation link commit
  or roll back together. The percentages are read from one locked active-fund
  snapshot at confirmation time; missing positive percentages fail explicitly.
- A failed posting leaves the occurrence actionable and unlinked.
- Confirming an already confirmed occurrence is idempotent.
- Postponing one occurrence never changes its rule or siblings.
- A concurrent rule edit either precedes confirmation and invalidates its stale
  optimistic version, or follows it and preserves the confirmed snapshot.

## Calendar read policy

- The monthly grid loads every API page in its bounded 42-day range, so a large
  number of rules cannot silently hide calendar events.
- The action list intentionally shows the first 12 pending/postponed events and
  displays both the visible and complete filtered counts.
- A confirmed occurrence links to its exact actual operation; its stored
  schedule snapshot is not relabelled as the current financial fact.

The complete decision and persistence consequences are recorded in
[ADR 0003](../decisions/0003-recurring-rules-and-occurrences.md).

## Deferred questions

- Richer recurrence expressions beyond the implemented weekly/monthly interval.
- A user-selectable missing-day policy for dates 29–31 and leap day.
- Background materialization without an external job queue.
- Migration semantics if instance timezone changes after schedules exist.
