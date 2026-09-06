# HS-175-03 — Event-born scheduled recordings

- **Project:** holdspeak
- **Phase:** 175
- **Status:** done
- **Depends on:** HS-175-02
- **Unblocks:** HS-175-06
- **Owner:** unassigned

## Problem

Scheduled recordings today are cron-based only. The `ScheduledRecording`
model (db/scheduled_recordings.py:16) has a `calendar_event_id` column
(line 34) and `calendar_uid` and `calendar_source_id`, but auto-creation
from calendar events is unimplemented. The owner must manually create a
recording for every meeting. The arc says: "scheduled recordings born
from events" — a calendar event with a meeting URL should automatically
arm a recording.

## Scope

- In:
  - When the calendar ingest conductor refreshes and finds an upcoming
    event with a `meeting_url`, it auto-creates an armed
    `ScheduledRecording` linked via `calendar_event_id`,
    `calendar_uid`, and `calendar_source_id`.
  - The recording inherits the event's title and time; the conductor
    arms it at the event's `starts_at` and disarms at `ends_at`.
  - The owner can override (change title, time) or cancel any
    event-born recording without affecting the calendar event.
  - Idempotent: re-ingesting the same event does not create duplicate
    recordings (keyed by `calendar_uid` + `calendar_source_id`).
  - The recording row on the desk shows provenance: "From: Standup
    (Outlook)" with the calendar source chip.
  - The recording arms at `starts_at − lead` and records at the event
    like every scheduled recording; the Auto-record toggle (OFF by
    default) is the owner's standing consent (ruling B11); Cancel is
    final across refreshes.
- Out:
  - An arm-and-wait mode (the built behaviour records at the event like
    every scheduled recording — ruling B11; his word may flip it).
  - Creating calendar events from the desk (write-back).
  - Recordings for events without a meeting_url (those are not
    meetings).

## Acceptance criteria

- [ ] A calendar event with a meeting_url auto-creates an armed
      ScheduledRecording linked via calendar_event_id (arms at
      −lead, records at the event; the toggle is the consent — B11).
- [ ] The recording inherits the event's title and time; the
      conductor arms at starts_at, disarms at ends_at.
- [ ] Override and cancel work without affecting the calendar event.
- [ ] Re-ingesting the same event does not create a duplicate
      recording (idempotent by calendar_uid + calendar_source_id).
- [ ] The recording row shows provenance: the calendar source chip
      (Article III: the source is local, the chip names it).
- [ ] Every auto-creation is receipted (Article XI).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k event_born_recording`
  - Event with meeting_url creates a recording; event without does not.
  - Re-ingest of same event does not duplicate.
  - Override and cancel do not affect the calendar event row.
  - The conductor arms at starts_at and disarms at ends_at.
- Integration: the rig seeds an ICS source with two events (one with
  meeting_url, one without), runs the conductor refresh, and verifies
  one recording is created with correct provenance.
- Manual: the owner connects a calendar; an upcoming meeting auto-creates
  an armed recording visible on the desk.

## Notes / open questions

- The existing `scheduled_recording_conductor.py` arms and disarms on
  cron expressions. The event-born path is a second arming source: the
  conductor checks both cron-based and event-based recordings on each
  tick.
- Events that are cancelled or rescheduled in the calendar: the next
  ingest refresh should update or cancel the linked recording. Propose:
  if the event disappears from the ICS, the linked recording is
  disarmed with a "calendar event removed" reason.
