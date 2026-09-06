# Counsel on the built phase — 175 Calendar and the Clock — THE RE-READ

Counsel re-read the WORKING TREE of `feat/calendar-clock` (uncommitted, 2026-09-05
late) after the three fix lanes (W1 conductor + brief wire, W2 arrival, W3
Settings/Room/Rhythm). Read-only; every claim carries `file:line` from the tree;
every reproduction ran on a temp DB under an isolated HOME and never touched the
owner's database or hub. The first report (`counsel-on-built-175.md`, twelve
conditions C1–C12) is the yardstick; the design's Addendum 2 rulings B11–B15 are
the law the build is judged against — B11 (an event-born recording records at
the event; the toggle is consent to record; Cancel works the whole life and is
final) is the orchestrator's ruling and is not relitigated here.

---

## VERDICT: RATIFY-WITH-CONDITIONS

The spine is true now. An event arms a recording under the owner's standing
consent (OFF by default), he can take that consent back from the row for its
whole visible life, his cancel outlasts every refresh, Remove/Disable disarm and
prune, Unlink is durable on the face that shows the link, the matcher runs in
the right order with no phantom column, the faces print his clock, the brief's
two windows do not overlap and the headline counts what it counts, and the
meeting Watch's verbs mean what they say. Ten of twelve conditions are PAID; C1
and C8 are PARTIAL on small, named remainders; C12 is the owner's walk and is
honestly still open (story 06 `in-progress`).

What the re-read found are consequences of the rulings on the edges — a
recurring meeting, a DST week, a second arm of the same event, the Delete verb
— each a code fix of an hour, none a redesign. Six numbered conditions ride the
ratification; the owner's questions are carried below with the evidence.

Proof counsel ran (isolated HOME):

- `tests/unit/test_hs175_event_recordings.py test_hs175_calendar_wire.py
  test_hs175_cancel_owner.py test_hs175_calendar_sources.py
  test_hs175_meeting_watch.py test_hs175_week_brief.py
  test_hs175_door_week_local.py` → `152 passed in 43.85s`.
