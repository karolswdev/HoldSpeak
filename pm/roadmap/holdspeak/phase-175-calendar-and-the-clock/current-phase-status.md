# Phase 175 - Calendar and the Clock

**Last updated:** 2026-09-05 (late — the faces built).

## Goal

Real calendar events on the desk: the 146 adapter feeds the week's
meetings, and scheduled recordings are born from upcoming events instead
of manual cron. A meeting Watch adapter lets Rooms observe their
meetings as entities alongside GitHub and Jira. The Monday brief's
window widens to the calendar week so the owner sees what happened AND
what is coming. The calendar becomes a first-class input, not a hidden
column.

## Status

**ACTIVE 5/9 — wire done, the FOUR FACES BUILT to the ratified boards (2026-09-05, resumed on the owner's word). Branch `feat/calendar-clock`, draft PR #558 on main; 170–174 merged to main.**

**Where we are (2026-09-05, late — the faces).** Resumed on his word ("I think you could continue working out 175 no?"). Four Fedaykin face lanes built to the ratified boards in one tree with strict file ownership, each shot beside its board at 1440 + 393 and bounced until it matched: (a) the arrival's WEEK strip, NEXT with the Room token, the MEETINGS section, the orphan armed row (`story-02-shots/`); (b) Settings → Meetings' CALENDAR section on the module the hub row opens — source rows, the in-world connect well with a mic, `Snapshot`, Auto-record with `5 MIN BEFORE` and `N MATCHED THIS WEEK`; the 146-era Calendar group retired so the calendar is said once, its verbs (`Edit` · `Disable`/`Enable` · `Remove` with an in-world confirm) carried onto the new rows because a face that replaces another never loses a working verb (`story-03-shots/`); (c) the Room's real meeting Watch — created when a meeting links, backfilled once by the sweep, evaluated by the sweep, feeding SINCE YOU LOOKED (`story-04-shots/`); (d) Rhythm's Weekly brief row and the brief's THIS WEEK / SINCE FRIDAY at one gutter, `this_week` added to the section vocabulary (`story-05-shots/`). Rulings from the build are in the design's Addendum 2 (B1–B9). One scar: a lane ran `git stash` in the shared tree to measure a before-count and dropped it; ten files reverted to HEAD and were recovered from the dangling stash commit via `git fsck`; the no-tree-git-verbs law is now in `.claude/agents/opus-worker.md`. Hygiene: the census (`assets/hygiene-census-175.md`), the P2-2 snapshot-model fence PAID (local/LAN preferred, host recorded), the tz-aware lookahead default, the logged Watch-query load; four items parked in BACKLOG.md. The canonical schema snapshot regenerated (the 02 wire's join table + index + `born_from`). 08 the docs paid (thirteen markers verified against the shipped tree; the 173 drafter diagram's `PAR` alias renamed so the mermaid guard renders). The runner's walk on his desk (06, read-only, every write denied; `assets/story-06-shots/`, evidence captured with the token redacted): no calendar connected, auto-record OFF, one upcoming scheduled recording; the arrival, Settings → Meetings' CALENDAR (Connect calendar · Add · Snapshot; Auto-record OFF), a real Room's SOURCES (GH · Jira; no linked meetings so no MEETINGS row), and Rhythm (`Monday brief · DAILY 08:00 · LAST AUG 19`) all read honestly at both widths. Found on his desk, not ours to touch: two `Sprint Review · AUG 20` meetings are seed rows earlier walks (167/168) left in his real database (`m-glass-167-walk`, `m-168-walk-001`) — his to delete; the queued `Already titled` job (172) still his to Skip; the recorded-meetings row prints `0 MIN` (172's face, a counter of zero — backlog). The runner's Settings leg was re-pointed to the hub's real path (`configure-settings` → the Meetings row's Open). Counsel-on-built (assets/counsel-on-built-175.md): BOUNCE on twelve conditions, six reproduced. C1 ruled B11 (an event-born recording records at the event like every scheduled recording; the toggle is consent to record; carried to the owner). C2–C11 PAID across three fix lanes (W1 the conductor + the brief wire; W2 the arrival + the recording Cancel; W3 Settings/Room/Rhythm/the snapshot egress) — rulings B12–B15. Counsel's re-read (assets/counsel-on-built-175-reread.md): RATIFY-WITH-CONDITIONS, ten of twelve paid, six conditions riding — (1) Cancel means THIS occurrence of a recurring meeting (tombstone keyed by `(source, uid, starts_at)`), (2) every arm has its own create receipt, (3) Delete on an event-born row behaves as Cancel and never removes the tombstone, (4) per-instant local time on the DST edge (the door's strip, the Room's week, the Settings matched count), (5) the copy matches B11 and B11 is a suite test that runs both conductors, (6) the owner's attended walk — 1–5 PAID (rulings B16–B17), 6 is his. Schema 75 (`owner_cancelled_at`, `calendar_starts_at`, `calendar_event_link_suppressions`); api-surface 667 with the unlink route's consumer; the walk runner follows `arrival-this-week`. Counsel's P2 ledger parked in BACKLOG.md. Then his attended walk, 07's flip, the close (09), #558 out of draft.

Earlier (2026-09-05 21:45): 01 the design ratified by counsel (RATIFY-W-C; five conditions paid in the design addendum; canvas republished). 02–05 the wire landed with tests.

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
  - A separate arm-and-wait mode: an event-born recording behaves like
    every scheduled recording — it arms at −lead and records at the
    event; the Auto-record toggle (OFF by default) is the consent
    (ruling B11; the owner's word may flip it to arm-and-wait).

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
| HS-175-01 | The design (the calendar week, the event-born recording, the meeting Watch entity on the canvas) | done | [story-01-the-design](./story-01-the-design.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-175-02 | Calendar events on the desk (the week view, the next seam, events as material) | done | [story-02-calendar-events-on-the-desk](./story-02-calendar-events-on-the-desk.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-175-03 | Event-born scheduled recordings (auto-create from calendar events with meeting URLs) | done | [story-03-event-born-recordings](./story-03-event-born-recordings.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-175-04 | The meeting Watch adapter (MeetingWatchSource: meetings as Watch entities in a Room) | done | [story-04-the-meeting-watch-adapter](./story-04-the-meeting-watch-adapter.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-175-05 | The week brief (Monday brief window widened to the calendar week; calendar + meeting collectors) | done | [story-05-the-week-brief](./story-05-the-week-brief.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-175-06 | The walk (his desk: the event-born recording, the week brief, the meeting Watch entity) | in-progress | [story-06-the-walk](./story-06-the-walk.md) | -- |
| HS-175-07 | The hygiene lane (items from THE-TUESDAY-ARC.md section 4 that this phase's tree touches) | done | [story-07-the-hygiene-lane](./story-07-the-hygiene-lane.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-175-08 | The docs (the calendar in the architecture; the week brief in the guide) | done | [story-08-the-docs](./story-08-the-docs.md) | [evidence-story-08](./evidence-story-08.md) |
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
| Event-born recording false positives | Medium | Only events with a meeting URL auto-create recordings; the owner can cancel any armed recording; the toggle is OFF by default and is the consent to record; Cancel is final across refreshes (ruling B11) | > 50% of auto-created recordings are for non-meeting events |
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
