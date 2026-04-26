# HS-2-06 — Step 5: Meeting runtime wiring

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-03 (scoring), HS-2-04 (dispatch), HS-2-05 (persistence)
- **Unblocks:** HS-2-07 (synthesis runs after the pipeline materializes), HS-2-09 (config gate flips this on in production)
- **Owner:** unassigned

## Problem

Spec §9.6 calls for: wire router into `holdspeak/meeting_session.py`
on segment updates and finalization, add fallback when scoring fails,
keep the stop path deadlock-safe, ship integration tests at
`tests/integration/test_multi_intent_routing.py` +
`test_multi_intent_stop_path.py`. Audit (post-HS-2-05): no MIR wiring
in `meeting_session.py` at all and neither integration test file
exists. This is the first phase-2 story with material new code rather
than a typed-bridge over already-built infra.

## Scope

- **In:**
  - New module `holdspeak/plugins/pipeline.py` — pure end-to-end orchestrator (`process_meeting_state(state, host, *, profile, threshold, hysteresis, db, ...) -> MIRPipelineResult`) chaining HS-2-03 windowing/scoring + HS-2-04 dispatch + HS-2-05 persistence. Per-stage `try/except` so failures degrade gracefully (MIR-F-012); nothing raises into the caller.
  - `MeetingSession.__init__` accepts `mir_routing_enabled: bool = False`, `mir_profile: str = "balanced"`, `mir_plugin_host`, `mir_db` — off by default; production wiring of the host/db happens in HS-2-09.
  - `MeetingSession.stop()` invokes the pipeline after the existing intel + title + web-server + diarizer cleanup (so it sees the finalized segments). Wrapped in `try/except`; result parked on `self._mir_last_result` for downstream introspection. No lock held during the pipeline call, so no new deadlock surface (MIR-R-005).
  - Re-exports `process_meeting_state` + `MIRPipelineResult` from `holdspeak/plugins/__init__.py`.
  - Unit tests at `tests/unit/test_intent_pipeline.py` (5 cases) covering pure-pipeline behavior, missing-id, empty-segments, end-to-end, persistence, and graceful per-plugin failure.
  - Integration tests:
    - `tests/integration/test_multi_intent_routing.py` (3 cases) — full pipeline end-to-end through a fake state, including MIR-F-008 idempotency dedup on re-run and MIR-F-005 transitions across an arc.
    - `tests/integration/test_multi_intent_stop_path.py` (3 cases) — `MeetingSession.stop()` with MIR enabled persists results + survives an exploding plugin host without propagating; explicit `pytest.mark.timeout(15)` to fail loud rather than hang.
- **Out:**
  - **On-segment-update wiring** (the other half of spec §9.6 line 1) — defers to a future story. Stop-path wiring satisfies MIR-R-005 (persist partial progress before stop finalization) and is the safer first hook in a 1375-line threaded session class. Streaming-on-segment is a more invasive refactor that wants its own scope.
  - Production config plumbing for `mir_plugin_host` / `mir_db` — HS-2-09's job.
  - Synthesis from MIR pipeline output — HS-2-07's job.

## Acceptance criteria

- [x] `process_meeting_state(state, host, ...)` returns a typed `MIRPipelineResult` with `windows`, `scores`, `transitions`, `runs`, `errors`.
- [x] Empty segments → empty result with `errors == []`.
- [x] Missing `state.id` → empty result with the error recorded (no raise).
- [x] One unknown plugin id in the route's chain → typed `PluginRun(status="error")` records, **pipeline still completes** (MIR-F-012).
- [x] When `db` is supplied, windows + plugin runs land in `db.list_intent_windows` + `db.list_plugin_runs`.
- [x] `MeetingSession(mir_routing_enabled=False).stop()` is byte-identical to pre-HS-2-06 behavior — no MIR import, no DB writes, `_mir_last_result is None`.
- [x] `MeetingSession(mir_routing_enabled=True, mir_plugin_host=host, mir_db=db).stop()` persists windows + plugin runs and parks the result on `_mir_last_result`.
- [x] Pipeline exception during stop → caught + logged; `stop()` still returns the final state (MIR-F-012, MIR-R-005).
- [x] Stop-path tests have explicit `@pytest.mark.timeout(15)` to fail loud on any new deadlock.
- [x] Spec §9.6 verification gate green: `uv run pytest -q tests/integration/test_multi_intent_routing.py tests/integration/test_multi_intent_stop_path.py` → `6 passed`.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 932 passed, 12 skipped, 0 failed in 16.84s. Pass delta vs. HS-2-05 (921): +11.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_intent_pipeline.py -q` (5 cases).
- **Integration:** `uv run pytest tests/integration/test_multi_intent_routing.py tests/integration/test_multi_intent_stop_path.py -q` (3 + 3 cases).
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Two minor first-pass test mistakes (not implementation bugs): (1) end-to-end test asserted `status in {success, deduped}` but architecture-keyword segments activated the architecture intent chain whose plugins (`mermaid_architecture`, `adr_drafter`) weren't registered → fixed by registering the full union; (2) stop-path integration test forgot to `db.save_meeting(state)` before `stop()`, so MIR persistence had no FK target → fixed.
- The on-segment-update half of spec §9.6 line 1 is **deferred**. Wiring MIR into the in-flight transcription loop touches `_transcribe_loop` + the intel-segment cadence + the per-segment lock, all on the hot path. Better as its own story once the stop-path path has bedded in. Documented as a follow-up here so HS-2-09 knows it's outstanding.
- The pipeline's `try/except` around dispatch is largely redundant because `dispatch_window` already isolates per-plugin failures into `PluginRun(status="error")`. Kept anyway as a defense-in-depth boundary for any *non-plugin* exception (e.g. `preview_route` blowing up on a malformed score map).
