# HS-4-03 — Project KB authoring API + UI (`WFS-CFG-003`)

- **Project:** holdspeak
- **Phase:** 4
- **Status:** done
- **Depends on:** HS-4-02 (block authoring API patterns established; reuse atomic-write helper)
- **Unblocks:** kb-enricher templates with `{project.kb.*}` placeholders becoming usable in dogfood without writing YAML
- **Owner:** unassigned

## Problem

`detect_project_for_cwd()` (HS-3-01) auto-detects `name`, `root`,
`anchor`, but the optional `kb` mapping only loads when the user
hand-authors `<root>/.holdspeak/project.yaml`. The kb-enricher's
`{project.kb.stack}` / `{project.kb.recent_adrs_short}` /
`{project.kb.task_focus}` template placeholders (DIR-01 §8.4) are
a real value-add — but only if writing the KB file is easy.

This story ships a web API + UI for editing
`<root>/.holdspeak/project.yaml`'s `kb.*` keys.

## Scope

- **In:**
  - `GET /api/dictation/project-kb` → returns `{detected: ProjectContext | null, kb: dict | null, kb_path: str | null}`. When no project is detected, returns 200 with all fields null and a `message: "no project root detected from cwd=<X>"`.
  - `PUT /api/dictation/project-kb` → body is `{kb: {<key>: <value>, ...}}`; writes (or creates) `<root>/.holdspeak/project.yaml` containing `{kb: <body.kb>}`. Atomic write per `WFS-CFG-006`. Returns the new context.
  - `DELETE /api/dictation/project-kb` → removes `<root>/.holdspeak/project.yaml` if it exists; preserves the `<root>/.holdspeak/` directory itself (because it's also the anchor signal).
  - Validation: kb keys are strings matching `[A-Za-z_][A-Za-z0-9_]*` (so dotted-path placeholders like `{project.kb.stack}` resolve cleanly via `kb_enricher._lookup`); kb values are strings or null. Reject anything else with field-level 4xx.
  - Web UI panel: shows auto-detected `name/root/anchor` (read-only); below, a free-form key/value editor for kb fields. Add/remove/rename rows. Save button persists via PUT; "Reset" button reverts to last-loaded.
  - Integration tests: CRUD happy-path + error cases (no project detected on PUT, bad key format, atomic write rollback on schema failure).
- **Out:**
  - Locking down the kb schema (e.g., requiring specific keys like `stack`, `recent_adrs_short`). The schema is open per phase decisions.
  - Markdown rendering for kb values — strings only.
  - Multi-project KB editor — scoped to the cwd-detected project per phase risk.

## Acceptance criteria

- [x] All 3 endpoints implemented and integration-tested.
- [x] Atomic write semantics: `test_put_bad_key_422_and_atomic_rollback` asserts on-disk byte equality vs. snapshot after a rejected PUT.
- [x] Key validation regex enforced server-side; surfaces a 422 with the offending key in the error body.
- [x] UI panel shipped (`/dictation` "Project KB" section): shows detected context, allows add/remove of kb rows, save/reset/delete actions.
- [x] Round-trip verified by `test_round_trip_put_then_get`. Pipeline-cache invalidation reuses the `on_dictation_config_changed` callback shipped in HS-4-02; same caveat applies (unwired in `web_runtime.py` today, contract-shaped for HS-4-04 to wire from a controller).
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS (1052 passed, +16 vs. HS-4-02 baseline 1036).

## Test plan

- **Integration:** `tests/integration/test_web_project_kb_api.py` covering each endpoint.
- **Regression:** documented full-suite command (metal excluded).

## Notes / open questions

- `<root>/.holdspeak/` is also the strongest project-anchor signal in `detect_project_for_cwd()`. Creating it via PUT therefore *also* upgrades cwd detection from `git`/manifest anchor to `holdspeak` anchor — document this side effect in evidence.
- Reuse the atomic-write helper from HS-4-02 if extracted; otherwise inline the same temp-and-rename pattern.
