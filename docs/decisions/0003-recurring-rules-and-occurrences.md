# ADR 0003: recurring rules and expected occurrences

## Status

Accepted for `0.1.0-beta.1`; revisit after real calendar use.

## Context

Hermes needs recurring income, expense and transfer plans without allowing a
plan to affect the physical ledger. Materialization must be bounded and safe to
retry. Editing a rule must not rewrite an occurrence the owner has already
confirmed, postponed or cancelled.

## Decision

Scheduling owns two kinds of records:

- a **recurring rule** is the current template and recurrence definition;
- an **expected occurrence** is a dated snapshot generated from one rule.

Rules support `daily`, `weekly`, `monthly` and `yearly` frequencies. The start
date is the recurrence anchor. An optional end date is inclusive. Weekly rules
select a non-empty unique set of ISO weekdays and repeat every one, two or three
weeks. Monthly rules repeat every one, two or three months on the start day.
Daily and yearly rules use interval one. Monthly rules accept only start days
1–28, and yearly rules reject 29 February, so generation never invents a policy
for a missing calendar day. API validation and database checks enforce the same
frequency/interval/weekday shape.

Materialization covers `[today, today + 1 calendar year]` in the configured
application timezone. Both boundaries are inclusive. A unique
`(rule_id, scheduled_on)` identity and a row lock on the rule make repeated or
concurrent materialization idempotent.

An occurrence stores:

- immutable `scheduled_on`, its identity in the source sequence;
- mutable `due_on`, changed only by postponing that occurrence;
- a complete operation snapshot: type, accounts, category, amount and
  description;
- status `pending`, `postponed`, `cancelled` or `confirmed`;
- `manually_modified`, an explicit boundary protecting owner changes;
- an optimistic version and, after confirmation, the actual operation link.

Rule edits synchronize only current/future non-confirmed,
non-manually-modified occurrences.
Matching dates receive the new snapshot. Dates removed by the new recurrence or
by disabling the rule are automatically cancelled. Newly matching dates are
materialized. An automatically cancelled occurrence may be restored if a later
rule edit makes its original date valid again. Confirmed, postponed and manually
cancelled occurrences never change implicitly.

Untouched occurrences that become overdue remain actionable. Advancing the
materialization window never cancels or deletes them.

Confirmation locks the occurrence and calls the Operations public posting
contract in the same database transaction. Posting and the `confirmed` link
therefore commit or roll back together. Repeated confirmation returns the same
link and cannot create a second financial operation. Postponing and cancelling
never call Operations and cannot change actual balances.

Rule replacement locks the rule and its occurrences before acquiring category
and account reference locks. Confirmation starts with the occurrence and then
uses the same category-before-account order as ordinary posting. If a rule edit
wins, a confirmation carrying the old occurrence version is rejected; if
confirmation wins, the subsequent synchronization preserves that snapshot.

All scheduling values are calendar dates. The application timezone determines
`today`. Creating the first recurring rule locks timezone changes through the
settings API. Migrating an existing schedule to another timezone is outside
this release.

## Consequences

- Expected data is suitable for the calendar and later forecasting but remains
  separate from the financial journal.
- Snapshotting preserves the exact intent shown before confirmation.
- Rule edits require synchronization work but do not surprise owners by
  rewriting manual decisions.
- More expressive recurrences, missing-day policies and timezone migration need
  a future decision rather than hidden defaults.
