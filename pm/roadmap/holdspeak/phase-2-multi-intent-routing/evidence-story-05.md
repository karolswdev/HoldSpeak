# Evidence — HS-2-05 (Persistence + migration)

**Story:** [story-05-persistence.md](./story-05-persistence.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/persistence.py` (new) — typed-bridge writers
  over the existing `MeetingDatabase` CRUD:
  - `record_intent_window(db, window, score, ...)` — validates
    `window_id` match, derives `active_intents` from
    `IntentScore.labels_above_threshold()` when not supplied, writes
    via `db.record_intent_window`.
  - `record_plugin_run(db, run)` + `record_plugin_runs(db, runs)` —
    `status="deduped"` flips the persisted `deduped` flag.
  - `record_artifact_with_lineage(db, *, ..., lineage)` — validates
    artifact-id + meeting-id match, packs
    `lineage.window_ids → ("window", w_id)` and
    `lineage.plugin_run_keys → ("plugin_run", k)` for `db.record_artifact`.
- `holdspeak/plugins/__init__.py` — re-exports as `persist_intent_window`,
  `persist_plugin_run`, `persist_plugin_runs`, `record_artifact_with_lineage`
  (the `persist_*` prefix avoids colliding with the engine-side
  `db.record_*` names that some callers import directly).
- `tests/unit/test_intent_persistence.py` (new) — 8 cases.

## Why db.py wasn't touched

Pre-HS-2 audit showed `holdspeak/db.py` already at `SCHEMA_VERSION = 10`
with every spec §6.2 table in place — `intent_windows`,
`intent_window_scores`, `plugin_runs`, `plugin_run_jobs`, `artifacts`,
`artifact_sources` — created via idempotent
`CREATE TABLE IF NOT EXISTS` plus explicit per-version migrations.
Engine-side CRUD (`record_intent_window`, `list_intent_windows`,
`record_plugin_run`, `list_plugin_runs`, `record_artifact`,
`list_artifacts`) all working. `tests/unit/test_db.py::TestMirPersistence`
already covers MIR-D-001..D-006 round-trip on the engine API. This
story added the typed-contract front-door so HS-2-06+ callers don't
hand-shuffle field positions.

## Test output

### New unit tests (this story)

```
$ uv run pytest tests/unit/test_intent_persistence.py -q
........                                                                 [100%]
8 passed in 0.36s
```

### First-pass failures + fixes

Two failures on the first run, both my mistakes (not implementation bugs):

1. `AttributeError: 'MeetingDatabase' object has no attribute 'record_synthesized_artifact'` — the method is `db.record_artifact`. Fixed with a one-line rename in `persistence.py`.
2. `AttributeError: 'dict' object has no attribute 'source_type'` — `ArtifactSummary.sources` is typed `list[dict[str, str]]`, not a list of objects. Fixed the test with dict-key access (`s["source_type"]`).

Re-ran clean.

### Spec §9.5 verification gate

```
$ uv run pytest -q tests/unit/test_db.py::TestMirPersistence
......                                                                   [100%]
6 passed in 1.62s
```

The eight new cases:

1. `test_record_intent_window_round_trips_typed_score` — window + score → `db.list_intent_windows` carries them; active intents derived from `labels_above_threshold`.
2. `test_record_intent_window_rejects_window_id_mismatch` — `IntentScore.window_id != IntentWindow.window_id` → `ValueError`.
3. `test_record_plugin_run_round_trips_typed_record` — `PluginRun(success)` → `db.list_plugin_runs` shows it with `idempotency_key` preserved.
4. `test_record_plugin_run_marks_deduped_status_with_dedup_flag` — `status="deduped"` → persisted `deduped=True`.
5. `test_record_plugin_runs_persists_batch_in_order` — three-record batch → all three readable; statuses preserved including `error`.
6. `test_record_artifact_with_lineage_packs_window_and_plugin_run_sources` — `ArtifactLineage` round-trips to `art.sources` as `("window", w)` and `("plugin_run", k)` rows.
7. `test_record_artifact_rejects_lineage_id_mismatch` — `lineage.artifact_id != artifact_id` → `ValueError`.
8. `test_back_compat_meeting_without_intent_data_loads_clean_mir_d_006` — empty meeting reads as `[]` from all three list-* methods.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
921 passed, 12 skipped in 14.91s
```

Pass delta vs. HS-2-04 baseline (913 passed): **+8** (the new
`test_intent_persistence.py` cases). Skip count unchanged at 12.

## Acceptance criteria — re-checked

All checked in [story-05-persistence.md](./story-05-persistence.md).

## Deviations from plan

- Spec §9.5 listed `holdspeak/db.py` schema/migration edits and a
  test file at `tests/unit/test_db_intent_timeline.py`. The schema
  is already ahead of spec, and the engine-side coverage already
  lives in `tests/unit/test_db.py::TestMirPersistence`. Adding a
  redundant `test_db_intent_timeline.py` would have duplicated
  effort; the new test file uses the spec-suggested-but-not-required
  name `test_intent_persistence.py` to clearly mark it as the
  typed-bridge layer.
- Documented gap: `PluginRun.started_at` / `finished_at` are not
  persisted (the engine schema only has `duration_ms` + `created_at`).
  HS-2-10 owns the decision to add columns or stash these in
  `output_json["_run_clock"]`.

## Follow-ups

- HS-2-06 — `MeetingRuntime` calls `persist_intent_window(db, w, s)` +
  `persist_plugin_runs(db, dispatch_window(...))` after each window.
- HS-2-07 — synthesis pass calls `record_artifact_with_lineage(...)`
  after deduping per-window outputs.
- HS-2-10 — decide on `started_at`/`finished_at` persistence shape.

## Files in this commit

- `holdspeak/plugins/persistence.py` (new)
- `holdspeak/plugins/__init__.py` (re-exports)
- `tests/unit/test_intent_persistence.py` (new)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-05-persistence.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-05.md` (this file)
- `pm/roadmap/holdspeak/README.md` ("Last updated" line)
