# Calendar and the Clock -- the settled design (Phase 175, story 01)

> **DRAFT -- pending 171.**

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 6, "Phase 175"):
Tuesday 07:55, the brief in the shade says "This week: 4 meetings, 12
Watch items changed, 2 commitments due Fri." He never created the
recording for the Architecture Review at 10:00 -- it was born from the
calendar event he accepted in Outlook. Before the review he opens the
Room; SINCE YOU LOOKED shows the meeting's Watch entity with its
decisions from last time. The calendar gave the desk its clock.

The face canon binds (docs/internal/UX-CANON.md); the Door's, the
Arrival's, the Heartbeat's, the Loop Closes', and the Steward's grammar
(Phases 169--173) are the ratified precedent.


> **ON THE CANVAS (2026-09-05)** — twelve boards published at
> https://claude.ai/code/artifact/113102aa-7bc9-4508-a334-79e22d542155 ;
> counsel reading; faces build to the ratified boards under the standing
> goal; **his word gates the merge** (stacked on 174 #557).

## D0 -- the Tuesday moment

Monday 07:55. The arrival reads:

    NEXT . STANDUP . 10:00 . ROOM Q4 PLATFORM

The WEEK strip under the headline shows five day tokens (MON--FRI);
today is accented; Monday has two dots (two meetings), Thursday has one.
Three meetings this week touch his Rooms; each carries its Room name as
a muted token. The standup's recording armed itself at 09:55 -- five
minutes before the event's `starts_at`. He never created the recording;
the calendar event had a meeting URL; the conductor auto-created the
armed recording on its last refresh.

The week brief on Monday reads the calendar week, not yesterday:
"This week: 4 meetings, 12 Watch items changed, 2 commitments due Fri.
Next: Standup at 10:00 (recording armed)." In the Room, SOURCES shows
`MEETINGS . 2 THIS WEEK . NEXT THU 14:00`.


## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| The calendar is read where it lives | Constitution Article III | The 146 adapter reads ICS from a local file path or an HTTPS URL the owner pasted (integrations.py:18-26); no OAuth flow, no API key, no calendar leaves the machine; the snapshot adapter (calendar_snapshot_service.py) extracts from screenshots via vision -- local model |
| Reading a calendar is free | Constitution Article V:5 | Calendar ingest is a read (parsing ICS bytes, writing to the local `calendar_events` table); no egress, no model invocation, no effect; exempt from admission |
| Arming a recording is his standing consent per event or per Room | Constitution Article V:1 | The owner enables `ARM RECORDINGS . FOR ROOM MEETINGS` on a Room or `ARM ALL CALENDAR MEETINGS` in Settings; that toggle IS the consent act to RECORD; each auto-created recording arms at `starts_at − lead` and records at the event like every scheduled recording (ruling B11; OFF by default) |
| No counters of zero | UX-CANON.md rule A.8 | The WEEK strip is absent when no calendar is connected; the meeting watch row is absent when no meetings are linked; the MEETINGS count in SOURCES carries no zero; the brief's WEEK section is absent when calendar_events is empty |
| Every verb the library Button | UX-CANON.md rule A.1 | `Connect calendar` on the arrival, `Cancel` on the armed recording, `Add` / `Dismiss` on suggested meetings, `Generate` on the brief -- all library Button |
| The NEXT line said once | UX-CANON.md rule A.7 | The arrival's NEXT carries the event title, time, and Room token; the Room header does not repeat the same event; the Room's SOURCES says `NEXT THU 14:00` (a different event) |
| No prose | UX-CANON.md rule A.3 | The WEEK strip is tokens; the armed recording is tokens; the brief's WEEK section is tokens; no sentences anywhere |
| No modals | UX-CANON.md rule A.4 | The WEEK strip and the armed recording are inline on the arrival; the calendar source settings are in-world rows in Settings; the event-born recording overrides are inline |
| Egress where egress happens | UX-CANON.md rule A.9, Article III | The calendar source row shows `ICS . <host>` when the URL is HTTPS (the egress at ingest time); the snapshot row shows `THIS DEVICE` (vision model local); `NO EGRESS` never stated -- absence is the signal |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |
| Ledger not gate | Owner ruling | Every calendar refresh, every auto-created recording, every meeting watch evaluation -- receipted; no ceremony beyond the receipt |


## D2 -- the faces (element by element, species named)

### (a) The arrival's WEEK strip (under NEXT)

**Position:** under the NEXT line on ChairHome.tsx (today at :420-445,
between the headline and the NEEDS YOU section). Absent when no calendar
source is connected (the existing `NO CALENDAR . Connect calendar` empty
state at :420-431 stays; when a calendar IS connected but zero events
exist in the coming week, the strip is also absent -- rule A.8).

**The strip** (a horizontal token row, not a SurfaceLedgerRow):

- Five to seven day tokens (MON--SUN, or MON--FRI when the owner's
  work-week omits weekends). Each token:
  - Caption step (11 mono uppercase): the day abbreviation (`MON`,
    `TUE`, ...).
  - Dots: one dot per meeting on that day (a small circle glyph,
    `surface-token[data-chip]`). Maximum 4 dots; 5+ reads `5+`.
  - Today's token is accented (`data-today` attribute; the accent
    colour from `--color-accent`).
  - Absent days (no meetings) still show the day label with no dot
    (the structure conveys the week's shape; the zero dot is not a
    counter of zero -- it is the honest emptiness of the day).
- Below the dots, the total: `N MEETINGS THIS WEEK` (secondary step,
  12 mono). Omitted when the strip itself would be absent.

