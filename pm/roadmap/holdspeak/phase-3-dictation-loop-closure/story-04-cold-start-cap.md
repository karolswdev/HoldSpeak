# HS-3-04 — DIR-R-003 cold-start hard-cap

- **Project:** holdspeak
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HS-3-03 (counters in place so the disable event is visible)
- **Unblocks:** "useful" being protected from a runaway first call
- **Owner:** unassigned

## Problem

DIR-01 §9.6 (`DIR-R-003`) requires the cold-start path — first call
after `holdspeak` launch with `warm_on_start=false` — to complete or
short-circuit within `max_total_latency_ms × 5`; otherwise it must
log and disable the LLM stage for the session. Without this guard,
a misconfigured wheel (the §12 #2 risk) or an under-provisioned
machine can hang the dictation pipeline on the very first hotkey
press of a session — the opposite of "actually useful."

## Scope

- **In:**
  - In the LLM runtime wrapper (or wherever `classify` is dispatched), detect the cold-start condition (`first call this session AND warm_on_start=false`) and start a wall-clock timer.
  - If the call exceeds `max_total_latency_ms × 5`, raise/return a deterministic short-circuit, log a structured warning, and set a session-scoped `disabled_for_session=True` flag that future calls check before invoking the runtime.
  - Make sure the disable is *session-scoped*, not persisted: a fresh `holdspeak` launch retries.
  - Unit test: forced cold-start path with a stubbed slow runtime asserts short-circuit + disable semantics.
  - Integration test: pipeline with the disabled flag set falls back to the lexical (non-LLM) path without raising.
- **Out:**
  - Warm-path runaway detection — explicitly deferred per the phase status doc.
  - Persistent disable across launches.
  - User-visible UI signal — doctor output is sufficient for this phase.

## Acceptance criteria

- [ ] Cold-start path detects exceedance of `max_total_latency_ms × 5` and short-circuits.
- [ ] Session is marked LLM-disabled; subsequent classify calls return the short-circuit immediately without invoking the runtime.
- [ ] A structured log line names the breach (measured ms vs. cap) at WARN level.
- [ ] Doctor surface (HS-3-03 counter check or a sibling) reports `llm_disabled_for_session=true` when the breach has occurred.
- [ ] Unit + integration tests pass.
- [ ] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.

## Test plan

- **Unit:** `tests/unit/test_runtime_cold_start_cap.py` — stub a slow runtime, assert short-circuit + disable.
- **Integration:** pipeline with `llm_disabled_for_session=True` produces a fallback final text and does not raise.
- **Regression:** documented full-suite command.

## Notes / open questions

- The cap value is `MeetingConfig.max_total_latency_ms × 5` only if such a field exists in DIR-01's config; if DIR-01 stores it under a different name, follow the spec name. Verify at implementation.
- Time the cold-start at the wrapping call boundary (not inside the model load) so the cap covers load + first inference jointly, matching spec §9.6 wording.
