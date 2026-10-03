# C3 / #744 — single-pass conditions

Muad'Dib's verdict, relayed in the lane dispatch: **MERGE-WITH-CONDITIONS**.
The owner instructed: **"no further check round; pay these, prove them, merge."**
Astra session: `01a10029-d5c8-79c2-9522-6af087f3e7e0`.

1. C1: READY must count newly ready, unseen meetings. Historical summaries
   do not count. `intel_complete` / `aftercare_ready` and a durable unseen
   read supply the state; opening the meeting clears it. Fence multiple old
   summaries, one newly ready meeting, and opening it; red before green.
   Tenets 3 and 7: the owner needs a useful mark for work he has not seen.
2. C2: merge `origin/main` (the dispatch names `fc12a18d`, including #743),
   preserve both atlas branches, regenerate the API, boundary and graph
   references, and resolve source anchors against the merged source.

C3-W remains Muad'Dib's: Dock CSS and overflow at 1440/393, SENT time,
and removing `DOCK_PRESS_MS` from `ChairDesk.tsx`. Story 13 stays
`in-progress`; its done flip requires C3-W.

The People time question is separate: H-B4's brief returns
`next_one_on_one` as an event object with `starts_at` copied from the
calendar projection (`holdspeak/services/people_service.py`,
`_calendar_event_view`). `holdspeak/calendar_ingest.py` rejects date-only
`DTSTART` values and emits UTC ISO timestamps through `_utc_iso`. The
confirmed relationship detail exposes the same timestamp as a string.
Thus H-B4 does not supply a date-only value to `formatDockTime`.

## Execution record

C1 and C2 are paid, including final integration with main `e9b01e227` / C6 after the requested `fc12a18d` / C8. Astra’s execution verdict is MERGE under the owner’s explicit single-pass ruling; final proof and the failure ledger are recorded
in [the lane report](../lane-13-astra.md).

The first three worker spawns used full-history forks and inherited Astra
despite the requested model override. Astra stopped those sessions and
re-dispatched fresh contexts. The replacement session records confirm
`gpt-5.6-luna`, reasoning `xhigh`: C1 `01a1002f-e1a5-7351-af3a-ac696674838b`,
C2 `01a10030-6148-73d3-ac1d-f63b627beaff`, and H-B4 rebase
`01a10030-b0ad-75f3-8385-dd7852daef31`.
