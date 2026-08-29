# Evidence - HS-147-04

- **Story:** HS-147-04 - Meeting provenance (the event on the record)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T06:28:15Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) uv run --python 3.13.11 pytest -q tests/unit/test_event_linked_provenance.py tests/unit/test_scheduled_recording_conductor.py tests/unit/test_db.py && (cd web && npx vitest run src/pages/cores/history/__tests__/catalogRailOriginLine.test.tsx)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 722e8459b801281786ccbcdbcdc0467d21cdd88d

```text
........................................................................ [ 52%]
.................................................................        [100%]
137 passed in 34.62s

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  1 passed (1)
      Tests  4 passed (4)
   Start at  00:28:50
   Duration  559ms (transform 163ms, setup 40ms, import 242ms, tests 26ms, environment 178ms)
```

## Orchestrator triage note (2026-08-29)

Verified beyond the builder's word: 137 Python + 34 web focused
green re-run and read. The thread is the explicit
`pending_calendar_event_id` attribute mirroring `pending_title`
exactly as the counsel's D7 amendment demanded (set by the
web_server lambda, read+cleared under state_lock in meeting_glue,
persisted through the meetings repository); the conductor fire test
proves sched.calendar_event_id crosses the seam; the glue-level
stub-law test proves it lands on the meetings row. Enrichment is
server-side (`_enrich_calendar_origin`) with honest degradation —
a vanished event row yields absent fields, never a dangling error,
deliberately tested. MCP needed no schema change (the field rides
the service dict passthrough). Non-event paths byte-identical
(pending-absent test).

**Honest deferral:** the LIVE origin-line shot (1440+393) rides
story 07's walk, where a real near-time fire produces a linked
meeting — the component test pins the render
(`data-meeting-origin="calendar-event"`) meanwhile. Named here so
the walk cannot skip it.

**Guard duty discharged at the wave level:** the census pin drift
this story's models edits caused (1122→1123 etc.) was remapped and
shipped with story 02's commit; both censuses 18/18 green at this
capture.
