# Evidence — HS-2-04 (Plugin host integration)

**Story:** [story-04-plugin-host.md](./story-04-plugin-host.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/dispatch.py` (new) — `dispatch_window`,
  `dispatch_windows`, `_to_plugin_run` adapter. Each plugin invocation
  is wrapped with real `time.time()` boundaries so `PluginRun.started_at`
  / `finished_at` are honest wall-clock values, not derived from
  `PluginRunResult.duration_ms` alone. Per-plugin try/except mirrors
  `PluginHost.execute_chain`'s isolation but emits a typed
  `PluginRun(status="error", ...)` on uncaught exceptions.
- `holdspeak/plugins/__init__.py` — re-exports `dispatch_window`
  + `dispatch_windows`.
- `tests/unit/test_intent_dispatch.py` (new) — 6 cases.

## Why PluginHost itself wasn't touched

`PluginHost` already implements every spec §9.4 requirement
(idempotency cache, ThreadPoolExecutor timeouts, per-plugin
try/except failure isolation, capability gating, deferred queue,
structured logging, metrics). HS-2-04's gap was the typed-bridge
orchestrator — the same pattern HS-2-03 used for scoring/transitions:
typed contract output over existing runtime infra.

## Test output

### New unit tests (this story)

```
$ uv run pytest tests/unit/test_intent_dispatch.py -q
......                                                                   [100%]
6 passed in 0.03s
```

### First-pass failures + fixes

The first run of the new tests produced two failures
(`AssertionError` on chain length) — both my test assumptions, not
implementation bugs. The `balanced` profile with a `delivery=0.9`
score yields a 5-plugin chain (`project_detector,
requirements_extractor, action_owner_enforcer, milestone_planner,
dependency_mapper`) after dedupe of base + intent chains, not the
2 I'd hand-counted. Fix: register the full chain in the idempotency
test, and use a no-active-intents score in the ordering test so the
chain stays at the 3-plugin balanced base. Implementation unchanged.

### Spec §9.4 verification gate

```
$ uv run pytest -q tests/unit/test_plugin_host.py tests/unit/test_plugin_host_idempotency.py
.......................                                                  [100%]
23 passed in 0.16s
```

The six new cases:

1. `test_dispatch_window_returns_typed_plugin_runs_for_chain` — typed records, chain order matches `preview_route` output, every record carries `window_id`/`meeting_id`/`profile` + `finished_at >= started_at`.
2. `test_dispatch_window_passes_active_intents_into_plugin_context` — the route's active-intents reach the plugin context.
3. `test_dispatch_window_idempotency_dedups_second_dispatch_mir_f_008` — second dispatch all `status="deduped"`; each stub ran once across both batches.
4. `test_dispatch_window_isolates_plugin_failure_mir_r_004` — one chain plugin raising → typed `error` record, sibling plugins still execute.
5. `test_dispatch_windows_preserves_window_order_with_typed_records` — three windows × three plugins = 9 records in document order; per-window stub call count = 3.
6. `test_dispatch_window_missing_plugin_id_surfaces_as_error_record` — unregistered plugin id → typed `error` record with `"Unknown plugin"` in `.error`; chain continues.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
913 passed, 12 skipped in 15.14s
```

Pass delta vs. HS-2-03 baseline (907 passed): **+6** (the new
`test_intent_dispatch.py` cases). Skip count unchanged at 12. Metal
excluded per the standing project memory.

## Acceptance criteria — re-checked

All checked in [story-04-plugin-host.md](./story-04-plugin-host.md).

## Deviations from plan

- Spec §9.4 listed `holdspeak/plugins/host.py` and added test files
  `test_plugin_host.py` + `test_plugin_host_idempotency.py` as edit
  targets. Both already exist (pre-HS-2 infra) and cover the entire
  Step-3 surface; this story added only the typed-output bridge that
  the new `PluginRun` contract type (HS-2-02) made possible. Editing
  `host.py` would have been scope creep.

## Follow-ups

- HS-2-05 — DB schema for `PluginRun` + `ArtifactLineage`; the
  dispatcher's typed output is what HS-2-05 will persist.
- HS-2-06 — meeting runtime calls `dispatch_windows(host,
  zip(windows, scores), profile=...)` to drive live processing.
- The dispatcher does not carry plugin **output** on `PluginRun`
  (the contract keeps output in `PluginRunResult`). HS-2-07 will wire
  output capture into `ArtifactLineage` if needed; for now the join
  is `ArtifactLineage.plugin_run_keys → PluginRun.idempotency_key`.

## Files in this commit

- `holdspeak/plugins/dispatch.py` (new)
- `holdspeak/plugins/__init__.py` (re-exports)
- `tests/unit/test_intent_dispatch.py` (new)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-04-plugin-host.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-04.md` (this file)
- `pm/roadmap/holdspeak/README.md` ("Last updated" line)
