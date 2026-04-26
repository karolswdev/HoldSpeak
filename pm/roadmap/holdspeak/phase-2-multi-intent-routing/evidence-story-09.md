# Evidence — HS-2-09 (Config + feature flags)

**Story:** [story-09-config-flags.md](./story-09-config-flags.md)
**Date:** 2026-04-26
**Status flipped:** backlog → done

## What shipped

- `holdspeak/config.py` — added 6 spec-named MIR-01 fields to
  `MeetingConfig` plus `__post_init__` validation and the
  `intent_hysteresis()` helper.
- `holdspeak/meeting_session.py` — `MeetingSession.__init__` accepts
  `mir_window_seconds`, `mir_step_seconds`, `mir_score_threshold`,
  `mir_hysteresis`, `mir_synthesize`. `stop()` threads them into
  `process_meeting_state(...)`.
- `tests/unit/test_config_intent_router.py` (new, 7 cases) — defaults,
  hysteresis converter, all 4 validation classes, dict round-trip.
- `tests/integration/test_meeting_session_intent_config.py` (new, 3 cases)
  — config → MeetingSession → pipeline end-to-end (disabled gate keeps
  pipeline off; enabled gate persists with configured profile +
  threshold; window/step config changes window count).
- `tests/unit/test_config.py::TestMeetingConfig.test_default_values`
  — extended to cover the 6 new defaults.

## Test output

### New unit tests

```
$ uv run pytest tests/unit/test_config_intent_router.py -q
.......                                                                  [100%]
7 passed in 0.04s
```

### New integration tests

```
$ uv run pytest tests/integration/test_meeting_session_intent_config.py -q
...                                                                      [100%]
3 passed in 0.31s
```

### Spec §9.9 verification gate

```
$ uv run pytest -q tests/unit/test_config.py tests/unit/test_doctor_command.py
... (config + doctor tests both pass)
```

The 7 new config cases:

1. `test_intent_router_defaults_are_conservative` — all 6 fields at spec defaults; `intent_router_enabled` is `False`.
2. `test_intent_hysteresis_helper_converts_windows_to_float` — 0/1/4/20 windows → 0.0/0.05/0.20/0.5 (cap).
3. `test_intent_window_seconds_must_be_positive` — `0` and negative both raise.
4. `test_intent_step_seconds_must_be_positive`.
5. `test_intent_score_threshold_must_be_in_unit_interval` — boundaries OK; `-0.1` and `1.1` raise.
6. `test_intent_hysteresis_windows_must_be_non_negative` — `0` OK; `-1` raises.
7. `test_plugin_profile_must_be_non_empty_string` — `""` and `"   "` both raise.
8. `test_intent_router_fields_round_trip_via_to_dict` — `dataclasses.asdict` includes every new field.

The 3 new integration cases (each with `@pytest.mark.timeout(15)`):

1. `test_disabled_router_config_keeps_pipeline_off` — default config (`intent_router_enabled=False`) → no MIR persistence, no `_mir_last_result`.
2. `test_enabled_router_config_drives_pipeline_with_tuned_threshold` — config with `plugin_profile="architect"` + `intent_score_threshold=0.4` → persisted windows carry both values; `_mir_last_result.errors == []`.
3. `test_window_step_seconds_change_window_count` — same transcript with `(120s, 120s)` vs `(15s, 5s)` window/step → second produces strictly more windows.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
965 passed, 12 skipped in 16.19s
```

Pass delta vs. HS-2-08 baseline (954): **+11** (7 new unit + 3 new
integration + 1 extended `test_default_values` case). Skip count
unchanged at 12.

## Acceptance criteria — re-checked

All 10 checked in [story-09-config-flags.md](./story-09-config-flags.md).

## Deviations from plan

- **Web settings API validation deferred.** Spec §9.9 mentions
  "Update settings API validation in `holdspeak/web_server.py`."
  The existing settings endpoints accept arbitrary JSON; rejecting
  invalid MIR field values at the API surface is additive and not
  on the critical path. HS-2-10 doctor checks will catch
  misconfigured *runtime* state at startup, which is the
  higher-leverage check.
- **`mir_enabled` / `mir_profile` not renamed.** Spec naming for
  pipeline knobs is `intent_router_enabled` / `plugin_profile`.
  The existing `mir_enabled` / `mir_profile` fields control the
  web-controls UI surface (HS-2-08), not the pipeline gate.
  Renaming would be a config-schema breaking change for users with
  persisted `config.json` files. Both surfaces coexist; the
  spec-named fields drive the pipeline. A future cleanup can
  converge them once the web UI is fully wired.

## Follow-ups

- HS-2-10 — MIR-specific doctor checks (verify host-registered
  plugins match config'd profile chain; warn when
  `intent_router_enabled=True` but `mir_plugin_host=None` at
  session construction).
- Future story — settings API validation in `web_server.py`,
  rejecting malformed MIR field values before they reach the
  config layer.
- Future cleanup — converge `mir_enabled` / `intent_router_enabled`
  semantics after the web UI is fully wired against MIR-01.

## Files in this commit

- `holdspeak/config.py` (+6 fields, __post_init__ validation, intent_hysteresis helper)
- `holdspeak/meeting_session.py` (+5 kwargs threaded into process_meeting_state)
- `tests/unit/test_config.py` (extended TestMeetingConfig.test_default_values)
- `tests/unit/test_config_intent_router.py` (new, 7 cases)
- `tests/integration/test_meeting_session_intent_config.py` (new, 3 cases)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-09-config-flags.md`
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-09.md` (this file)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md`
- `pm/roadmap/holdspeak/README.md`
