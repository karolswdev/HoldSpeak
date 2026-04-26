# Evidence — HS-2-07 (Synthesis pass)

**Story:** [story-07-synthesis.md](./story-07-synthesis.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/contracts.py` — additive: `PluginRun.output: dict | None = None`. `to_dict()` includes the field.
- `holdspeak/plugins/dispatch.py` — `_to_plugin_run` threads `result.output` onto the typed `PluginRun`.
- `holdspeak/plugins/persistence.py` — `record_plugin_run(db, run)` persists `run.output` by default; explicit `output=` kwarg still wins (back-compat with HS-2-05 callers).
- `holdspeak/plugins/synthesis.py` — `to_artifact_lineage(draft) -> ArtifactLineage` typed projection; `synthesize_and_persist(db, meeting_id, *, max_artifacts, plugin_runs=None) -> tuple[list[ArtifactDraft], list[ArtifactLineage]]` orchestrator.
- `holdspeak/plugins/pipeline.py` — `process_meeting_state(synthesize=False, max_artifacts=200, ...)`. `MIRPipelineResult` grows `artifacts` + `artifact_lineages` fields (default empty).
- `holdspeak/plugins/__init__.py` — re-exports `synthesize_and_persist` + `to_artifact_lineage`.
- `tests/unit/test_artifact_synthesis_persist.py` (new) — 5 cases.
- `tests/integration/test_artifact_synthesis_pipeline.py` (new) — 3 cases.

## Why this looked like a typed-bridge story but had real teeth

Synthesis logic + dedup + 3 unit tests already existed
(`synthesize_meeting_artifacts` in `synthesis.py`). But:
1. Nothing persisted the `ArtifactDraft` output anywhere.
2. The typed `ArtifactLineage` contract from HS-2-02 had no producer.
3. `process_meeting_state` had no synthesis hook.
4. The integration test file spec §9.7 names didn't exist.
5. Most importantly: `PluginRun` didn't carry output, so synthesis
   reading from `db.list_plugin_runs(meeting_id)` would have read
   empty output payloads and dedupe-everything-into-one. The contract
   needed an additive `output` field threaded through dispatch +
   persistence to make synthesis meaningful end-to-end.

## Test output

### New unit tests

```
$ uv run pytest tests/unit/test_artifact_synthesis_persist.py -q
.....                                                                    [100%]
5 passed in 0.27s
```

### New integration tests

```
$ uv run pytest tests/integration/test_artifact_synthesis_pipeline.py -q
...                                                                      [100%]
3 passed in 0.16s
```

### Spec §9.7 verification gate

```
$ uv run pytest -q tests/unit/test_artifact_synthesis.py \
                   tests/integration/test_artifact_synthesis_pipeline.py
......                                                                   [100%]
6 passed in 0.18s
```

### Combined HS-2-07 set

```
$ uv run pytest tests/integration/test_artifact_synthesis_pipeline.py \
                tests/unit/test_artifact_synthesis_persist.py \
                tests/unit/test_artifact_synthesis.py -q
...........                                                              [100%]
11 passed in 0.36s
```

### Regression spot-check on the additive contract change

```
$ uv run pytest tests/unit/test_intent_contracts.py \
                tests/unit/test_intent_dispatch.py \
                tests/unit/test_intent_persistence.py \
                tests/unit/test_intent_pipeline.py \
                tests/unit/test_artifact_synthesis.py -q
.............................                                            [100%]
29 passed in 0.44s
```

The eight new cases:

**Unit (`test_artifact_synthesis_persist.py`)**
1. `test_to_artifact_lineage_separates_window_and_plugin_run_sources` — typed projection split by `source_type`, ordering deterministic.
2. `test_to_artifact_lineage_empty_sources_yields_empty_lists` — degenerate input safe.
3. `test_synthesize_and_persist_writes_artifacts_with_lineage` — seeds windows + runs (with identical outputs across two windows), runs orchestrator, asserts: 1 deduped draft, lineage spans both windows + both runs, persisted via `db.list_artifacts` with both `intent_window` source rows.
4. `test_synthesize_and_persist_empty_meeting_returns_empty_pair` — no rows on disk → `([], [])`, no artifacts persisted.
5. `test_synthesize_and_persist_accepts_explicit_plugin_runs_iterable` — supplying `plugin_runs=[...]` bypasses `db.list_plugin_runs`.

**Integration (`test_artifact_synthesis_pipeline.py`)**
1. `test_process_meeting_state_synthesizes_when_flag_set` — pipeline w/ `synthesize=True` → artifacts + lineages populated, persisted artifacts visible via `db.list_artifacts`, every artifact has a matching lineage by id.
2. `test_process_meeting_state_synthesize_off_by_default` — without the flag, no synthesis, no artifacts on disk; plugin-runs persistence still happens.
3. `test_synthesis_dedupes_identical_outputs_across_overlapping_windows` — every plugin yields exactly one artifact (MIR-F-009).

### First-pass failures + fixes

One failure on the integration dedup test, my mistake (not
implementation): the stub initially included `active_intents` from
context in its output dict. Different windows have different active
intents → output hashes differ → no dedup. Fix: drop `active_intents`
from the stub output so identical-summary plugin runs hash to the
same dedup key. The synthesizer's behavior was correct; the test
inputs needed to be identical for dedupe to fire.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
940 passed, 12 skipped in 17.53s
```

Pass delta vs. HS-2-06 baseline (932): **+8** (5 unit + 3 integration).
Skip count unchanged at 12.

## Acceptance criteria — re-checked

All 11 checked in [story-07-synthesis.md](./story-07-synthesis.md).

## Deviations from plan

- **Reverses HS-2-04's "no output on PluginRun" decision.** The
  HS-2-04 story file explicitly documented that `PluginRun` would
  not carry output. HS-2-07 needs the output payload for synthesis,
  so an additive `output: dict | None = None` field landed on the
  contract. Default-None keeps the change non-breaking; verified
  with the 29-case adjacent regression above.
- **Synthesis hook in `MeetingSession.stop()` deferred.** The
  pipeline carries the flag (`synthesize=True`), but the
  `MeetingSession.stop()` invocation in HS-2-06 doesn't yet flip
  it on. HS-2-09 (config + flags) is the right place to surface
  `mir.synthesize` as a user-controllable knob and pass it through
  to `process_meeting_state`.

## Follow-ups

- HS-2-08 (web/CLI surfaces) — query `db.list_artifacts(meeting_id)`
  to render synthesized artifacts with lineage in the meeting
  dashboard / `holdspeak meeting artifacts` CLI subcommand.
- HS-2-09 (config + flags) — add `mir.synthesize` config knob and
  thread through to `MeetingSession` → `process_meeting_state`.
- Future: support synthesis confidence calibration once real LLM
  outputs replace the lexical scorer.

## Files in this commit

- `holdspeak/plugins/contracts.py` (additive: PluginRun.output)
- `holdspeak/plugins/dispatch.py` (thread output through _to_plugin_run)
- `holdspeak/plugins/persistence.py` (persist run.output by default)
- `holdspeak/plugins/synthesis.py` (to_artifact_lineage + synthesize_and_persist)
- `holdspeak/plugins/pipeline.py` (synthesize flag + 2 new MIRPipelineResult fields)
- `holdspeak/plugins/__init__.py` (re-exports)
- `tests/unit/test_artifact_synthesis_persist.py` (new, 5 cases)
- `tests/integration/test_artifact_synthesis_pipeline.py` (new, 3 cases)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-07-synthesis.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-07.md` (this file)
- `pm/roadmap/holdspeak/README.md` ("Last updated" line)
