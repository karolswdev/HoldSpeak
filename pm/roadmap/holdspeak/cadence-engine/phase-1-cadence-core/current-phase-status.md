# Cadence Phase 1 — Cadence core

**Status:** planned (lead phase, fully storied). **Start here:** `../README.md` (the program chart —
the trust boundary, the resolved architecture decisions, and the verified seam map).

**Last updated:** 2026-06-28 (authored).

## Objective

Stand up the loop/nudge/policy **substrate** with **zero external side effects and zero LLM
dependency**, entirely off by default. After Phase 1 the runtime can, when enabled, project Open
Loops from meeting action items + pending actuator proposals, score their staleness, decide which
are due under a quiet-hours-respecting policy, and expose them on the CLI — all deterministic and
local. Surfaces (web, agent push, Telegram, briefs) build on this in later phases.

## Why it leads

Everything else asks this substrate: the web coach reads loops, the agent-blocker push is a loop
source, Telegram delivers nudges, the brief ranks loops. Get the models, the source-projection
idempotency, the scoring, and the off-switch right here and the rest is surfaces.

## The load-bearing decisions (from the chart, applied)

- **Off by default.** `CadenceConfig.enabled = False`; the `CadenceMixin` thread never starts when
  off → the runtime is byte-identical to today. Proven by a test.
- **Source-projected loops.** The collector idempotently upserts by `source_type:source_id`; user
  lifecycle state (snoozed/killed/nudge_count) is preserved across re-collection. A killed loop is
  never resurrected unless the source materially changes.
- **Daemon thread on `runtime_stop_event`**, mirroring `PluginQueueMixin` (`web_runtime.py:477`).
- **No actuators touched in Phase 1.** Pending proposals are a *read* source; cadence proposes
  nothing yet (that starts in Phase 6/7, always via the existing actuator path).

## Stories

| ID | Title | Status |
|----|-------|--------|
| CAD-1-01 | Cadence models + SQLite migrations (`cadence_*` tables, `CadenceRepository`) — **leads** | todo |
| CAD-1-02 | The collector (meeting action items + pending proposals → source-projected loops) | todo |
| CAD-1-03 | Stale-scoring v1 (deterministic, explainable) | todo |
| CAD-1-04 | Cadence policies + quiet hours + the `CadenceMixin` tick (off by default) | todo |
| CAD-1-05 | CLI: `holdspeak cadence status \| loops \| run-now` | todo |
| CAD-1-06 | Unit tests for scoring, policy, quiet hours, snooze/kill idempotency | todo |

## Where we are

Not started; fully storied. **CAD-1-01 leads** (the models + tables everything else reads/writes).
1-02/1-03 then build on it; 1-04 wires the tick + config gate; 1-05 exposes it; 1-06 locks the
behavior. The whole phase is local + deterministic + off-by-default — a green `uv run pytest -q`
and a `holdspeak cadence run-now` that prints projected loops is the bar.

## Exit criteria

- `holdspeak cadence status` / `loops` / `run-now` work locally.
- `run-now` projects loops from imported meeting actions + pending proposals, scored and ordered.
- **No external side effects exist** in the cadence package (grep proves no connector calls).
- With `CadenceConfig.enabled = False` (default), the runtime starts no cadence thread and behaves
  identically to `main` (test-proven).
- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py` green.
