# UI/UX vision

## Document status

This document combines the owner-confirmed product direction from 2026-08-02,
the current `0.4.0` interface approved on 2026-08-18, and hypotheses for future
development. The current implementation is the baseline for the first public
release, but this document does not define a final design system or approve
screens that have not yet been implemented.

The document is based on the confirmed Hermes domain model, the current
[project status](../project-status.md), the [roadmap](../roadmap.md), external
research, and five supplied visual references. The references establish the
desired feel; they are not mockups to copy.

## North star: understand consequences before deciding

Owner-confirmed direction from 2026-08-18:

> **Hermes helps the owner understand what will happen to their money next and
> test a financial decision before it becomes a fact.**

The main product question is:

> **What will happen if I make this financial decision now?**

Tracking remains the foundation, but it is not the final goal. The Hermes
product ladder is:

```text
Facts → Intentions → Forecast → Scenario → Consequences → Decision
```

The past helps identify patterns, the present provides an exact starting point,
and the future combines known plans and obligations. A scenario temporarily
adds a hypothetical decision and compares the result with the baseline forecast
without changing the ledger or schedule.

The future **Oracle** capability continues the ancient Greek theme of the Hermes
name. Its primary **What if?** action presents alternative financial scenarios
as parallel possible futures. This is a metaphor, not a promise of infallible
prediction: Oracle must disclose the facts, assumptions, sources, and
uncertainty behind a result.

## Interface product promise

Hermes should feel like a modern personal-finance command center: precise,
composed, and ready for action. Shortly after opening it, the owner should
understand:

- how much money physically exists;
- how much already has a purpose in funds;
- how much remains free;
- which obligations are approaching;
- whether expected events may cause a shortfall;
- what changed recently and what action needs attention now.

Free money is the owner-confirmed priority. The main everyday questions are:
“How much is free now?”, “How much will be free after the selected number of
days?”, “What will happen if I make this decision?”, and “Where did most of the
money go?”. Total money, debts and liabilities, and trends provide context but
must not compete with the primary answer.

The interface must not judge the owner, induce guilt, or hide uncertainty behind
an optimistic visualization. Its job is to create control through clear facts,
consequences, and next actions.

## Primary user

The first user is the sole owner of a self-hosted instance and the author of the
project. They manage their own money but are not expected to know accounting
terminology, financial analytics, or double-entry bookkeeping. The interface
should nevertheless remain understandable to a broader audience because the
owner is likely to publish the project.

The interface does not assume one usage frequency. It supports:

- short daily sessions for entering and checking operations;
- a weekly review of free money, funds, and upcoming events;
- periodic expense analysis and adjustment of financial plans;
- occasional administrative work such as setup, archiving, import, backup, and
  restore.

Hermes must not assume multiple users, a bank connection, or permanent access
to external services.

## User jobs

### Understand the present

- see physical account balances and a compatible combined total;
- distinguish physical, virtually reserved, and free money;
- find recent operations and quickly verify why a balance changed;
- notice states requiring attention without searching several sections.

### Record facts

- quickly create income, expense, transfer, or adjustment operations;
- understand which accounts, categories, and funds an operation affects;
- safely correct an erroneous operation without partially saved effects;
- preserve exact monetary values and see dates in an understandable context.

### Assign money to intentions

- treat funds as purposes assigned to real money, not as extra accounts;
- allocate incoming money with a preview of the result;
- understand where fund money is physically held;
- see the free and reserved portions of each account.

### Look forward

- see expected income, expenses, transfers, and obligations;
- understand the minimum projected balance and possible shortfall date;
- reveal the events that changed a particular forecast point;
- distinguish facts, confirmed plans, and estimates.

### Test a decision before acting

- add a hypothetical purchase, income, date move, or amount change without
  changing facts or confirmed plans;
- compare baseline and alternative scenarios over the same horizon;
- see changes in minimum balance, free money, stress windows, and affected
  funds;
- test the owner's stop-loss and a separate system-suggested risk boundary;
- save a selected scenario or create only a plan draft through a separate,
  explicit action.

### Analyze the past

- compare expenses across periods;
- drill an aggregate down to its source operations;
- filter a large journal without losing the current context;
- find anomalies and recurring expenses without receiving an opaque “financial
  score”.

