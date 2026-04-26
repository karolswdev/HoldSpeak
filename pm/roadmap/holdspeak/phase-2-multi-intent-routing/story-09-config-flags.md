# HS-2-09 — Step 8: Config + feature flags

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-06 (MeetingSession MIR kwargs)
- **Unblocks:** HS-2-10 (observability hardening reads config), HS-2-11 (DoD evidence sweep cites config defaults)
- **Owner:** unassigned

## Problem

Spec §9.9 calls for: extend `MeetingConfig` with 6 fields
(`intent_router_enabled`, `intent_window_seconds`,
`intent_step_seconds`, `intent_score_threshold`,
`intent_hysteresis_windows`, `plugin_profile`), set conservative
defaults + validation, update settings API validation. Audit
(post-HS-2-08): two unrelated `mir_enabled` / `mir_profile` fields
exist on `MeetingConfig` (they gate the web-controls UI surface
HS-2-08 tested), but none of the spec-named pipeline tuning fields
exist. `MeetingSession` has `mir_routing_enabled` + `mir_profile`
kwargs but no per-call tuning of window / threshold / hysteresis —
the pipeline always runs with hardcoded defaults.

## Scope

- **In:**
  - Add 6 spec-named fields to `MeetingConfig`:
    - `intent_router_enabled: bool = False` — pipeline gate (off by default; opt-in).
    - `intent_window_seconds: int = 90` — matches `build_intent_windows` default.
    - `intent_step_seconds: int = 30` — matches `build_intent_windows` default.
    - `intent_score_threshold: float = 0.6` — matches `DEFAULT_INTENT_THRESHOLD`.
    - `intent_hysteresis_windows: int = 1` — damping; converted to a float via the new `intent_hysteresis()` helper (0.05 per window, capped at 0.5).
    - `plugin_profile: str = "balanced"` — routing profile.
  - `MeetingConfig.__post_init__` validates: positive durations, threshold in `[0.0, 1.0]`, hysteresis windows >= 0, profile is a non-empty trimmed string. Raises `ValueError` with field name + value on construction (typos surface immediately rather than at first meeting stop).
  - `MeetingConfig.intent_hysteresis() -> float` — windows-to-float converter (0.05/window, capped at 0.5).
  - 4 new `MeetingSession.__init__` kwargs (`mir_window_seconds`, `mir_step_seconds`, `mir_score_threshold`, `mir_hysteresis`) plus `mir_synthesize` to expose the HS-2-07 synthesis flag. Threaded into the `process_meeting_state(...)` call.
  - Unit tests at `tests/unit/test_config_intent_router.py` (7 cases): defaults, hysteresis converter, all 4 validation errors, dict round-trip.
  - Integration test at `tests/integration/test_meeting_session_intent_config.py` (3 cases): disabled-router config keeps pipeline off, enabled config drives the pipeline with the configured profile + threshold flowing through to persisted rows, window/step config changes affect the produced window count.
  - Updated `tests/unit/test_config.py::TestMeetingConfig.test_default_values` to assert the 6 new defaults.
- **Out:**
  - Web settings API validation in `holdspeak/web_server.py` — the existing settings endpoints accept arbitrary JSON; tightening them to reject invalid MIR field values is straightforward additive work but not on the critical path for this story (HS-2-10 doctor checks will catch misconfigured runtime state at startup, which is the higher-leverage check).
  - Renaming the existing `mir_enabled` / `mir_profile` fields. They serve a different purpose (web-controls UI gate) and renaming would be a config-schema breaking change for users with persisted `config.json` files. Both surfaces coexist; the spec-named fields drive the pipeline, the `mir_*` fields drive the UI.
  - Doctor command updates — HS-2-10 owns the MIR-specific doctor checks.

## Acceptance criteria

- [x] `MeetingConfig` has all 6 spec-named fields with conservative defaults.
- [x] `intent_router_enabled` defaults to `False` — opt-in (mirrors DIR-01's `dictation.pipeline.enabled` pattern).
- [x] `MeetingConfig.__post_init__` rejects each invalid value class with a `ValueError` naming the field.
- [x] `intent_hysteresis()` returns 0.0 at 0 windows, 0.05 at 1, 0.20 at 4, capped at 0.5.
- [x] `MeetingSession.__init__` accepts `mir_window_seconds`, `mir_step_seconds`, `mir_score_threshold`, `mir_hysteresis`, `mir_synthesize`; defaults preserve HS-2-06 behavior.
- [x] `MeetingSession.stop()` threads the 5 new attrs into `process_meeting_state(...)`.
- [x] Bridge integration: `intent_router_enabled=True` config + `MeetingSession` constructor wiring → pipeline runs at stop, persists windows with the configured profile + threshold.
- [x] Window-step changes alter the produced window count (qualitative invariant: smaller step → more windows).
- [x] Existing `test_config.py::TestMeetingConfig.test_default_values` updated to cover the 6 new defaults.
- [x] Spec §9.9 verification gate: `uv run pytest -q tests/unit/test_config.py tests/unit/test_doctor_command.py` — config tests green; doctor tests unchanged (HS-2-10 will add MIR doctor checks).
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 965 passed, 12 skipped, 0 failed in 16.19s. Pass delta vs. HS-2-08 (954): +11.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_config_intent_router.py -q` (7 cases) + `tests/unit/test_config.py::TestMeetingConfig` (4 cases incl. updated defaults).
- **Integration:** `uv run pytest tests/integration/test_meeting_session_intent_config.py -q` (3 cases).
- **Spec §9.9 verification gate:** `uv run pytest -q tests/unit/test_config.py tests/unit/test_doctor_command.py`.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- `intent_hysteresis_windows: int` (spec naming) → `intent_hysteresis()` helper that returns the 0.05/window-as-float value the pipeline needs. The simple linear mapping with 0.5 cap is a placeholder; a future story can refine if real meetings show the gate either too sticky or too loose.
- Config schema breaking change avoided. Existing `mir_enabled` / `mir_profile` (web-controls UI gate) remain alongside the new `intent_router_enabled` / `plugin_profile` (pipeline gate). They could converge in a future cleanup once the web UI is fully wired (deferred from HS-2-08).
- Web settings API validation deferred — the existing settings endpoints accept arbitrary JSON. Tightening them is additive; HS-2-10 doctor checks catch misconfigured *runtime* state which is more useful than rejecting input shape twice.