**Empty state:** the strip is absent. The NEXT line alone carries the
arrival's temporal signal. The `NO CALENDAR . Connect calendar` state
fires only when `calendar_configured` is false (door_service.py:143).

**Species used:** surface-token[data-chip] (for dots and day labels),
Button (ghost, for `Connect calendar` -- already exists at :428).

**Widths:** 1440 -- the strip is one row of day tokens under NEXT,
inline. 393 -- the strip stacks under NEXT; day tokens stay in one
scrollable row (`overflow-x: auto` on the strip container).


### (b) The meeting row's Room token and the event-born recording

**Position:** the `upcoming` list in the door response (door_service.py
:266-298), rendered on the arrival as part of the NEXT / upcoming
section. The event-born recording appears as an armed row in the
upcoming rail when its `starts_at` is within the horizon.

**The calendar event row** (rendered from `door.upcoming`, already
partially built in door_service.py:266):

- Primary (15/600): the event title (`Standup`).
- Cells (secondary step, 12 mono):
  - Time token: `10:00` (the event's `starts_at`, formatted HH:MM).
  - Room token: `ROOM . Q4 PLATFORM` (the Room name, when the event
    matches a Room via the meeting-project link or the event-Room
    matcher). Absent when no Room match (rule A.8).
  - Provenance token: the calendar source label (`O365 SNAPSHOT` /
    `WORK` / the ICS host; from `source_label` on calendar_events,
    schema.py:3505).
- When the event has an armed recording (armed_index lookup in
  door_service.py:277):
  - `ARMS HH:MM` token (the recording's arm time, typically 5 min
    before `starts_at`). StateChip success tone.
  - `Cancel` verb (Button ghost dense) -- cancels the armed recording
    without affecting the calendar event.

**The event-born recording row** (when an event auto-created a recording
and the recording is armed):

- Primary (15/600): the recording title (inherited from the event title).
- Cells:
  - `ARMED` token (StateChip success).
  - Time token: `09:55` (the arm time).
  - Provenance: `FROM . Standup (WORK)` -- the event title and the
    calendar source label.
- Trailing verbs:
  - `Cancel` (Button ghost dense) -- disarms the recording.

**Species used:** SurfaceLedgerRow, surface-token[data-chip], StateChip
(success for ARMED), Button (ghost dense), EgressChip (absent -- local
recording, no egress).


### (c) Settings -- Meetings' calendar rows

**Position:** inside the Meetings module (MeetingsConfig.tsx:25, opened
from the hub row). Below the existing capture/export config. A new
`CALENDAR` section (SurfaceSection).

**Section caption:** `CALENDAR` (caption step, 11 mono uppercase).

**Each calendar source row** (SurfaceLedgerRow, 52px lead slot):

- Lead: StateChip `*` (success = last refresh succeeded, failure = last
  refresh failed, idle = never refreshed).
- Primary (15/600): the source label (`WORK`, `PERSONAL`, the ICS host
  for URL sources, `O365 SNAPSHOT` for snapshot sources).
- Cells (secondary step, 12 mono):
  - Type token: `ICS` (for file/URL sources) or `SNAPSHOT` (for
    vision-extracted sources).
  - EgressChip: `<host>` when the source URL is HTTPS (the egress at
    ingest time; e.g. `outlook.office365.com`). Absent for file sources
    (no egress).
  - Count: `N CALENDARS` (the number of distinct calendar UIDs from
    events with this source_id; from a `COUNT(DISTINCT uid)` on
    `calendar_events`). Absent when zero (rule A.8 -- this means no
    successful ingest yet).
  - Last-read token: `LAST READ HH:MM` (the most recent
    `last_seen_at` from events with this source_id). Absent when never
    read.
- Trailing: no verb on existing sources (the source was added via
  Settings writes; editing is the existing Settings path).

**The connect row** (when no sources exist or the owner wants to add
another):

- A single SurfaceLedgerRow:
  - Primary: `Connect calendar`.
  - Trailing: Button ghost `Add` -- opens a StringGadget well (inline,
    rule A.4) where the owner pastes an ICS URL or a file path.
    `Save` (primary dense) validates via
    `validate_calendar_subscription` (integrations.py:60) and adds the
    source. `Cancel` (ghost dense) collapses the well.

**The auto-record toggle** (SurfaceLedgerRow, below the sources):

- Primary (15/600): `Auto-record`.
- Cells:
  - CycleGadget: `ARM ALL CALENDAR MEETINGS` / `ARM ROOM MEETINGS ONLY`
    / `OFF`. Default: `OFF` (Article IV: armed is the owner's explicit
    act; the toggle is the standing consent).
  - When not OFF: a muted token `5 MIN BEFORE` (the lead time before
    `starts_at` when the recording arms).

**Species used:** SurfaceSection (caption), SurfaceLedgerRow, StateChip,
surface-token[data-chip], EgressChip, CycleGadget, StringGadget, Button
(ghost, primary dense, ghost dense).

**Widths:** 1440 -- source rows are single-line. 393 -- EgressChip and
count wrap under the label; the connect well stacks full-width.


### (d) The Room's SOURCES gaining the meeting watch row

**Position:** inside the Room's SOURCES section
(ProjectRoomCore.tsx:371-450). The meeting watch row sits alongside
the existing GitHub and Jira Watch source rows.

**The row** (SurfaceLedgerRow, 52px lead slot, matching the existing
Watch source row grammar):

- Lead: a source emblem token `MTG` (surface-token[data-chip], caption
  step; matching the `GH` / `J` pattern from the existing sources).
- Primary (15/600): `MEETINGS`.
- Cells (secondary step, 12 mono):
  - Count: `N THIS WEEK` (the count of meetings linked to this Room
    that fall within the current calendar week). Absent when zero
    (rule A.8).
  - Next token: `NEXT THU 14:00` (the next meeting linked to this Room,
    day + time). Absent when no future meeting.
  - Last-run token: StateChip `CHECKED HH:MM` (the timestamp of the
    last meeting Watch evaluation on this Room) or `NEVER` (idle) when
    no evaluation has run.
- Trailing: `Pause` / `Resume` / `Retire` (Button ghost dense) --
  matching the existing Watch verbs in the SOURCES section.

**When no meetings are linked:** the meeting Watch row is absent from
SOURCES (rule A.8). No `MEETINGS . 0` row.

**The MeetingWatchSource entity shape** (following the Watch entity
grammar from watch_sources.py:58-111 for GitHub and :294-370 for Jira):

- `entity_type`: `"meeting"` (new value alongside `"pull_request"`,
  `"issue"`, `"branch_ci"`).
- `title`: the meeting title.
- `date`: the meeting's `started_at` timestamp.
- `participants`: the participant count (or a list of speaker labels).
- `decisions_count`: from `decision_records` linked via
  `meeting_projects`.
- `commitments_count`: from `decision_commitments` / `action_items`
  linked via `meeting_projects`.
- `intel_status`: the latest intelligence run status (`ran` / `failed` /
  `off`).
- `updated_at`: the latest intel run timestamp or commitment status
  change (whichever is most recent).

**SINCE YOU LOOKED:** the Room's existing SINCE YOU LOOKED logic
(ProjectRoomCore.tsx:224-225, `maxCheckedAt`) reads `updated_at` from
all Watch entities. The meeting entity's `updated_at` participates in
the same delta, so a new intel run or a new commitment from a linked
meeting triggers a SINCE YOU LOOKED change.

**Species used:** SurfaceLedgerRow, surface-token[data-chip], StateChip,
Button (ghost dense).

**Widths:** 1440 -- the row is one line (lead / primary / cells /
verbs). 393 -- cells wrap under primary; verbs at the bottom.


### (e) The week brief on Monday (Rhythm's brief row)

**Position:** the Rhythm module's brief row (CadenceCore.tsx:344, the
existing `Monday brief` SurfaceLedgerRow). The row's label and cells
change when the calendar is connected and the window is widened.

