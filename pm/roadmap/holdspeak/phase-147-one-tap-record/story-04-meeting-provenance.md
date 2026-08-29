# HS-147-04 — Meeting provenance (the event on the record)

- **Project:** holdspeak
- **Phase:** 147
- **Status:** ready
- **Depends on:** HS-147-01
- **Unblocks:** HS-147-07
- **Owner:** unassigned

## Problem

Only `title` and `principal` cross the fire seam
(`scheduled_recording_conductor.py:509` →
`web_server.py:986-991` → `runtime/meeting_glue.py:293-298`), and
the `meetings` table has no calendar column (`db/schema.py:25-50`) —
a recorded meeting cannot say which calendar event it was.

## Scope

### In (settled-design D7)

- `meetings.calendar_event_id TEXT` (nullable, additive,
  declarative reconcile).
- Thread `calendar_event_id` through the seam via an explicit
  `pending_calendar_event_id` callback attribute mirroring
  `pending_title` (counsel finding 3): `_fire` passes it, the
  `web_server.py:986-991` lambda sets the attribute,
  `meeting_glue.py:293-298` reads and persists it in
  `_start_meeting()` (`meeting_glue.py:175-361`).
- Meeting read surfaces (list/get API + MCP `meeting.get`/`.list`)
  expose the field; the Meetings surface shows a quiet origin line
  (source label + event title) on linked records — fewest words, no
  prose.
- Unlinked meetings unchanged byte-for-byte (manual record, import,
  non-event schedules).

### Out

- Follow-through schema (cards already carry `meeting_id`; the
  chain closes transitively); backfilling old meetings; any egress
  surface (all local).

## Acceptance criteria

1. A fired event-linked recording produces a meeting row carrying
   `calendar_event_id`, proven through the REAL conductor fire path.
2. The Meetings surface shows the origin line on the linked record
   and nothing on unlinked ones — shot at 1440 + 393.
3. Meeting API/MCP read paths expose the field; manual and
   non-event recording paths are regression-free.

## Test plan

Conductor→glue integration test (fire carries the id), meeting
repository/service unit tests, Meetings-surface component test +
live shots both widths.
