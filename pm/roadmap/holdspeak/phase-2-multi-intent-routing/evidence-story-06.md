# Evidence — HS-2-06 (Meeting runtime wiring)

**Story:** [story-06-runtime-wiring.md](./story-06-runtime-wiring.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/pipeline.py` (new) — pure orchestrator
  `process_meeting_state(state, host, *, profile, threshold,
  hysteresis, window_seconds, step_seconds, db, timeout_seconds,
  defer_heavy)` returning typed `MIRPipelineResult`. Per-stage
  `try/except` so windowing → scoring → transitions → dispatch →
  persistence each degrade gracefully (MIR-F-012); nothing raises
  into the caller.
- `holdspeak/meeting_session.py` — `MeetingSession.__init__` accepts
  4 new kwargs (`mir_routing_enabled`, `mir_profile`,
  `mir_plugin_host`, `mir_db`), all defaulting to off / None.
  `MeetingSession.stop()` invokes the pipeline after intel + title +
  web-server + diarizer cleanup, wrapped in `try/except`. Result
  parked on `self._mir_last_result`.
- `holdspeak/plugins/__init__.py` — re-exports `process_meeting_state`
  + `MIRPipelineResult`.
- `tests/unit/test_intent_pipeline.py` (new) — 5 cases.
- `tests/integration/test_multi_intent_routing.py` (new) — 3 cases.
- `tests/integration/test_multi_intent_stop_path.py` (new) — 3 cases.

## Why this story is the first non-bridge in phase 2

HS-2-02..05 each filled typed-contract gaps over already-built MIR-01
infrastructure (host, scoring, transitions, persistence). The
meeting-session integration was genuinely missing — no MIR imports in
`meeting_session.py`, neither integration test file existed. This
story shipped real new code (pipeline orchestrator + stop-path hook)
with full integration coverage.

## Test output

### New unit tests

```
$ uv run pytest tests/unit/test_intent_pipeline.py -q
.....                                                                    [100%]
5 passed in 0.26s
```

### Spec §9.6 verification gate

```
$ uv run pytest -q tests/integration/test_multi_intent_routing.py \
                   tests/integration/test_multi_intent_stop_path.py
......                                                                   [100%]
6 passed in 0.30s
```

### Combined HS-2-06 test set

```
$ uv run pytest tests/unit/test_intent_pipeline.py \
                tests/integration/test_multi_intent_routing.py \
                tests/integration/test_multi_intent_stop_path.py -q
...........                                                              [100%]
11 passed in 0.46s
```

The eleven new cases:

**Unit (`test_intent_pipeline.py`)**
1. `test_process_meeting_state_returns_empty_result_for_empty_segments`
2. `test_process_meeting_state_returns_error_when_id_missing`
3. `test_process_meeting_state_runs_full_pipeline_end_to_end`
4. `test_process_meeting_state_persists_when_db_supplied`
5. `test_process_meeting_state_dispatch_failure_is_recorded_not_raised`

**Integration: routing (`test_multi_intent_routing.py`)**
1. `test_pipeline_end_to_end_persists_typed_outputs` — full chain → `db.list_intent_windows` + `list_plugin_runs` carry the typed output 1:1.
2. `test_pipeline_rerun_dedupes_via_host_idempotency_cache` — second pass against the same state → all `runs[].status == "deduped"`, no new plugin invocations (MIR-F-008, MIR-F-009).
3. `test_pipeline_emits_transitions_across_intent_arc` — at least 2 transitions across an architecture → delivery → incident arc (MIR-F-005).

**Integration: stop-path (`test_multi_intent_stop_path.py`)**
1. `test_meeting_session_stop_runs_mir_pipeline_when_enabled` — stop persists windows + runs, parks result on `_mir_last_result`.
2. `test_meeting_session_stop_is_byte_identical_when_mir_disabled` — no MIR persistence, `_mir_last_result is None`.
3. `test_meeting_session_stop_survives_mir_pipeline_exception` — exploding host → `stop()` still returns the final state (MIR-F-012, MIR-R-005).

All three stop-path cases have `@pytest.mark.timeout(15)` to fail loud on any deadlock regression.

### First-pass failures + fixes

Two mistakes in tests, neither in implementation:

1. End-to-end pipeline test asserted `r.status in {"success", "deduped"}` but architecture-keyword segments activated the architecture intent chain whose plugins (`mermaid_architecture`, `adr_drafter`) weren't in the test host registry → `error` status instead → assertion failed. Fix: register the full union of every plugin id any profile/intent chain references.
2. Stop-path integration test forgot to `db.save_meeting(state)` before `stop()`, so MIR persistence had no FK target. Fix: pass `db` into `_seed_active_state` and call `db.save_meeting` there.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
932 passed, 12 skipped in 16.84s
```

Pass delta vs. HS-2-05 baseline (921): **+11** (5 unit + 3 routing
integration + 3 stop-path integration). Skip count unchanged at 12.

## Acceptance criteria — re-checked

All 10 checked in [story-06-runtime-wiring.md](./story-06-runtime-wiring.md).

## Deviations from plan

- **On-segment-update wiring deferred.** Spec §9.6 line 1 says "Wire
  router into `meeting_session.py` on segment updates and
  finalization." This story wired finalization (the stop path) only.
  In-flight wiring touches `_transcribe_loop` + the intel cadence +
  the per-segment lock, all on the hot path of a 1375-line threaded
  class. Better as its own follow-up story; documented in story file
  Notes so HS-2-09 (config + flags) knows the surface is not yet
  fully gated.
- Pipeline's outer `try/except` around dispatch is somewhat
  defensive — `dispatch_window` already isolates per-plugin failures
  internally. Kept as a belt-and-suspenders boundary for any
  non-plugin exception (e.g. `preview_route` malformed input).

## Follow-ups

- New story (TBD): on-segment-update wiring of MIR into
  `_transcribe_loop`, with care for the per-segment lock + intel
  cadence interaction.
- HS-2-07 (synthesis): consume `MIRPipelineResult.runs` +
  `MIRPipelineResult.transitions` to materialize artifacts with
  `ArtifactLineage`.
- HS-2-09 (config + flags): expose `mir.routing.enabled` /
  `mir.profile` config knobs so `MeetingSession` constructor
  receives them from the user's settings.

## Files in this commit

- `holdspeak/plugins/pipeline.py` (new)
- `holdspeak/plugins/__init__.py` (re-exports)
- `holdspeak/meeting_session.py` (4 new kwargs + stop() hook)
- `tests/unit/test_intent_pipeline.py` (new)
- `tests/integration/test_multi_intent_routing.py` (new)
- `tests/integration/test_multi_intent_stop_path.py` (new)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-06-runtime-wiring.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-06.md` (this file)
- `pm/roadmap/holdspeak/README.md` ("Last updated" line)
