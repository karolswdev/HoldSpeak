# HS-43-01 — Wizard shell + motion + a11y (Welcome)

- **Project:** holdspeak
- **Phase:** 43
- **Status:** done (2026-06-06)
- **Depends on:** none (reuses the Phase-42 /api/setup/status + runtime_activity WS)
- **Unblocks:** HS-43-02, HS-43-03, HS-43-04
- **Owner:** unassigned

## Problem
The Phase-42 first-run was a flat status checklist of identical left-accent cards.
A world-class first run is a focused, full-screen, step-by-step **wizard**.

## Scope
- In: `/welcome` — a full-screen takeover (NOT the AppLayout dashboard): a
  step-progress rail (Welcome→…→You're set), directional slide/fade motion, the
  **Welcome** step (cinematic display type + animated soundwave), and the shell
  for the remaining steps. Funnel/progressive disclosure; Step N-of-M; Back/Skip
  (user freedom); **focus moves to the step heading** on transition;
  `prefers-reduced-motion` respected; SVG glyphs (no emoji). A live **Permissions**
  step (status tiles polling `/api/setup/status`) + a celebratory **Done** step.
  Server `/welcome` route.
- Out: the Model picker (HS-43-02), the live first-dictation reward (HS-43-03),
  the presence toggle (HS-43-04) — stubbed here.

## Acceptance criteria
- [x] `/welcome` is a full-screen wizard (not a dashboard) with a progress rail +
      one step at a time; the route serves the built page (build-agnostic).
- [x] Distinct per-step visual treatment (escape the one left-accent card);
      directional motion; reduced-motion safe.
- [x] Step N-of-M, Back + Skip, focus-to-heading on transition; SVG glyphs.
- [x] The Welcome + live Permissions + Done steps render; suite green.

## Test plan
- Integration: `tests/integration/test_web_welcome_wizard.py` (route + funnel/a11y).
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