**The row update** (SurfaceLedgerRow):

- Primary (15/600): `Weekly brief` (replaces `Monday brief` when the
  calendar is connected and the window is widened to the full week;
  stays `Monday brief` when no calendar -- the brief is still
  day-windowed without calendar data).
- Cells:
  - When calendar connected: `WEEKLY MON 08:00` (CycleGadget or a
    muted token -- the day and time the brief regenerates on its cadence
    loop; from the 171 design's brief cadence in runtime/cadence.py:62).
  - StateChip: `LAST SEP 04` (the date of the most recent brief) or
    `NEVER` (idle, when no brief has been generated).
  - When calendar data exists in the brief: a summary token
    `N MEETINGS . M WATCH ITEMS . K COMMITMENTS DUE` (the week's
    totals from the brief's sections). Absent when the brief has no
    calendar section (rule A.8).
- Trailing: `Generate` (Button ghost) -- triggers immediate brief
  regeneration (existing verb from 171).

**The brief's WEEK section** (inside the brief detail face, opened from
the shade or the Rhythm row):

The brief gains two new subsections within its item list:

1. `THIS WEEK` (what is coming):
   - Meetings: `N MEETINGS` with the next event title and time.
   - Armed recordings: `N ARMED` -- events with auto-created recordings.
   - Commitments due: `N DUE` with the first commitment's text and day.
   - Absent when no calendar events and no commitments in the week
     (rule A.8).

2. `SINCE FRIDAY` (what happened -- the existing items from the
   existing lookback window, UNCHANGED; counsel's condition 2 ruled the
   brief a two-window design):
   - The existing collectors (Watch changes, pipeline events, breakage,
     meetings) keep today's window (Monday looks back to Friday 17:00,
     other days to the preceding business day).
   - Each item carries its existing shape: `text`, `detail`,
     `source_ref`, `priority`.

**The window ruling** (monday_brief_service.py:134-153):

- `compute_window()` is UNCHANGED: period_start = preceding business
  day at 17:00; period_end = now. Monday looks back 3 days (to Friday
  17:00); weekdays look back 1 day (monday_brief_service.py:140-147).
  The "what happened" half and its `SINCE FRIDAY` label keep it.
- 175 ADDS a second, forward window for the "what's coming" half:
  `now` to Sunday 23:59 local of the current ISO week. Only the
  calendar-event, armed-recording and commitments-due collectors read
  it. The two halves never overlap.
- When no calendar is connected: the brief falls back to the existing
  day-windowed behaviour (the calendar collectors produce zero items;
  the existing collectors still run with the widened window; no harm
  from a wider window -- more items is more information).

**Species used:** SurfaceLedgerRow, surface-token[data-chip], StateChip,
Button (ghost), CycleGadget (if the recurrence day is editable; a muted
token if fixed).

**Widths:** 1440 -- the row is one line. 393 -- cells wrap under the
label; the summary token stacks. The brief detail's WEEK section
follows the existing brief item rendering at both widths.


### All faces: dimensions

Every artboard at 1440 (the window at its design width) and 393 (the
glass / phone-width container query on `surface`). Three type steps
minimum per face: display (26/650) for the arrival headline, primary
(15/600) for event titles and row names, secondary (12 mono) / caption
(11 mono uppercase) for tokens, day labels, section labels, and
provenance chips.


## D3 -- the wire

### The calendar adapter's read cadence (the heartbeat's sweep)

