# Financial scenarios

## Owner-confirmed direction

Scenarios answer: “What will change if I make this financial decision?” A
scenario is a temporary, hypothetical overlay over one coherent baseline
forecast. It does not mutate actual operations, expected occurrences, funds or
other domain state.

The future capability is named **Oracle**; its primary user action is **What
if?**. The name is product language, not a claim of certain prediction.

## Financial truth boundary

The authoritative calculation remains deterministic and exact. It consumes
public read contracts and applies structured hypothetical inputs using the same
financial semantics as the baseline forecast.

A local AI adapter may:

- translate natural language into a structured scenario draft;
- identify missing material inputs and request clarification;
- select a supported scenario command;
- explain an already calculated comparison.

It may not calculate balances authoritatively, bypass domain validation, write
to another module, post an operation or silently create a planned occurrence.
Every supported scenario must also be constructible without AI.

## Conceptual model

- `ScenarioBaseline`: coherent source snapshot, scope, horizon and assumptions.
- `ScenarioDraft`: typed hypothetical changes supplied or approved by the user.
- `ScenarioComparison`: baseline and alternative outcomes plus exact deltas.
- `ScenarioRiskBoundary`: user stop-loss or explainable system suggestion.
- `SavedScenario`: optional named hypothesis, separate from confirmed plans.

These names describe future concepts, not approved tables or API DTOs.

## Invariants

- Running, editing or discarding a scenario is read-only for every financial
  owning module.
- Baseline and alternative use the same source snapshot, scope, currency and
  horizon.
- Money remains `Decimal`/`NUMERIC` and exact decimal strings; AI never parses
  authoritative amounts through binary floating point.
- A scenario distinguishes actual facts, confirmed plans, hypothetical changes
  and model-derived estimates.
- Missing amount, date, account/fund scope or other material input is not
  invented silently.
- A saved scenario remains hypothetical. Converting it into a plan creates a
  draft for the owning composer and requires an explicit ordinary confirmation.
- Conversation text is not persisted by default.
- Failure or absence of the local model cannot disable structured scenario
  calculation.

## Stop-loss and suggested boundary

A user-defined stop-loss is a preference indicating an undesirable lower bound;
it does not mutate ledger rules and does not by itself reject a valid operation.

A system-suggested boundary is derived from explainable structured facts and/or
historical statistics. It must expose its method, period and inputs, remain
separate from the user value and be omitted when evidence is insufficient.
Whether either boundary becomes an enforceable policy is explicitly deferred.

## Persistence

The default scenario is ephemeral. Optional saved scenarios require a future
retention and invalidation design: source data may change after saving, so a
reopened scenario must identify its original baseline and recalculate or declare
it stale. Saving raw conversations is out of scope.

## Open design questions

- Initial set of supported hypothetical commands and ranges.
- Snapshot/version strategy for saved scenario comparison.
- Scope and inheritance of user stop-loss settings.
- Explainable method for suggesting a risk boundary.
- Whether scenario calculation belongs inside Forecasting or behind a separate
  read-side Scenarios module once detailed contracts are designed.
- Local model packaging, resource limits and update policy.
- Whether semantic retrieval proves useful; a vector index is optional,
  derived and rebuildable, never a source of financial truth.
