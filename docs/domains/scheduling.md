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

## Initialization assumptions

- Confirmation must be idempotent so retries cannot create duplicate actual
  operations.
- Materialization needs a deterministic occurrence identity and a bounded future
  window rather than infinite generation.

## Open questions

- Recurrence expression and timezone/daylight-saving semantics.
- When and how future occurrences are materialized without a job queue.
- Editing a rule: affect only future unmodified occurrences or regenerate them.
- Whether `postponed` is a persistent state or a transition back to `pending`
  with a new due date.