- `tests/unit/test_api_surface.py test_delta_schema.py test_door_routes.py
  test_door_mcp.py test_hs169_wire.py` → `77 passed, 1 skipped` (the skip is
  the owner's-real-DB guard).
- vitest `SettingsCalendar.test.tsx scheduledRecordingSlice.test.ts
  RhythmBriefSummary.test.ts room175sources.test.tsx
  pullouts/views/__tests__` → `Test Files 5 passed, Tests 49 passed`.
- The first report's seven reproductions re-run (below), plus nine new hunts in
  `scratchpad/reread175_hunt.py`.
- Not re-run by counsel: the four e2e glass rigs (the lanes' own logs in the
  scratchpad read `w2-rigs-all.log: 21 passed in 99.67s`, `w3_rigs2.log:
  rhythm 3 passed · settings 4 passed`); the shots under `story-0{2,3,4,5}-shots/`
  were read by eye against the boards.

---

## The reproductions, re-run

| Repro | Before (bda20aa8) | Now (tree) | Reading |
|---|---|---|---|
| R1 `Design` Room + 401k webinar under `room_linked` | links + ARMS | `links after refresh 1: [('ce_70bb8','title')]` · `recordings after refresh 2: [('Design your 401k plan (webinar)', True, 'idle', 'calendar_event')]` | **Reproduces BY DESIGN** (B14). Owner's question 1. Unlink is the remedy on the face. |
| R2 `room_linked` needs two refreshes | `refresh 1: recordings=0` | `after refresh 1: links= 1 recordings= 1` | PAID (C6b). |
| R3 Watch-query JSON candidates | warning every refresh | branch gone (`calendar_ingest_conductor.py:290-295`); `TestNoWatchQueryWarning` | PAID (C6a). |
| R4 owner cancel re-armed | second row `idle True` | `after owner cancel + refresh: [('sr_4c45…', 'cancelled', False)]` | PAID (C3). |
| R5 manual link orphaned on a time change | `links for new id: []` | `links for new id: [manual]`, no orphan row | PAID (C6c). |
| R6 retired Watch resurrected | `ensure again -> w_32d2…` | `after retire, ensure again -> None \| watches on room: [('w_349e…','retired')]` | PAID (C7a). |
| R7 pause invisible | row `live` | **crashes by design**: `w2 is None` (R6's ensure now returns None on a retired Room, so the script's `w2["id"]` is a TypeError). Pause is proven by `TestPauseShowsPaused` (MTG, GH, J) and the shot `room-sources-meetings-paused-1440.png` (`PAUSED · Resume`). | PAID (C7b). |
| `repro_h7.py` real cancel path | re-armed, zero receipts | `cancel_armed on idle row: SUCCEEDED` → after refresh #2 still one row `cancelled False` | PAID (C2+C3). |
| `repro_h6.py` (TZ=Europe/Warsaw) | next-week Mon 00:30 counted; Next in UTC | `headline: 2 meetings this week` · `Next: Standup 11:00 local at 11:00` | PAID (C11/C8). |
| `repro_compose.py` | `3 meetings this week, 3 watch items` | `3 meetings this week, 2 armed, 1 commitment due.` | PAID (C11). |
| `repro_orphans.py` | s2's arms stay; last source never pruned | B: `('s2', 0, 'cancelled', 2)`; C: `calendar_events by source: []`; D: `FINAL enabled scheduled_recordings: []` | PAID (C4). |

---

## C1–C12

### C1 — "armed, never started" settled (B11) — **PARTIAL**

The build is the ruling: the ingest leaves the row `idle, enabled,
next_fire_at = starts_at − lead` (`calendar_ingest_conductor.py:822-835`) and
the 136 conductor records at the event. Counsel proved the whole path with both
conductors (hunt H-G, `reread175_hunt.py`): `ingest left: idle enabled= True
fires at 2026-09-07T08:05:00+00:00` → `after _tick at next_fire_at: recording
last_outcome= recording_started | start_meeting called: 1 with
calendar_event_id= ce_33686b5`. The meeting row carries the event id
(`scheduled_recording_conductor.py:532`), which is what makes C11's dedup real.

Copy corrected: design law row (`settled-design-calendar-clock.md:49`), D1
(`:436-437`), `docs/USER_GUIDE.md:1375-1380` ("records at the event … Cancel on
the row stops it for good"), story-03 In bullets + AC (`story-03:35-49`), the
phase-status risk row (`current-phase-status.md:170`).

**Remains:**
- Three places still say the opposite: `current-phase-status.md:82-83` Scope/Out
  "Recording auto-start (the recording is armed, the owner starts it; Article IV:
  voice arms, it does not fire)"; `story-03-event-born-recordings.md:40-41` Out
  "Auto-starting the recording at event time (the conductor arms it; starting is
  Article IV's domain)"; `story-01-the-design.md:50` "not started (Article IV)".
  Article VI:3 — the phase's own charter contradicts its ruling.
- The suite carries no test that runs BOTH conductors.
  `TestArmsLikeEveryScheduledRecording::test_event_born_row_is_handed_to_the_scheduled_conductor`
  (`test_hs175_event_recordings.py:280-302`) is honestly named and proves the
  hand-off only; the hollow `TestNeverStarted` is gone. C1's "how to prove" asked
  for the terminal state; counsel's H-G is that test — lift it into the file.

### C2 — a real Cancel on the arrival — **PAID**

`scheduled_recording_service.py:422-470`: `recording` → 409 `already_recording`
("Already recording; stop the meeting instead"); `arming` → the 136 seam;
`idle` + enabled + `calendar_event_id` → `_cancel_idle_event_recording`
(`:500-540`: receipt `scheduled_recording.cancelled.owner`, `enabled=0,
state='cancelled', last_outcome='owner_cancelled'`, `owner_cancelled_at`
stamped `:542-562`, broadcast). The store returns the refusal by name
(`scheduledRecordingSlice.ts:68-91`, `CancelArmedResult` in `types.ts:89-95`);
the face names it on the row (`ChairHome.tsx:536-548`, `CAN'T CANCEL · <reason>`
at `:1359-1363`, `:1433-1437`) and withholds Cancel while `recording`
(`:1350-1356`, `:1438-1448`), the door carrying `armed.state`
(`door_service.py:338-340`, `:596-599`). Tests:
`test_hs175_cancel_owner.py` (8), `test_hs175_door_week_local.py::TestArmedRowState`;
rig `test_arrival_cancel_idle_event_born`, `test_arrival_cancel_refused_names_reason`
(lane log 21 passed). Shots: `arrival-cancelled-1440.png`,
`arrival-cancel-refused-1440.png` (`RECORDING` chip + the named refusal).

### C3 — the owner's cancel is final — **PAID**, with one consequence (condition 1)

`list_owner_cancelled_uids` (`db/scheduled_recordings.py:367-388`): the
cancelled row IS the tombstone, keyed `(calendar_source_id, calendar_uid)`,
`enabled=0` and (`owner_cancelled_at` OR `last_outcome IN ('owner_cancelled',
'cancelled')`). The conductor skips it with ONE refusal receipt
(`calendar_ingest_conductor.py:783-801`, `:865-879`). The 136 countdown cancel
is the owner's word too — proven by hunt H-G2: `cancel_armed -> True` →
`cancelled enabled= False last_outcome= cancelled` → `after refresh: enabled
rows= 0 skip receipts= 1`. `event_removed` and the source-gone pair are not
tombstones (`test_event_removed_is_not_a_tombstone`,
`test_reenabled_source_rearms_under_the_toggle`). Tests:
`TestOwnerCancelIsFinal` (3 incl. the rescheduled occurrence), `TestOwnerCancelStamp`.

**Consequence (hunt H-B, condition 1):** a recurring series shares one uid across
its occurrences (`calendar_ingest.py:215-229` expands RRULE). `RRULE:FREQ=DAILY;
COUNT=5` → `occurrences projected: 5 uids: ['u-rec'] armed: 5`; cancel the
FIRST → `armed= 4 tombstoned uids: {'u-rec'}`; two more occurrences enter the
feed → `armed= 4 skip receipts= 1`. So Cancel on Tuesday's standup leaves
Wed–Fri armed (already created) and refuses every occurrence from next week on —
neither "this one" nor "the series". B12 keyed the tombstone by uid for the
rescheduled-occurrence case; on a series that key is wrong twice over. The
Tuesday case IS a recurring standup.

### C4 — Remove/Disable disarms — **PAID**

`refresh()` runs `_prune_unlisted_sources` before the zero-sources return
(`calendar_ingest_conductor.py:203-209`, `:228-276`): projection deleted
(`delete_sources_not_in`, empty list → delete all, `db/calendar_events.py:132-135`),
idle event-born rows cancelled `calendar_source_disabled` /
`calendar_source_removed` with receipts (`db/scheduled_recordings.py:389-441`,
`_write_source_gone_receipt :881-892`), link orphans dropped (`:273-276`).
Tests: `TestSourceRemovedDisarms` (5). The snapshot's ICS leaves with its source:
`calendar_snapshot_service.py:359-398` (`is_generated_ics` refuses anything
outside `snapshot_dir()`; receipted `calendar.source.removed`),
`routes/system/settings.py:67-94`, `:118-126` (before/after id diff on any write
that touches `calendar.sources`). Hunt H-F on non-path URLs: `https://…` →
False, `''`/`None` → False, `/etc/hosts` → False, a `..` traversal inside a URL →
False. Tests: `TestSnapshotIcsRemoval` (5).

### C5 — a durable Unlink — **PAID** (on the face that shows the link)

Schema 75 `calendar_event_link_suppressions` (`db/schema.py:4068-4079`), keyed
`(source, uid, project)`; `unlink`/`unlink_event` write it
(`db/calendar_event_projects.py:88-125`); `replace_auto_links` honours it
(`:250-288`); a manual `link` clears it (`:78-86`). Route DELETE `/link` is
durable (`routes/calendar_events.py:91-113`). The arrival's event row carries
`Unlink` beside the ROOM token (`ChairHome.tsx:1320-1341`; hover-verb at the
desk width, always visible on coarse pointers and at the phone width,
`chair.css:184-204`, `:437-440`, `:467-470`), refusal named
(`CAN'T UNLINK · …`). Tests: `TestUnlinkIsDurable` (3: refresh, unlink-all +
manual re-link, time change); rig `test_arrival_unlink_room[1440/393]`. Shots:
`arrival-unlink-1440.png`, `-393.png`.

The Room's MEETINGS row carries no `Unlink` — it is the Watch row, and the Room
lists no per-event rows in V0, so there is nowhere for the verb to sit. `N THIS
WEEK` counts linked events the owner cannot see or unlink from the Room. Noted
as P2-7 and folded into the owner's question 1.

### C6 — the matcher — **PAID**

Watch-query branch dropped (`calendar_ingest_conductor.py:278-347`; the
docstring says why); the matcher runs before the per-source auto-create
(`:211-224`); manual links snapshot before the replace and rebind by
`(source_id, uid)` to the nearest occurrence (`:413-420`, `:441-442`,
`:451-502`; `rebind_manual_link` upserts so a title link on the successor
cannot collide, `db/calendar_event_projects.py:217-234`). A uid that split
into two occurrences: the nearest gets the manual link, the other whatever the
matcher says — sound. Tests: `TestMatcherRunsBeforeAutoCreate`,
`TestNoWatchQueryWarning`, `TestManualLinkFollowsTimeChange` (2). R1 published
as the owner's question 1 (B14).

### C7 — the meeting Watch's verbs are real — **PAID**

Retire is a tombstone: `ensure_meeting_watch` counts a Watch in ANY state as
existing (`watch_service.py:1284-1296`, `:1317-1326`); the sweep's backfill
SQL no longer excludes retired (`heartbeat_service.py:364-387`); a retired
Watch is not a source row (`project_service.py:948-951`). Pause reads `state`
first (`:980-988`) — shared with GH/J deliberately; a paused GH/J row that
read `live` before now reads `paused` (`TestPauseShowsPaused::
test_github_and_jira_rows_paused_after_pause_watch`); the group merge takes
the worst state (`:1105-1109`) and `CLEAR` requires `live` (`:1130-1131`) so a
paused row never says CLEAR. Creation receipted on both paths with `why`
(`:1386-1446`; `routing_glue.py:314`, `project_service.py:2913`). Tests:
`TestRetireIsATombstone` (4), `TestPauseShowsPaused` (2),
`TestCreationIsReceipted` (3); rig `test_retire_is_a_tombstone`. The face shows
`PAUSED` beside `Resume` (`ProjectRoomCore.tsx:1063-1067`; shot
`room-sources-meetings-paused-1440.png`). `test_hs169_wire.py` was re-pointed
honestly (the `meeting` connector is a real source now; a legacy `native`
connector still says CAN'T CHECK).

### C8 — local time everywhere — **PARTIAL** (condition 4)

One helper family: `project_service.local_now/local_week_bounds/utc_z/aware_iso`
(`:60-107`); `calendar_sources.py:55-64` (`_iso_week_range_local`) and
`read_calendar_sources` (`last_read_at` as an instant, `last_read` hub-local,
`:129-138`); the door's `_local_zone/_local_week_bounds/_week_strip`
(`door_service.py:453-524`, day buckets in Python by local date, bounds ride the
payload); the Room's `_meeting_calendar_tokens` (`project_service.py:883-939`)
and `checkedAt/nextCheckAt` with an offset (`:1071-1072`); the brief's `_utc_iso`
(`monday_brief_service.py:960-971`, naive `now` read as local) and `Next:` in the
brief's zone (`:809-811`); the faces format the viewer's clock
(`SettingsCore.tsx:137-146`, `BriefView.tsx:81-119`, `CadenceCore`). Tests at
−06:00 / Denver: `test_hs175_door_week_local.py` (6), `TestSourcesPayloadClocks`
(4), `TestRoomRowClocks` (5), `TestForwardHalfReadsFromNow` (3). Shots agree
with the menu-bar clock (`LAST READ 19:05` beside `07:05 PM`; `CHECKED 19:05`
beside `READ 19:05`).

**Remains (hunt H-C):** the default zone is `datetime.now().astimezone()` — a
FIXED offset for now, not a zone (`door_service.py:456`,
`project_service.py:62-66`). Across a DST edge the arithmetic keeps the wrong
offset. TZ=America/Denver, now = Sun 2026-11-01 20:00 MST (after the fall-back):
`helper Monday: 2026-10-26T00:00:00-07:00 -> 07:00Z | true local Monday …-06:00
-> 06:00Z | OFF BY ONE HOUR`; the strip with the production default `total=1
dots=[('SAT', 1)]` vs ZoneInfo `total=2 dots=[('MON', 1), ('SUN', 1)]` — a Sunday
00:30 meeting is a SAT dot and a Monday 00:30 meeting drops out of the week.
Twice a year, the transition week, events within the shifted hour. The fix is
per-instant `astimezone()` (no argument) for bucketing and a wall-clock Monday
made aware by `astimezone()` for the bound — the same helpers, no new API.

### C9 — honest tokens — **PAID** (one plumbing item to P2)

`DAILY 08:00` on the Rhythm row (`CadenceCore.tsx:468-474`; USER_GUIDE
`:1398-1401`); THIS WEEK bounded by `week.ends_at` while NEXT reads the
projection (`ChairHome.tsx:515-527`; rig `test_arrival_this_week_bound`);
`N EVENTS` (`calendar_sources.py:78-89`, `SettingsCore.tsx:1407`; USER_GUIDE
`:1319-1321`); the Room's NEXT from linked future calendar events
(`project_service.py:883-939`; `test_next_from_future_linked_event_not_from_meeting_entities`);
the rig seeds only producible states (`test_hs175_room_glass.py` now seeds a
calendar event + link, not a future `started_at`); `THIS DEVICE` off file ICS
rows (`SettingsCore.tsx:1400-1405`; shot `settings-calendar-1440.png`: WORK
carries `ICS · 1 EVENT · LAST READ 19:05`, no chip); `5+` exactly
(`ChairHome.tsx:1270-1278`, own testid `arrival-week-overflow`; rig
`test_arrival_week_overflow_reads_five_plus`); Rhythm's summary through
`countToken` with ARMED named (`CadenceCore.tsx:135-159`; shot `2 MEETINGS ·
1 ARMED · 1 COMMITMENT DUE`); the two board PNGs re-exported
(`story-01-shots/ArrivalArmedOrphan.png` reads `2 MEETINGS THIS WEEK` /
`MEETINGS 2`; `SettingsMeetingsCalendar*.png` modified). `ux_canon_scan.py`
runs clean on the 175 files.

**P2:** the duplicate `data-testid="arrival-meetings"` is NOT split
(`ChairHome.tsx:652` and `:717` both) and the rig's `count() >= 1` still cannot
catch a duplicate section (first report P2-14). Test plumbing; no face defect.

### C10 — the snapshot's egress before the upload — **PAID** (second face parked)

`resolve_snapshot_egress` (`calendar_snapshot_service.py:806-845`) reads the
same ranking the dispatch uses (`_rank_vision_targets :783-803`,
`_egress_from_route_entries :751-780`); the direct dispatch captures egress the
moment the revision is captured, BEFORE the image leaves, and returns it on
failure too (`:632-660`, `:685-691`, `:704-706`); `paired_device` names its
endpoint host or node (`_egress_for_scope :735-748`). The payload carries
`snapshot_egress` (`calendar_sources.py:183-191`, `:163-166`); the chip sits
beside `Snapshot` (`SettingsCore.tsx:152-165`, `:1452-1462`; shot: `192.168.1.50`
before the verb); `Edit` withheld on the SNAPSHOT row (`:1414-1418`,
`:1425-1428`). Tests: `TestSnapshotEgress` (7 incl. the failure path). The
review core's chip is parked in `BACKLOG.md:1055` — after the upload, it is
provenance, not the decision point; P2-6.

### C11 — the brief's two windows — **PAID** (`due_at` field to P2)

Forward half `[now, Sunday 23:59]` from `compute_lookahead(period_end)`, UTC-
normalised for the string compare (`monday_brief_service.py:204-221`); dedup
against the lookback's recorded occurrences by projection id — keyed by the
occurrence, so a recurring series' next occurrence survives its last recording
(`:230-235`, `:975-994`; the design said `calendar_uid`, the build is stricter
and right); commitments due by the owner's local DATES (`:246-248`, `:997-1011`)
and said once (`:257-272`, `:653-669`, `:719-721`); `_compose` counts meetings /
armed / due / decisions, never "watch items", `Next:` excluded (`:330-359`).
Hunt H-E: this_week empty + one change → `'1 thing changed.'`; all empty →
`'Nothing material changed.'`. Tests: `TestForwardHalfReadsFromNow` (3),
`TestRecordedOccurrenceDedup` (2), `TestComposeCountsCalendarItems` (2),
`TestCommitmentSaidOnce`, `TestComputeWindowByteIdentical`. Shot
`brief-week-1440.png`: `2 MEETINGS · NEXT SPRINT PLANNING 20:06 · 1 ARMED · 1
DUE · SAT`.

**P2:** `due_at` is still carried inside `detail` as `text | YYYY-MM-DD`
(`:936-941` join; `BriefView.tsx:233` split) — the `|`-in-text and empty-text
edges of the first report's H6-4 stand; the day token itself is now local
(`parseLocal`, `BriefView.tsx:84-92`).

### C12 — the walk — **OPEN (honestly)**

The runner no longer clicks `Continue later` (`tests/e2e/live175_walk.py:208-216`
prints and moves on) and the Settings leg opens the real path
(`:716-730`). Story 06 is `in-progress` (`story-06-the-walk.md:5`) — not flipped
on the calendar-less walk; `walk-facts.md` still reads `DATA` on every 175 beat
(`calendar_configured False`, `week_days 0`, `meetings_source_present False`).
The owner's attended walk with a connected source is the exit gate and is owed.

---

## Hunts the brief named, and what they found

| Hunt | Result |
|---|---|
| A cancelled cron schedule | Unaffected: `list_owner_cancelled_uids` requires `calendar_uid != ''` (`db/scheduled_recordings.py:381`); a cron row's uid is `''`. The 136 countdown cancel on a recurring cron row still advances `next_fire_at` (`_advance_after_terminal :611-633`). |
| A source re-enabled after Disable | Re-arms under the toggle (`test_reenabled_source_rearms_under_the_toggle`) — honest per B12. **But the second arm writes no receipt** (hunt H-A): `after Enable: rows= [('sr_cfea1','idle',True), ('sr_d2198','cancelled',False)] created receipts= 1`. The create receipt's discriminator is `event_born:{event_id}` (`calendar_ingest_conductor.py:851-863`) → `INSERT OR IGNORE` (`:981`). The first report's H1-2 receipt gap, still open on this path. Condition 2. |
| The suppression table vs a manual re-link | Sound: `link(manual)` deletes the suppression (`db/calendar_event_projects.py:78-86`); `rebind_manual_link` leaves suppressions alone; `test_unlink_all_survives_and_a_manual_link_clears_it`. Suppression is by uid → unlinking one occurrence of a series unlinks the series for that Room (same key as the tombstone; consistent, and part of owner question 6). |
| `rebind_manual_link` on a uid that split into two occurrences | Nearest-to-old-start wins (`:483-493`); the other occurrence gets the matcher's verdict; upsert cannot collide. Sound. |
| The local-week helpers across a DST edge | **Defect** (H-C above). Condition 4. |
| The brief's headline when `this_week` is empty | Honest (H-E). |
| PAUSED on GH/J rows | Behaviour changed deliberately and for the better: a GH/J watch the owner paused used to read `live` (the `enabled`-only derivation predates 175); it now reads `paused` with `Resume`. Proven for all three (`test_github_and_jira_rows_paused_after_pause_watch`). No CLEAR on a paused row. |
| The settings removal hook on a non-path URL | Safe (H-F): only a file inside `snapshot_dir()` is ever deleted; a URL, an empty value, `/etc/hosts` and a traversal all refuse. |

## New hunts (counsel's own)

| Hunt | Result |
|---|---|
| H-B a recurring uid | Condition 1 (see C3). |
| H-G both conductors | B11's claim proven: `recording`, `start_meeting called: 1` with the event id. Condition 5 lifts it into the suite. |
| H-G2 cancel during the countdown | Tombstone holds (`last_outcome='cancelled'`, `owner_cancelled_at None` — the OR covers it). PAID. |
| H-H the owner DELETES the event-born row | **Re-armed by the next refresh with no receipt**: `rows after delete + refresh: [('sr_1cc86','idle',True)] created receipts= 1`. `delete_schedule` (`scheduled_recording_service.py:398-420`) hard-deletes any non-arming row, the tombstone with it. No face calls `deleteSchedule` today (only the slice, `scheduledRecordingSlice.ts:55`), but the MCP tool `scheduled_recording_delete` is on under the open throttle. Condition 3. |
| H-I 147's one-tap arm after Cancel | The owner's newer word wins: a fresh `idle True` row (`born_from=''`), the refresh does not duplicate it. Sound. |
| H-D Disable then Enable with a manual link | The manual link is gone (`manual links for the Room after Disable/Enable: []`) — `delete_orphans` drops it with the projection. No face makes manual links in V0; P2-3. |

---

## Conditions (ride the ratification)

| # | What | Where | How to prove |
|---|---|---|---|
| **1** | Cancel on a recurring meeting means ONE thing, said and proven. Counsel's recommended V0: key the tombstone by occurrence — `(source, uid, starts_at)` of the cancelled row — so Cancel is "this meeting"; a cancelled occurrence that later MOVES re-arms (a moved meeting is a new fact the row shows as `ARMS`). Alternative if the owner rules "the series": cancel every enabled sibling with the same uid in the same act, receipted per row. Either way the already-armed siblings and the not-yet-created occurrences must agree. Carry "this one or the series?" as owner question 6. | `db/scheduled_recordings.py:367-388`; `calendar_ingest_conductor.py:783-801`; `scheduled_recording_service.py:500-540` | Hunt H-B inverted in `test_hs175_event_recordings.py`: `RRULE:FREQ=DAILY;COUNT=5`, cancel the first → the other four stay armed AND the sixth/seventh arm (or, under "series", zero armed and no new arms) — one assertion set, no middle state. |
| **2** | Every arm is receipted. The create receipt's discriminator carries the schedule id (`event_born:{event_id}:{schedule_id}`), so the second arm after Enable, after Delete, or after a rescheduled occurrence writes its own row. Article V:2. | `calendar_ingest_conductor.py:851-863` | Hunt H-A inverted: Disable → Enable → `created.calendar_event` receipts == 2. |
| **3** | `delete_schedule` on an event-born row leaves the owner's word behind: either it cancels (the C2 path — tombstone + receipt) instead of deleting, or it refuses by name (`event_born_cancel_instead`). Hard delete stays for cron rows. | `scheduled_recording_service.py:398-420`; the MCP tool `scheduled_recording_delete` | Hunt H-H inverted: delete → refresh → zero enabled rows, one skip receipt. |
| **4** | The local zone survives a DST edge: bucket each instant with `parsed.astimezone()` (system zone, per instant) and make the Monday bound from a naive local wall clock (`datetime.combine(local_date, time(0)).astimezone()`) in `project_service.local_week_bounds`, `door_service._local_week_bounds/_week_strip`, `calendar_sources._iso_week_range_local`. | `project_service.py:60-76`; `door_service.py:453-524`; `calendar_sources.py:55-64` | Hunt H-C inverted at TZ=America/Denver, now = 2026-11-01 20:00: Monday bound `06:00Z`, strip `MON 1 · SUN 1`. Same for the spring edge (2026-03-08). |
| **5** | The copy matches the ruling everywhere: `current-phase-status.md:82-83`, `story-03:40-41` (the Out bullet), `story-01-the-design.md:50`. And B11's claim lives in the suite: a test that runs the ingest conductor then the 136 conductor's `_tick` (countdown 0, a fake `start_meeting_fn`) and asserts `recording` + the start call with the event id (counsel's H-G). | the three docs; `test_hs175_event_recordings.py:280-302` | `grep -rn "not started\|owner starts\|Article IV's domain" pm/roadmap/holdspeak/phase-175*` → 0; the test green. |
| **6** | The walk (C12) is walked: story 06 flips only after his desk shows the strip, NEXT with a Room token, an armed row with a working `Cancel`, `Unlink` in frame, the Room's MEETINGS row, the THIS WEEK brief — each a `MATCH` in `walk-facts.md` — and his answers to the questions below recorded verbatim. | `tests/e2e/live175_walk.py`; `story-06-the-walk.md` | `walk-facts.md` with `MATCH` rows for the seven beats. |

## P2s (ledger; pay when touched)

- P2-1 `due_at` as its own field on the commitment item (`monday_brief_service.py:936-941`; `BriefView.tsx:233`) — the first report's H6-4.
- P2-2 The duplicate `arrival-meetings` testid (`ChairHome.tsx:652`, `:717`) and the rig's `>= 1` (first report P2-14).
- P2-3 Disable → Enable drops the source's manual links (`delete_orphans` after the projection is deleted; hunt H-D). Matters once a `Link to Room` verb exists.
- P2-4 R2's rebind re-arms at `starts_at − 60 s` (`calendar_ingest_conductor.py:611-616`, the 147 rule) while an event-born row arms at `− lead` (5 min): a moved event-born meeting loses four minutes of lead.
- P2-5 Dead clauses `cep.match_source != 'suppressed'` (`calendar_sources.py:111`; `project_service.py:906`, `:915`) — suppression is a table now, no row ever carries that value.
- P2-6 The snapshot review core's egress chip (`BACKLOG.md:1055`).
- P2-7 The Room shows no per-event rows, so `Unlink` lives on the arrival only; `N THIS WEEK` on the MTG row counts links the owner cannot inspect from the Room.
- P2-8 Two boundary shapes for the same instant: `utc_z` writes `…Z` (`project_service.py:79-86`, the ingest's form, `calendar_ingest.py:410-412`) while the brief's `_utc_iso` writes `…+00:00` (`monday_brief_service.py:960-971`) and its docstring claims the ingest's shape. Digits compare first so only an equal-second boundary differs; make it one helper.
- P2-9 Remove/Disable still poke no refresh (`settings_service.py` has no conductor call): a removed source's events show for up to 900 s (first report P2-5).
- P2-10 The brief shot shows `Ania owns the API spec` twice (the DUE commitment under THIS WEEK and a `REVIEW DECISION` under SINCE FRIDAY): different objects with one text, a rig-seeding artifact — but A.7 on a real desk if a decision's text equals its commitment's.
- P2-11 The tree carries modified PNGs under phases 141, 144, 145, 152 (`git status`): the rigs re-shot other phases' assets while running. Not 175's; the orchestrator should stage deliberately.

## The owner's questions (carried; his word outranks counsel)

1. **Auto-link vs suggestion-only.** V0 auto-links by ≥ 4-letter whole word. Evidence, still live in the tree: a Room named `Design` links "Design your 401k plan (webinar)" and, under `ARM ROOM MEETINGS ONLY`, arms it (R1 output above). The remedy today is `Unlink` on the arrival row (durable). Does he want the 172 `SUGGESTED · Add / Dismiss` grammar instead?
2. **The toggle = consent to record at the event, or arm-and-wait?** Ruled B11 for the build. Counsel's proof of what the build does: at `starts_at − 5 min` the row enters `arming`, ten seconds later capture starts (`recording`, `start_meeting` called — hunt H-G). The faces say `ARMS HH:MM`, then `RECORDING`; `Cancel` works until capture starts. If he wants arm-and-wait, C1(a) of the first report is the shape.
3. **Remove means gone?** Built: Remove/Disable cancel the source's armed recordings with receipts, prune its events off the desk, and Remove deletes the snapshot's extracted ICS. Enable re-arms under the toggle. Confirm.
4. **Whose clock?** Built: the hub's local week on the wire and the viewer's browser clock on the faces (they coincide on his desk). The calendar's own zone per event is not offered. Confirm.
5. **A Room with linked meetings but a retired Watch.** Built: allowed; the MEETINGS row disappears and is never recreated by link or sweep. `Retire` sits on no live meeting row (API/MCP only; `BACKLOG.md:1059`). Withhold Retire, or put it on the row?
6. *(new)* **Cancel on a recurring meeting: this one, or the series?** Today it is neither (condition 1). Counsel recommends "this one".
7. *(carried from B10)* The calendar section is captioned `THIS WEEK`, the board says `MEETINGS`.

## What counsel could not verify

- The four glass rigs at runtime (not re-run; the lanes' logs cited above).
- The owner's machine zone (the shots' menu-bar clock and the tokens agree in whatever zone the rig ran).
- The snapshot flow end to end with a real vision model (the egress resolution is proven on the profile ranking, not on a dispatch).
- Whether any MCP client on his desk calls `scheduled_recording_delete` (condition 3 is reachable, not observed).

## Reproductions

- `/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/1687fab9-1620-43a6-afab-0649194bf7ae/scratchpad/reread175_hunt.py`
  (H-A … H-I; run with `HOME=$(mktemp -d) TZ=America/Denver`).
- The first report's `repro175.py`, `repro_h6.py`, `repro_h7.py`, `repro_compose.py`,
  `repro_orphans.py` — outputs in the table above; R7 crashes by design.
