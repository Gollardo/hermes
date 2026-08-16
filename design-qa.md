# Funds visual refinement — design QA

## Evidence

- Source visual truth: `/private/tmp/hermes-funds-current-desktop.png`
- Implementation desktop: `/private/tmp/hermes-funds-final-desktop.png`
- Implementation mobile/menu: `/private/tmp/hermes-funds-final-mobile.png`
- Desktop viewport and pixels: `1600 × 1000`, device scale factor `1`, no density normalization required.
- Mobile viewport and pixels: `390 × 844`, device scale factor `1`, no density normalization required.
- State: authenticated `/funds`, populated summary, six active funds, closed desktop menus; mobile capture includes the first fund's `Ещё` menu.

## Full-view comparison

The source and final desktop captures were opened together at the same viewport. The final implementation preserves the page shell, content, values and primary actions while establishing a clearer reading order: two primary monetary totals, compact secondary percentages, one row of allocation actions and a single aligned fund list instead of nested cards.

## Focused-region comparison

The fund list and mobile action menu were inspected separately because exact amounts, progress labels and the disabled archive explanation are too small to judge reliably in the full-page comparison. Comparable values retain tabular alignment and significant decimal places. The mobile menu remains within the viewport and exposes the archive condition as visible text.

## Required fidelity surfaces

- Fonts and typography: existing application family and weights preserved; names and balances are primary, allocation percentages are secondary and no longer uppercase badges.
- Spacing and layout rhythm: nested fund cards and letter tiles removed; rows share aligned target, balance and action columns with separators. Mobile rows stack in the same semantic order.
- Colors and tokens: only existing surface, line, ink, muted and accent tokens are used.
- Image quality and assets: the screen contains no product imagery or new assets; existing shell icons and logo are unchanged.
- Copy and content: financial values and domain labels are unchanged. Empty optional fund descriptions are omitted, count is labeled, and disabled archive state has visible explanatory copy.

## Findings and comparison history

### Iteration 1

- P2: desktop allocation actions wrapped into an uneven second row. Fixed by keeping the three action groups on one line above the existing responsive breakpoint.
- P2: the mobile fund menu extended beyond the left viewport edge. Fixed by anchoring its dropdown to the left of the trigger on narrow screens.

### Final comparison

No actionable P0, P1 or P2 findings remain. The compact list, summary hierarchy and progressive disclosure match the approved refinement intent without changing the existing financial workflow.

## Primary interactions checked

- `Создать фонд` opens the existing fund dialog.
- `Выделить со счёта` opens the existing allocation dialog.
- `Другие операции` exposes both existing transfer actions.
- `Ещё` exposes archive/restore, and a non-empty fund explains why archive is disabled.
- Browser console: no errors during the checked interactions.

## Follow-up polish

- P3: the existing expanded narrow-screen navigation consumes substantial vertical space before page content. It is a shared shell decision and was intentionally left outside this funds-only change.

final result: passed
