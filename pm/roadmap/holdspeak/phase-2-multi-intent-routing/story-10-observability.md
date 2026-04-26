# HS-2-10 — Step 9: Observability + hardening

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-04 (PluginHost metrics), HS-2-06 (pipeline), HS-2-09 (config)
- **Unblocks:** HS-2-11 (DoD evidence sweep cites doctor + counter output)
- **Owner:** unassigned

## Problem

Spec §9.10 calls for: structured logs in router + host, runtime
counters / telemetry hooks, integration test for failure isolation,
plus the unit observability test file. Audit (post-HS-2-09):

- `tests/unit/test_intent_observability.py` already exists with
  3 cases covering router counters (`get_router_counters`),
  plugin-host metrics (`PluginHost.get_metrics`), and structured-log
  fields with secret redaction (covers MIR-O-001/002/003).
- `holdspeak/plugins/router.py` already exposes `get_router_counters()`
  + `reset_router_counters()` for routed/dropped windows.
- `holdspeak/plugins/host.py` already emits structured JSON logs
  with `meeting_id`/`window_id`/`plugin_id`/`intent_set` and runs
  per-status metric counters + secret redaction by key-token match.

The genuine gaps:

1. **Missing failure-isolation integration test** (`tests/integration/test_intent_failure_isolation.py`) — MIR-R-004 unit coverage exists in the dispatcher, but no end-to-end pipeline test through persistence.
2. **No MIR doctor checks** — DIR-01 added 2 (`LLM runtime`, `Structured-output compilation`); MIR-01 has none. The user can have `intent_router_enabled=True` with an unknown `plugin_profile` and only find out at first meeting stop.

## Scope

- **In:**
  - 2 new doctor checks in `holdspeak/commands/doctor.py`, both honoring the DIR-DOC-003 never-FAIL pattern (MIR-01 is opt-in; misconfiguration is at most `WARN`):
    - `_check_mir_routing(config)` — when disabled: `PASS "disabled (opt-in)"`. When enabled: validate `plugin_profile` against `available_profiles()`; `WARN` for unknown profile with a fix hint; otherwise `PASS` with the active routing summary (profile, window/step, threshold, hysteresis_windows).
    - `_check_mir_telemetry()` — smoke-check that `get_router_counters()` and `PluginHost().get_metrics()` are callable + return dict shapes; always `PASS` with the key set in detail.
  - `collect_doctor_checks()` updated to include both checks in display order (after the dictation pair).
  - `tests/unit/test_doctor_command.py` extended with 5 cases covering: pass-when-disabled, pass-when-enabled-with-valid-profile, warn-for-unknown-profile, never-FAIL invariant across all gate states, telemetry smoke shape.
  - New `tests/integration/test_intent_failure_isolation.py` (3 cases): one failing chain plugin → siblings still execute (MIR-R-004); failing run persisted as `status=error` with `error` populated; multiple-failure scenario still produces full chain coverage.
- **Out:**
  - New router/host code. The structured-log fields, secret redaction, and counters all already exist (verified by the pre-existing 3-case `test_intent_observability.py` and host's `_log_event` impl).
  - Stop-path hardening beyond what HS-2-06 already shipped (the `@pytest.mark.timeout(15)` integration tests + lock-free pipeline call).
  - Phase doctor for `MeetingSession` constructor wiring (e.g., warn when `intent_router_enabled=True` but `mir_plugin_host=None`) — needs a way to peek into how the user actually constructs the session, which doesn't have a public introspection surface yet. Defer.

## Acceptance criteria

- [x] `_check_mir_routing(config)` returns `PASS "disabled"` when `intent_router_enabled=False`.
- [x] `_check_mir_routing(config)` returns `PASS` with active config summary when enabled with a valid `plugin_profile`.
- [x] `_check_mir_routing(config)` returns `WARN` (not FAIL) for an unknown `plugin_profile`, with a fix hint that names `plugin_profile`.
- [x] `_check_mir_routing` never returns `FAIL` (verified across disabled / enabled / garbage-profile gate states).
- [x] `_check_mir_telemetry()` always returns `PASS` with both `router_counters=[...]` and `host_metrics=[...]` in detail; `routed_windows` + `dropped_windows` keys both surface.
- [x] `collect_doctor_checks()` includes both new checks; existing 16 doctor unit cases remain green.
- [x] `tests/integration/test_intent_failure_isolation.py` ships with 3 cases, all pass.
- [x] One failing plugin in a routed chain → sibling plugins still execute (MIR-R-004), persisted runs reflect mixed `success`/`error` statuses, failure error surfaces in the persisted `error` field.
- [x] Spec §9.10 verification gate green: `uv run pytest -q tests/unit/test_intent_observability.py tests/integration/test_intent_failure_isolation.py` → `6 passed`.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 973 passed, 12 skipped, 0 failed in 17.28s. Pass delta vs. HS-2-09 (965): +8.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_doctor_command.py tests/unit/test_intent_observability.py -q` (16 + 5 + 3 = 24 cases).
- **Integration:** `uv run pytest tests/integration/test_intent_failure_isolation.py -q` (3 cases).
- **Spec §9.10 verification gate:** `uv run pytest -q tests/unit/test_intent_observability.py tests/integration/test_intent_failure_isolation.py`.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Both new doctor checks live next to the DIR-01 dictation checks in `collect_doctor_checks`. Display order: `dictation runtime` → `dictation compile` → `MIR routing` → `MIR telemetry`. This groups the two MIR-01 phases visually in `holdspeak doctor` output.
- `_check_mir_telemetry` instantiates a throwaway `PluginHost()` to probe `get_metrics()` shape — that's safe (no plugins registered, no execution) but worth knowing if the host's constructor ever grows side effects.
- Future story: MeetingSession-construction-time check — warn when the user has `intent_router_enabled=True` but the wired-in `mir_plugin_host` is `None`. Needs a session introspection surface; punt to a follow-up since the failure mode is benign (the pipeline simply no-ops when host is None — see HS-2-06 stop-path code).
