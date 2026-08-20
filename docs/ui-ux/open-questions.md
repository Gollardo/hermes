# Open UI/UX questions

## How to use this document

A question is resolved only after an explicit owner answer. Record decisions
with a date and, when they affect domain semantics or architecture, carry them
into the corresponding authoritative document.

P0 questions block approval of the primary UX or visual direction. P1 questions
are needed before detailed design of the relevant screen. P2 questions may be
tested after early prototypes and real use.

On 2026-08-18 the owner approved the current implemented `0.4.0` interface as
the first-public-release baseline. Remaining questions therefore concern future
improvements and do not block release unless a later decision marks them as a
new blocker.

## Owner-confirmed P0 direction — 2026-08-02

### Product focus

- After login, total money, free money, debts, and their trends are the
  priorities. Free money is the primary total.
- Dashboard is mainly an overview but supports fast operation creation.
- Primary questions are “How much money is free now?”, “How much will be free
  after the selected number of days?”, and “Where did most of the money go?”.
- Dashboard includes limited shared statistics: category expenses, income, and
  account-balance trends in suitable charts.
- The primary action on a list or section creates its key entity; on a specific
  entity page it edits that entity.
- The product does not prescribe usage frequency. It supports both short,
  frequent sessions and less frequent overview sessions.
- The first user is the project owner, but the interface remains understandable
  to a broader audience for possible public distribution.

Debts and their trends are a future interface direction and must not appear as
a working block before the relevant roadmap scope exists.

### Visual direction

- A modern minimalist interface with a premium feel.
- The light Quixotic image is the primary visual reference.
- The approved first-prototype direction is a light neutral base with a muted
  green accent.
- Soft surfaces, rounded shapes, whitespace, and restrained gradients are
  acceptable when they do not harm density or readability.
- A strongly branded style is not yet needed; the workspace remains neutral.
- Dark mode is deferred and not a current priority.
- No accessibility requirements beyond the baseline were specified; baseline
  contrast, keyboard navigation, visible focus, and reduced motion remain
  mandatory quality standards.

### Operation creation

- Operations are usually entered as a series for a day. Manual entry and future
  import should be equally understandable routes into the journal.
- Income and expense are the most frequent types.
- Income and expense choose meaning or category first, then amount.
- Category is required. Whether description is required remains open.
- Ordinary MVP operations need no separate payee; counterparty matters more for
  outgoing debts.
- Use a fact date without exact time.
- The current modal is approved for the first public release; a side panel may
  be explored later as an alternative pattern.
- A persistent draft is acceptable in principle, but retention period and safe
  storage method remain open.
- “Save and add another” applies where it supports batch entry.
- Ordinary creation requires no separate confirmation when the effect is
  visible in advance. Dangerous changes require confirmation.

These decisions guide UX but do not replace domain decisions about posting,
concurrency, and rounding. The owner separately confirmed the no-negative-
balance policy on 2026-08-18.

## Remaining P0 questions

1. Is description required for an ordinary operation, or always optional?
2. Should a draft survive only accidental form close, page reload, or also
   logout and login from another device?
3. How long should a draft persist, and which financial fields may be stored
   locally?

### Confirmed numeric presentation

Amounts and percentages render as `100 000,00` and `12,50%`. Numeric inputs
accept comma and dot while server precision remains exact. Individual values use
`ROUND_HALF_UP`. When exact server shares form a 100% breakdown, only displayed
hundredths are smoothed by a stable largest-remainder method and also total
`100,00%`.

## P1 — dashboard

1. What period should historical blocks use by default?
2. Which upcoming-obligation horizon is useful: 7, 14, or 30 days?
3. Which deserves more space: recent operations, forecast, or expense analysis?
4. Which two or three charts best answer the approved dashboard questions, and
   what default period should each use?
5. How many accounts are typically active, and is a full dashboard breakdown
   needed?
6. Should expected operations be confirmable directly on dashboard?
7. Is a privacy mode needed to hide amounts quickly while showing the screen?
8. When does a configurable dashboard become justified: after MVP, after weeks
   of use, or never?

## P1 — tables, search, and data

1. How important are tables compared with cards and charts?
2. What typical and maximum operation volume should prototypes and performance
   checks use?
3. Which fields does the owner remember when searching for an operation?
4. Which filters are needed almost every time, and which may be disclosed on
   request?
5. Are saved filters needed, and which repeated selections are expected?
6. Are bulk actions needed before import or only after real data accumulates?
7. Is pagination, “load more”, or another controlled approach preferable for a
   long journal?
8. Is running balance needed in an account-specific journal?
9. Are tags needed beyond two-level categories, and for which jobs?

## P1 — funds

Owner-confirmed on 2026-08-14: a fund has an editable target amount, exact
percentage, and progress bar; creation may immediately reserve money only for a
new fund, while a separate action moves assignment between funds on one
account. Target date is not approved. Owner-confirmed on 2026-08-18: manual-mode
rounding remainder remains free; a fund cannot become negative; archiving is allowed only
at zero balance and releases nothing automatically.

1. Does reasoning start from the fund (“How much for vacation?”) or account
   (“What is reserved on the card?”)?
2. Which matters most in the first fund row: amount, allocation percentage, or
   physical breakdown?
3. Does the implemented amount target also need a target date?
4. Which incoming amounts receive percentage allocation?
5. Is allocation always explicit, or sometimes part of income creation?
6. Is a “funds × accounts” matrix needed, and at what entity count?
7. Should expense default to free money or suggest the last fund?

