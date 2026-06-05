# HS-40-04 — Memory + telemetry UI

- **Project:** holdspeak
- **Phase:** 40
- **Status:** done (2026-06-05)
- **Depends on:** HS-40-01, HS-40-02
- **Unblocks:** none
- **Owner:** unassigned
- **Evidence:** [evidence-story-04.md](./evidence-story-04.md)

## Problem

Correction memory and depth telemetry are API-only (`/api/dictation/corrections`,
the readiness `depth` block). A user can't see what the copilot has learned or
how fast it's running. With persistence landing in HS-40-02, the memory is now
worth showing — and curating.

## Scope

- In:
  - A Signal **"What the copilot has learned"** panel: list the persistent
    corrections (kind / gist / value / when), with **curate** affordances —
    add, remove, and clear — plus the `corrections_enabled` toggle in context.
    Wired to `GET`/`POST /api/dictation/corrections` (+ a delete; add the route
    if missing).
  - A Signal **depth-telemetry** panel: render the readiness `depth` block —
    per-stage p50/p95 (a simple Signal bar/sparkline is fine, no chart lib
    required), the budget-guidance hints, the multi-pass timings, and the
    correction-store size.
  - Both surfaced in the dictation cockpit; rebuild the bundle (commit `web/src`
    only — `_built/` is gitignored).
- Out:
  - A heavyweight charting dependency — keep it Signal CSS unless something
    trivial is already vendored.
  - Persisting telemetry (out of phase).

## Acceptance criteria

- [x] The memory panel lists persistent corrections and can add/remove/clear
      them (a delete path exists on the API + UI); the enable/disable toggle is
      present.
- [x] The telemetry panel renders per-stage p50/p95 + budget guidance +
      multi-pass timings from `/api/dictation/readiness` `depth`.
- [x] Both panels are rich Signal (not flat tables); empty states are handled.
- [x] No secret content is shown (corrections are gist-only already).
- [x] Bundle rebuilt; no `_built/` staged; screenshots captured.

## Outcome

A new **Memory** tab with a curation panel (deletable correction cards + add
form + Forget-all + an in-context `corrections_enabled` toggle) and a depth
telemetry panel (per-stage p50/p95 bars, budget guidance, multi-pass chips,
stat tiles). Added the missing `DELETE /api/dictation/corrections/{id}` +
`DELETE /api/dictation/corrections` routes and `CorrectionStore.list_for_display`
/`remove`/durable-`clear`; GET now carries the durable `id`+`created_at`.
Playwright-verified (list/delete/telemetry render); screenshot in `evidence/`.
Suite 2221/16. See [evidence-story-04.md](./evidence-story-04.md).

## Test plan

- API: if a delete/clear route is added, integration-test it
  (`tests/integration/test_web_dictation_corrections_api.py`).
- Build: `cd web && npm run build`.
- Manual / screenshot: record a correction, see it in the panel, delete it; view
  telemetry after a few dry-runs.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- A delete/clear corrections route likely needs adding (the current API is
  GET/POST only) — keep it consistent with the existing route shapes + the
  persistence repo (HS-40-02).
- Telemetry is in-memory and resets on restart — label it "this session" so the
  empty-after-restart state isn't confusing.
- Use the `ui-ux-pro-max` skill + Signal tokens; reuse the Phase-36 card idioms.
