# Phase 96 — The Design System: final summary

**Closed:** 2026-07-18, seven stories in one day, by owner directive
("use ui-styling and design-system as Phase 96"), at machine-verifiable
scope under the standing close directive: the owner's design-polish
sitting rides UAT Campaign 13 (extended with the `desk-os-design-polish`
scenario) together with the Desk OS verdict.

## What shipped

- **One source of truth (HS-96-01).** `web/design-tokens.json`, three
  layers per the vendored skill; the adapted generator emits `tokens.css`
  and the TS mirror `tokens.gen.ts` with a `--check` drift gate first in
  `npm run check`. All 117 pre-existing tokens preserved with identical
  computed values (proven mechanically); 61 added, codifying the
  primitives and the Desk OS chrome (the z ladder, window physics, the
  glow pool, zone tints).
- **The gate and the burn-down (HS-96-02).** The token validator (colors,
  z-index, ms literals in component CSS) runs in `npm run check` and
  fails on stale allow-list entries; 86 literals became named tokens
  (`--desk-glass`, `--desk-window-fill`, the `--shadow-ink` ramp, the
  washes, `--accent-cool`, the completed ladder); 69 reasoned exceptions
  remain (atmosphere art, local stacking). Window physics and GL palettes
  import the generated mirror — CSS/TS drift is structurally impossible.
- **The state contract (HS-96-03).** `docs/internal/DESIGN_SYSTEM.md`
  carries per-component state matrices in token vocabulary (guard-locked);
  one pressed grammar landed across `.btn` and eleven chrome families;
  the global focus ring was audited and adopted; the keyboard walk shows
  14/14 tab stops ringed.
- **One material (HS-96-04).** A single `:where()` rule carries the
  window family (fill, radius 18, elevation, glass); the pull-out keeps
  only its per-kind tinted edge; the menu rides the transient tokens;
  named normalizations recorded; the assembled storm holds 8.3ms median
  with the glass family-wide.
- **The keyboard truth (HS-96-05).** Windows manage focus without traps
  (in on open, back on close, Escape closes); the menu speaks the full
  Radix keyboard pattern hand-rolled; a focused GL-world object surfaces
  as a visible chip; axe gates ride the suite. The Radix decision is
  recorded: patterns yes, primitives no.
- **Docs and locks (HS-96-06).** The design system is canon in
  `DESIGN_SYSTEM.md`, wired into web/README's add-a-surface path and the
  architecture doc's locks list.
- **The closeout (HS-96-07).** The assembled eight-walk chain green on
  the restyled production bundle with zero failed API responses; the
  storm within the Phase 95 envelope (median 8.3ms, p95 10.0ms); all
  guards and suites green; Campaign 13 extended with the design-polish
  beats for the owner's sitting.

## Deferrals, named honestly

- **The owner's design-polish verdict** — the `desk-os-design-polish`
  scenario in Campaign 13 (with BACKLOG candidate Z's sitting).
- **Zone rename by keyboard** — rides the pull-out's rename verb; a
  dedicated keyboard path is triage material.
- **The 69 allow-listed literals** — the atmosphere art stays by design;
  the one-off shades shrink as future styling passes touch their files
  (the gate's stale-entry rule guarantees the list only shrinks).
- **Busy-state stragglers** — the pattern is documented; individual
  widgets converge as they are touched.

## Handoff

The Swift Desk can now consume `web/design-tokens.json` directly — the
palette, ladder, and physics constants are data, not CSS. The HSM
catch-up phase should generate its Swift constants the same way the web
generates `tokens.gen.ts`.
