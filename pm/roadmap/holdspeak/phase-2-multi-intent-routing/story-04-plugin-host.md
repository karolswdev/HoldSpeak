# HS-2-04 — Step 3: Plugin host integration

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-02 (typed contracts), HS-2-03 (typed scoring)
- **Unblocks:** HS-2-06 (meeting runtime wiring), HS-2-07 (synthesis)
- **Owner:** unassigned

## Problem

Spec §9.4 calls for plugin-host execution semantics, idempotency-key
generation + duplicate suppression, timeout + failure isolation.
Audit (post-HS-2-03): `holdspeak/plugins/host.py::PluginHost` already
implements all of that — registry, `build_idempotency_key` + cache,
`ThreadPoolExecutor`-backed timeout, per-plugin `try/except` failure
isolation, capability gating, deferred queue, structured logging,
metrics. The genuine gap is the **typed-bridge orchestrator**: take
`IntentScore` + `IntentWindow`, derive the route's plugin chain, run
each plugin through the host with real wall-clock boundaries, and
return typed `PluginRun` contract records (not the runtime-only
`PluginRunResult` the host emits).

## Scope

- **In:**
  - New module `holdspeak/plugins/dispatch.py` with `dispatch_window(host, score, *, window, profile, ...)` and `dispatch_windows(host, pairs, *, profile, ...)`. Both return `list[PluginRun]`.
  - Adapter `_to_plugin_run(...)` populating `window_id`, `meeting_id`, `profile`, `started_at`, `finished_at` (real `time.time()` boundaries) from `PluginRunResult` + the window.
  - Per-plugin `try/except` mirrors `PluginHost.execute_chain`'s isolation but emits a typed `PluginRun(status="error", ...)` on uncaught exceptions (e.g. `KeyError` for unregistered plugin id).
  - Re-exports from `holdspeak/plugins/__init__.py`.
  - Unit tests at `tests/unit/test_intent_dispatch.py`: 6 cases covering chain shape, active-intents propagation, MIR-F-008 idempotency dedup, MIR-R-004 failure isolation, ordering, missing-plugin error surfacing.
- **Out:**
  - Persistence of `PluginRun` records to the DB (HS-2-05).
  - Wiring from the live meeting runtime (HS-2-06).
  - Replacing `PluginHost.execute_chain` — the dispatcher uses `host.execute` per plugin so it can wrap each call with real wall-clock boundaries; `execute_chain` stays available for callers that don't need the typed contract surface.

## Acceptance criteria

- [x] `dispatch_window` returns one `PluginRun` per plugin in the route-derived chain, in chain order.
- [x] Each `PluginRun` carries the input window's `window_id` + `meeting_id` and the resolved `profile`; `started_at` ≤ `finished_at` and `duration_ms ≥ 0`.
- [x] Dispatching the same scored window twice → second batch all `status="deduped"` (MIR-F-008); each underlying stub plugin runs exactly once.
- [x] One plugin in the chain raising → typed `PluginRun(status="error", error=...)`, sibling plugins still execute (MIR-R-004).
- [x] Unregistered `plugin_id` in the chain → typed `PluginRun(status="error")` with `"Unknown plugin"` in the error string; doesn't abort the rest.
- [x] `dispatch_windows` preserves window order; per-window `(window_id, plugin_id, transcript_hash)` keys exercise the host's idempotency naturally.
- [x] `tests/unit/test_intent_dispatch.py` ships with 6 cases, all pass.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 913 passed, 12 skipped, 0 failed in 15.14s. Pass delta vs. HS-2-03 (907): +6.

## Test plan

- **Unit:** `uv run pytest tests/unit/test_intent_dispatch.py -q` (6 cases).
- **Spec verification gate (§9.4):** `uv run pytest -q tests/unit/test_plugin_host.py tests/unit/test_plugin_host_idempotency.py` — pre-existing host tests must remain green.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- The dispatcher calls `host.execute` per plugin instead of `host.execute_chain` because the typed `PluginRun` contract carries `started_at` / `finished_at` (wall-clock), and `execute_chain` only surfaces `duration_ms`. Wrapping per-plugin gives honest timestamps without modifying the engine.
- `PluginRun` does not carry plugin **output** (the spec keeps output in the in-process `PluginRunResult`). HS-2-07 (synthesis) will wire output capture separately if needed; for now, lineage from `ArtifactLineage.plugin_run_keys → PluginRun.idempotency_key` is the join.
