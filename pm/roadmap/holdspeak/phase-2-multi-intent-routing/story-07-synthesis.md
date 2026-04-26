# HS-2-07 — Step 6: Synthesis pass

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-04 (dispatch produces PluginRun), HS-2-05 (artifact persistence), HS-2-06 (pipeline)
- **Unblocks:** HS-2-08 (web/CLI surfaces query persisted artifacts)
- **Owner:** unassigned

## Problem

Spec §9.7 calls for: synthesis pipeline in `holdspeak/plugins/synthesis.py`,
window-level artifact merge into a final set, lineage preservation,
unit + integration tests. Audit (post-HS-2-06): the synthesizer
(`synthesize_meeting_artifacts`) and 3 unit tests already exist —
dedup by `(plugin_id, output-hash)`, lineage via `ArtifactSourceRef`,
status by confidence. The genuine gaps:

1. **Persistence bridge.** `synthesize_meeting_artifacts` returns
   `ArtifactDraft` but nothing persists them — `db.record_artifact`
   is the engine method, no typed bridge exists.
2. **Typed lineage projection.** `ArtifactDraft.sources` is a list of
   `ArtifactSourceRef` (rich); the typed contract is `ArtifactLineage`
   from HS-2-02, with separate `window_ids` / `plugin_run_keys`.
3. **End-to-end pipeline integration.** `process_meeting_state` runs
   dispatch + persistence but not synthesis.
4. **Spec integration test.** `tests/integration/test_artifact_synthesis_pipeline.py`
   doesn't exist.
5. **Plugin run output threading.** `PluginRun` contract didn't carry
   `output`; the synthesizer needs it. Additive change to the contract
   (default None, non-breaking).

## Scope

- **In:**
  - Additive contract change: `PluginRun.output: dict | None = None`. Updates `_to_plugin_run` (dispatch.py) to thread `result.output` through, and `record_plugin_run` (persistence.py) to persist `run.output` when no explicit override is supplied.
  - New helpers in `holdspeak/plugins/synthesis.py`:
    - `to_artifact_lineage(draft) -> ArtifactLineage` — typed projection split into `window_ids` / `plugin_run_keys`.
    - `synthesize_and_persist(db, meeting_id, *, max_artifacts, plugin_runs=None) -> tuple[list[ArtifactDraft], list[ArtifactLineage]]` — orchestrator that reads `db.list_plugin_runs` (or accepts an explicit iterable), runs synthesis, persists each artifact via `db.record_artifact` with source rows.
  - `process_meeting_state(synthesize: bool = False, max_artifacts: int = 200, ...)` — when True (and `db` is supplied), runs `synthesize_and_persist` after dispatch+persist; result fields `artifacts` + `artifact_lineages` populated. Default `False` preserves HS-2-06 behavior.
  - `MIRPipelineResult` grows `artifacts: list[ArtifactDraft]` + `artifact_lineages: list[ArtifactLineage]` fields (default empty).
  - Re-exports from `holdspeak/plugins/__init__.py`.
  - Tests:
    - `tests/unit/test_artifact_synthesis_persist.py` (new) — 5 cases covering lineage projection, empty sources, end-to-end persist + read-back, empty meeting safety, explicit-iterable path.
    - `tests/integration/test_artifact_synthesis_pipeline.py` (new) — 3 cases covering pipeline-with-synthesis end-to-end, default-off behavior, dedup of identical outputs across overlapping windows (MIR-F-009, MIR-F-010, MIR-F-011).
- **Out:**
  - Hooking synthesis into `MeetingSession.stop()` — HS-2-06 only wires the dispatch+persist pass; flipping `synthesize=True` from there is HS-2-09's job (config knob).
  - Web/CLI surfaces over `db.list_artifacts(...)` — HS-2-08.

## Acceptance criteria

- [x] `PluginRun` carries optional `output: dict | None = None`; default is non-breaking (verified: 29 pre-existing intent + dispatch + persistence + pipeline + synthesis tests still pass).
- [x] `_to_plugin_run` threads `result.output` onto the typed `PluginRun`.
- [x] `record_plugin_run(db, run)` persists `run.output` by default; explicit `output=` kwarg still wins.
- [x] `to_artifact_lineage(draft)` returns an `ArtifactLineage` with `window_ids` (sorted) and `plugin_run_keys` (sorted) split by `source_type`.
- [x] `synthesize_and_persist(db, meeting_id)` reads `db.list_plugin_runs(meeting_id)` when `plugin_runs` not supplied, runs synthesis, persists every draft via `db.record_artifact` with source rows.
- [x] `process_meeting_state(synthesize=True, db=db)` populates `result.artifacts` + `result.artifact_lineages`; persisted artifacts are visible via `db.list_artifacts(meeting_id)`.
- [x] `process_meeting_state(synthesize=False)` (default) leaves both new fields empty; HS-2-06 disabled-path remains byte-identical.
- [x] Identical plugin outputs across overlapping windows dedupe to one artifact (MIR-F-009).
- [x] Lineage round-trip: `db.list_artifacts(...).sources` carries the `("intent_window", w_id)` and `("plugin_run", k)` rows (MIR-F-011).
- [x] Spec §9.7 verification gate green: `uv run pytest -q tests/unit/test_artifact_synthesis.py tests/integration/test_artifact_synthesis_pipeline.py` → `6 passed`.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 940 passed, 12 skipped, 0 failed in 17.53s. Pass delta vs. HS-2-06 (932): +8.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_artifact_synthesis.py tests/unit/test_artifact_synthesis_persist.py -q` (3 pre-existing + 5 new = 8 cases).
- **Integration:** `uv run pytest tests/integration/test_artifact_synthesis_pipeline.py -q` (3 cases).
- **Spec verification gate (§9.7):** `uv run pytest -q tests/unit/test_artifact_synthesis.py tests/integration/test_artifact_synthesis_pipeline.py`.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- One first-pass test failure (test bug, not implementation): the
  cross-window dedup test had a stub returning `active_intents` from
  the context, which differs per window → outputs hashed differently
  → no dedup. Fix: drop `active_intents` from the stub output so the
  hashes match. The behavior under test is correct; the assertion just
  needed identical inputs to dedupe.
- The HS-2-04 story-04 file documented "PluginRun does not carry plugin
  output" as deliberate. HS-2-07 reverses that with an additive default-None
  field — the original rationale (separate concerns: contract vs.
  runtime wrapper) was right at the time but synthesis genuinely needs
  the output payload to dedupe and summarize. Default-None keeps the
  contract change non-breaking; explicit consumers continue to work.
