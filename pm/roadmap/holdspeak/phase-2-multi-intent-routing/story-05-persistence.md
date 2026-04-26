# HS-2-05 — Step 4: Persistence + migration

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-02 (typed contracts), HS-2-04 (dispatcher emits PluginRun)
- **Unblocks:** HS-2-06 (meeting runtime persists what dispatch produces), HS-2-07 (synthesis stores ArtifactLineage), HS-2-08 (web/CLI surfaces query persisted state)
- **Owner:** unassigned

## Problem

Spec §9.5 calls for: schema-version bump, tables for windows / scores
/ plugin runs / lineage, CRUD methods for the timeline + plugin-run
persistence, migration tests. Audit (post-HS-2-04): `holdspeak/db.py`
is at `SCHEMA_VERSION = 10` and already has every table named in the
spec — `intent_windows`, `intent_window_scores`, `plugin_runs`,
`plugin_run_jobs`, `artifacts`, `artifact_sources` — all created via
idempotent `CREATE TABLE IF NOT EXISTS` with explicit version
migrations. CRUD is in place (`record_intent_window`,
`list_intent_windows`, `record_plugin_run`, `list_plugin_runs`,
`record_artifact`, `list_artifacts`, plus the queue lifecycle
methods). `tests/unit/test_db.py::TestMirPersistence` already
round-trips all four entities. The genuine gap is the **typed-bridge
adapters** that take the new HS-2-02 contract types
(`IntentWindow` + `IntentScore`, `PluginRun`, `ArtifactLineage`) as
inputs so callers don't hand-shuffle field positions or remember the
`(source_type, source_ref)` shape `record_artifact` expects for lineage.

## Scope

- **In:**
  - New module `holdspeak/plugins/persistence.py` with:
    - `record_intent_window(db, window, score, *, profile, ...)` — writes both `IntentWindow` + its `IntentScore` in one call; rejects window-id mismatch.
    - `record_plugin_run(db, run)` + `record_plugin_runs(db, runs)` — typed wrappers; `status="deduped"` flips the persisted `deduped` flag automatically.
    - `record_artifact_with_lineage(db, *, artifact_id, ..., lineage)` — packs `lineage.window_ids` + `lineage.plugin_run_keys` into the `(source_type, source_ref)` shape `db.record_artifact` expects; rejects artifact-id / meeting-id mismatch.
  - Re-exports from `holdspeak/plugins/__init__.py` (renamed exports `persist_intent_window` / `persist_plugin_run*` to avoid colliding with existing `db.record_*` names imported elsewhere).
  - Unit tests at `tests/unit/test_intent_persistence.py`: 8 cases covering MIR-D-001/002 typed window+score round-trip, MIR-D-003 typed plugin-run round-trip + deduped flag, MIR-D-004 typed lineage round-trip with both `window` and `plugin_run` source rows, MIR-D-006 back-compat (empty meeting loads clean), and validation errors on id mismatch.
- **Out:**
  - Schema changes: not needed; the schema covers MIR-D-001..D-006 today.
  - Persisting `PluginRun.started_at` / `PluginRun.finished_at` — `plugin_runs` only stores `duration_ms` + `created_at`. Documented as a known semantic gap; HS-2-10 (observability hardening) is the right place to either add columns or carry the timestamps in the existing `output_json` / `metadata_json`.
  - Replacing the existing `db.record_*` API or `PluginRunSummary`/`IntentWindowSummary` read-side projections — they remain for callers that want the persistence-shaped view.

## Acceptance criteria

- [x] `record_intent_window(db, window, score, ...)` round-trips an `IntentWindow` + its `IntentScore` to `db.list_intent_windows` (MIR-D-001, MIR-D-002).
- [x] `record_intent_window` derives `active_intents` from `IntentScore.labels_above_threshold()` when the caller doesn't pass it explicitly.
- [x] `record_plugin_run(db, PluginRun)` round-trips to `db.list_plugin_runs` with `idempotency_key` preserved (MIR-D-003).
- [x] `PluginRun.status="deduped"` → persisted record has `deduped=True`.
- [x] `record_plugin_runs(db, [...])` writes a batch in order, surfacing all rows in `list_plugin_runs`.
- [x] `record_artifact_with_lineage` packs `ArtifactLineage.window_ids` + `plugin_run_keys` as `("window", w_id)` / `("plugin_run", k)` source rows readable on `db.list_artifacts(...).sources` (MIR-D-004, MIR-F-011).
- [x] Validation: `IntentScore.window_id != IntentWindow.window_id` → `ValueError`. `ArtifactLineage.artifact_id != artifact_id` → `ValueError`.
- [x] Empty meeting (no MIR rows) loads cleanly — `list_intent_windows` / `list_plugin_runs` / `list_artifacts` return `[]` (MIR-D-006).
- [x] `tests/unit/test_intent_persistence.py` ships with 8 cases, all pass.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 921 passed, 12 skipped, 0 failed in 14.91s. Pass delta vs. HS-2-04 (913): +8.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_intent_persistence.py -q` (8 cases).
- **Spec verification gate (§9.5):** `uv run pytest -q tests/unit/test_db.py::TestMirPersistence` — pre-existing engine tests must remain green.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Two first-pass test failures, both my mistakes (not implementation bugs): (1) called `db.record_synthesized_artifact` — the method is actually `db.record_artifact`; fixed with a one-line rename in the adapter; (2) asserted `s.source_type` on `ArtifactSummary.sources` — the field is typed `list[dict[str, str]]`, fixed with dict-key access in the test.
- Documented gap: `PluginRun.started_at` / `finished_at` are not persisted. The contract carries them; the engine schema doesn't have columns for them. Consumer-side observability (HS-2-10) gets to decide whether to add columns or stash them in `output_json["_run_clock"]` — neither is in scope here.
