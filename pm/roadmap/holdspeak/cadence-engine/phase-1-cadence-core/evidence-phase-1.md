# Evidence — Cadence Phase 1 (cadence core)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase1-core`.

## What shipped (all six stories)

| Story | Files | Proof |
|-------|-------|-------|
| CAD-1-01 | `db/core.py` (cadence_* tables, v2→3), `cadence/models.py`, `db/cadence.py`, `db/__init__.py` | `tests/integration/test_cadence_store.py` (9) |
| CAD-1-02 | `cadence/collector.py`, `cadence/projects.py` | `tests/integration/test_cadence_collector.py` (5) |
| CAD-1-03 | `cadence/scoring.py` | `tests/unit/test_cadence_scoring.py` (6) |
| CAD-1-04 | `config.py` (`CadenceConfig`), `cadence/policies.py`, `cadence/scheduler.py`, `cadence/service.py`, `runtime/cadence.py`, `web_runtime.py` | `tests/unit/test_cadence_scheduler.py` (8) |
| CAD-1-05 | `commands/cadence.py`, `main.py` | `tests/unit/test_cadence_cli.py` (5) |
| CAD-1-06 | the guard | `tests/unit/test_cadence_guard.py` (4) |

## The substrate, demonstrated

A local end-to-end run (a seeded meeting with two action items + one pending GitHub-issue proposal):

```
Tick @ 2026-06-28T10:00:00
  projected: 3   open: 3   due now: 2
  Due to nudge (highest staleness first):
     16.8  Create issue: watchdog around intel queue   (proposal)
     12.8  File the watchdog issue                      (meeting_action)
   (-1.2  Maybe revisit the retry budget — needs_review, SUPPRESSED, not due)
```

The proposal (awaiting approval) outranks the owned+due action; the unreviewed/low-confidence
action becomes a quiet `needs_review` loop that is surfaced but **never pushed**. A second tick
re-projects to the same 3 loops (idempotent, no dupes). Completing an action closes its loop;
killing a loop survives re-collection.

## The trust boundary, enforced

- **Off by default:** `Config().cadence.enabled is False`; `WebRuntime.run()` starts the
  `CadenceMixin` thread only when enabled and joins it on stop — byte-identical when off.
- **No external side effects:** `test_cadence_package_has_no_external_side_effects` greps the whole
  `holdspeak/cadence/` package and fails on any `record_proposal`/`transition_proposal`/connector/
  network/`subprocess`/`tmux` reference. The collector reads proposals via
  `db.actuators.list_proposals` only.
- **Deterministic:** scoring + scheduling take an injected `now` (no clock/randomness inside).

## Proof

- `uv run pytest -q tests/unit/test_cadence_*.py tests/integration/test_cadence_*.py` → **37 passed.**
- `uv run pytest -q tests/unit/ -k "config or doctor or schema or cadence"` → **230 passed** (the
  `SCHEMA_VERSION 2→3` bump + the new `CadenceConfig` round-trip + snapshot are clean).
- Config round-trip: `cadence` persists in the saved JSON, `enabled=False` by default.
