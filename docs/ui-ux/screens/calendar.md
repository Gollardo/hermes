# Calendar and recurring operations direction

## Status

Owner-confirmed beta.1 scope implemented using the existing preliminary visual
direction. This is not approval of a final design system.

## User job

The owner needs to see what is expected, distinguish it from posted money and
resolve an occurrence with one deliberate action. The screen combines the
monthly context, an action-oriented upcoming list and recurring-rule management.

## Information hierarchy

1. Explanation that expected events do not affect actual balances.
2. Month navigation and visible account/type filters.
3. Seven-column monthly grid with status/type summaries.
4. Upcoming and overdue occurrences with confirm, date-specific postpone and
   cancel actions.
5. Rule list and create/edit form.

The calendar uses an internally scrollable grid on narrow screens instead of
expanding the document. The upcoming list becomes the primary mobile action
surface and is placed before the dense monthly grid. The first 12 actionable
events are shown with an explicit full-result count instead of looking like a
complete unpaginated list.

## States and actions

- `pending` and `postponed` expose quick actions.
- `confirmed` remains visible and links to the exact posted operation; route
  navigation resets scroll so the linked-fact context is visible immediately.
- `cancelled` remains visible but visually secondary.
- Overdue is communicated by text and boundary treatment, never by color alone.
- Every calendar chip contains a visible status label; color and strike-through
  are supplementary signals only.
- A failed confirmation keeps the occurrence and entered postpone date visible.
- Disabling a rule explains that untouched future occurrences are cancelled;
  manual and confirmed decisions are preserved.
- Editing a rule on a narrow screen moves focus context to the existing form;
  archived references already used by that rule stay named, but an active rule
  must select available references before it can be saved.

## Form rules

- Type is explicit: income, expense or transfer.
- Amount is an unsigned exact decimal with the base currency visible.
- Income and expense require a matching category and one account.
- Transfer requires two different accounts and no category.
- Start date is visible; end date is optional and inclusive.
- Monthly rules explain the supported 1–28 day range before submission.
- Description is optional and used as the human calendar title.

## Deliberately deferred

- Drag-and-drop rescheduling.
- Custom intervals and weekday sets.
- Notification delivery outside the application.
- Forecast balances or insufficiency projections inside calendar cells.
- Final decision whether Calendar and Forecast share a permanent top-level
  «План» container.
