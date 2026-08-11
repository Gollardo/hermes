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

- Supported frequencies are `daily`, `weekly`, `monthly` and `yearly`.
- `start_on` anchors the recurrence; `end_on` is optional and inclusive.
- Monthly starts are limited to days 1–28. Yearly rules cannot start on
  29 February. A nonexistent occurrence date is never silently shifted.
- Materialization includes today through the same calendar date one year ahead,
  evaluated in the configured application timezone.
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

## Financial invariants

- Rules and expected occurrences never create account or fund movements.
- Confirmation posts exactly one actual operation and links it atomically.
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

- Custom intervals, weekdays and richer recurrence expressions.
- A user-selectable missing-day policy for dates 29–31 and leap day.
- Background materialization without an external job queue.
- Migration semantics if instance timezone changes after schedules exist.
