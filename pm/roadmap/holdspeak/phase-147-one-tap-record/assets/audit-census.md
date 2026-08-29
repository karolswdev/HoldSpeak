# Phase 147 audit — structural census (event → record seams)

Read-only opus audit, 2026-08-28, against `feat/hs147-one-tap-record`
(= main `fabba984`). Every claim carries file:line. This is the
charter's evidence base alongside [audit-walk.md](./audit-walk.md).

## Plane 1 — the rail / calendar events

`CalendarSource {id, label, url, enabled}` —
`holdspeak/config/integrations.py:18-24`; display label fallback
label → hostname → "LOCAL" at `:100-113`; refresh cadence
`CALENDAR_REFRESH_SECONDS = 900` (15 min) at `:14`.

`calendar_events` table — `holdspeak/db/schema.py:3379-3395`:
`id` (TEXT PK, `ce_{sha256(subscription_revision \0 uid \0 starts_at)}`,
computed `calendar_ingest.py:381-385`), `uid`, `title`, `starts_at`
(UTC ISO), `ends_at` (UTC ISO), `location?`, `meeting_url?`,
`last_seen_at`, `subscription_revision`, `source_id`, `source_label`.
Unique index `(source_id, uid, starts_at)` `schema.py:3392-3393`;
upcoming index `(starts_at, id)` `:3394-3395`.