## P1 — plan and forecast

1. Should calendar, upcoming events, and forecast live in one Plan section?
2. What scope and horizon open by default?
3. Is intraday detail needed, or is end-of-day balance sufficient?
4. How does an overdue expected event affect forecast?
5. Are approximate amounts and ranges needed for utilities and other uncertain
   payments?
6. Which first confirmed what-if scenario types enter `2.0.0`?
7. Which is more useful beside the chart: event list or calendar?
8. Which warnings genuinely require action, and how far in advance?
9. Is an external notification needed, or is an in-app signal sufficient?
10. How should multiple currencies appear before an approved conversion model?

## P1 — analytics

1. How important are charts compared with total tables?
2. Which reports come first: category expenses, cash flow, balance trends, or
   fund movements?
3. Are previous-period comparisons needed, and what counts as comparable?
4. Should transfers and adjustments be excluded from specific reports, and how
   is that rule explained?
5. Are custom reports needed before stable questions are proven?
6. Which categories combine into “Other”, and how is the full list revealed?
7. Should selecting any segment always open a filtered journal?

## P1 — navigation and responsive behavior

1. Are target devices desktop-first with occasional mobile access, or equal
   mobile workflows?
2. Which four sections belong in mobile bottom navigation?
3. Should global search cover every entity or only the journal?
4. Does an experienced owner need a command palette?
5. Do categories belong in Settings or separate secondary navigation?
6. Does a side panel or separate page preserve operation-detail context better?
7. Which minimum viewport sizes and touch targets are officially supported?

## P2 — personalization and tone

1. Are custom icons and colors needed for accounts, categories, and funds?
2. Are emoji acceptable, or is one built-in icon set required?
3. Should message tone be strictly neutral, supportive, or lightly
   conversational?
4. Are illustrations needed in onboarding and empty states?
5. Should overview values hide cents or insignificant decimal digits while
   details retain precision?
6. Is a user-controlled table density setting needed?
7. Are widgets and dashboard reordering needed after real use?

## Proposed checks before design approval

1. Resolve the remaining P0 questions and establish terminology.
2. Low-fidelity wireframes for dashboard, journal, and operation creation
   without choosing a palette.
3. Cognitive walkthrough: understand state → create expense → verify effect →
   find it in the journal.
4. Fund prototype with a numerical example across two accounts and three funds.
5. Forecast prototype with a transfer, overdue event, and shortfall.
6. Visual spike of the approved light neutral-green direction on one overview
   and one dense-data screen.
7. Test keyboard-only use, zoom, long localized names, large amounts, and
   color-independent meaning.

## Decision log

Add entries after approval without rewriting the history of a question.

| Date | Question | Owner decision | Affected documents |
| --- | --- | --- | --- |
| 2026-08-02 | Product focus | Free money is primary; dashboard is an overview with fast operation creation, forecast, debts, and compact trends and analytics. | `vision.md`, `information-architecture.md`, `screens/dashboard.md` |
| 2026-08-02 | Visual direction | Modern neutral premium minimalism; Quixotic as the primary reference; light base and muted green accent; dark mode deferred. | `visual-direction.md` |
| 2026-08-02 | Operation creation | Income and expense are entered in series; category precedes amount; fact date has no time; modal is preferred; ordinary creation needs no separate confirmation. | `screens/operation-entry.md` |
| 2026-08-18 | Current `0.4.0` interface | Implemented navigation, modal composers, screen compositions, and responsive behavior are the first-public-release baseline; future design system and new screens require separate approval. | `../../DESIGN.md`, `vision.md`, `information-architecture.md`, `visual-direction.md`, `screens/` |
| 2026-08-18 | Audit trail | A separate immutable edit and deletion history is unnecessary for the current single-owner product. | `../domains/operations.md`, `../decisions/0001-financial-posting-model.md` |
| 2026-08-18 | Fund rules | Posting, coverage, rounding, remainder, and archive policy in ADR 0002 are confirmed for the current release. | `../decisions/0002-virtual-fund-ledger.md`, `../domains/funds.md` |
| 2026-08-18 | Recurrence constraints | Frequencies, intervals, valid dates, one-year materialization window, and protection of manually changed occurrences are confirmed. | `../decisions/0003-recurring-rules-and-occurrences.md`, `../domains/scheduling.md` |
| 2026-08-18 | UI amounts and percentages | Canonical display uses space grouping, comma, and exactly two fraction digits; input accepts comma and dot; `ROUND_HALF_UP`; exact 100% breakdowns use display-only largest remainder; server precision is unchanged. | `../../AGENTS.md`, `../../DESIGN.md`, `design-principles.md`, `visual-direction.md` |
| 2026-08-18 | North star and scenarios | Hermes primarily answers “What happens if I make this decision?”; Oracle is the capability name, What if? is the action and parallel-scenario mode. Scenarios are ephemeral by default and saved separately. | `vision.md`, `information-architecture.md`, `screens/forecast.md`, `screens/scenarios.md` |
| 2026-08-18 | AI boundary | Local AI is an optional interface to the deterministic core; the complete workflow works without AI, chat creates only a reviewable draft, and never writes a financial fact or plan directly. Conversations are not stored by default. | `../../DESIGN.md`, `../domains/scenarios.md`, `screens/scenarios.md` |
| 2026-08-18 | Risk boundary | The owner may set a stop-loss; Hermes may separately suggest an explainable boundary without automatically replacing the owner value or blocking an operation. | `../domains/scenarios.md`, `screens/scenarios.md` |
