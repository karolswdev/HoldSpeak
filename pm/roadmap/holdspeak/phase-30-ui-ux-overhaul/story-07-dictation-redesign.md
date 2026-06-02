# HS-30-07 — Dictation redesign

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
- **Depends on:** HS-30-04, HS-30-05
- **Unblocks:** HS-30-09
- **Owner:** unassigned

## Problem

`web/src/pages/dictation.astro` (~875 lines) is the densest configuration
surface: tabbed sections (Readiness, Blocks, Project KB, Project Context, Agent
Hooks, Runtime, Dry-run), a block/YAML editor, runtime config (pipeline backend,
model paths, latency), and a dry-run preview with per-stage timing. The Workbench
tab/strip treatment makes a complex page feel heavier than it is. Redesign it to
the IA spec on Signal.

## Scope

### In

- Rebuild the `dictation.astro` layout to the HS-30-01 IA: a clean tabbed
  structure (or the IA's chosen pattern), readable forms, the block/YAML editor as
  a first-class surface, and the dry-run preview as a clear input → pipeline-trace
  result.
- Apply Signal: form controls / inputs / selects / sliders on dark, code/YAML in
  JetBrains Mono, the dry-run trace timing legible, accent reserved for the
  primary action and active tab.
- Preserve all Alpine.js behaviour (`web/src/scripts/dictation-app.js`): tab
  state, block authoring, config persistence, dry-run round-trip — restyle markup,
  keep bindings + API calls intact.

### Out

- Backend / dictation-pipeline changes (`docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`
  is canon; this story doesn't touch it) — UI only.
- Other routes (HS-30-06/08).

## Acceptance criteria

- [x] `dictation.astro` matches the IA-spec layout in Signal: the 7 tabs are split
      into **two tiers** (Setup: Readiness…Agent Hooks · Runtime & test: Runtime,
      Dry-run) via a divider; panels are Signal cards with eyebrow headers; block
      editor + forms read on dark. `evidence/after-hs07/dictation.png`.
- [x] Form controls inherit the Signal field tokens (`--field-bg`/`--field-border`
      → dark) + the global accent focus ring; the section/scope tabs use the
      accent-tint active state.
- [x] Behaviour intact **by construction**: dictation is driven by vanilla JS
      (`dictation-app.js`) via `data-section`/`id` hooks — none were touched (CSS
      migration + one non-interactive `.tab-tier-sep` span + group divider only).
- [x] Before/after: `evidence/before/before-dictation.png` → `after-hs07/dictation.png`.
- [x] `npm run build` green; backend sweep green (2062 passed, 14 skipped).

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Visual / manual: `npm run dev`; exercise each tab, save a block, run a dry-run;
  screenshot the editor + the dry-run trace.
- Build: `npm run build` exit 0.

## Notes / open questions

- The dry-run pipeline trace is the page's signature feature — make the per-stage
  timing genuinely readable in Signal (this was cramped in Workbench).
