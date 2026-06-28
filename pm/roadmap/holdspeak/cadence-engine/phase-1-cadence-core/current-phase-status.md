# Cadence Phase 1 — Cadence core

**Status:** done (sim/local-proven; CI green). **Start here:** `../README.md` (the program chart —
the trust boundary, the resolved architecture decisions, and the verified seam map).

**Last updated:** 2026-06-28 (Phase 1 complete: all six stories built + tested; the substrate
projects scored loops from meetings + pending proposals, off by default, no external side effects).

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
| CAD-1-01 | Cadence models + SQLite migrations (`cadence_*` tables, `CadenceRepository`) — **leads** | done |
| CAD-1-02 | The collector (meeting action items + pending proposals → source-projected loops) | done |
| CAD-1-03 | Stale-scoring v1 (deterministic, explainable) | done |
| CAD-1-04 | Cadence policies + quiet hours + the `CadenceMixin` tick (off by default) | done |
| CAD-1-05 | CLI: `holdspeak cadence status \| loops \| run-now` | done |
| CAD-1-06 | Unit tests for scoring, policy, quiet hours, snooze/kill idempotency | done |

## Where we are

**Phase 1 is complete (all six stories done, CI green).** The substrate works end-to-end:
`holdspeak cadence run-now` projects scored Open Loops from meeting action items + pending actuator
proposals, ordered by staleness, with low-confidence extractions suppressed as quiet `needs_review`
loops — entirely local, deterministic, off by default, no external side effects.

- **CAD-1-01** — `cadence_*` tables (`SCHEMA_VERSION 2→3`, snapshot regenerated), models,
  `CadenceRepository` (source-projected; killed-stays-killed).
- **CAD-1-02** — `LoopCollector` over meeting actions + pending proposals; `resolve_project`;
  idempotent upsert; `close_missing` on source-gone.
- **CAD-1-03** — deterministic, explainable `score_loop` (+ `ScoreBreakdown`).
- **CAD-1-04** — `CadenceConfig` (off by default, `pressure`/quiet-hours), `default_policies`,
  the pure `due_loops` scheduler, `CadenceService.tick`, and the `CadenceMixin` daemon-thread tick
  wired into `WebRuntime.run()` **only when enabled** (byte-identical when off; thread joined on stop).
- **CAD-1-05** — `holdspeak cadence status | loops | run-now` (`--json`, `--all`).
- **CAD-1-06** — the no-external-side-effects guard + off-by-default gate + determinism tests.

**Proof:** 37 cadence tests green (`tests/unit/test_cadence_*` + `tests/integration/test_cadence_*`);
230 config/doctor/schema/cadence tests green; the schema migration + config round-trip verified.

**Next: Phase 2 (the web coach surface)** — `/api/cadence/*` + a `/cadence` page that reads this
substrate (loops, evidence deep-links, snooze/kill/close, egress badges).

## Exit criteria

- `holdspeak cadence status` / `loops` / `run-now` work locally.
- `run-now` projects loops from imported meeting actions + pending proposals, scored and ordered.
- **No external side effects exist** in the cadence package (grep proves no connector calls).
- With `CadenceConfig.enabled = False` (default), the runtime starts no cadence thread and behaves
  identically to `main` (test-proven).
- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py` green.
