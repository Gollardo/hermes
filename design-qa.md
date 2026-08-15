# Forecast redesign visual QA

## Evidence

- Source reference: `/Users/zuko/Desktop/Снимок экрана — 2026-08-15 в 15.44.04.png`
- Source dimensions: 3060 × 1858 px. It is a conceptual desktop mock, not a
  production viewport or a source of business values.
- Implementation route: `http://127.0.0.1:4300/forecast`
- Desktop capture: `design-qa/implementation-desktop-viewport.png`
- Desktop viewport: 1440 × 1000 CSS px, default browser zoom, desktop shell
  sidebar hidden to match the reference's content-first state.
- Mobile capture: `design-qa/implementation-mobile.png`
- Mobile viewport and capture: 390 × 844 CSS px. Layout overflow was checked
  separately against the complete 3025 px document height.
- Full comparison: `design-qa/reference-comparison.png`
- Focused chart comparison: `design-qa/chart-comparison.png`
- Verified state: all accounts, month, free-money mode, with a forecast cash gap
  and realistic planned events supplied by the local QA fixture.

The source and implementation were normalized into equal comparison panels.
The focused comparison uses the shared chart/KPI/risk region rather than
stretching the source screenshot to the implementation's different aspect
ratio. No density-based CSS scaling was required.

## Comparison history

### Pass 1

The first browser capture matched the intended hierarchy but exposed two P2
visual issues: the Y scale chose an unnecessarily coarse negative lower bound,
and the cash-gap date wrapped inside the narrow risk card. KPI and risk cards
also did not consistently fill their grid tracks.

Fixes applied:

- increased the target tick density while keeping rounded monetary ticks;
- kept risk dates on one line and tuned the supporting type size;
- stretched KPI and risk cards consistently within their tracks;
- constrained the mobile chart to a readable, horizontally scrollable width;
- added left/right tooltip positioning for points near chart edges.

### Pass 2

The final desktop and focused comparisons show the same information hierarchy
as the reference: one control row, decision KPI column, dominant forecast chart,
secondary risks/summary column, and a synchronized event lane. The final mobile
capture has no body-level horizontal overflow and preserves a readable chart
through its own scroll container.

### Pass 3 — code-review corrections

Semantic review found issues that the first visual comparison did not expose:
the plotted scale omitted a distinct actual starting balance, a cash gap inside
a recovered monthly interval had no chart marker, and every forecast point was
a separate `Tab` stop. The final capture and comparisons were regenerated after
adding the labelled «Сейчас» marker, exact monthly cash-gap marker and roving
keyboard navigation. Single-account transfer effects were also added to the
period reconciliation without changing the all-accounts layout.

## Final findings

- P0: none.
- P1: none.
- P2: none after the second pass.
- The difference in exact values, dates and event names is intentional: every
  surface uses the application's forecast dataset instead of copied mock values.
- The reference's recommendations and independent chart-granularity controls
  were intentionally omitted because they are not supported domain concepts.
- The primary KPI correctly becomes `0 ₽` when the selected forecast contains a
  negative day; it is not copied from the concept's contradictory sample values.
- Project color, type, radius, border and spacing tokens are reused. No parallel
  design-system layer or new chart dependency was introduced.
- Existing code-native icons and the SVG forecast renderer are reused; the
  reference does not require an additional raster asset.
- Free/all-money switching, risk selection, event selection, selected-day
  details and responsive horizontal chart/timeline scrolling were exercised.
- The actual starting balance participates in the Y scale and is visually
  separated from forecast closings. `Tab` enters the forecast-point series
  once; arrow-key navigation updates the selected point. The exact monthly
  risk-marker remains a separate action when present.
- A recovered cash gap in a monthly aggregate remains visible as a labelled
  exact-date marker and opens only that day's operations.
- Browser console errors in the verified states: none.
- Accessibility inspection covered visible focus styles, keyboard-focusable
  chart points, textual risk labels and signed monetary values.

## Result

passed