**Seam:** `calendar_ingest_conductor.py:146+` -- the conductor's
`refresh()` method (calendar_ingest_conductor.py:175; counsel's
condition 3 corrected the name) runs on the heartbeat's cadence tick
(from 171).
Today it runs on its own standalone schedule via
`start_calendar_ingest_conductor` (calendar_ingest_conductor.py:602).

**What 175 changes:** the conductor's refresh hooks into the heartbeat's
sweep cadence (the 171 design's `_cadence_loop` at web_runtime.py:529).
Each cadence tick calls the conductor's `refresh()` as one of its
sweep steps. The conductor's standalone thread (its own sleep loop) is
replaced by the cadence-driven tick.

**Read path:** for each enabled CalendarSource (integrations.py:18-26):
1. If the source URL is a local file path: read the file bytes directly.
2. If the source URL is an HTTPS URL: fetch the ICS bytes via
   `urllib3` (calendar_ingest_conductor.py:97-134). This is the ONLY
   egress in the calendar pipeline; the EgressChip on the Settings row
   names the host.
3. Parse the ICS bytes via `calendar_ingest.parse_calendar_bytes`
   (calendar_ingest.py:57). Pure, bounded, no network.
4. Project the parsed events into the `calendar_events` table via
   `CalendarEventRepository.replace_projection`
   (db/calendar_events.py:65). This is a replace-on-success pattern:
   all events for this source are replaced atomically.
5. Receipt written as a pipeline event.

**Snapshot adapter (alternative path):** the CalendarSnapshotService
(calendar_snapshot_service.py) extracts events from screenshots via
vision LLM, generates an ICS file, and registers it as a file-based
CalendarSource. The ICS file is then ingested by the normal conductor
path. This is the "paste a screenshot of your Outlook week view" flow.

**Refresh cadence:** the cadence tick (default 15 min from 171's design)
is sufficient. Calendar events do not change in real time; a 15-minute
stale window is acceptable (the story's risk table names this:
stale-for-one-tick is acceptable).

### The event-to-Room link

**How events reach a Room today:** they do not. Calendar events are
in the `calendar_events` table (db/schema.py:3490-3506) with no
`project_id` column. Meetings (the `meetings` table) link to Rooms via
`meeting_projects` (project_service.py:262,
meeting_glue.py:445 `_associate_meeting_with_projects`). Calendar events
and meetings are separate entities with no join today.

**What 175 builds:** an event-to-Room matcher that runs after each
calendar ingest refresh:

1. **Title match:** compare the event's `title` (calendar_events.title)
   against the Room's `name` and the Room's `sources` (Watch query
   strings). Case-insensitive substring match. Example: event "Q4
   Platform Standup" matches Room "Q4 Platform" because the Room name
   is a substring of the event title.
2. **Attendee match:** when the ICS carries attendee data (the existing
   parser extracts `location` and `meeting_url` but NOT attendees
   today -- this is a GAP; see D4 H3), compare attendee email/names
   against the Room's People (via the 172 People resolver). A match
   means the event involves a person the Room tracks.
3. **Explicit link:** the owner can manually link a calendar event to a
   Room (a verb on the event row: `Link to Room` opening a Room
   picker). This overrides the matcher.
4. The match result is persisted in a `calendar_event_projects` join
   table: `(calendar_event_id, project_id, match_source)` where
   `match_source` is `"title"`, `"attendee"`, `"manual"`.

**The NEXT seam:** `door_service.py:266-298` already merges calendar
events and scheduled recordings into the `upcoming` list. The Room's
`next` seam (the NEXT line on the arrival) reads from this list. What
175 adds: the event items in the upcoming list carry a `project_id`
and `project_name` (from `calendar_event_projects`) so the NEXT line
can show `ROOM . Q4 PLATFORM`.

### Event-born scheduled recordings

**Seam:** `calendar_ingest_conductor.py:195-268` -- the conductor
already manages calendar event lifecycle. After projecting events, a
new step:

1. For each event in the projection where `meeting_url IS NOT NULL`:
   - Check if an enabled `ScheduledRecording` already exists for this
     event via `calendar_event_id` (the unique index at
     db/schema.py:3483 enforces one live arm per event).
   - If none exists AND the owner's auto-record setting is enabled
     (from Settings > Meetings' `ARM ALL CALENDAR MEETINGS` or
     `ARM ROOM MEETINGS ONLY` filtered by the event-to-Room match):
     create a `ScheduledRecording` via
     `ScheduledRecordingRepository.create()` (db/scheduled_recordings.py
     :66) with `calendar_event_id`, `calendar_uid`, `calendar_source_id`
     set.
   - The recording's `next_fire_at` is set to `starts_at - 5 min`
     (the lead time). The recording's `title` inherits the event title.
   - The recording is created with `enabled=True`, `state="idle"`.
     The existing `scheduled_recording_conductor.py` arms it when
     `next_fire_at` arrives and records at the event, like every
     scheduled recording (ruling B11; the toggle is the consent).
2. For events that disappear from the ICS (no longer in the projection):
   - The linked recording is disarmed (`enabled=False`,
     `state="cancelled"`, `last_outcome="calendar_event_removed"`).
   - Receipt: `scheduled_recording.cancelled.calendar_event_removed`.
3. For events whose time changed:
   - The linked recording's `next_fire_at` is updated to the new
     `starts_at - 5 min`.

**Idempotency:** the unique index at db/schema.py:3483
(`idx_scheduled_recordings_calendar_event_armed`) prevents duplicate
arms for the same calendar_event_id.

### The MeetingWatchSource

**Seam:** `watch_sources.py:58` (GitHubWatchSource) and `:294`
(JiraWatchSource). No MeetingWatchSource exists today.

**What 175 builds:** a `MeetingWatchSource` class following the same
protocol:

```
class MeetingWatchSource:
    def snapshot(self, principal, *, query_kind, query):
        # query_kind: "meetings"
        # query: {"project_id": "..."}
        # Returns: list of meeting entities linked to this project
```

1. Read `meeting_projects` for the given `project_id`.
2. For each linked meeting: build an entity dict with the shape
   described in D2(d) (title, date, participants, decisions_count,
   commitments_count, intel_status, updated_at).
3. The entity's `updated_at` is `max(intel_snapshot.created_at,
   latest_commitment.updated_at, meeting.started_at)`.
4. Return the list of entity dicts.

**Registration:** the MeetingWatchSource is registered alongside GitHub
and Jira in the Watch source dispatch (watch_service.py, wherever
`GitHubWatchSource` is instantiated and dispatched by `provider` type).
The Room's source type for meetings is `"meeting"`.

**Zero egress:** the adapter reads from the local database only
(meetings, meeting_intel_snapshots, decision_records,
decision_commitments, meeting_projects). No CLI call, no network.
Article III satisfied.

### The brief's week window

**Seam:** `monday_brief_service.py:134-153` -- `compute_window()`.

**What 175 changes:** nothing in `compute_window()`. A new
`compute_week_ahead(now)` returns `(now, sunday_23_59_local)`; the
brief's forward half reads it.

The look-ahead (for "what's coming") reads calendar_events where
`starts_at > now AND starts_at <= sunday_23_59`. The look-back (for
"what happened") reads the existing collectors over the existing
`compute_window()` (unchanged). The two halves compose into the brief's
sections without overlap.

**New collectors:**

1. **Calendar events collector:** reads `calendar_events` for events in
   the week range. Produces BriefItems in a `"this_week"` section:
   - `N meetings` (count of events with starts_at in the week).
   - `Next: [title] at [time]` (the next event after now).
   - `N armed` (events with linked armed recordings).
   Each item's `source_ref` points to the calendar event id.

2. **Meeting Watch collector:** reads MeetingWatchSource entities (from
   story 04) for linked Rooms. Produces BriefItems in a `"meetings"`
   section:
   - Meetings with new decisions since the last brief.
   - Meetings with new commitments.
   - Commitments due this week.
   Dedup by `calendar_uid` to avoid repeating events that appeared in
   both collectors.

### The wire summary (file:line)

| Seam | File:line | Role |
|---|---|---|
| CalendarSource config | holdspeak/config/integrations.py:18 | ICS source definition (id, label, url, enabled) |
| CalendarConfig | holdspeak/config/integrations.py:34 | Multi-source container |
| validate_calendar_subscription | holdspeak/config/integrations.py:60 | Validates file path or HTTPS URL |
| calendar_ingest.parse_calendar_bytes | holdspeak/calendar_ingest.py:57 | Pure ICS parser (no IO) |
| CalendarIngestConductor.refresh | holdspeak/calendar_ingest_conductor.py:175 | Refresh of all sources, now driven by the sweep |
| CalendarEventRepository.replace_projection | holdspeak/db/calendar_events.py:65 | Atomic replace-on-success |
| CalendarEventRepository.list_upcoming | holdspeak/db/calendar_events.py:153 | Events after now, sorted by starts_at |
| calendar_events table | holdspeak/db/schema.py:3490 | id, uid, title, starts_at, ends_at, location, meeting_url, source_id, source_label |
| idx_calendar_events_upcoming | holdspeak/db/schema.py:3509 | Index on (starts_at, id) |
| ScheduledRecording model | holdspeak/db/scheduled_recordings.py:16 | calendar_event_id at :34, calendar_uid, calendar_source_id |
| idx_scheduled_recordings_calendar_event_armed | holdspeak/db/schema.py:3483 | Unique: one live arm per event |
| ScheduledRecordingRepository.create | holdspeak/db/scheduled_recordings.py:66 | Creates with calendar_event_id |
| CalendarSnapshotService | holdspeak/services/calendar_snapshot_service.py:1 | Vision-based extraction + ICS generation |
| door_service._upcoming | holdspeak/services/door_service.py:266 | Merges events + recordings into upcoming list |
| door_service._calendar_configured | holdspeak/services/door_service.py:143 | True iff an enabled source passes validation |
| DoorProjection.upcoming | web/src/desk/chair/ChairHome.tsx:87 | Array of upcoming items on the arrival |
| DoorProjection.calendar_configured | web/src/desk/chair/ChairHome.tsx:88 | Drives NO CALENDAR empty state |
| NEXT line | web/src/desk/chair/ChairHome.tsx:334-340 | Prefers door upcoming, falls back to rooms |
| NO CALENDAR state | web/src/desk/chair/ChairHome.tsx:420-431 | Shows Connect calendar verb |
| Armed countdown | web/src/desk/chair/ChairHome.tsx:392-446 | ARMED token + countdown + Cancel |
| Schedule button | web/src/desk/chair/ChairHome.tsx:999 | In capture bar footer |
| HistoryCore | web/src/pages/cores/HistoryCore.tsx:2 | Meetings board: Record wing, stream rows |
| MeetingsConfig | web/src/pages/cores/history/MeetingsConfig.tsx:25 | Capture + export config (Settings) |
| CadenceCore brief row | web/src/pages/cores/CadenceCore.tsx:344 | Monday brief row in Rhythm |
| ProjectRoomCore SOURCES | web/src/features/project-room/ProjectRoomCore.tsx:371 | Watch source rows in the Room |
| GitHubWatchSource | holdspeak/services/watch_sources.py:58 | GitHub adapter (protocol to follow) |
| JiraWatchSource | holdspeak/services/watch_sources.py:294 | Jira adapter (protocol to follow) |
| compute_window | holdspeak/services/monday_brief_service.py:134 | Day-windowed lookback (to be widened) |
| meeting_projects | holdspeak/services/project_service.py:262 | Meeting-to-Room link |
| _associate_meeting_with_projects | holdspeak/runtime/meeting_glue.py:445 | Auto-links meetings to Rooms |


## D4 -- counsel's hunts

### H1: An event arming a recording without his rule

The auto-record toggle in Settings (D2c) is the owner's standing
consent. If the toggle is OFF, no event-born recording is ever created.
If the toggle is `ARM ROOM MEETINGS ONLY`, only events matching a Room
create recordings. Hunt: the conductor's auto-create path must check the
toggle BEFORE creating a recording; a missing check bypasses Article V.
Test: set toggle to OFF, ingest an event with meeting_url, assert
`scheduled_recordings` count unchanged. Set toggle to `ARM ROOM MEETINGS
ONLY`, ingest an event not matching any Room, assert unchanged.

### H2: A calendar read that leaves the machine

The ONLY egress in the calendar pipeline is the HTTPS fetch in
`calendar_ingest_conductor.py:97-134`. Local file reads have zero
egress. Hunt: the Settings row's EgressChip must match the actual
fetch path -- `<host>` for HTTPS sources, absent for file sources.
The snapshot adapter's `SNAPSHOT_SOURCE_LABEL` is `"O365 SNAPSHOT"`
(calendar_snapshot_service.py:26); its extraction runs on a LOCAL model
(the model assignment, not a cloud call). Hunt: verify the snapshot
path's model assignment does not silently use a cloud model; the
EgressChip on the extraction receipt must name the model host.

### H3: A Room link by a fuzzy title match -- the false positive

The event-to-Room title matcher (D3, "event-to-Room link") uses
substring matching. An event "Platform Architecture Review" matching a
Room "Platform" also matches a Room "Review" if one exists. The false
positive links the event to the wrong Room. Hunt:
- The title match should prefer the LONGEST matching Room name (a
  shorter substring is a weaker signal).
- Matches below a threshold (e.g., the Room name is fewer than 4
  characters or the match is a common word like "Team") should be
  SUGGESTED, not auto-linked.
- The SUGGESTED row (from 172's grammar) with `Add` / `Dismiss` is the
  safer V0: no auto-link, only suggestions. The owner manually links.
  The brief's question: is auto-linking worth the false-positive risk,
  or should V0 be suggestion-only?
- **Ruled (counsel's condition 4, the orchestrator under the open
  throttle):** V0 AUTO-LINKS by title with the >= 4-character
  whole-word rule and prefers the longest Room name; every link is a
  receipt (`match_source=title`), the Room's MEETINGS row and the
  arrival's event row wear the link, and `Unlink` on either face
  removes it (`DELETE /api/calendar/events/{id}/link`). A wrong link
  files a recording under the wrong Room; it never loses the
  recording. His word can flip V0 to suggestion-only (question 1 in
  the walk).

### H4: A week strip with a counter of zero

The WEEK strip (D2a) shows day tokens with dots. A day with zero
meetings shows the day label with no dot. Hunt: is this a counter of
zero (rule A.8)? No -- the day label is structural (it conveys the
week's shape); the absent dot is the honest state, not a zero counter.
But: the total `N MEETINGS THIS WEEK` token IS a counter. When zero
meetings exist in the week, the ENTIRE strip is absent (not a strip
with `0 MEETINGS THIS WEEK`). Verify this.

### H5: The attendee match gap

The ICS parser (calendar_ingest.py) extracts `title`, `starts_at`,
`ends_at`, `location`, `meeting_url` from VEVENT components. It does
NOT extract `ATTENDEE` properties. Without attendees, the event-to-Room
matcher cannot match by person. Hunt: adding `ATTENDEE` extraction to
the parser is a scope question -- it widens the ingest surface. For V0,
title match + manual link may be sufficient. Attendee extraction can be
a follow-on if the false positive rate of title-only matching is
unacceptable.


## D5 -- the walk on his desk

The walk proves the Tuesday moment on his real desk with his real
calendar:

1. **Calendar connected.** Which calendar source does he connect? The
   adapter today supports: (a) a local `.ics` file path, (b) an HTTPS
   ICS URL (e.g. an Outlook/O365 ICS subscription link), (c) a vision
   snapshot of a calendar screenshot. His Outlook exports an ICS
   subscription URL. He pastes it in Settings > Meetings > Calendar >
   Add. The conductor refreshes; `calendar_events` populates.
2. **The WEEK strip.** The arrival shows the strip with his real
   meetings: day tokens with dots, today accented. He counts the
   meetings; they match his Outlook week.
3. **The NEXT line.** The arrival's NEXT reads his next meeting's title
   and time. If the event matches a Room, the Room token is shown.
4. **The armed recording.** His next meeting with a meeting URL
   (a Teams/Zoom/Meet link in the event) auto-created an armed
   recording. The arrival shows `ARMS HH:MM` with `Cancel`. He
   verifies the title matches the event.
5. **The Room's MEETINGS source.** He opens a Room linked to a
   recurring meeting. SOURCES shows the meeting Watch row with
   `N THIS WEEK . NEXT [day] [time]`. SINCE YOU LOOKED shows the
   meeting's entity with decisions from the last intel run (from 172).
6. **The week brief.** The brief in the shade (or Rhythm > Generate)
   shows the WEEK frame: meetings count, armed recordings, Watch
   changes, commitments due. The backward window is the existing one;
   the forward window runs to Sunday.
7. **His word.** Stopwatch per face. Screenshots at both widths. His
   verdict recorded verbatim.


## Honest sizes

| Story | Size | Rationale |
|---|---|---|
| 01 The design | S | Artboards from this doc; no code |
| 02 Calendar events on the desk | M | The WEEK strip face (new), the NEXT seam enhancement, the event-to-Room matcher (new join table + substring logic), the Settings CALENDAR section (new); the ingest pipeline and DB already exist |
| 03 Event-born recordings | M | Auto-create in the conductor (new conditional after projection), the idempotency index already exists, the override/cancel verbs exist; the auto-record toggle (new CycleGadget in Settings); the rescheduled/cancelled event handling |
| 04 The meeting Watch adapter | M | A new WatchSource class following the established protocol; entity shape with counts from existing tables; registration in the dispatch; the Room SOURCES face gains one row type |
| 05 The week brief | M | Widen compute_window (one function change); two new collectors (calendar events + meeting Watch); the brief detail gains one section; the Rhythm row label change |
| 06 The walk | S | His desk, seven beats; no code |
| 07 The hygiene lane | S--M | Census + payment of items the phase's tree touches |
| 08 The docs | S | Screenshots + architecture diagrams |
| 09 The close | S | Suite, baseline, canon ratchet, counsel, PR |
| **Total** | **M** | The calendar ingest and scheduled recording machinery already exist; 175 connects them to the desk and the Room |


## Addendum -- counsel on the design (2026-09-05): RATIFY-W-C, five conditions

| # | Condition | Ruling | Paid where |
|---|---|---|---|
| 1 | ArrivalArmedOrphan: strip `3 MEETINGS THIS WEEK` vs section `MEETINGS 2` | The strip and the section count ONE set: the week's calendar events. The orphan armed recording is a recording, not an event; it sits in its own row grammar below the section and is never counted as a meeting. | Board: strip now reads `2 MEETINGS THIS WEEK` |
| 2 | Brief window: D3 snippet said Monday 00:00; the board says SINCE FRIDAY | Two-window design. `compute_window()` UNCHANGED (the SINCE FRIDAY half); a new forward window `now -> Sunday 23:59` feeds THIS WEEK. | D2(e), D3 rewritten above; wire lane 04/05 briefed |
| 3 | `refresh_all` does not exist | Corrected to `refresh` (calendar_ingest_conductor.py:175). | D3 and the wire summary |
| 4 | Auto-link vs suggestion-only unsettled | V0 auto-links (>= 4-char whole word, longest Room name wins), every link a receipt, `Unlink` on both faces, nothing lost on a wrong link. His word may flip it. | H3 above; story 03 AC |
| 5 | `ARM ROOM MEETINGS ONLY` consent is blind | The toggle row carries the matched fact `N MATCHED THIS WEEK` (absent at zero per A.8) so the rule's reach is on the same face. | The three Settings boards |

P2s: P2-1 (the same event in two sources arms twice) is named in the
risk table as accepted for V0 -- Cancel is one verb; P2-2 the snapshot
model assignment gets a fence test in the hygiene lane (local-or-named);
P2-3 NEXT vs the first row is headline-vs-detail, kept; P2-4 the Well
board's missing Auto export row is a mockup simplification -- the build
keeps the full Settings layout and unfolds the well inline.

Counsel's three questions for the owner ride in the walk (story 06):
auto-link vs suggestion-only; the two-window brief; a confirmation step
before an auto-linked event arms.


## Addendum 2 -- build rulings (2026-09-05, the faces)

| # | Question raised by the build | Ruling |
|---|---|---|
| B1 | Past events in the current week: the strip's `count_per_day` counts Mon-Sun including events already past; the MEETINGS section lists only what is still coming. On a Thursday the two differ. | Two honest facts, kept. The strip counts the WEEK'S SHAPE (dots == `N MEETINGS THIS WEEK`, always). The MEETINGS section counts ITS ROWS (what is still coming). The only strip defect is dots != total. |
| B2 | The Room's MEETINGS row: the wire registered the MeetingWatchSource but nothing creates a meeting Watch on a Room. A synthetic row (NEVER, no verbs, no SINCE YOU LOOKED) was proposed. | Rejected as hollow. The row is a REAL Watch: created idempotently when a meeting is linked to a Room (routing_glue + the manual link path) and backfilled once by the heartbeat sweep for Rooms that already have linked meetings; both receipted. CHECKED comes from the sweep; Pause/Resume are real; the entity's `updated_at` feeds SINCE YOU LOOKED. |
| B3 | The orphan armed row's provenance printed `FROM · RETRO ()` when the event had left the upcoming projection. | The source label resolves from the event by id (any event, not only upcoming), then from the recording's `calendar_source_id`, else the token prints without parentheses. |
| B4 | The NEXT line's Room token was proposed as backlog. | Not backlog: `NEXT · STANDUP · 10:00 · ROOM · Q4 PLATFORM` is the board; the arrival composes it from the next calendar event's `project_name`. |
| B5 | The brief's forward items landed in the `changed` section (closed vocabulary). | `this_week` is added to the section vocabulary additively and ordered first; the four existing sections keep their order. |
| B6 | The snapshot adapter's direct-dispatch fallback could pick a cloud vision model and record no host (P2-2). | Paid: local/LAN vision profiles are preferred; a non-local pick records the host on the egress from the revision's endpoint (fence: tests/unit/test_hs175_snapshot_model_fence.py). |
| B7 | The design pointed the Settings CALENDAR section at MeetingsConfig.tsx (the Meetings window's gear panel). The ratified board is the Settings → Meetings module the hub row opens (SettingsCore `case "meetings"`), which already carried a 146-era Calendar group. | The board wins: the CALENDAR section lives in SettingsCore's meetings case and REPLACES the 146-era group (the calendar said once, one grammar). The gear panel stays as it was. The existing `Snapshot` verb (the vision adapter's entry) is kept beside `Add` — a working verb is never dropped; counsel-on-built rules its final place. |
| B8 | The brief face's SINCE FRIDAY half was built as the 171 fold groups with `00` counters, on the claim that "unchanged window" meant "unchanged face". | Condition 2 kept the WINDOW unchanged, not the face. The ratified board shows flat rows (kind token · primary · detail · emblem chip); counters of zero are a bounce on their own. Behaviours the 132/129 tests protect (per-item triage, drill filters, BACK, the card cap) survive the grammar change. |
| B9 | D2(c) said "no verb on existing sources; editing is the existing Settings path" — but B7 retired that path. The old group's tests named what it could do: disable, edit the URL, remove (with confirmation), add, and surface the snapshot upload's refusal in the status bar. | The verbs move onto the new rows in the ledger's hover-verb grammar: `Disable` / `Enable`, `Edit` (unfolds the same connect well under the row, pre-filled), `Remove` with a one-step in-world confirm. All write through the existing sources wire; the snapshot refusal keeps reaching the status bar. A face that replaces another never loses a working verb. |
| B10 | The arrival already carries a MEETINGS section (the recorded meetings, 172's grammar); the board captioned the calendar section MEETINGS too, so a desk with a calendar would say the caption twice over two row grammars. Seen on the owner's desk walk (no calendar: only the recorded section showed). | The calendar section is captioned `THIS WEEK` (the strip's `N MEETINGS THIS WEEK` and the brief's THIS WEEK already name it); the recorded-meetings section keeps MEETINGS. Carried to the owner as a board deviation. |
| B11 | Counsel-on-built (assets/counsel-on-built-175.md) BOUNCED on C1: the scheduled-recording conductor STARTS capture at the event, while D1/D3, story 03 and the guide said "armed, never started". | Ruled by the orchestrator under the open throttle and the 136 law (a scheduled recording records at its time): an event-born recording behaves exactly like a cron scheduled recording — it arms at `starts_at − lead` and records at the event. The Auto-record toggle (OFF by default) is the owner's standing consent to RECORD those meetings; `Cancel` must work for the row's whole visible life and be final across refreshes. The copy is corrected. Carried to the owner: "is the toggle consent to start capture at −5 min, or to arm and wait for Record?" — his word flips it. C2–C11 are defects and are paid; C12's runner note paid (no `Continue later` click). |
| B12 | Counsel C2/C3: the arrival's Cancel refused every state but `arming`, and a cancelled event-born row was re-armed by the next refresh. | Cancel is lawful for an `idle` event-born row (disabled, `cancelled`, `owner_cancelled`, receipt `scheduled_recording.cancelled.owner`) and for `arming` (the 136 path); on a `recording` row Cancel is withheld and the honest verb is the meeting's Stop, the refusal named on the row (`CAN'T CANCEL · <reason>`). The cancelled row IS the tombstone, keyed `(calendar_source_id, calendar_uid)`; the conductor skips it with one receipt. `event_removed` and source-gone cancellations are not tombstones — the toggle's consent stands if the event returns. |
| B13 | Counsel C4/C5: Remove/Disable left recordings armed and the last source never pruned; the API unlink was undone by the next refresh. | `refresh()` prunes unlisted and disabled sources BEFORE the zero-sources return (projection deleted, links dropped, idle recordings cancelled with `calendar_source_removed` / `_disabled` receipts). Unlink is durable through an additive `calendar_event_link_suppressions` table honoured by `replace_auto_links`; a manual link clears it. Schema 75; the canonical snapshot regenerated. |
| B14 | Counsel C6: the matcher's Watch-query branch selected a column that does not exist and warned every refresh; `room_linked` needed two refreshes; manual links orphaned on a time change. | The Watch-query branch is dropped (title match is the V0); the matcher runs before per-source auto-create; manual links rebind by `(source_id, uid)`. Counsel's R1 (a Room named `Design` links a 401k webinar) still reproduces BY DESIGN under the ≥4-char whole-word rule — that is the owner's question 1; Unlink is the remedy until his word. |
| B15 | Counsel C8/C9 (the arrival): the strip bucketed UTC days; THIS WEEK showed the 14-day projection; overflow read `{n}+`. | The week and its buckets are the hub's LOCAL Mon–Sun (`door.week.starts_at/ends_at` ride the payload); the THIS WEEK section is bounded by `week.ends_at` while NEXT still reads the projection; overflow reads exactly `5+`. |
| B16 | Counsel re-read (assets/counsel-on-built-175-reread.md, RATIFY-W-C): the owner-cancel tombstone keyed by `(source, uid)` made Cancel on one occurrence of a recurring meeting refuse the whole series while its armed siblings stayed armed. | Cancel means THIS ONE: the tombstone is keyed by occurrence `(source, uid, starts_at)`; siblings untouched. "This one or the series?" is carried to the owner. Every arm writes its own create receipt (the discriminator carries the schedule id). Delete on an event-born row behaves as Cancel and never removes the tombstone. |
| B17 | Counsel re-read: the local zone came from `datetime.now().astimezone()`, a fixed offset, so on the DST edge the week bound lands an hour off and a dot shifts a day. | Per-instant local conversion everywhere the week is computed (the door's strip, the Room's week, the Settings matched count); a DST-edge test at America/Denver 2026-11-01 pins it. |
