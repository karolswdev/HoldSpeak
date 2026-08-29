# Evidence - HS-147-02

- **Story:** HS-147-02 - The tap (rail verb + armed state, web)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T06:25:37Z

- **Command:** `bash -c HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright uv run --python 3.13.11 pytest -q tests/e2e/test_hs147_one_tap_glass.py tests/unit/test_event_linked_arm.py tests/unit/test_door_read_model.py tests/unit/test_door_routes.py tests/unit/test_door_transport_parity.py tests/unit/test_door_mcp.py && (cd web && npx vitest run src/desk/chair/lanes/DoorBoardLane.test.tsx src/desk/store/__tests__/scheduledRecordingSlice.test.ts)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 942e79e0cd237ae81098f39f1e480b87d3bbcf57

```text
...............................................                          [100%]
47 passed in 17.37s

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  2 passed (2)
      Tests  41 passed (41)
   Start at  00:25:55
   Duration  1.33s (transform 324ms, setup 88ms, import 479ms, tests 602ms, environment 382ms)
```

## Orchestrator triage note (2026-08-29)

Verified on real glass beyond the builder's word: the NEW e2e proof
(tests/e2e/test_hs147_one_tap_glass.py, orchestrator-authored
verification harness) drives a REAL tap on RECORD THIS through the
story-01 route on a live hub — armed chip appears, server truth
asserted (one_shot, enabled, linked id), two-beat cancel returns the
row, and the refusal leg is HONEST: an out-of-band arm leaves the row
stale, the tap hits the live L1 guard, and ALREADY ARMED renders
in-flow (shot rail-refusal-1440.png). Fresh context for the 393 leg
(walk-law). Both existing Door glass files green serially (11/11)
under the new row geometry. Shots eyeballed AND cross-read by the
orchestrator: the 60s lead is visible (schedule 1h58m vs event 1h59m
in the pre-ruling shot).

**Design ruling made from the cross-read (decision log):** the armed
event initially rendered TWICE on the rail (its EVENT row + the
linked schedule as a near-duplicate SCHEDULED RECORDING row a minute
earlier). Ruled: one intent, one row — a linked schedule is
suppressed from the schedules half while its event is in the
projection (the event row wears ARMED); if the event leaves the
projection the schedule row reappears (pending work is never
hidden). Surgical fix in door_service._upcoming with a unit pin +
glass assertion; exhibit re-shot after the fix.

**Deviation rulings:** DELETE (not /cancel) disarms an idle linked
one-shot — correct authority split, the countdown cancel route stays
for arming-state; the component owning its apiFetch error path
matches the DoorCard verb precedent — accepted.

Also rides this commit: the guard remaps from the wave (capability
census extract_via_router 574→592; routing census models pins
1122→1123, 683→684, 1121→1122 — all pure 1:1 line-drift, verified
matched; censuses 18/18 green).
