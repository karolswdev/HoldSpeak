# Evidence — Cadence Phase 2 (the web coach surface)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase2-web`.

## What shipped

| Story | Files | Proof |
|-------|-------|-------|
| CAD-2-01 | `cadence/next_action.py` | `tests/unit/test_cadence_next_action.py` (6) |
| CAD-2-02/03 | `web/routes/cadence.py` + `web_server.py` + `web/routes/__init__.py` | `tests/integration/test_cadence_routes.py` (5) |
| CAD-2-04 | `web/src/pages/cadence.astro` + `web/src/scripts/cadence-app.js` + `web/routes/pages.py` (`/cadence`) | `TestCadenceUiSmoke` (2) |
| CAD-2-05 | the tests above | all green |

## The surface

- **`/api/cadence/*`** — `GET status`, `GET loops?all=`, `GET loops/{id}`, `POST run-now`, and the
  lifecycle `POST loops/{id}/{snooze,kill,close}`. Every loop response carries its `evidence` (with
  deep links), a deterministic `next_action`, and an honest `egress: {scope:"local"}` badge. A
  **killed** loop survives re-projection through the route (`test_kill_survives_reprojection_via_route`).
- **`next_action.py`** (deterministic, no LLM) — proposal→`approve_proposal`, owned action→
  `create_issue` draft (body cites owner/due/source), unowned→`assign_owner`, `needs_review`→
  `review_draft`, agent_question→`reply_to_agent`. The "next decision is cheap" promise, the LLM
  draft deferred to Phase 7.
- **`/cadence` page** — *Now* (top pushable loops) + *Open loops*, each card showing the score, the
  source/owner/review chips, the **prepared next move** in an accent callout, evidence deep-links,
  the egress chip, and one-tap **Snooze / Mark done / Kill loop**. A *Run now* button re-projects.
  All loop text is rendered with **`textContent`** (titles come from transcripts — source is data,
  never markup; the prompt-injection rule). Card CSS is `<style is:global>` (the Astro-scoped-CSS
  gotcha — scoped CSS never reaches JS-injected DOM).

## Trust boundary held

No autonomous external side effect: lifecycle actions are local `cadence_*` writes; a `next_action`
that maps to a connector is a **draft** (executing it remains the actuator approve→execute path,
Phase 6/7). The Phase-1 `test_cadence_package_has_no_external_side_effects` guard still passes
(`next_action.py` added no forbidden call).

## Proof

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py
  tests/integration/test_web_server.py` → **137 passed.**
- `cd web && npm run build` → **15 pages** built (the `/cadence` page compiles; `cadence-app.js`
  bundles with its `egress-badge.js` import).
