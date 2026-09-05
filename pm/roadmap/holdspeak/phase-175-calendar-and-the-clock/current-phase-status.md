# Phase 175 - Calendar and the Clock

**Last updated:** 2026-09-05.

## Goal

Real calendar events on the desk: the 146 adapter feeds the week's
meetings, and scheduled recordings are born from upcoming events instead
of manual cron. A meeting Watch adapter lets Rooms observe their
meetings as entities alongside GitHub and Jira. The Monday brief's
window widens to the calendar week so the owner sees what happened AND
what is coming. The calendar becomes a first-class input, not a hidden
column.

## Status

**ACTIVE 0/9 — STACKED on 174 (PR #557) on 173 (#556) on 172 (#555) on 171 (#554) on 170 (#553); branch `feat/calendar-clock` off `feat/reach`.**

**Depends on:** Phase 171 merged (the cadence row drives the brief's
recurrence and the scheduled-recording conductor's ticks).

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday, 07:55. The brief in the shade says: "This week: 4 meetings,
12 Watch items changed, 2 commitments due Fri. Yesterday: Standup
produced 2 decisions, 1 commitment. Next: Architecture Review at 10:00
(recording scheduled)." He never created the recording; it was born
from the calendar event he accepted in Outlook. Before the review he
opens the Room; SINCE YOU LOOKED shows the meeting's Watch entity with
its decisions from last time. The calendar gave the desk its clock.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
calendar_events 0 on his desk despite the ingest pipeline existing
(the 146 adapter is wired but the desk never reads the events as
material); scheduled recordings are cron-only (the calendar_event_id
column exists at db/scheduled_recordings.py:34 but auto-creation from
events is unimplemented); the Monday brief ran ONCE (1839 items on
2026-08-24) and is day-windowed (monday_brief_service.py:89-108),
never week-windowed; no MeetingWatchSource exists (watch_sources.py
has only GitHubWatchSource:58 and JiraWatchSource:294).

## Scope

- In:
  - Calendar events as readable desk material: the `calendar_events`
    table (schema.py:3490-3506, populated by calendar_ingest_conductor.py)
    surfaces in a WEEK view on the desk and in the Room as "what's
    coming"; the `next` seam (project_service.py:426) returns the next
    event alongside scheduled recordings.
  - Event-born scheduled recordings: upcoming calendar events with a
    meeting URL auto-create an armed `ScheduledRecording` linked via
    `calendar_event_id` (db/scheduled_recordings.py:34); the conductor
    arms and disarms on the event's time; the owner can override or
    cancel.
  - The meeting Watch adapter: a `MeetingWatchSource` that makes
    meetings and their extracted decisions/commitments (Phase 172)
    observable as Watch entities in a Room; the same entity grammar as
    GitHub PRs and Jira issues.
  - The Monday brief week-widened: `compute_window`
    (monday_brief_service.py:89-108) expands to the full calendar week;
    the brief's collectors read `calendar_events` for what is coming
    and the meeting Watch entities for what happened; the frame says
    "This week" not "Since yesterday."
  - The design on the library before build (canvas at 1440 + 393).
  - His walk on his desk: a recording born from an event, the week
    brief in the shade, the meeting Watch entity in the Room.
- Out:
  - New calendar ingest sources (the 146 adapter is sufficient; the
    snapshot adapter at calendar_snapshot_service.py is already shipped).
  - Calendar write-back (creating events from the desk; Article V:
    watching is free, creating events is a future phase).
  - Real-time calendar sync (the conductor's periodic refresh is
    sufficient; push-based sync is a future phase).
  - Integration with external calendar APIs beyond ICS (Google
    Calendar API, Exchange API; the owner's calendar exports ICS).
  - Recording auto-start (the recording is armed, the owner starts it;
    Article IV: voice arms, it does not fire).

## Exit criteria (evidence required)

- [ ] Calendar events from the ingest pipeline appear on the desk as
      readable material; the `next` seam returns the next event; the
      owner's desk shows > 0 calendar_events.
- [ ] A calendar event with a meeting URL auto-creates an armed
      ScheduledRecording linked via calendar_event_id; the conductor
      arms it on time.
- [ ] MeetingWatchSource exists; meetings and their
      decisions/commitments are observable as Watch entities in a Room.
- [ ] The Monday brief's window covers the full calendar week; the
      brief reads calendar_events for what is coming and meeting Watch
      entities for what happened.
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build.
- [ ] His walk on his desk: a recording born from an event, the week
      brief in the shade, the meeting Watch entity in the Room; his
      word.
- [ ] Zero egress (Article III); every operation receipted (Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-175-01 | The design (the calendar week, the event-born recording, the meeting Watch entity on the canvas) | in-progress | [story-01-the-design](./story-01-the-design.md) | -- |
| HS-175-02 | Calendar events on the desk (the week view, the next seam, events as material) | backlog | [story-02-calendar-events-on-the-desk](./story-02-calendar-events-on-the-desk.md) | -- |
| HS-175-03 | Event-born scheduled recordings (auto-create from calendar events with meeting URLs) | backlog | [story-03-event-born-recordings](./story-03-event-born-recordings.md) | -- |
| HS-175-04 | The meeting Watch adapter (MeetingWatchSource: meetings as Watch entities in a Room) | backlog | [story-04-the-meeting-watch-adapter](./story-04-the-meeting-watch-adapter.md) | -- |
| HS-175-05 | The week brief (Monday brief window widened to the calendar week; calendar + meeting collectors) | backlog | [story-05-the-week-brief](./story-05-the-week-brief.md) | -- |
| HS-175-06 | The walk (his desk: the event-born recording, the week brief, the meeting Watch entity) | backlog | [story-06-the-walk](./story-06-the-walk.md) | -- |
| HS-175-07 | The hygiene lane (items from THE-TUESDAY-ARC.md section 4 that this phase's tree touches) | backlog | [story-07-the-hygiene-lane](./story-07-the-hygiene-lane.md) | -- |
| HS-175-08 | The docs (the calendar in the architecture; the week brief in the guide) | in-progress | [story-08-the-docs](./story-08-the-docs.md) | -- |
| HS-175-09 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-09-the-close](./story-09-the-close.md) | -- |

## Where we are

**2026-09-05 21:20 — ACTIVATED, STACKED.** Under the standing goal the
faces build to counsel-ratified boards and his word gates the MERGE.
Twelve boards for D2 (a)–(e) on the canvas
(https://claude.ai/code/artifact/113102aa-7bc9-4508-a334-79e22d542155),
counsel reading; the wire lanes (02 · 03 · 04/05), the docs (08) and the
runner (06) drafting in this worktree. Merge order stays his: #553 → #554 → #555 → #556 → #557 → 175's.

Earlier: 
PLANNED. Waiting for Phase 171 to merge (the cadence row drives the
brief's recurrence and the conductor's ticks).

The recon is complete:

**Calendar ingest today:** the pipeline exists and works.
`calendar_ingest.py` parses ICS into `CalendarEventCandidate` objects;
`calendar_ingest_conductor.py:146+` runs the periodic refresh; the
`calendar_events` table (schema.py:3490-3506) is multi-source since
HS-146-01. The CalendarSnapshotService
(calendar_snapshot_service.py, HS-146-07) is the vision-based adapter
the arc references. But on the owner's desk: calendar_events 0 --
the pipeline runs but the desk never reads the events as material.

**Scheduled recordings today:** cron-based only.
`ScheduledRecording` (db/scheduled_recordings.py:16) has a
`calendar_event_id` column (line 34) and `calendar_uid` and
`calendar_source_id`, but auto-creation from calendar events is
unimplemented. The conductor
(scheduled_recording_conductor.py) arms and disarms on cron
expressions.

**Monday brief today:** day-windowed, not week-windowed.
`compute_window()` (monday_brief_service.py:89-108) uses a 1-day
lookback (3 on Monday back to Friday 17:00). The brief has zero
calendar-event awareness. It ran once (1839 items on 2026-08-24) and
never again.

**Watch sources today:** only GitHubWatchSource (watch_sources.py:58)
and JiraWatchSource (watch_sources.py:294). No MeetingWatchSource
exists. Meetings are not observable as Watch entities.

**The `next` seam:** project_service.py:426 mentions "next scheduled
recording or calendar event" -- a comment naming the intent, not a
full implementation.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| ICS refresh latency | Low | The conductor's periodic refresh (15 min default) is sufficient; the calendar is not real-time; stale-for-one-tick is acceptable | Stale event > 2 ticks observed; the owner misses a meeting that changed |
| Event-born recording false positives | Medium | Only events with a meeting URL auto-create recordings; the owner can cancel any armed recording; the recording is ARMED, not started (Article IV) | > 50% of auto-created recordings are for non-meeting events |
| MeetingWatchSource entity shape mismatch | Low | Meetings have title, date, participants, decisions, commitments; the entity shape maps to the existing Watch entity grammar (title, status, assignee, updated_at) | The Watch entity shape cannot express meeting semantics without a schema change |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- The exact calendar week boundary (Monday 00:00 to Sunday 23:59 vs
  the owner's work-week preference) -- decided at design time.
- Whether the meeting Watch adapter surfaces individual decisions as
  separate entities or rolls them into the meeting entity -- decided
  at design time from the Room's SINCE YOU LOOKED grammar.
- Whether event-born recordings inherit the calendar event's title or
  get a separate name -- decided at design time.
