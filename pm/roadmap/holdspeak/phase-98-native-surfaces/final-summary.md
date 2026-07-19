# Phase 98 — Native Surfaces: final summary

**CLOSED 9/9, 2026-07-18 — scaffolded and shipped the same day**, at
machine-verifiable scope under the standing close directive; the
owner's live verdict rides the next UAT sitting (Campaign 13's
desk-os-design-polish scenario now walks the native interiors and the
window-driven reflow).

## What this phase was

The owner's standing verdict: "none of the Desk OS feels like an OS —
windows feel like glued-in HTML panes, zero consistent look and
feel." Phase 97 fixed how windows BEHAVE; this phase re-crafted what
lives INSIDE them. The seam was mechanical: every demoted core was a
Signal-era web page (viewport-media grids, nested Panel chrome, raw
data dumps, permanent button walls, modal confirms) hosted in a desk
window.

## What shipped

- **The surface idiom** (DESIGN_SYSTEM.md, Article VIII floors): one
  material with no double chrome; the WINDOW is the viewport
  (`.desk-surface-body` is a size container; kit layouts reflow via
  `@container` at the 560px breakpoint); a denser scale
  (`--desk-surface-*` tokens); honest rows (humanTime/deSnake/
  presentValue — unknowns omitted); verbs have homes (one sticky verb
  bar; revealed row verbs; destructive verbs are inline two-step
  `ConfirmVerb`s, never modals); one state grammar (`SurfaceState`).
- **The kit** `web/src/desk/surface/`: SurfaceVerbs, SurfaceSection,
  SurfaceRows/Row, SurfaceState, SurfaceColumns, SurfaceSplit,
  SurfaceFacts, SurfaceCode, MetricStrip, ConfirmVerb, surface-float,
  the formatters. Interior furniture (tab strip, disclosures, the
  transcript list) quieted onto the window material.
- **All fourteen cores converted** (Cadence as the HS-98-01 reference,
  then Dictation, Meetings, Live, Activity, Settings, Setup,
  Workbench, Studio, Components, Commands, Profiles, Companion,
  RuntimeDocs). Meetings' detail and import, Commands' and Profiles'
  editors, and every confirm left their modals. Wire contracts stayed
  byte-identical throughout.
- **The seam retired:** the guard
  (`tests/unit/test_native_surfaces_guard.py`) forbids the page
  grammar in cores; its conversion ledger shrank to EMPTY and is
  locked closed. 69 dead react-app.css rules deleted (−377 lines);
  four stale token-gate entries left with them (67 → 63); every
  surviving class's consumer named in HS-98-07's census.
- **Frame fixes the shots forced:** the phone sheet no longer
  overflows 393 (desktop min-width floor vs `is-sheet`), plus a
  hover/status honesty pass ("[object Object]", mid-recording "Ready
  to record", raw ISO timestamps).
- **Proof:** the assembled chain — smoke, windows, shell, cores,
  dictation (real voice through Whisper), meetings (real recording),
  config (round-trip persists), lastexits (15 routes + a real
  workflow save), reflow, the six-leg grammar chain, and the new
  `surfaces` leg (all 14 windows opened at 1440 AND 393, zero page
  grammar in the live DOM, zero failed API responses, 28 shots looked
  at). Storm assembled: 8.3ms median / 9.2 p95 / 9.4 max on hardware
  GL — the Phase 95 envelope holds (layout events read 48 with the
  Meetings window open under the drag path vs 1 bare; every frame
  stayed under 10ms — recorded honestly in evidence). Full python
  sweep + `npm run check` (289 web tests, axe in suite) captured.

## Riders and handoff

- **FirstWords.tsx / AmbientLayer.tsx** still speak
  `signal-eyebrow`/`button-row` outside the guard's scope (named in
  HS-98-07's census) — fold them into the idiom when those surfaces
  are next touched.
- **The Living World** (staged next): object↔window morph, grounding,
  one object family — the windows now deserve the world around them.
- **HSM One Grammar on Glass**: the iPad consumes the tokens, the
  window grammar, and now the surface idiom (DioWindow + sheet kill;
  the HSM 28 program).
- The storm's assembled layout-event delta (48 vs 1) is understood as
  hover-reactive furniture under the drag path and cost no frame
  time; if a future storm shows frame-time regression, start there.

## The owner's walk

Campaign 13 (`uat/campaigns/owner-13-desk-os.yaml`) — the
desk-os-design-polish scenario now includes: look INSIDE Dictation/
Meetings/Settings (one idiom, honest rows, inline two-steps), and
resize the Meetings window to watch the content answer the WINDOW.
