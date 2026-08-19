# Oracle · What if?

## Status

The owner confirmed the product direction and safety rules on 2026-08-18. The
screen, specific model, API, and scenario storage are not implemented and
require separate design and architecture review before entering a release
scope.

## Name and promise

**Oracle** is the name of the Hermes capability for comparing possible
financial futures. **What if?** is its primary action and scenario-mode name.
The combined name preserves the ancient Greek theme of Hermes and communicates
parallel financial alternatives.

Oracle does not claim to know the future. It answers a more precise question:

> What changes in the known financial forecast if this decision is added while
> every other disclosed assumption remains the same?

## Primary job

Test a purchase, income change, payment move, or another hypothesis with as few
steps as possible without changing the ledger or confirmed plan.

## Baseline flow

1. The owner selects “What if?” and enters free text or opens the regular
   structured form.
2. An optional local AI adapter extracts action type, amount, date, scope, and
   conditions into a structured draft.
3. The interface shows the interpreted fields. A materially unknown field
   triggers one concise clarification; the model never fills it silently.
4. The deterministic engine calculates the alternative from the same coherent
   snapshot, scope, and horizon as the baseline forecast.
5. The response states the consequence first, then shows comparison, risks,
   assumptions, and sources.
6. The scenario disappears on close unless the owner separately chooses “Save
   scenario” or “Create plan draft”.

## Minimum structured form without AI

- hypothesis type;
- amount or amount change;
- date or date change;
- account or compatible combined scope;
- optional fund or source of money;
- comparison horizon.

AI shortens the path to this form but never unlocks a financial capability that
is unavailable without it.

## Response composition

1. **Answer:** one verifiable sentence about the main consequence.
2. **Before → after:** free money, minimum balance, minimum date, period end, and
   nearest stress window.
3. **Risk boundaries:** the owner's stop-loss and a separate system suggestion
   with an explanation of its method.
4. **Why:** the events and funds that changed the result.
5. **Assumptions:** included income, expenses, obligations, horizon, and unknown
   factors.
6. **Variants:** change amount or date, remove an event, compare, or save.

The chart reveals the comparison; it is not the only answer.

## Stop-loss and system-suggested boundary

The owner can configure a monetary stop-loss for a compatible scope: a balance
below which a scenario is considered undesirable. It is a risk preference, not
a prohibition on a financial operation.

Hermes may separately suggest a boundary from explainable data, such as
mandatory expenses for the upcoming period, a stable expense baseline, or
required coverage of confirmed events. The suggested boundary:

- never replaces the owner's value automatically;
- shows its method, data period, and components;
- is omitted when evidence is insufficient;
- can be accepted, changed, or hidden;
- does not block an action without a separate future product decision.

## Handling uncertainty

Every response element belongs to one class:

- **fact** — ledger-derived state;
- **confirmed plan** — an expected event or obligation;
- **scenario** — a temporary user hypothesis;
- **estimate** — statistical or model-derived input with source and confidence.

If a date or amount is a range, the result does not collapse it into one exact
number without an explicit policy. The system shows a range or several boundary
scenarios.

## Saving and actions

- By default, neither the scenario nor conversation text is stored.
- A saved scenario remains a separate hypothesis and does not alter the factual
  forecast.
- “Create plan draft” transfers reviewed structured fields into the expected-
  event composer.
- Only normal explicit confirmation in that composer can write a plan.
- Chat never directly creates, confirms, or posts a financial operation.

## States and errors

- **AI disabled or unavailable:** structured scenario entry works completely.
- **Ambiguous request:** show the interpreted part and one specific
  clarification.
- **Insufficient history:** deterministic forecasting works; a historical
  suggestion is honestly absent.
- **Forecast unavailable:** model-generated plausible text cannot replace the
  answer.
- **Source-data conflict:** recalculate the scenario from a new snapshot after
  a clear notice.
- **Incompatible currencies:** combined totals remain prohibited until a
  conversion-aware model exists.

## Future prototype checks

- A purchase with a known amount and date.
- The same purchase without a date and with one concise clarification.
- Moving the purchase beyond a stress window.
- A scenario crossing the owner's stop-loss.
- Different owner and system-suggested boundaries.
- A complete keyboard-only path without AI.
- Closing without saving and explicitly creating a plan draft.
