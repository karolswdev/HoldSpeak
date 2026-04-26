# Evidence — HS-2-10 (Observability + hardening)

**Story:** [story-10-observability.md](./story-10-observability.md)
**Date:** 2026-04-26
**Status flipped:** backlog → done

## What shipped

- `holdspeak/commands/doctor.py` — 2 new MIR-01 checks
  (`_check_mir_routing`, `_check_mir_telemetry`) wired into
  `collect_doctor_checks()` between the dictation pair and the
  hotkey/text-injection group. Both honor DIR-DOC-003 (never FAIL).
- `tests/unit/test_doctor_command.py` — extended with 5 new cases
  covering pass-when-disabled, pass-when-enabled, warn-for-unknown-profile,
  never-FAIL invariant, telemetry smoke shape.
- `tests/integration/test_intent_failure_isolation.py` (new, 3 cases)
  — MIR-R-004 end-to-end through the pipeline.

## Why no router/host code changes

Pre-HS-2-10 audit confirmed the structured-log fields,
secret-key redaction, router counters, and host metrics already
exist (`holdspeak/plugins/router.py::get_router_counters`,
`holdspeak/plugins/host.py::_log_event` + `_increment_metric`),
covered by 3 pre-existing cases in
`tests/unit/test_intent_observability.py` (router counter, host
metrics across 4 statuses, structured log + secret redaction).
This story added the missing doctor checks and the missing
integration test the spec named.

## Test output

### New + extended doctor tests

```
$ uv run pytest tests/unit/test_doctor_command.py -q
.....................                                                    [100%]
21 passed in 0.24s
```

(16 pre-existing + 5 new MIR cases.)

### New integration test

```
$ uv run pytest tests/integration/test_intent_failure_isolation.py -q
...                                                                      [100%]
3 passed in 0.16s
```

### Spec §9.10 verification gate

```
$ uv run pytest -q tests/unit/test_intent_observability.py \
                   tests/integration/test_intent_failure_isolation.py
......                                                                   [100%]
6 passed in 0.18s
```

The five new doctor cases:

1. `test_mir_routing_check_pass_when_router_disabled` — `intent_router_enabled=False` → `PASS "MIR-01 routing pipeline disabled (opt-in)"`.
2. `test_mir_routing_check_pass_when_enabled_with_valid_profile` — `intent_router_enabled=True, plugin_profile="architect"` → `PASS` with active routing summary.
3. `test_mir_routing_check_warn_for_unknown_profile` — typo'd profile → `WARN`, fix hint mentions `plugin_profile`.
4. `test_mir_routing_check_never_returns_fail` — invariant verified across 3 gate states (DIR-DOC-003 compliance).
5. `test_mir_telemetry_check_smoke_passes` — both `router_counters=[...]` and `host_metrics=[...]` keys present in detail; `routed_windows` + `dropped_windows` surface specifically.

The three new failure-isolation cases:

1. `test_failing_plugin_does_not_block_chain_siblings_mir_r_004` — one plugin raises → typed `PluginRun(status="error")` for the failing one; sibling plugins still run with `status="success"`; pipeline `errors == []` (per-plugin failures land on the typed records, not the outer try/except).
2. `test_failing_plugin_runs_persisted_with_error_status` — failed run on disk via `db.list_plugin_runs` with `status="error"` and `error="...intentionally exploding..."`; at least one sibling persisted with `status="success"`.
3. `test_pipeline_keeps_running_when_every_other_plugin_explodes` — alternating fail/succeed plugins → both statuses surface; full chain coverage preserved (one record per registered plugin).

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
973 passed, 12 skipped in 17.28s
```

Pass delta vs. HS-2-09 baseline (965): **+8** (5 new doctor + 3 new
integration). Skip count unchanged at 12.

## Acceptance criteria — re-checked

All 10 checked in [story-10-observability.md](./story-10-observability.md).

## Deviations from plan

- **No router/host code changes.** Spec §9.10 line 1 ("Add structured
  logs in router and host") and line 2 ("Add counters/telemetry hooks")
  are already satisfied by pre-HS-2 infra. This story added only the
  spec-named integration test + the doctor checks the spec implies but
  doesn't list explicitly.
- **MeetingSession-construction-time check deferred.** A nice-to-have
  doctor signal would be: warn when `intent_router_enabled=True` but
  `mir_plugin_host=None` at session construction. Needs a session
  introspection surface that doesn't exist; the failure mode is benign
  (the pipeline no-ops when host is None — see HS-2-06 stop-path code).
  Documented as a follow-up.

## Follow-ups

- HS-2-11 (DoD sweep) — exercise the new doctor checks during the
  evidence bundle capture and include their output in `41_doctor_checks.log`.
- Future: MeetingSession-construction-time doctor signal for the
  `intent_router_enabled=True ∧ mir_plugin_host=None` config.

## Files in this commit

- `holdspeak/commands/doctor.py` (+2 checks + collect wiring)
- `tests/unit/test_doctor_command.py` (extended, +5 cases)
- `tests/integration/test_intent_failure_isolation.py` (new, 3 cases)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-10-observability.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md`
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-10.md` (this file)
- `pm/roadmap/holdspeak/README.md`
