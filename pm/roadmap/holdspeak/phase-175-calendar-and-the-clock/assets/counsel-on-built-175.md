# Counsel on the built phase — 175 Calendar and the Clock

Counsel read: commit `bda20aa8` on `feat/calendar-clock` (2026-09-05, "the four
faces built to the ratified boards"). Read-only; every claim carries a
`file:line`; reproductions ran on temp DBs under an isolated HOME and never
touched the owner's database or hub. Working-tree drift since the commit
(B10 caption `THIS WEEK`, the walk runner's Settings selectors, story-06
evidence and shots) is noted where it changes a finding; line numbers are the
commit's unless marked *tree*.

Canon measured against: Constitution Articles III (local first, honest
egress), IV (voice arms, it does not fire), V (consent is the spine; every
attempt a receipt; refusal by name), VI (honest by construction; copy never
promises what the code does not do), IX (proof over claim); UX-CANON A.1, A.7,
A.8, A.9, A.10, A.11, D; the ratified design with Addendum 1 (conditions 1–5)
and Addendum 2 (B1–B10).

---

## VERDICT: BOUNCE

The wire is real and most of it is careful (the read path, the projection
replace, the R1/R2/R3 reconciliation, the MeetingWatchSource with zero
egress, the two-window brief's `compute_window` untouched, the local/LAN
preference on the vision dispatch). But the phase's spine — an event arms a
recording under the owner's standing consent, and he can take that consent
back on the face — is not true as built:

1. The event-born recording does not "arm, never start". At `starts_at − 5
   min` the scheduled-recording conductor arms it and **fires it ten seconds
   later** (`COUNTDOWN_SECONDS = 10`); it starts capture. The phase scope,
   story 03, the design's D1 law and the USER_GUIDE all say the opposite.
2. The arrival's `Cancel` on that recording is dead for its whole visible
   life (the row says `ARMS 09:55` from 07:55; the route refuses anything not
   in `arming`; the store swallows the 409; no refusal is shown).
3. An owner's cancel (however he reaches it) is **re-armed by the next
   15-minute refresh** — reproduced.
4. Removing or disabling a calendar source leaves its event-born recordings
   armed (they fire); removing the last source never prunes its events off
   the desk — reproduced.
5. `Unlink` — condition 4 of the ratified design — exists on neither face,
   and an API unlink of a title link is undone at the next refresh.
6. A common-word Room name (`Design`) auto-links a personal event ("Design
   your 401k plan (webinar)") and, under `ARM ROOM MEETINGS ONLY`, arms it —
   reproduced. With 1–3 that is a recording the owner never chose, cannot
   cancel from the arrival, and that returns if he cancels elsewhere.

Each of these is a code fix of hours, not a redesign; the boards stand. The
bounce is on Article IV/V/VI grounds, not on the faces. His word outranks
counsel (the standing ruling); if he rules that the Auto-record toggle IS
consent to start capture, condition C1 becomes a copy fix and a real Cancel,
and the verdict lifts to RATIFY-WITH-CONDITIONS on C2–C7.

---

## The hunts

### H1 — Consent: can any event arm a recording without his rule? (Article V)

**Default and gate are right.** `MeetingConfig.auto_record = "off"`
(`holdspeak/config/meeting.py:49`), validated to the closed set at
`:162-168`; the conductor returns before any query when off
(`holdspeak/calendar_ingest_conductor.py:604-606`); `room_linked` filters on
the join (`:626-641`, `:650-651`). Tests: `tests/unit/test_hs175_event_recordings.py`
`TestAutoRecordOff`, `TestAutoRecordRoomLinked` (31 passed with
`tests/unit/test_hs175_calendar_wire.py`, isolated HOME).

**H1-1 (P0) — "armed, never started" is not what the code does.** The
recording is created `enabled=True, next_fire_at = starts_at − lead`
(`calendar_ingest_conductor.py:668-687`). The scheduled-recording conductor
picks up any enabled `idle` row whose `next_fire_at <= now`
(`holdspeak/scheduled_recording_conductor.py:338-359`), enters `arming`
(`:362-390`), waits `COUNTDOWN_SECONDS = 10` (`:35`, `:407-421`) and calls
`_fire` → `_start_meeting_fn` (`:473-530`). So capture starts at
`starts_at − 4:50`. The phase says otherwise everywhere:
`current-phase-status.md` Scope/Out "Recording auto-start … the recording is
armed, the owner starts it"; `story-03-event-born-recordings.md:35-39`
"ARMED, not started … Auto-starting the recording at event time" is Out;
design D1 "each auto-created recording is armed, never started (Article IV)"
and D3 "(Article IV: armed, not started)"; `docs/USER_GUIDE.md:1376-1377`
"Armed never means started: the recording waits for the conductor's existing
capture flow" — the existing capture flow IS the firing. Article VI:3. The
test that carries the claim, `TestNeverStarted::test_no_recording_state_from_event_born`
(`test_hs175_event_recordings.py:290-299`), runs only the ingest conductor
and asserts the row is not already `recording` — it never runs the conductor
that fires. Article IX: a hollow proof.

**H1-2 (P0) — the owner's cancel is re-armed.** The unique index is partial:
`WHERE calendar_event_id != '' AND enabled = 1` (`holdspeak/db/schema.py:3493-3494`).
Every cancel path ends `enabled=0` (`scheduled_recording_conductor.py:427-438`;
`db/scheduled_recordings.py:333-353`). `_create_event_born_recordings` reads
"none exists" as "no live arm" (`calendar_ingest_conductor.py:612-624`, the
`UNIQUE constraint failed` catch at `:693-695`) and inserts again. Reproduced
(`scratchpad/repro175.py` R4, temp DB):

```
created: sr_236b45cefc03 idle True
after owner cancel + refresh: [('sr_783e6cba1320', 'idle', True), ('sr_236b45cefc03', 'cancelled', False)]
```

The H6/H7 lane reproduced the same with the real cancel path and found the
second arm leaves **zero** new receipts: the create receipt is idempotent on
`event_born:{event_id}` (`:701-713` → `INSERT OR IGNORE` at `:770-824`).
Article V:2 — an attempt without a receipt.

**H1-3 (P0) — a removed or disabled source leaves its recordings armed.**
(H8/H9 lane, reproduced.) `refresh()` prunes a removed source's events
(`calendar_ingest_conductor.py:194-195` → `db/calendar_events.py:125-142`) but
R3 cancel runs only inside `_refresh_source` for sources still enabled
(`:359-362`, `:392`, `:533`); `cancel_for_event_removed` has no other caller.
With **zero** enabled sources `refresh()` returns at `:184-186` before the
prune at `:194`, so disabling the last source never removes its events: the
arrival keeps saying `NEXT · <removed meeting>` (the Door reads
`calendar_events` with no source gate, `door_service.py:268-272`;
`ChairHome.tsx:539-542` prefers `next` over NO CALENDAR) while the strip hides
(`ChairHome.tsx:576`). Article IV inverted by his own Remove.

**H1-4 (P1) — `ARM ROOM MEETINGS ONLY` needs two refreshes for a new event.**
Per-source auto-create runs inside `_refresh_source` (`:392`) BEFORE the
matcher runs once per `refresh()` (`:197-202`), so a new event's link does
not exist when its arm is decided. Reproduced (R2): `after refresh 1:
links=1 recordings=0 / after refresh 2: links=1 recordings=1`. A meeting
accepted 20 minutes ahead under this mode is never armed. Move the matcher
before the per-source create, or run the create after the matcher.

**H1-5 (P2) — the create receipt names the event but not the rule.**
`_write_event_born_receipt` (`:701-713`) carries `calendar_event:{id}`; not
`all_calendar` / `room_linked` / the link's `match_source`. Article V:2
"who, what, where" — the "why" is the toggle, and it is not on the receipt.

### H2 — Egress: where the pipeline leaves the machine (Article III, A.9)

**The ICS path is right.** The only fetch is `CalendarSourceReader._read_https`
(`calendar_ingest_conductor.py:107-135`): no headers, no cookies, no proxy,
redirects refused by name. The Settings row's host comes from the same URL
(`holdspeak/web/routes/calendar_sources.py:43-52`, `egress: host is not None`
at `:157`); file sources carry no host (`test_file_source_no_egress`). The
sweep receipt names the HTTPS host per source (`heartbeat_service.py:335-345`).
The MeetingWatchSource reads only local tables
(`holdspeak/services/watch_sources.py:406-560`; `test_zero_egress`).

**H2-1 (P1) — the snapshot's vision egress is never on a face, and is
recorded only after the bytes left.** B6 paid the *recording*: the direct
dispatch now ranks `same_device < paired_device < private_network <
external_service` (`calendar_snapshot_service.py:580-597`) and derives
`egress.host` from the revision endpoint (`:640-653`) — but only on success
(`:637`); a cloud dispatch that fails returns `egress: None` (`:655-661`)
after the image was sent. The route keeps only the LAST image's egress
(`routes/calendar_snapshot.py:98-105`, `:129-130`). And no face reads it:
`CalendarSnapshotReviewCore.tsx` has no `egress`/`EgressChip` (grep: none);
the Settings `Snapshot` verb (`SettingsCore.tsx:1423`) posts the upload with
no host chip beside it. Article III:2 says "at the point of decision"; A.9
says "never missing where a fetch is triggered". The `paired_device` → `mesh`
scope records no host either (`:650`) — bytes leave this machine to another.

**H2-2 (P2) — `THIS DEVICE` on a file ICS row.** The built shot
`story-03-shots/settings-calendar-1440.png` shows `ICS · THIS DEVICE` on the
file source `WORK`. The design's own law row says "`NO EGRESS` never stated
— absence is the signal" and D2(c) "Absent for file sources". The board shows
`THIS DEVICE` only on the SNAPSHOT row (where a model runs). A reassurance
chip is A.9 decoration.

### H3 — The Room link: the false positive, and `Unlink` on both faces

**H3-1 (P0) — `Unlink` exists on neither face.** Addendum 1 condition 4
(paid on paper): "`Unlink` on either face removes it
(`DELETE /api/calendar/events/{id}/link`)". The route exists
(`holdspeak/web/routes/calendar_events.py:87-106`). `grep -in "unlink|link to
room|/api/calendar/events"` over `ChairHome.tsx`, `ProjectRoomCore.tsx`,
`SettingsCore.tsx` → one hit, the unrelated `project.resource.unlinked` label
(`ProjectRoomCore.tsx:202`). The arrival's event row carries `ROOM · <name>`
and `Cancel` only (`ChairHome.tsx:1249-1290`); the Room's MEETINGS row carries
`Pause`/`Resume` only (`ProjectRoomCore.tsx:1028-1080`). There is no `Link to
Room` picker either (design D3 "Explicit link"). A wrong auto-link cannot be
undone from any face.

**H3-2 (P1) — even the API unlink of a title link is undone in 15 minutes.**
`replace_auto_links` deletes every non-manual row and re-inserts the matcher's
output (`holdspeak/db/calendar_event_projects.py:105-123`); DELETE `/link`
removes rows but writes no suppression (`calendar_events.py:87-106`). The next
`refresh()` re-links the same event to the same Room. A durable unlink needs a
tombstone (`match_source='suppressed'` or a `(event uid, project)` deny row).

**H3-3 (P0 chain) — a realistic mislink that arms.** Rooms named after a
common word of ≥ 4 letters (`Design`, `Hiring`, `Mobile`, `Growth`, `Weekly`,
`Platform`) whole-word-match every event containing it. Reproduced (R1):
Room `Design` + event "Design your 401k plan (webinar)" with a Zoom URL under
`room_linked` → `links: [('ce_70bb8', 'title')]` → `recordings after refresh
2: [('Design your 401k plan (webinar)', True, 'idle', 'calendar_event')]`. The
"longest Room name wins" rule cannot help when only one Room matches. The
design's own example (Rooms `Platform` and `Review`, event "Platform
Architecture Review") resolves to `Platform` by length, which is the right
one — the failure mode is a single common-word Room, not two competing ones.

**H3-4 (P1) — the matcher's Watch-query branch is broken SQL.**
`SELECT query FROM connector_watches WHERE project_id = ?`
(`calendar_ingest_conductor.py:229-232`) — the column is `query_json`
(`db/schema.py:2309`). Every refresh logs `watch query load failed for
project <id>: no such column: query` once per Room (repro output, R1/R2).
Census N3 "the logged Watch-query load" paid a warning for a query that can
never run. Even fixed, the column is a JSON string
(`{"repository":"acme/platform"}`, R3) that `re.escape` turns into a pattern
no title contains; the design's "compare against the Room's sources (Watch
query strings)" is dead code either way. Drop the branch or match on the
decoded values.

**H3-5 (P1) — a manual link is orphaned when the event's time changes.**
Projection id = `sha(revision, uid, starts_at)` (`calendar_ingest.py:412-415`);
`calendar_event_projects` has no FK and no rebind. Reproduced (R5): after the
event moves one hour, `links for new id: []` and the manual row survives
against a dead id forever (`replace_auto_links` never touches manual rows).
The recording rebinds by uid (R2 at `:483-522`); the link does not. Editing a
source's URL changes the revision and orphans every manual link at once.

### H4 — Counters of zero and one count (A.8, B1)

**No zero prints.** Every 175 count is gated by truthiness or `countToken`
(`ChairHome.tsx:576, 599, 616, 1233`; `SettingsCore.tsx:1455-1461` — the
lead is clamped ≥ 1 at `meeting.py:170` so `0 MIN BEFORE` cannot print;
`BriefView.tsx:216-218, 296-335`; `project_service.py:929-930`). The A8
scanner (`scripts/ux_canon_scan.py:260-291`) reports zero hits on the 175
lines — and is blind to server-formatted tokens, which is where the lies
below live.

**H4-0 (P1, a lie on a face) — `WEEKLY MON 08:00` names a cadence that does
not exist.** `CadenceCore.tsx:459-461` prints it whenever the calendar is
configured. The brief regenerates once per DAY after quiet hours close
(`holdspeak/runtime/cadence.py:97, 114` → `should_send_daily_brief`,
`holdspeak/cadence/brief.py:98-105`; no weekday anywhere). The design D2(e)
cited "runtime/cadence.py:62" for a weekly cadence; nothing there is weekly.
The rig enshrines the token (`test_hs175_rhythm_brief_glass.py:307-308`).
Article VI:3. Say `DAILY 08:00` (the truth) or build the weekly cadence.

**H4-1 (P1) — the strip's days are UTC days.** `_week_strip` buckets by
`SUBSTR(starts_at,1,10)` on UTC-stored `starts_at` from a UTC Monday
(`door_service.py:378-410`; `db/calendar_events.py:171-186`;
`calendar_ingest.py:407` stores `+00:00`). The owner is at −06:00: a Monday
20:00 meeting is a TUE dot; on Sunday evening at 18:00 local the strip is
already next week. Dots == total holds (same buckets), so the B1 invariant
passes while the day is wrong. Same UTC week in `matched_this_week`
(`calendar_sources.py:55-64`, backlogged) and `LAST READ HH:MM`
(`calendar_sources.py:141-146`) — the shot shows `LAST READ 23:47` beside a
menu-bar clock of 05:47 PM, and the Room shot `CHECKED 23:47` beside a footer
`READ 17:48`. Article VI:1 approximations labeled — these are not labeled.

**H4-2 (P1) — the calendar section's count is not "this week".** B1 ruled
"the MEETINGS section counts ITS ROWS (what is still coming)". The rows are
`door.upcoming` calendar events with **no horizon** (`ChairHome.tsx:510-516`;
`list_upcoming` filters only `starts_at >= now`, `db/calendar_events.py:153-160`).
A four-week ICS feed lists four weeks under a caption that now reads `THIS
WEEK N` (tree, B10, `ChairHome.tsx:1253`) — the caption became a lie the
moment B10 renamed it. Bound the rows to the strip's week end.

**H4-3 (P1) — `N CALENDARS` counts events.** `COUNT(DISTINCT uid)`
(`calendar_sources.py:85-89`) is the VEVENT count; the unit test seeds two
events and asserts `2` (`tests/unit/test_hs175_calendar_sources.py:97-113`).
A 40-event feed reads `40 CALENDARS`. Carried faithfully from the design's own
text (D2(c) "distinct calendar UIDs") — a design defect, still a lie on the
face (A.10, VI:3). `N EVENTS`, or drop it.

### H5 — The real Watch: idempotency, retire, pause, the sweep

**Idempotent across the two paths and the backfill** — yes, while the
watch is `active`/`paused`: `ensure_meeting_watch` checks
`state != 'retired'` twice (`watch_service.py:1274-1281`, `1307-1315`);
`routing_glue.py:311-316` and `project_service.py:2806-2811` call it on link;
the sweep backfills Rooms lacking a non-retired meeting watch
(`heartbeat_service.py:361-395`). A Room cannot end with two live meeting
Watches (`test_linking_two_meetings_creates_one_watch`).

**H5-1 (P1) — `Retire` is undone by the next sweep or the next link.** The
retired row is excluded from both existence checks, so `ensure_meeting_watch`
creates a new one. Reproduced (R6): `created: w_f0964d384b4f` → retire →
`ensure again -> w_32d2d0990bb4 | watches on room: [('w_32d2d0990bb4',
'active'), ('w_f0964d384b4f', 'retired')]`. The heartbeat's backfill SQL
(`heartbeat_service.py:369-378`) runs every sweep, not "once" as B2 says: a
retired meeting Watch is resurrected within 15 minutes. A.11 in reverse — a
verb whose effect is silently reverted. Fix: treat a retired meeting watch as
"the owner said no" (exclude Rooms with ANY meeting watch from backfill; the
link path likewise).

**H5-2 (P1) — `Pause` never shows as paused; `Resume` is unreachable.**
`pause_watch` sets `state='paused'` and leaves `enabled` alone
(`watch_service.py:356-367`); `_read_room_sources` derives `paused` from
`enabled` only (`project_service.py:855-861`). Reproduced (R7): `state=
paused enabled= True` → `room sources: [('meeting', 'live', ['1 THIS
WEEK'])]` — the row still says `Pause`. The sweep does honour the pause
(`list_due_watches` filters `state IN ('active','tested')`,
`db/automations.py:433-450`), so evaluation stops while the face says live.
This grammar is shared with the GitHub/Jira rows — likely inherited from
167/169 — but B2 claimed "Pause/Resume are real" for this row, so 175 owns
proving it. `list_project_watches` also returns retired rows
(`db/automations.py:137-145`), which the (provider, scope) merge folds into
the live row.

**H5-3 (P2) — creation on the link path has no receipt.** B2: "both
receipted". The sweep's receipt carries `meeting_watch.backfill`
(`heartbeat_service.py:425-427`); `ensure_meeting_watch` writes none, and
neither caller does (`routing_glue.py:311-316`, `project_service.py:2806-2811`).

**H5-4 (P1) — the Room row's `NEXT` can never be true on a real desk.**
The tokens read the Watch's entities, which are `meetings` rows
(`watch_sources.py:441-450`, `date = started_at`); `NEXT` is "first entity
with `date > now`" (`project_service.py:936-950`). A recorded meeting never
starts in the future. The board's `MEETINGS · 2 THIS WEEK · NEXT THU 14:00`
was specified from linked *calendar events* (D2(d) "the next meeting linked
to this Room"); the build never reads `calendar_event_projects` for the row.
The rig gets its `NEXT SUN 14:00` by seeding a meeting with a future
`started_at` (`tests/e2e/test_hs175_room_glass.py:280-294`) — a state the
product cannot produce (Article IX). Also `N THIS WEEK` compares naive local
`isoformat()` strings with stored `started_at` (`project_service.py:922-930`).

### H6 — The brief's two windows (H6/H7 lane; verified by me on the wire)

**`compute_window` unchanged** — body byte-identical to `be6c630e`
(docstring only; `monday_brief_service.py:137-161`). ✓

**H6-1 (P1) — the forward half compares naive local strings with UTC
`starts_at`.** `generate()` is always called with a naive local `now`
(`runtime/cadence.py:112,121`; `routes/monday_brief.py:112`), and
`compute_lookahead(period_end)` inherits it (`:213`), so census N1's
"tz-aware default" at `:171` is never reached from production. Lane repro
under `TZ=Europe/Warsaw`: a next-week Monday 00:30 local event counted in
"3 meetings this week"; `Next:` skipped the meeting one hour away and printed
its UTC time.

**H6-2 (P1) — the halves overlap; the promised dedup does not exist.**
Condition 2 ruled `now → Sunday 23:59` and "never overlap"; `generate()`
uses `week_start = Monday 00:00` for the meeting count and commitments-due
(`:204-211`, `:716-721`, `:840-847`), so Monday-afternoon meetings are a
SINCE FRIDAY row AND inside "N meetings this week". D3 and story-05:81 promise
dedup by `calendar_uid`; none exists (`grep calendar_uid` in the service: 0).

**H6-3 (P1) — the headline miscounts.** `_compose` (`:305-320`) counts
every non-count `this_week` item (`Next:`, `N armed`, due rows) as a "watch
item" → `3 meetings this week, 3 watch items` on a desk with zero Watch
changes; the shade flattens to `4 THINGS` (`SystemShade.tsx:125`, `:548`);
Rhythm maps `calendar:armed` to `WATCH ITEMS` (`CadenceCore.tsx:287-288`).
No zero can print (truthiness gates, `:296-331`) — that part is honest.

**H6-4 (P2) — the `text | YYYY-MM-DD` DUE contract.** `" | ".join`
(`:866-871`) vs `.split(" | ")` (`BriefView.tsx:210-212`): a `|` in the
commitment text drops the day; an empty text prints the date as the text;
`new Date("YYYY-MM-DD")` is UTC midnight so `dayToken` prints `THU` for a
Friday west of UTC. Carry `due_at` as its own field.

**H6-5 (P2) — `Generate` returns the day's cached brief** (`:191-198`), so
Rhythm's verb never regenerates after the first run and the `Next:` line goes
stale all day; inherited mechanism, new consequence. Section vocabulary:
`this_week` is enforced only by `_SECTIONS` (`:15`) and `test_brief_mcp.py:47`;
no other reader switches on section names — no breakage found.

### H7 — The orphan row and the cancelled recording (H6/H7 lane)

Verified sound: a cancelled recording is never ARMED (`list_enabled` filters
`enabled=1`, `db/scheduled_recordings.py:126-131`); a moved event rebinds
`next_fire_at` (R2, `:483-522`) and shows as an event row wearing `ARMS`, not
as an orphan; a title change follows through R1 (`:420-449`). B3's provenance
fix holds (`door_service.py:274-300`; `test_hs175_door_orphan.py`, 3 tests).

**H7-1 (P0) — the arrival's `Cancel` is a dead verb for the row's whole
visible life.** `ChairHome.tsx:524-527, 1282, 1327` → `cancelArmedSchedule`
(`scheduledRecordingSlice.ts:68-77`, `catch { return false }`) → `POST
/api/scheduled-recordings/{id}/cancel` → `cancel_armed` refuses unless
`state == "arming"` (`scheduled_recording_service.py:436-440`, 409
`not_armed`). Event-born rows are `idle` from creation until `starts_at − 5
min` (`db/scheduled_recordings.py:96`; `scheduled_recording_conductor.py:338-359`)
and `arming` for ten seconds. The face refetches `/api/door` and the row
stays `ARMS 09:55 · Cancel`. No refusal named (V:3, A.10); a verb that does
nothing (A.11). The glass rig asserts the button's presence only
(`tests/e2e/test_hs175_arrival_glass.py:469-470`, `578-579`); story-03's
"Override and cancel work" box is unchecked and no cancel test exists.

**H7-2 (P2) — R1/R2/R3 leave no receipt.** Refresh-in-place, rebind and
event-removed cancel are `log.info` only (`calendar_ingest_conductor.py:449,
523, 534`); the design promised `scheduled_recording.cancelled.calendar_event_removed`.

### H8 — The Settings rows (H8/H9 lane)

Verified sound: every verb writes through PUT `/api/settings`
(`SettingsCore.tsx:1255, 1381, 1394`; `system/settings.py:86`); Remove's
confirm is an in-world Button pair (`:1389-1397`; no `confirm(`); no raw
`<button>`; `meeting.auto_record` round-trips face → config → conductor
(`:1453`; `meeting.py:49`; `calendar_ingest_conductor.py:604`); Save on an
`http://` URL shows a plain reason with no stack (vitest
`SettingsCalendar.test.tsx:155-174`, 14 passed).

**H8-1 (P1) — Remove of the SNAPSHOT source leaves the extracted ICS on
disk** (`~/.local/share/holdspeak/calendar-snapshots/<id>.ics`,
`calendar_snapshot_service.py:354-363`; the only `unlink` is the tmp-file
cleanup at `:375`). Custody residue after "Remove" — the owner's hard
boundary.

**H8-2 (P1) — `Edit` on the SNAPSHOT row pre-fills the generated path**
(`SettingsCore.tsx:1380`); saving another URL keeps the `SNAPSHOT` type
(derived from the label, `:1356`, route `:37-40`) and the next upload
overwrites it back by label (`calendar_snapshot.py:188-190`). Withhold `Edit`
on snapshot rows.

**H8-3 (P2) — the refusal wording is the wire's**: `calendar source
"sources[2]": calendar.subscription must be a file path or HTTPS URL`
(`settings_service.py:936-945` ← `integrations.py:84`). Plain, but a 146-era
key name; canon grammar is `CAN'T READ · must be a file path or HTTPS URL`. A
nonexistent file path is accepted silently (`integrations.py:69-72,97`) and
the row sits `idle` forever with no reason (the backlogged per-source status;
`BACKLOG.md:1049`).

**H8-4 (P2) — a disabled source loses its facts** (the route skips it,
`calendar_sources.py:120-121`) while its events stay on the desk until the
next refresh (or forever — H1-3). `5 MIN BEFORE` is real config but editable
nowhere on the face. Neither Remove nor Disable pokes the conductor
(`settings_service.py`: no refresh trigger), so a removed source's events
show for up to 900 s.

### H9 — The walk runner `tests/e2e/live175_walk.py` (H8/H9 lane)

Decision table denies every write by name and there is no flag that lifts
it (`:1461-1463`; all API calls GET). Bundle check raises `HUB SERVES NO
BUNDLE` (`:1536-1540`). All 17 `data-testid` selectors match the built faces
(tree; at `bda20aa8` proper the Settings leg opened `"open-settings"`, a key
no opener answers — hollow until the tree fix).

**H9-1 (P1) — one latent write path.** The runner clicks `Continue later`
whenever `chair-first-value` renders (`:213-215`, `:1547-1553`);
`FirstWords.tsx:253-265` POSTs `/api/notes` when text is present and
`:212-218` POSTs `/api/desk/seed` + PUTs `/api/setup/onboarding`. Not
reachable on his onboarded desk; the "arms nothing" law at `:7-8` is not true
by construction. Deny the click, or assert the chair is absent.

**H9-2 (P1) — the walk that ran proved none of the seven beats.**
`evidence-story-06.md` (tree, 2026-09-06T00:00:31Z): `calendar=False,
upcoming=1, auto_record=off`; `walk-facts.md`: `week_days 0`,
`meeting_rows_with_room 0`, `meeting_rows_with_arms 0`, `meetings_source_present
False`, `brief_row_label Monday brief`. Every 175 fact is `DATA`, none
`MATCH`. The runner is honest (it stops at nothing and says so), but story 06
is marked done on a desk with no calendar; D5 beats 1–6 and the three owner
questions were not walked. Story-06's own note (`:60-62`) says the
prerequisites "must be set up during the walk". The walk also found the
inherited `AUG 20 Sprint` duplicate (A.7) and expected-value vocabulary that
is stale (`:872`, `:881`).

### H10 — Boards vs build

**H10-1 (P1) — two `MEETINGS N` sections on one arrival at `bda20aa8`.**
The 172 recorded-meetings section (`ChairHome.tsx:665-673`, caption `:1037`)
and the new calendar section (`:599-606`, caption `:1249`) both render, both
under `data-testid="arrival-meetings"` (`:601`, `:666`); the boards draw each
alone. The tree's B10 recaptions the calendar section `THIS WEEK` — right
call — but leaves the duplicate testid and the unbounded rows (H4-2).

**H10-2 (P2) — the strip's overflow reads `{count}+`** (`ChairHome.tsx:1220-1224`,
`7+` for seven; the design says `5+`), and the overflow span reuses
`data-testid="arrival-week-dot"`, so the rig's dots == total would fail at
5+ (the rig seeds 3).

**H10-3 (P2) — Rhythm's summary never singularizes and mislabels ARMED.**
`CadenceCore.tsx:282-288` builds `${n} MEETINGS · WATCH ITEMS · COMMITMENTS
DUE` by regex: the shot reads `1 WATCH ITEMS · 1 COMMITMENTS DUE`
(`rhythm-weekly-brief-1440.png`); `calendar:armed` is counted as a WATCH
ITEM while the brief face calls it `1 ARMED` (`BriefView.tsx:217`).
`countToken` exists for this.

**H10-4 (P2) — two ratified PNGs are stale against their mockups.**
`story-01-shots/ArrivalArmedOrphan.png` still reads `3 MEETINGS THIS WEEK` /
`MEETINGS 2` (condition 1 says "Board: strip now reads 2";
`mockups/ArrivalArmedOrphan.dc.html` does); `SettingsMeetingsCalendar.png`
and `…Phone.png` carry no `N MATCHED THIS WEEK` though the mockup HTML does
(condition 5). The build follows the addendum. Re-export the PNGs so the
owner's word is on what was built.

**H10-5 — inventory.** Build shows, board does not: `Snapshot` beside `Add`
(ruled below); per-row `Edit · Disable/Enable · Remove` at rest (B9, real
handlers `SettingsCore.tsx:1380-1396`, in-world confirm); `THIS DEVICE` on
file ICS rows (H2-2); `PEOPLE · UNAVAILABLE` on the brief
(`BriefView.tsx:414-417`, a pre-175 L2 state the board omits — honest, keep);
the 393 Intelligence-row overlap (parked `BACKLOG.md:1048`). Board shows,
build does not: source emblem chips on SINCE FRIDAY rows (rendered only when
`sourceEmblem()` resolves, `BriefView.tsx:363-365`; the rig never exercises
it — unshot); `Retire` on the Room row (D2(d); the ratified board itself
shows `Pause` only — build matches the board). Matches: NEXT with the Room
token (`ChairHome.tsx:245-255, 421-425`); event row `ROOM / source / ARMS /
Cancel` (`:1258-1287`); the orphan row without hollow parentheses (B3);
Auto-record with `5 MIN BEFORE` only when not OFF and `N MATCHED THIS WEEK`
only under `room_linked` (`SettingsCore.tsx:1455-1461`); the Room row's
`MTG MEETINGS · CHECKED/NEVER · Pause/Resume`; the brief's THIS WEEK rows.
`.arrival-orphan-from` is 10px (`chair.css:204-207`), off the type scale.
Every verb on the four faces has a real handler; no raw `<button>`.

- `SettingsMeetingsCalendar.png` vs `settings-calendar-1440.png`: the board
  has no verbs on source rows and no `Snapshot`; the build has `Edit ·
  Disable · Remove` per row (B9) and `Add · Snapshot` (B7). Ruled below.
  The build shows `THIS DEVICE` on a file ICS row (H2-2) and `LAST READ` in
  UTC (H4-1). The board's `2 CALENDARS` is the design defect H4-3 carried.
- `RoomSourcesMeetings.png` vs `room-sources-meetings-1440.png`: the shot's
  `NEXT SUN 14:00` is a seeded impossibility (H5-4); `CHECKED 23:47` beside
  `READ 17:48` (H4-1); `Pause` only, no `Retire` on the live row (design
  D2(d) lists `Pause / Resume / Retire` — `Retire` sits on the cant-check
  row only, `ProjectRoomCore.tsx:994`); the `SUGGESTED` row's `Add` has no
  handler (`:1016`, inherited).

**Ruling on the `Snapshot` verb (B7 asked counsel).** It stays beside `Add`
on the Connect-calendar row: it is the vision adapter's only entry, it opens
a real face, and a working verb is never dropped (A.11 inverse). Two
conditions ride with it: the egress host of the vision model must be on that
face before the upload (H2-1), and `Edit` is withheld on the row it creates
(H8-2).

---

## Conditions

| # | What | Where | How to prove |
|---|---|---|---|
| **C1** | Settle "armed, never started" one way. Either (a) an event-born recording arms without firing — the conductor's `_arm` for `born_from='calendar_event'` enters `arming` with no countdown fire and waits for the owner's start (his existing `Record` on the armed row), or (b) his word rules the Auto-record toggle IS consent to start capture at `starts_at − lead`, and the copy is corrected everywhere it lies: `current-phase-status.md` Scope/Out, `story-03:35-39`, design D1/D3, `docs/USER_GUIDE.md:1376-1377`, and the toggle's own token gains the fact (`RECORDS AT −5 MIN`). | `scheduled_recording_conductor.py:362-421`; the docs named | A test that runs BOTH conductors on a temp DB: ingest → `_tick` at `next_fire_at` → assert the terminal state (a: `arming` with no `_start_meeting_fn` call; b: `recording`). `TestNeverStarted` is replaced or renamed to what it proves. |
| **C2** | A real `Cancel` on the arrival: for an `idle` event-born row the verb disables it (`enabled=0, state='cancelled', last_outcome='owner_cancelled'`) with a receipt; the refusal, if any, is named on the row. The store stops swallowing errors (`scheduledRecordingSlice.ts:68-77`). | `scheduled_recording_service.py:422-470` (a new `cancel` that accepts `idle`), `ChairHome.tsx:524-527` | Unit: cancel on idle → row disabled + receipt; glass rig: click → the row loses `ARMS` (`test_hs175_arrival_glass.py`). |
| **C3** | The owner's cancel is final: `_create_event_born_recordings` skips any event that has a row with `last_outcome IN ('owner_cancelled','cancelled')` for the same `calendar_event_id` (or a tombstone keyed by `(source_id, uid)` so a rescheduled occurrence stays cancelled). | `calendar_ingest_conductor.py:612-699` | R4 of `scratchpad/repro175.py` inverted: after cancel + refresh, exactly one row, `enabled=0`. Add it to `test_hs175_event_recordings.py`. |
| **C4** | Remove/Disable disarms: the prune runs even with zero enabled sources (`refresh()` `:184-195`), and every enabled recording whose `calendar_source_id` is no longer enabled is cancelled with `last_outcome='calendar_source_removed'` and a receipt. Removing the SNAPSHOT source deletes its ICS file. | `calendar_ingest_conductor.py:175-202`; `calendar_snapshot_service.py:354-363` | The H8/H9 lane's repro (`scratchpad/repro_orphans.py`) inverted; `calendar_events` empty and no enabled recordings after the last source is removed. |
| **C5** | `Unlink` on both faces (condition 4 of the ratified design), durable: DELETE `/link` writes a suppression row (`match_source='suppressed'`) that `replace_auto_links` honours; the arrival's event row and the Room's MEETINGS row carry `Unlink` (ghost dense). `Link to Room` may stay parked if he keeps V0 auto-link. | `db/calendar_event_projects.py:105-123`; `routes/calendar_events.py:87-106`; `ChairHome.tsx:1249-1290`; `ProjectRoomCore.tsx:1028-1080` | Unit: unlink → refresh → still unlinked; glass rig at 1440/393 with the verb in frame; `ux_canon_scan` A1 unchanged. |
| **C6** | The matcher: fix or drop the Watch-query branch (`SELECT query` → the column is `query_json`; the values are JSON), run the matcher BEFORE the per-source auto-create, and rebind manual links by `(source_id, uid)` when a projection id changes (or delete orphan manual rows in `replace_auto_links`). Publish the common-word risk as the owner's question 1 with the R1 evidence. | `calendar_ingest_conductor.py:197-202, 229-232, 392` | R1–R3, R5 of `scratchpad/repro175.py` inverted; no `no such column` warning in the refresh log. |
| **C7** | The meeting Watch's verbs are real: `Retire` is not resurrected (backfill and link path skip Rooms with any meeting watch, or key on a `retired_by_owner` mark); `Pause` shows `Resume` (`w_state` reads `state`, not `enabled`, in `_read_room_sources` — shared with GitHub/Jira rows, so prove all three); creation on the link path is receipted. | `heartbeat_service.py:361-395`; `watch_service.py:1262-1376`; `project_service.py:855-861` | R6/R7 inverted; `test_hs175_meeting_watch.py` gains retire-stays-retired and pause-shows-paused. |
| **C8** | Local time everywhere the face prints a clock or a day: the strip's day buckets, `LAST READ`, `CHECKED`, `matched_this_week`, the brief's lookahead, the Room's `N THIS WEEK`. One week-boundary helper (the backlog already names it) taking the owner's tz; the brief's `generate()` receives an aware `now`. | `door_service.py:378-410`; `calendar_sources.py:55-64, 141-146`; `monday_brief_service.py:146, 171, 204-211`; `project_service.py:922-950` | A unit test at `TZ=America/Denver` with a Monday 20:00 local event: MON dot, `LAST READ 17:47`; the H6/H7 lane's `repro_h6.py` inverted. |
| **C9** | Honest tokens: Rhythm's row says `DAILY 08:00` until a weekly cadence exists (H4-0); the arrival's calendar section bounded to the week it is captioned with (`THIS WEEK N` == rows in `[now, week_end)`) and the duplicate `arrival-meetings` testid split; `N CALENDARS` → `N EVENTS` (or a real calendar count); the Room row's `NEXT` from linked calendar events (`calendar_event_projects`) or withheld; the rig seeds only states the product can produce; `THIS DEVICE` off file ICS rows; the strip overflow `5+` per the design; Rhythm's summary through `countToken` with ARMED named. | `CadenceCore.tsx:282-288, 459-461`; `ChairHome.tsx:510-516, 601, 1220-1224, 1253`; `calendar_sources.py:85-89`; `project_service.py:936-950`; `test_hs175_room_glass.py:280-294` | The A8 scanner stays green; the four rigs re-shot at 1440/393 beside the boards; the two stale board PNGs re-exported from their mockups (H10-4). |
| **C10** | The snapshot's egress on the face before the upload: an `EgressChip` with the resolved vision host (or `THIS DEVICE`) beside `Snapshot` and on the review core, resolved from the same ranking the dispatch uses; egress recorded on failure too; `paired_device` records the host. | `SettingsCore.tsx:1423`; `CalendarSnapshotReviewCore.tsx`; `calendar_snapshot_service.py:637-661` | `test_hs175_snapshot_model_fence.py` gains the failure-path host; a shot with the chip in frame. |
| **C11** | The brief's two windows as ruled: the forward half reads `[now, Sunday 23:59]` (not `week_start`) for the meeting count and commitments due; dedup by `calendar_uid` against the lookback's `Meeting recorded` rows; `_compose` counts calendar items as calendar items (`N meetings · next · N armed · N due`), not "watch items"; `due_at` carried as a field. | `monday_brief_service.py:204-211, 305-320, 716-721, 840-871`; `BriefView.tsx:210-212` | `test_hs175_week_brief.py` with UTC-stored `starts_at` and a Monday-afternoon meeting: appears once. |
| **C12** | The walk is walked: story 06 flips done only after his desk has a source connected, the strip, NEXT with a Room token, an armed row, the Room's MEETINGS row and the THIS WEEK brief — each a `MATCH` in `walk-facts.md` — and his three answers recorded verbatim. The runner's `Continue later` click is denied by the decision table. | `tests/e2e/live175_walk.py:213-215, 1547-1553`; `story-06-the-walk.md` | `walk-facts.md` with `MATCH` rows for the seven beats; the shots beside the boards. |

## P2s (ledger, pay when touched)

- P2-1 The create receipt names the rule (`all_calendar` / `room_linked` /
  `match_source`) — `calendar_ingest_conductor.py:701-713`.
- P2-2 R1/R2/R3 reconciliation receipts (design promised
  `scheduled_recording.cancelled.calendar_event_removed`) — `:449, 523, 534`.
- P2-3 Withhold `Edit` on the SNAPSHOT row; `5 MIN BEFORE` editable or
  labelled fixed — `SettingsCore.tsx:1380, 1456`.
- P2-4 Save's refusal in canon grammar (`CAN'T READ · …`), and a file path
  that does not exist refused at Save — `integrations.py:69-97`.
- P2-5 Remove/Disable poke one conductor refresh — `settings_service.py`.
- P2-6 `Generate` regenerates (`monday_brief_service.py:191-198`); the
  heartbeat's generate gets a receipt (`cadence.py:119` NullObserver).
- P2-7 The `SUGGESTED` row's `Add` has no handler (`ProjectRoomCore.tsx:1016`,
  inherited from 172) — withhold or wire.
- P2-8 `Retire` on the live meeting row (design D2(d)); today only on the
  cant-check row (`ProjectRoomCore.tsx:994`).
- P2-9 The runner's expected-value vocabulary (`live175_walk.py:872, 881`).
- P2-10 Per-source refresh status (already `BACKLOG.md:1049`) — the row can
  never say `failure` (`calendar_sources.py:125-131`); Article VI:2.
- P2-11 The 393 Intelligence-row overlap (already `BACKLOG.md:1048`).
- P2-12 `.arrival-orphan-from` at 10px, off the type scale (`chair.css:204-207`).
- P2-13 The brief's SINCE FRIDAY emblem chips are unshot (`BriefView.tsx:363-365`);
  a rig row whose `source_ref` resolves would prove the board's chip.
- P2-14 The rig's `count() >= 1` on `arrival-meetings` cannot catch a
  duplicate section (`test_hs175_arrival_glass.py:434-437`); assert one.

## The owner's questions (carried from the design, plus counsel's)

1. **Auto-link vs suggestion-only.** V0 auto-links by ≥ 4-letter whole word.
   Counsel's evidence: a Room named `Design` links a 401k webinar and, under
   `ARM ROOM MEETINGS ONLY`, arms it (R1). Does he want the 172 `SUGGESTED ·
   Add / Dismiss` grammar instead, or auto-link with a durable `Unlink` (C5)?
2. **The two-window brief.** `SINCE FRIDAY` (unchanged) + `THIS WEEK`
   (forward to Sunday). Does one brief with two clocks read right on a
   Monday, or does he want the week only?
3. **A confirmation step before an auto-linked event arms.** Counsel's
   sharpened form after H1-1: is the Auto-record toggle his consent to
   *start capture* at `starts_at − 5 min`, or only to arm and wait for his
   `Record`? (C1.) If start: does he want a longer countdown than ten
   seconds for calendar-born recordings, with the arrival showing it?
4. *(new)* **Remove means gone?** When he removes a calendar source, should
   its already-armed recordings cancel (C4) and the snapshot's extracted ICS
   be deleted from disk?
5. *(new)* **Whose clock?** The faces print UTC today (H4-1). His local time
   everywhere, or the calendar's own zone per event?
6. *(new)* **`Retire` on the meeting Watch.** Should a Room with linked
   meetings be allowed to have no meeting Watch (C7), or is the Watch a fact
   of the link that cannot be retired — in which case withhold `Retire`.

## What counsel could not verify

- The faces at runtime with a live hub — the dead `Cancel` and the paused
  row are proven at the service seam and by `python -c` against temp DBs,
  not clicked. A booted rig would confirm; counsel does not boot his hub.
- The owner's machine timezone (assumed −06:00 from the shots' menu-bar
  clock vs the `23:47` tokens; the H6/H7 lane reproduced under Warsaw).
- The CycleGadget snap-back on a slow PUT (H8/H9 lane, timing-dependent).
- Whether `Pause` on GitHub/Jira rows was already broken before 175 (the
  `enabled`-vs-`state` derivation predates the phase; not bisected).
- The snapshot flow end to end with a real vision model.

## Reproductions

- `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/1687fab9-1620-43a6-afab-0649194bf7ae/scratchpad/repro175.py`
  (R1 mislink-arms, R2 ordering, R3 JSON candidates, R4 re-arm after cancel,
  R5 orphaned manual link, R6 retire resurrected, R7 pause invisible).
- The H6/H7 lane: `repro_h7.py` (re-arm via the real cancel path, receipt
  count), `repro_h6.py` (brief tz), `repro_compose.py` (headline counts).
- The H8/H9 lane: `repro_orphans.py` (removed source leaves arms; last
  source never pruned).
- Scoped runs (isolated HOME): `tests/unit/test_hs175_event_recordings.py`
  + `test_hs175_calendar_wire.py` → `31 passed in 7.91s`;
  `test_hs175_calendar_sources.py` → `8 passed`; the five 175 unit files
  collect 56; vitest `SettingsCalendar.test.tsx` → `14 passed`.