**Identity facts:** ICS-feed UIDs are RFC-5545-stable, so the
projection `id` is stable across refreshes — but it hashes
`starts_at`, so a TIME SHIFT mints a NEW id (old row deleted by
`replace_projection`, `db/calendar_events.py:62-123`, which
atomically replaces a source's whole projection). The snapshot
adapter mints `uid = f"{uuid.uuid4()}@holdspeak-snapshot"` PER
CONFIRM (`services/calendar_snapshot_service.py:289`) — no stable
identity across re-imports. Recurring VEVENTs share one `uid` across
occurrences (uniqueness only with `starts_at`).

Serving: `GET /api/door` (`web/routes/door.py:22-24`) →
`DoorService._upcoming()` (`services/door_service.py:170-181`) merges
enabled future scheduled recordings + `list_upcoming(now_iso)`
calendar events, sorted `(starts_at, source, id)`. Calendar item
shape (`door_service.py:200-218`): `{id, source:"calendar_event",
target_ref:"calendar_event:{id}", title, starts_at, ends_at,
location, meeting_url, state:"scheduled", source_id, source_label}`.
All-day events never reach the projection
(`calendar_ingest.py:296` skips date-only); past events filtered at
`door_service.py:170-181`. Timezone handling is sound end to end
(`_as_utc`/`_utc_iso` `calendar_ingest.py:369-375`; snapshot local
wall-clock fixed at the 146 close).

Web: `DoorUpcomingItem` type `DoorBoardLane.tsx:39-52` (no
`lawful_verbs`); `UpcomingRail` `:260-305` renders passive `<li>`
rows — **zero interactive affordances per row** except the external
"Meeting link" anchor; the only button is header "Schedule
recording" `:266-268`.

## Plane 2 — scheduled recording (Phase 136)

`scheduled_recordings` table — `db/schema.py:3354-3375`: `id`
(`sr_{uuid}`), `title`, `cron_expr`, `tz` ('UTC'), `one_shot` (0/1),
`duration_minutes` (60), `enabled` (0), `revision`, `created_at`,
`last_fired_at?`, `next_fire_at?`, `armed_at?`, `deadline_at?`,
`state` CHECK (idle, arming, recording, stopped, cancelled, refused,
missed), `last_outcome`, `last_receipt_id`, `delegation_receipt_id`.
Partial index `(enabled, next_fire_at) WHERE enabled=1` `:3374-3375`.
**No calendar link columns exist.**

Routes (`web/routes/scheduled_recordings.py`, prefix
`/api/scheduled-recordings`): GET `/`, POST `/` (title, cron_expr,
tz, one_shot, duration_minutes, enabled), GET/PATCH/DELETE
`/{id}`, POST `/{id}/cancel`. MCP: `scheduled_recording.list/
create/update/delete/cancel_armed` (`mcp/tools.py:374-417`).

Conductor (`scheduled_recording_conductor.py`): 60 s tick (`:100`);
`_tick` `:338` fires when `next_fire_at <= now`, minute-dedupe
`_fired_minutes` `:113`; `_arm` `:368` → state "arming", broadcasts
`scheduled_recording.arming` with `countdown_seconds`
(`COUNTDOWN_SECONDS = 10`, `:35`); `_countdown_then_fire` `:400`;
`_fire` `:473` sets `deadline_at = now + duration*60` (`:486`) and
calls `self._start_meeting_fn(principal, title=sched.title)`
(`:509`), arms auto-stop `threading.Timer` `:537-544`; `_auto_stop`
`:546` → `_stop_meeting_fn` (wired `web_server.py:992-996`).
One-shot disables after any terminal outcome
(`_advance_after_terminal` `:587-600`); recurring advances cron
`:603-608`. Auto-stop is purely duration-based — **no "stop at event
end" concept**.

Meeting seam: `_start_meeting_fn` wired `web_server.py:986-991` as
`callbacks.pending_title = title; callbacks._start_meeting(principal)`;
`pending_title` applied `runtime/meeting_glue.py:293-298`. **Only
title + principal cross this seam.**

## Plane 3 — meetings + provenance

`meetings` table — `db/schema.py:25-50`: id, started_at, ended_at?,
title?, duration_seconds, intel_*, mic_label, remote_label, web_url?,
capture_*, route_fence_*, transcription_*, checkpoint_*,
`provenance` ('desktop'), sync/created/updated stamps. **No
calendar-linking column.** Creation: `POST /api/meeting/start`
(`web/routes/meetings/live.py:91-111`) → `MeetingService
.start_capture()` (`services/meeting_service.py:67-99`) →
`_start_meeting()` (`runtime/meeting_glue.py:175-361`) — no
calendar-event parameter anywhere. Title default None
(`meeting_session/models.py:124`); set by pending_title, PATCH
`live.py:121-139`, or deferred auto-title.

**Exhaustive grep verdict: NO code path connects a calendar event to
a recording or meeting. The systems are fully disjoint.**

Downstream: follow-through cards carry `CardProvenance.meeting_id`
(`follow_through_service.py:51-59`) — a linked meeting makes
follow-through traceable to the calendar event transitively.

## Plane 4 — the tap surface

Verb registry `web/src/desk/verbRegistry.ts:163` (no
recording/calendar verbs); floor/object menus `floorMenu.ts:32,:56`;
**DoorCard inline `lawful_verbs` buttons are the closest precedent**
(`DoorBoardLane.tsx:454-499`, dispatch via `commandForDoorVerb()`
`:114-162` — a fixed HTTP adapter table with four verbs today).
`ScheduleCreateWindow` (`components/ScheduleCreateWindow.tsx:62-124`)
is an in-world DeskWindowFrame with NO pre-fill context; store action
`openScheduleCreate()` takes no arguments. `CaptureHero`
(`chair/hero/CaptureHero.tsx`) renders arming/countdown off the
`scheduled_recording.*` broadcasts.

## Plane 5 — gaps and risks

1. **Snapshot UIDs unstable** (uuid4 per confirm) — armed recordings
   orphan on re-import.
2. **Time shift = new projection id** — a link by `id` orphans; `uid`
   survives shifts but isn't unique alone (recurring).
3. **No duplicate-arming guard** at any layer.
4. **Tick granularity:** events < ~70 s out can start up to 60 s late.
5. **No stop-at-event-end**; duration must be computed at arm time.
6. **Event deleted from feed** → nothing notices; armed recording
   fires for a cancelled meeting.
7. All-day and past events: non-issues (filtered upstream).

## Charter inputs (the seam map)

| Seam | File:line |
|---|---|
| `scheduled_recordings` schema (+link cols, unique guard) | `db/schema.py:3354-3373` |
| `ScheduledRecording` dataclass | `db/scheduled_recordings.py:16-33` |
| `ScheduledRecordingService.create_schedule()` | `services/scheduled_recording_service.py:158-199` |
| POST route body | `web/routes/scheduled_recordings.py:66-87` |
| `DoorService._calendar_event_item()` (+armed ref) | `services/door_service.py:200-218` |
| `DoorUpcomingItem` + `UpcomingRail` + verb table | `DoorBoardLane.tsx:39-52, 260-305, 114-162` |
| Conductor `_fire` → meeting seam | `scheduled_recording_conductor.py:473-544` |
| `_start_meeting_fn` wiring | `web_server.py:986-991` |
| `_start_meeting()` | `runtime/meeting_glue.py:175-361` |
| `meetings` schema (+link col) | `db/schema.py:25-50` |
| Snapshot UID mint | `services/calendar_snapshot_service.py:289` |
| MCP `scheduled_recording.create` | `mcp/tools.py:380-392` |

Half-built already: the merged time-sorted rail; the proven one-shot
lifecycle; the `lawful_verbs` inline-button pattern; the title seam;
`ScheduleCreateWindow`'s `createSchedule()`; the meetings
`provenance` column concept.
