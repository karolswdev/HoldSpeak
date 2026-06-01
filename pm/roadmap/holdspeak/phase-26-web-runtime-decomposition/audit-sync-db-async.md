# Audit — Sync DB calls in async handlers (HS-26-06)

**Date:** 2026-06-01. **Scope:** the extracted `holdspeak/web/routes/*` modules.

## The pattern

Every data route is an `async def` FastAPI handler that calls the **synchronous**
SQLite layer directly (`get_database()` then `db.get_meeting(...)`,
`db.list_artifacts(...)`, etc.). Count of sync-DB references by module:

| module | sync-DB call sites | async handlers |
|---|---|---|
| `activity.py` | 91 | (largest) |
| `meetings.py` | 49 | |
| `projects.py` | 34 | |
| core / dictation / pages / system | 0 | — |

(~174 sync-DB references across ~118 async handlers total.)

Because these run inside `async def`, each DB call occupies the event loop for its
duration — it is not awaited off-loop.

## Does this stall the WebSocket broadcast loop?

The broadcast path (the thing we care about for "cadence"):

- `MeetingWebServer.broadcast()` is called from the **meeting/background thread**
  and schedules the coroutine onto the server loop via
  `asyncio.run_coroutine_threadsafe(self._ws.broadcast(message), loop)`
  (`web_server.py:337`).
- `_duration_loop()` runs **on** the loop (`asyncio.create_task`) and emits a
  duration frame at a **1 Hz** cadence.

So a sync DB call in an HTTP handler can delay a pending broadcast/duration tick
by *at most the call's wall-clock duration*. The question is whether any handler's
DB work is long enough to matter against a 1 Hz cadence.

**Assessment:** No, under realistic local conditions.

- The DB is local SQLite; the routine reads here (`get_meeting`, `list_artifacts`,
  `list_meetings`, speaker/intel/project queries) are point lookups or
  `limit`-bounded lists — sub-millisecond to low-single-digit-ms in practice.
- These are **user-triggered request handlers**, not anything on the periodic
  broadcast path; they fire on navigation, not continuously.
- A few ms of loop occupancy is imperceptible against a 1 Hz duration cadence and
  event-driven broadcasts.

### Heaviest call sites (watch list, not offloaded)

- `activity.py::_activity_status_payload` → `db.list_activity_records(limit=5000)`
  (also counts records). Bounded at 5000 rows; on a very large activity ledger
  this is the most likely to grow.
- `meetings.py::api_list_meetings` with `search` → `db.search_transcripts(...)`
  (FTS over transcripts).
- `meetings.py::api_export_meeting` → `db.list_artifacts(..., limit=200)` +
  render.

None of these is on the broadcast path; all are bounded; none demonstrably stalls
the loop today.

## Decision

**Document, do not offload** — matching this phase's deferred decision
("offload only those that demonstrably stall the WebSocket broadcast loop;
default: document the blocking calls"). A full async DB rewrite is explicitly out
of scope (story §Out).

- **No offload applied.** No handler exhibits a demonstrable stall at local-SQLite
  latencies against the 1 Hz cadence, so wrapping calls in
  `asyncio.to_thread`/executor would add complexity with no measured benefit
  (and the project skips pre-measurement spikes by policy).
- **Trigger for revisiting:** if profiling on a large real DB shows a single
  handler holding the loop long enough to visibly hitch the duration ticker or WS
  events (rule of thumb: >100 ms), offload *that specific* call via
  `await asyncio.to_thread(db.<call>, ...)` and cover it with a focused test. The
  watch-list above is where to look first.

## AC coverage

- [x] Sync-DB-in-async audit **recorded** (this file).
- [x] Any offload covered by a test or a **documented rationale** — rationale for
      **no** offload documented above, with an explicit re-visit trigger.