## What Hermes is not

### Not a banking application

A banking interface is usually organized around a bank product: cards,
transfers to external recipients, tariffs, credit offers, and payment status in
the banking network. Hermes is organized around the owner's personal model of
money, regardless of where the money is held.

Hermes:

- combines a management view across several accounts;
- connects actual operations with virtual funds and future events;
- helps decide what money should do next;
- does not imitate bank cards or promote financial products;
- does not promise bank synchronization or an externally current balance when
  data is entered manually.

### Not an accounting package

Accounting software organizes its interface around journal entries, charts of
accounts, period closing, statutory reports, and auditor roles. Accounting
correctness remains an internal foundation in Hermes, but the interface speaks
in the language of user intent.

Instead of debit and credit, the owner sees income, expense, transfer, and
adjustment. Instead of directly editing a balance, they see an explainable
operation. Instead of reports for their own sake, they receive an answer about
available money, the nearest risk, or the reason for a change.

### Not an expense table

The journal remains an important working view, but it does not define the whole
product. Hermes connects past operations, the current assignment of money, and
future obligations into one decision-making model.

## Product research findings

The research looks for transferable patterns, not a feature list to copy.

| Category | Observation | Application to Hermes |
| --- | --- | --- |
| Personal finance | YNAB connects saving to a clear goal and shows progress rather than only a balance. Actual separates expected operations from facts and permits exact, approximate, or range amounts. | Show the purpose of money and degree of confidence; translate a complex model into the language of intentions. |
| Banking dashboards | Monzo Trends combines accounts, shows money in and out, and subtracts upcoming payments from the available balance. Revolut keeps one time context across widgets and offers breakdowns by category, recipient, and account. | Start with availability and the nearest risk; apply one period to the entire screen; provide understandable breakdowns. |
| Productivity apps | Linear opens frequent creation with one command, preserves a draft, and uses contextual properties. Filters update the view immediately and can be saved as another view of the same data. | Fast keyboard input, safe drafts, contextual defaults, and persistent working context. |
| Analytics dashboards | Metabase applies shared filters to several cards and can drill from a chart point to source rows. | One filter set for a related screen; every meaningful aggregate drills down to operations. |
| Self-hosted applications | Actual frames local-first through data ownership, no trackers, progressive disclosure, and device adaptation. Its register combines search, filters, bulk selection, and adjustable density. | Trust comes from transparency and control; complexity appears when needed; desktop and touch workflows may differ. |

Research sources:

- [YNAB: Goal Tracking](https://www.ynab.com/features/goal-tracking) and
  [The YNAB Method](https://www.ynab.com/guide/foundations-the-ynab-method);
- [Actual Budget: Schedules](https://actualbudget.org/docs/schedules/),
  [Account Register](https://actualbudget.org/docs/tour/accounts/), and
  [Product Vision](https://actualbudget.org/docs/vision/);
- [Monzo: Summary and Trends](https://monzo.com/help/budgeting-overdrafts-savings/web-the-differences-between-Summary-and-Trends)
  and [Revolut: spending and income analytics](https://help.revolut.com/help/accounts/budget-and-analytics/how-can-i-see-my-spending-and-income-analytics/);
- [Linear: issue creation](https://linear.app/docs/creating-issues) and
  [filters](https://linear.app/docs/filters);
- [Metabase: dashboard filters](https://www.metabase.com/docs/latest/dashboards/filters)
  and [drill-through](https://www.metabase.com/docs/latest/questions/visualizations/drill-through).

## Limits on borrowing patterns

Do not copy the following from references without validation:

- a financial score without a verifiable model and useful action;
- decorative bank cards, advertisements, social feeds, or investment watchlists
  that do not match the Hermes domain;
- a set of KPI cards added only to fill a grid;
- complex charts with no route to the source data;
- an AI assistant, cloud dependencies, or automatic recommendations outside the
  confirmed scope;
- a customizable dashboard before real use reveals stable needs.

## Direction success criterion

The direction succeeds when an owner can, without training, answer four
owner-confirmed questions—“How much is free now?”, “How much will be free after
the selected number of days?”, “What will happen if I make this decision?”, and
“Where did most of the money go?”—and then complete the relevant action without
doubt about which data will change.
