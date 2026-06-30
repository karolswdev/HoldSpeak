# Evidence — HS-69-03: Gradient + hairline tokens

**Date:** 2026-06-30
**Verdict:** done. The gradient tokens are present and consumed; proven by the
substrate computed-style probes + every screenshot's glyph chips.

## What shipped (substrate wave, confirmed)

- `web/src/styles/tokens.css`:
  - `--accent-gradient: linear-gradient(135deg, #FF9D5C 0%, #FF6B35 50%, #F24A2E 100%)`
  - `--bg-gradient: linear-gradient(180deg, #191B23 0%, #0E0F13 100%)`
- Consumed by `.glyph-chip` (`background: var(--accent-gradient)`) and the
  directional `.signal-card::before` top-lit gradient hairline.

## Proof

- **`screenshots/probes.json`** (HS-69-02): every probed `.signal-card` reports
  `::before background-image: linear-gradient(rgba(255, 255, 255, 0.12…` — the
  directional top-lit hairline, not a flat inset.
- The amber **glyph chips** (the gradient fill) are visible in every screenshot
  this phase — the dashboard home cards, the sheet header, the Qlippy cards, the
  workbench node chips, the inspector, the companion desk.
