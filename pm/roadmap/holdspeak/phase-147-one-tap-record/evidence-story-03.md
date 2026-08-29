# Evidence - HS-147-03

- **Story:** HS-147-03 - The honest follow (reconciliation + snapshot identity)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T06:27:02Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_event_linked_reconcile.py tests/unit/test_calendar_snapshot_production_path.py tests/unit/test_event_linked_arm.py tests/unit/test_calendar_ingest_conductor.py tests/unit/test_calendar_ingest.py tests/unit/test_calendar_events_repository.py tests/unit/test_calendar_snapshot_service.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 234becdf8d890e4a5ab01fc9f376968ce2156539

```text
........................................................................ [ 80%]
..................                                                       [100%]
90 passed in 24.55s
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder's word: 89+ focused tests re-run and
read (now 91 with the story-02 suppression pins in the shared arm
file). R1/R2/R3 land inside the ingest tick, scoped per-source
(D3a); X1 enforced by the idle-only working set with deliberate
arming/recording immunity tests; D3b taken as the
idempotent-with-caught-errors path (per-schedule try/except + list
failure guard — a reconcile crash cannot kill the ingest tick; a
dangling link self-heals next refresh). The counsel's R1
refresh-in-place amendment is implemented and pinned (end-time-only
extension refreshes duration under the same id). Snapshot UIDs are
content-deterministic through generate_ics and proven round-trip
through the real parser.

**Deviation rulings (orchestrator tie-breaker):**
- No arm→shift→fire proof against the real recording conductor —
  ACCEPTED: the conductor lifecycle is already proven in story 01's
  test; the rebind only rewrites next_fire_at, and the conductor
  fires on next_fire_at unconditionally. Story 07's walk still
  exercises a real near-time fire.
- The pre-replace-snapshot fallback chain (snapshot →
  next_fire_at+60 → created_at) can, in the rare case of a failed
  pre-read on a fire-now arm, degrade an R2 rebind to an R3 cancel.
  LEDGERED: requires a DB read failure inside a single tick; the
  cancel is loud (event_removed) and re-armable, never silent.
