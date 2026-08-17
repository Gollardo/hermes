# Design QA: operation modal forms

## Evidence

- Source visual truth: `/var/folders/nw/xdxz9z097v3fyc6g6mqsjgjm0000gn/T/TemporaryItems/NSIRD_screencaptureui_elHYDE/Снимок экрана — 2026-08-17 в 19.59.19.png`
- Source pixels: `1640 × 1750`; Safari capture supplied by the owner.
- Implementation screenshot: `/private/tmp/hermes-operation-modal-final.png`
- Implementation pixels and CSS viewport: `581 × 987`, device density `1x`.
- Route and state: `/operations`, new expense composer, description collapsed, submit disabled.
- Browser-rendered evidence: in-app browser; no console errors, only Angular/Vite development messages.

The captures use different browser engines and viewport sizes. The comparison therefore treats the
source as before-state evidence and checks control consistency, hierarchy, density, copy and
responsive behavior rather than claiming pixel-identical fidelity.

## Findings

- No actionable P0, P1 or P2 issue remains in the verified state.
- Fonts and typography: the existing Hermes font stack and hierarchy are preserved; labels remain
  readable and the optional section is visually secondary.
- Spacing and layout rhythm: the narrow viewport stacks fields consistently, keeps the modal within
  the viewport and keeps the action area visible. The source's permanently visible textarea no
  longer dominates the form.
- Colors and tokens: existing surface, border, accent and muted tokens are retained. Disabled
  actions now use explicit token colors instead of a browser-dependent filter.
- Image and icon fidelity: the form contains no raster imagery. Native select and date affordances
  remain platform-owned; the existing close glyph is unchanged.
- Copy and content: required financial fields and labels are unchanged. Only the optional disclosure
  text `Добавить описание` was added.
- Focused control comparison: type, category, amount, account, fund and date controls all render at
  `48px` in the verified browser state. The optional description expands without hiding the footer.

## Comparison history

1. Before: Safari showed visibly different select/input heights, a long single-column form, an
   always-visible large textarea and a heavy full-width disabled action.
2. Fixes: explicit control geometry and disabled colors, responsive form grid, progressive
   description disclosure, scrollable body and a separate action footer.
3. After: the verified narrow state has uniform controls, a shorter reading path and a visible
   action area. No P0/P1/P2 correction was required after the final capture.

## Follow-up polish

- P3: repeat the same screenshot and keyboard-focus check in real Safari. The in-app browser cannot
  verify Safari's native picker rendering directly.
- P3: replace the existing text close glyph only if Hermes adopts a shared icon source; do not add an
  isolated icon dependency for this modal.

final result: passed
