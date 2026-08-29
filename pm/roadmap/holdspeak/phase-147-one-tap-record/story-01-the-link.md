# HS-147-01 — The link (schema + arm verb, server side)

- **Project:** holdspeak
- **Phase:** 147
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-147-02, HS-147-03, HS-147-04
- **Owner:** unassigned

## Problem

No code path connects a calendar event to a recording
(audit-census.md, plane 5): `scheduled_recordings` has no link
columns (`db/schema.py:3354-3375`), the create route accepts no
event reference (`web/routes/scheduled_recordings.py:66-87`), and
nothing guards against double-arming.

## Scope

### In (settled-design D1, D2)

- Additive columns per D1: `calendar_event_id` / `calendar_uid` /
  `calendar_source_id` on `scheduled_recordings`
  (`db/schema.py:3354-3373`, declarative reconcile), dataclass
  fields (`db/scheduled_recordings.py:16-33`), partial unique index
  for invariant L1.
- `ScheduledRecordingService.create_schedule()`
  (`services/scheduled_recording_service.py:158-199`) accepts
  optional `calendar_event_id` and computes title / one_shot /
  enabled / tz / duration (remainder rule for in-progress events;
  480-min cap) / `next_fire_at = starts_at − 60 s` per D2.
  fromisoformat/astimezone only.
- Named refusals through the route and MCP:
  `calendar_event_not_found`, `event_already_ended`,
  `event_already_armed`.
- `POST /api/scheduled-recordings` body + MCP
  `scheduled_recording.create` (`mcp/tools.py:380-392`) accept
  `calendar_event_id`; list/get responses expose the link fields.
- `DoorService._calendar_event_item()`
  (`services/door_service.py:200-218`) projects
  `armed_schedule_id` by joining enabled schedules on
  `calendar_event_id` (the read side story 02 renders).
- Guard/census upkeep: api-surface manifest if the route shape
  regenerates; register any new one-path/capability sites WITH
  attribution comments (the census guards catch new seams — that is
  a feature).

### Out

- All web UI (02); reconciliation (03); meeting provenance (04).

## Acceptance criteria

1. One tap's worth of API — `POST /api/scheduled-recordings
   {calendar_event_id}` alone — yields an enabled one-shot schedule
   whose title/times/duration match the event, computed server-side.
2. An in-progress event arms for the remainder and fires on the
   next conductor tick; an ended event refuses by name.
3. A second arm of the same event refuses `event_already_armed`;
   after the first reaches a terminal outcome the event is armable
   again.
4. `/api/door` upcoming items carry `armed_schedule_id` when a live
   link exists.
5. The full scheduled-recording lifecycle (arm → countdown → fire →
   auto-stop → terminal advance) is exercised against the REAL
   conductor with fakes only at the engine-factory level (the stub
   law).

## Test plan

Focused: `tests/` scheduled-recording service + route suites
(extend in place), new arm-from-event cases (compute rules, the
three refusals, L1 uniqueness, remainder rule, lead), door service
projection test. Conductor lifecycle integration test with a
near-immediate linked event.
