# Evidence — HS-40-04 — Memory + telemetry UI

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-40/hs-40-01-settings-api-knobs`
- **Owner:** unassigned

## What shipped

A new **Memory** tab on `/dictation` with two Signal panels:

- **What the copilot has learned** — lists the (now persistent) corrections as
  elevated cards (kind chip · gist · → corrected value · relative time · a `×`
  remove button), with an **add** form, a **Forget all** clear, and an
  in-context `corrections_enabled` **toggle switch** that PUTs `/api/settings`.
  Empty state handled.
- **Pipeline depth · this session** — renders the readiness `depth` block:
  runs/budget/corrections stat tiles, per-stage **p50/p95** rows with a
  proportional bar (turns red at ≥66% of budget), the **budget-guidance**
  warnings, and the last **multi-pass** rewrite timings as chips. Labelled
  "this session" (in-memory, resets on restart). Empty state handled.

### Backend (curation needs a delete path)

The API was GET/POST only. Added:

- `DELETE /api/dictation/corrections/{id}` — remove one persistent correction.
- `DELETE /api/dictation/corrections` — clear all (ring + durable).
- `GET` now returns each item's durable `id` + `created_at` (via the new
  `CorrectionStore.list_for_display()`), so the UI can address rows for delete.

`CorrectionStore` gained `list_for_display()`, `remove(id)` (deletes from the
repo + reloads the ring), and `clear()` now also clears the repo. With no
repository these degrade gracefully (no ids → `remove` is a no-op 404).

## Files touched

- `holdspeak/plugins/dictation/corrections.py` — `list_for_display`, `remove`,
  `clear` (now durable), `_reload_ring`.
- `holdspeak/web/routes/dictation/pipeline.py` — GET uses `list_for_display`;
  new `DELETE /{id}` + `DELETE` (clear) routes.
- `web/src/pages/dictation.astro` — the Memory tab + the two panels' markup +
  Signal CSS (`.mem-item` / `.mem-add` / `.depth-stage` / `.depth-track` /
  `.depth-guidance` / `.depth-pass-chip`).
- `web/src/scripts/dictation-app.js` — `loadMemory` / `renderMemoryCorrections`
  / `renderMemoryDepth` / `addCorrection` / `deleteCorrection` /
  `clearAllCorrections` / `toggleCorrectionsEnabled` / `relativeTime`; the
  Memory tab wired into `activateSection`.
- `tests/unit/test_dictation_correction_store.py` — +6 (list_for_display
  with/without repo, remove from ring+repo, remove no-op without repo, clear
  durable).
- `tests/integration/test_web_dictation_corrections_api.py` — +5 (items carry
  id, delete by id + 404 on repeat, clear all, delete-without-repo 404, the
  Memory-tab page surface).
- `tests/unit/test_dictation_routes_split.py` — locked route table updated for
  the two new DELETE routes (28 → 30).
- `pm/.../evidence/memory_panel.png` — screenshot.

Bundle rebuilt (`cd web && npm run build`); only `web/src` committed — `git
status` shows **no** `holdspeak/static/_built/`.

## Verification artifacts

> `uv run` is broken on this machine; tests run via `.venv/bin/python -m pytest`.

- Build: `cd web && npm run build` → `8 page(s) built`, no errors.
- **Playwright drive**: seeded 3 persistent corrections + 3 telemetry runs →
  Memory tab shows `mem items: 3 · depth stages: 3 · pass chips: 2`; clicking a
  card's `×` removed it (`3 → 2`). Screenshot `evidence/memory_panel.png` (both
  panels, incl. the red `project-rewriter p95 452ms is 75% of the 600ms budget`
  guidance).
- Targeted: `.venv/bin/python -m pytest -q tests/unit/test_dictation_correction_store.py tests/integration/test_web_dictation_corrections_api.py tests/unit/test_dictation_routes_split.py`
  → all green.
- Ruff (touched py) → `All checks passed!`.
- Full suite: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`
  → `2221 passed, 16 skipped` (was 2211/16; +10).

## Acceptance criteria — re-checked

- [x] Memory panel lists persistent corrections + can add/remove/clear (a delete
      path exists on the API + UI); the enable/disable toggle is present —
      Playwright-proven + `test_delete_correction_by_id` / `test_clear_all_corrections`.
- [x] Telemetry panel renders per-stage p50/p95 + budget guidance + multi-pass
      timings from `/api/dictation/readiness` `depth` — Playwright shows 3 stage
      rows + 2 pass chips + the guidance card.
- [x] Both panels are rich Signal (elevated correction cards, toggle switch,
      stat tiles + proportional bars), not flat tables; empty states handled.
- [x] No secret content shown (corrections are gist-only + secret-rejected at
      record time, unchanged).
- [x] Bundle rebuilt; no `_built/` staged; screenshot captured.

## Deviations from plan

- The in-context toggle actually **writes** `corrections_enabled` (PUTs
  `/api/settings`) rather than being read-only — a richer affordance, consistent
  with the cockpit.
- `GET /api/dictation/corrections` now reflects the **persistent** set (with
  ids) when a repo is attached, falling back to the in-memory ring otherwise —
  needed so the UI can delete by id. Existing GET/POST tests still pass (the
  `key`/`kind`/`value` shape is unchanged).
