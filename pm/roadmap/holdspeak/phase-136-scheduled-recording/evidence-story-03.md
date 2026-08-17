# Evidence - HS-136-03

- **Story:** HS-136-03 - The Chair surface
- **Status:** done
- **Date:** 2026-08-17

## Proof

### Captured run — 2026-08-17T06:27:03Z

- **Command:** `uv run python scripts/schedule_walk_hs136.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 305f41ed73d5b65725c7f132fa6681222ec1fb1f

```text
  hub pid=6162 home=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/hs136-walk-ujspfm_c port=53402
  PASS  seed schedule via POST /api/scheduled-recordings  status=201

== ===== viewport 1440x900 ===== ==

== schedule create control @1440 ==
  PASS  chair rendered
  PASS  Schedule button on hero
  PASS  create window opened
  PASS  a text field is focused in the create window  tag=INPUT label=Title
  PASS  speak-to-fill mic present in the create window
  SHOT  schedule-create-window-1440.png  in-world create control: title+mic, mode, datetime, duration
  PASS  zero console errors  schedule create control @1440  []

== meetings lane SCHEDULED entry @1440 ==
  PASS  meetings lane present
  PASS  SCHEDULED badge in the Meetings lane
  PASS  scheduled entry names its next fire
  SHOT  meetings-scheduled-entry-1440.png  Meetings lane: a SCHEDULED recording with next-fire time
  PASS  zero console errors  meetings scheduled entry @1440  []

== ===== viewport 393x900 ===== ==

== schedule create control @393 ==
  PASS  chair rendered
  PASS  Schedule button on hero
  PASS  create window opened
  PASS  a text field is focused in the create window  tag=INPUT label=Title
  PASS  speak-to-fill mic present in the create window
  SHOT  schedule-create-window-393.png  in-world create control: title+mic, mode, datetime, duration
  PASS  zero console errors  schedule create control @393  []

== meetings lane SCHEDULED entry @393 ==
  PASS  meetings lane present
  PASS  SCHEDULED badge in the Meetings lane
  PASS  scheduled entry names its next fire
  SHOT  meetings-scheduled-entry-393.png  Meetings lane: a SCHEDULED recording with next-fire time
  PASS  zero console errors  meetings scheduled entry @393  []

== RESULT ==
  PASS x21   FAIL x0   SHOTS x4
  shot  schedule-create-window-1440.png  in-world create control: title+mic, mode, datetime, duration
  shot  meetings-scheduled-entry-1440.png  Meetings lane: a SCHEDULED recording with next-fire time
  shot  schedule-create-window-393.png  in-world create control: title+mic, mode, datetime, duration
  shot  meetings-scheduled-entry-393.png  Meetings lane: a SCHEDULED recording with next-fire time
```

## Orchestrator verification (the done call)

- **Live screenshot walk** (`scripts/schedule_walk_hs136.py`, 1440 + 393,
  captured above): 21 checks pass, 0 fail, 4 shots in `assets/walk/`.
  Proves the DeskWindow create control (title focused, speak-to-fill mic,
  mode/when/duration, ember Schedule verb) and the Meetings-lane
  SCHEDULED entry with a correct relative next-fire time, at both widths,
  zero console errors.
- **The walk caught what vitest could not** (mocked data hides these):
  1. `next_fire_at` rendered as "JAN 21 09:22" (1970) — a seconds-vs-ms
     serialization bug; fixed by serializing all five epoch timestamp
     fields as ISO-8601 strings in `_schedule_dict`.
  2. The six `scheduled_recording.*` frames registered but flagged
     "wired nowhere" by `test_realtime_frame_registry` — fixed: the
     conductor emits via `broadcast("...")` and the hero consumes via
     literal `subscribe("...")`, both scanner-recognized.
  3. `ScheduleCreateWindow` error copy too terse for the product-copy
     law (`failure-missing-facts`) — fixed to state retained work + next
     action.
  4. API-surface manifest drift from the new client fetches — regenerated.
- **Full suite** (isolated HOME, `-n auto`): 5923 passed, 0 failed. Two
  concurrency failures seen in an earlier run
  (`test_device_recording_tick`, `test_node_link_two_process`) were
  confirmed pre-existing flakes (2/2 serial green), not regressions.
- Focused vitest: 84 passed across the slice, CaptureHero, MeetingsLane,
  and ChairHome suites. The arming countdown's transient state is proven
  by the CaptureHero suite and will be proven end-to-end on real
  hardware in HS-136-04's live-metal walk.

## Shots

- `assets/walk/schedule-create-window-{1440,393}.png` — the in-world
  create control.
- `assets/walk/meetings-scheduled-entry-{1440,393}.png` — the Meetings
  lane SCHEDULED entry with next-fire time.
