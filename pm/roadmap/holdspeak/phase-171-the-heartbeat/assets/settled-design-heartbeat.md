# The Heartbeat -- the settled design (Phase 171, story 01)

> **DRAFT -- pending 170's merge and his word on 170's canvas.**

The owner's Tuesday moment (THE-TUESDAY-ARC.md section 2, "Phase 171"):
08:05, one notification, the shade opens with NEEDS YOU across Rooms and
the Monday brief already regenerated. He never opened a Room to learn
it. The face canon binds (docs/internal/UX-CANON.md); the Door's and
the Arrival's grammar (Phases 169-170) are the ratified precedent.

## D0 -- the Tuesday moment

08:05. His Mac shows one macOS notification: "HoldSpeak -- 3 need you
across 2 projects." He clicks; the system shade opens. PROJECTS is the
first section: one row per Room that has items, the count, the first
WHY, and `Open`. The dock badge reads `3`. The Monday brief regenerated
overnight, unattended; its row sits in the shade. He types Cmd+K,
types a project name, lands in the Room. He never opened a Room to
learn what needs him.

The sweep ran while he slept. The cadence row in Settings reads
`EVERY 15 MIN` with `QUIET 22:00--08:00` and `NEXT 08:20`. Every tick
was receipted. Nothing left the machine.

## D1 -- the laws

| Law | Source | How it binds |
|---|---|---|
| Nothing leaves the machine | Constitution Article III | The notification is local (UNUserNotificationCenter / libnotify); the body names the COUNT only unless he opts in; no remote push |
| Watching is free | Constitution Article V | The sweep, the cache, the aggregate, the shade poll -- all reads; no write, no egress |
| The notification names the count only | Article III.1 | Default body: `N need you across M projects`; Room names only under a content-opt-in setting (off by default) |
| Quiet hours | integrations.py:209-210, cadence/scheduler.py:25-26,30 | Notifications suppressed during `quiet_hours_start..quiet_hours_end` (default 22:00--08:00); the brief regeneration waits until the window closes |
| No counters of zero | UX-CANON.md rule A.8 | The PROJECTS section is absent when the aggregate is zero; the dock badge is absent at zero; the brief row is absent when no brief exists |
| Every verb the library Button | UX-CANON.md rule A.1 | `Open` on shade rows, `Run now` on the cadence row, `Generate` on the brief caption -- all library Button |
| One egress vocabulary | UX-CANON.md, 170 settled (counsel M1) | `THIS DEVICE` on every face that names a host (the notification is local; the sweep reads local DB) |
| No prose | UX-CANON.md rule A.3 | Tokens, verbs, counts, names. The shade rows are species, not sentences |
| No modals | UX-CANON.md rule A.4 | The shade is a panel, not a modal; the cadence row edits in world |
| Ledger not gate | Owner ruling | Every tick receipted via pipeline_events (Article XI.2); no ceremony beyond the receipt |
| Design before build | UX-CANON.md rule A.2 | This document is the design; artboards at 1440 + 393 drawn from it; his word before any code |

## D2 -- the faces (element by element, species named)

### (a) The shade's PROJECTS section

**Position:** FIRST section in the SystemShade, ABOVE the existing
"Needs you" (approve-queue) section (SystemShade.tsx:120). Absent when
the aggregate count is zero (rule A.8).

**Section caption:** `PROJECTS` (caption step, 11 mono uppercase 0.06em)
with the aggregate fact as the count: `N need you across M projects`
(secondary step, 12 mono). When only one project contributes: `N need
you`. When only door items contribute (no Room): `N need you`.

**Rows** (SurfaceLedgerRow, 52px lead slot, one per Room with count > 0):

- Lead: the project glyph (the Room's kind glyph from the Door grammar;
  SurfaceLedgerRow lead slot).
- Primary (15/600): the project name (ellipsis, `min-width: 0`).
- Cells: a count token `N` (surface-token[data-chip], secondary step),
  the first WHY from the aggregate as a muted token (secondary step,
  truncated to 40ch).
- Trailing: `Open` (Button ghost) -- opens the Room via
  `openSurfaceOr("project-room", "/projects", projectId)`.

**Empty state:** the section is absent (the headline in the arrival said
`Nothing needs you`; the shade omits the section entirely).

**Species used:** SurfaceSection (caption + count), SurfaceLedgerRow,
surface-token[data-chip], Button (ghost).

**Widths:** 1440 -- the row is a single line (lead / name / count / WHY /
Open). 393 -- the WHY token wraps under the name; `Open` stays trailing.

### (b) The macOS notification

**Title:** `HoldSpeak` (the app name; UNUserNotificationCenter title
field).

**Body:** `3 need you across 2 projects` (the aggregate). When one
project: `3 need you`. Never Room names, never WHY text, never item
content -- unless the content-opt-in setting is enabled (off by default;
Article III).

**Content-opt-in variant:** body becomes `3 need you across 2 projects --
Gov: PR review overdue` (the first WHY per project, one line each, max 3
lines). This variant requires the owner to enable it in Settings ->
Rhythm.

**Trigger:** the EDGE of the needs-you count. The edge rule: fire when
the count crosses from 0 to > 0, OR when the count increases since the
last notification. Do NOT fire when the count stays the same or
decreases. The edge detector tracks `last_notified_count` across
restarts (a DB column or a cadence policy row).

**Quiet hours:** no notification fires during `quiet_hours_start` to
`quiet_hours_end` (integrations.py:209-210). An edge that occurs during
quiet hours is SWALLOWED -- no deferred fire after the window closes
(the next sweep's edge will fire naturally if the count is still > 0).

**Per-project mute:** a boolean on the project settings. A muted
project's needs-you items are excluded from the aggregate count for
notification purposes (they still appear in the shade for browsing).

**Click action:** clicking the notification opens the desk in the
browser (the existing presence host pattern: open `http://localhost:PORT`
in the default browser). The shade opens with PROJECTS visible.

**Implementation host:** the Cocoa child process
(desktop_presence_cocoa.py). The notification dispatches from the AppKit
runloop via UNUserNotificationCenter. Requires adding a
`UNUserNotificationCenterDelegate` to the existing `_CocoaPresenceUI`
class and requesting authorization at startup.

**Linux:** libnotify via the existing `_LibnotifyNotifier` in
desktop_presence_freedesktop.py:89. Same edge rule, same quiet hours,
same body text. The existing `notify()` method (line 103) is the seam --
it takes a `spec` dict; the heartbeat spec is `{title: "HoldSpeak",
body: "N need you..."}`.

**Species used:** none (OS-native notification; not a web component).

### (c) The dock badge

**Which launcher:** the `attention` launcher on the dock
(Dock.tsx:26, `ACTIONABLE_LAUNCHERS`). The badge reads the aggregate
needs-you count from the cached route.

**Value:** the aggregate count (an integer). Zero = no badge (the
badge span is not rendered; rule A.8).

**Tone:** `data-tone="warn"` when any item has severity `danger`
(overdue); default otherwise.

**Species used:** `desk-chip desk-dock-badge` (the existing dock badge
chip on Dock.tsx:146/194).

**Wire:** the dock launcher's `badge` field is set from the cached
`/api/desk/needs-you` response's `count` field, polled on the same
interval as the shade (or pushed via the store when the shade fetches).

### (d) Settings -> Rhythm's cadence row

**Position:** inside the Rhythm module (settingsPrefs.tsx:47, key
`rhythm`). The existing Rhythm row shows `N LOOPS` or `NO LOOPS`
(settingsPrefs.tsx:463-475). The cadence row sits INSIDE the Rhythm
module detail face (opened by `Open` on the hub row), not on the hub
itself.

**The row** (SurfaceLedgerRow):

- Primary (15/600): `Watch sweep`.
- Cells:
  - CycleGadget: the interval picker (`EVERY 15 MIN` / `EVERY 30 MIN` /
    `EVERY 1 HR` / `EVERY 4 HR`). The options are the cadence interval
    for `evaluate_due` calls. Default: `EVERY 15 MIN`.
  - A muted token: `QUIET 22:00--08:00` (from integrations.py:209-210;
    read-only on this row -- edited in the quiet-hours setting).
  - A muted token: `NEXT 08:20` (the earliest `next_evaluation_at` from
    the watches, formatted as a local time; absent when no watches are
    graduated).
- Trailing: `Run now` (Button ghost) -- triggers one immediate
  `evaluate_due` call and refreshes the row's NEXT token.

**The brief row** (SurfaceLedgerRow, in the same Rhythm module):

- Primary (15/600): `Monday brief`.
- Cells:
  - A token: `DAILY AFTER 08:00` (the brief regenerates once per day
    after quiet hours close; read-only).
  - StateChip: `LAST SEP 04` (the date of the most recent brief) or
    `NEVER` (muted, when no brief has been generated).
- Trailing: `Generate` (Button ghost) -- triggers immediate brief
  regeneration.

**The hub row update:** the Rhythm hub row on settingsPrefs.tsx:465 gains
a second cell when the sweep is active: `SWEEP ON` (StateChip success)
or stays `NO LOOPS` when nothing is configured.

**Species used:** SurfaceLedgerRow, CycleGadget, StateChip,
surface-token[data-chip], Button (ghost).

### (e) PROJECTS in Cmd+K

**Section:** a new verb group `"projects"` in the verb registry
(verbRegistry.ts). The entries are DYNAMIC -- registered from the
active project list fetched via `/api/projects`.

**Each entry:**

- `id`: `project.open.<projectId>`.
- `label`: the project name.
- `group`: `"projects"`.
- `glyph`: the project kind glyph (from KIND_GLYPH.project,
  verbRegistry.ts:236).
- `keywords`: `["project", "room", <project name words>]`.
- `badge`: the needs-you count (omitted when zero; rule A.8). Displayed
  as a trailing chip in the verb row.
- `run`: `() => openSurfaceOr("project-room", "/projects", projectId)`.

**Dynamic registration pattern:** follows the existing coder-session
dynamic pattern. A `useEffect` in the verb-registry provider fetches
`/api/projects` on mount, registers one verb per active project, and
cleans up on unmount.

**Species used:** the existing verb-row rendering in the command deck
(the verb registry's standard row with glyph + label + badge).

### (f) The Monday brief in the shade

**Position:** inside the PROJECTS section (when it exists) as a
separate subsection, or as its own section below PROJECTS when no
projects have needs-you items but a brief exists.

**The row** (SurfaceLedgerRow):

- Lead: a brief glyph.
- Primary (15/600): `Monday brief`.
- Cells: `N THINGS` (surface-token, the item count from the brief) and
  a date token `SEP 04` (secondary step, the brief's generated_at date).
- Trailing: `Open` (Button ghost) -- opens the brief detail face.

**Empty state:** the row is absent when no brief exists (rule A.8).
Never `No brief yet` in the shade -- that belongs on the arrival only.

**Species used:** SurfaceLedgerRow, surface-token[data-chip], Button
(ghost).

### All faces: dimensions

Every artboard at 1440 (the window at its design width) and 393 (the
glass / phone-width container query on `surface`). Three type steps
minimum per face: display (26/650) for the shade headline or
notification count, primary (15/600) for names and rows, secondary
(12 mono) / caption (11 mono uppercase) for tokens and section labels.

## D3 -- the wire

### The scheduler stamps `next_evaluation_at`

**Seam:** `watch_service.py:922` -- the `_make_txn_hook` closure inside
`evaluate_due` already writes `next_evaluation_at` via:
```
conn.execute("UPDATE connector_watches SET last_evaluated_at=?, next_evaluation_at=?, ...")
```
**Current gap:** `next_evaluation_at` is null on the owner's watches
because `evaluate_due` has never been called (cadence_loops 0 on his
desk). The cadence engine thread (web_runtime.py:529-534) starts ONLY
when `_cadence_enabled()` returns true. The initial stamp must be set
when the owner configures the sweep interval -- the first `Run now` or
the first cadence tick writes it.

**Schema column:** `db/schema.py:2324` -- `next_evaluation_at TEXT` on
`connector_watches`. Already exists.

**Due-watch query:** `db/automations.py:451-456` -- selects watches
where `next_evaluation_at IS NOT NULL AND next_evaluation_at <= now`,
ordered by `next_evaluation_at ASC`. Already works when the column is
populated.

**Per-watch cadence:** `evaluation_cadence_minutes` on each watch
(steward.py:295-309 validates 1..10080). The sweep interval in
Settings controls the tick frequency; per-watch cadence controls how
often THAT watch evaluates within the tick.

### The aggregate route and cache

**Seam:** `web/routes/projects.py:380-449` -- `GET /api/desk/needs-you`.
Currently queries every active Room per request (the N+1 named in
THE-TUESDAY-ARC.md). The 171 cache:

- A server-side in-memory cache (or a DB-backed cache row) keyed by
  owner id.
- Invalidated by the cadence tick (after `evaluate_due` completes) and
  by a `?force=true` query parameter.
- Cache lifetime equals the sweep interval (the cadence setting).
- The route checks the cache first; on miss, runs the current N+1
  aggregation and writes the cache.
- Response time target: < 50 ms from cache hit (the current N+1 is
  unbounded).

### The notification bridge in the Cocoa host

**Seam:** `desktop_presence_cocoa.py` (373 lines). The `_CocoaPresenceUI`
class (line 52) has AppKit, WebKit, Foundation imports but no
UNUserNotificationCenter import and no notification call.

**What is added:**
- Import `UserNotifications` (pyobjc bridge for
  UNUserNotificationCenter).
- At startup: `UNUserNotificationCenter.currentNotificationCenter()
  .requestAuthorizationWithOptions_completionHandler_(...)`.
- A `_dispatch_notification(title, body)` method on `_CocoaPresenceUI`
  that creates a `UNMutableNotificationContent`, sets title and body,
  and delivers via `addNotificationRequest_withCompletionHandler_`.
- A `UNUserNotificationCenterDelegate` that handles
  `userNotificationCenter_didReceiveNotificationResponse_
  withCompletionHandler_` -- on click, opens the desk URL in the
  default browser.
- The edge detector: the hub polls `/api/desk/needs-you` on the cadence
  interval; when the count crosses its edge, it calls
  `_dispatch_notification` unless in quiet hours.

**Linux seam:** `desktop_presence_freedesktop.py:103` --
`_LibnotifyNotifier.notify(spec)` already takes `{title, body}`. The
heartbeat adds the same edge-detection loop and quiet-hours check,
calling `notify()` with the heartbeat spec.

### The brief's cadence loop

**Seam:** `runtime/cadence.py:62-90` -- `_maybe_push_daily_brief`
already has the daily-push logic and quiet-hours check. The brief
regeneration is the missing piece:

- Before pushing to Telegram, call `MondayBriefService.generate()`
  (services/monday_brief_service.py:110) to regenerate the brief if
  the last one is stale (older than the brief interval, default 24h).
- The same daily condition (after quiet hours, once per calendar day)
  governs both regeneration and push.
- The regeneration is receipted via pipeline_events.

### The five conductor loops in parallel

**Seam:** `web_runtime.py:519-534`. Currently TWO daemon threads:

1. Plugin queue (`_deferred_plugin_queue_loop`, line 519, thread
   `HoldSpeakMirPluginQueue`).
2. Cadence engine (`_cadence_loop`, line 529, thread
   `HoldSpeakCadenceEngine`, conditional on `_cadence_enabled()`).

The other background work runs on different mechanisms:
3. Recording tick (`device_recording_tick.py` via `runtime/meeting_glue.py:346` -- `self.recording_ticker.start()`; runs its own 5s tick thread started by `_start_meeting`, stopped by `_stop_active_meeting`).
4. Transcriber warm (`_warm_transcriber_in_background`, web_runtime.py:536 -- a one-shot daemon thread via `runtime/transcriber_state.py:202`).

The story's scope: make the plugin queue and cadence loops independent
(a crash in one does not halt the other -- today they are already
separate threads, but error handling should be verified). The recording
tick and transcriber warm are already independent (they start/stop on
their own lifecycle). The "five loops" named in the arc may be four
in practice (the fifth may be the needs-you cache refresh itself, which
is new). Document what exists; cover what exists.

**Error boundary:** each loop wraps its per-tick work in its own
try/except. The cadence loop already does this (cadence.py:60). The
plugin queue loop should be verified. A crash logs and continues; it
never terminates the thread.

## D4 -- counsel's hunts

- **H1: The N+1 cache staleness.** The shade polls the cache; the cache
  is invalidated by the cadence tick. A tick that fails silently leaves
  stale data. Hunt: the cache must carry a `refreshedAt` timestamp;
  the shade shows `CHECKED N MIN AGO` when stale beyond 2x the interval.
- **H2: Notification without authorization.** macOS requires user
  authorization for UNUserNotificationCenter. If denied, the edge
  detector fires but the notification is swallowed. Hunt: the cadence
  row should show `NOTIFICATIONS OFF` (warning StateChip) when
  authorization is denied, with a ghost `Allow` verb that opens System
  Settings.
- **H3: Edge detector drift.** If the hub restarts, the
  `last_notified_count` is lost and the next tick fires a spurious
  notification. Hunt: persist `last_notified_count` in the DB (a
  cadence policy row or a dedicated column on the needs-you cache).
- **H4: Quiet hours and the brief.** The brief regenerates "after quiet
  hours close." If the desk is not open at 08:00, does the brief
  regenerate? Yes -- the cadence loop runs unattended; the first tick
  after quiet hours close triggers it. But if the Mac is asleep, the
  cadence thread is suspended. Hunt: the first tick after wake should
  check the brief freshness and regenerate if stale.
- **H5: The shade polls while open.** If the shade is open for 30 min,
  it polls 2x per minute (the existing pattern in SystemShade.tsx).
  Hunt: the PROJECTS section should use the cached route (< 50 ms);
  the poll interval should match the cadence interval, not a shorter
  interval.
- **H6: Per-project mute vs the dock badge.** Muted projects are
  excluded from the notification count. Are they excluded from the dock
  badge? They should be: the dock badge and the notification use the
  same aggregate. Hunt: a single mute flag must affect both.
- **H7: Cmd+K verb staleness.** Dynamic verbs from `/api/projects` are
  registered on mount. If a project is created while the desk is open,
  the verb list is stale until the next mount. Hunt: a bus event or a
  poll on the project list (the existing useProjectList hook) should
  re-register verbs.

## D5 -- the walk on his desk

The walk proves the Tuesday moment on his real desk with his real
projects:

1. **The notification.** A project has needs-you items (a Watch
   evaluation produced a new NEEDS YOU row since the last check). The
   macOS notification fires within 10 s: "HoldSpeak -- N need you
   across M projects." Stopwatch on the latency.
2. **The click.** He clicks the notification. The desk opens in Safari.
   The shade opens with PROJECTS visible.
3. **The shade PROJECTS.** The rows match his real projects: name,
   count, first WHY. He clicks `Open` on a row; the Room opens.
4. **The dock badge.** The dock launcher shows the aggregate count. He
   closes the Room; the count persists until the next sweep clears it.
5. **The brief.** The Monday brief regenerated overnight (or since his
   last visit). The shade shows the brief row with the date. He clicks
   `Open`; the full brief opens.
6. **Cmd+K.** He types Cmd+K, types a project name. The entry appears
   with the count badge. He selects it; the Room opens.
7. **Quiet hours.** He sets quiet hours to cover the current hour. No
   notification fires. He clears quiet hours; the next edge fires.

The walk is seven beats at both widths (1440 + 393). Stopwatch per face
(Article IX.2). His words verbatim. His verdict.

## Honest sizes

| Story | Size | Rationale |
|---|---|---|
| 01 The design | S | Artboards from this doc; no code |
| 02 The cadence row | M | The sweep interval setting + parallel loops + the cadence UI row; the scheduler stamp is one line but the Settings face is new |
| 03 The needs-you aggregate | S-M | A cache wrapper around the existing route; the invalidation signal is the cadence tick |
| 04 PROJECTS in the shade | M | A new section in SystemShade + dock badge wiring; the row grammar is settled from the Arrival |
| 05 macOS notifications | M-L | UNUserNotificationCenter from pyobjc + the edge detector + quiet hours + per-project mute + Linux fallback; the notification bridge is new territory |
| 06 Monday brief recurring | S | One call added to the existing `_maybe_push_daily_brief`; the shade row is one SurfaceLedgerRow |
| 07 PROJECTS in Cmd+K | S | Dynamic verb registration following the existing pattern; one fetch, one registration per project |
| 08 The walk | S | His desk, seven beats; no code |
| 09 The docs | S | Re-shot for the new faces + the heartbeat Mermaid diagram |
| 10 The close | S | Gates, sweep, the PR |


## D3 addendum (2026-09-05 06:50) — the notifier as built

`holdspeak/desktop_notify.py`: macOS posts through `osascript -e 'display
notification …'` (the PyObjC `UserNotifications` bridge is not in the
venv, and `UNUserNotificationCenter` refuses an unbundled python process
anyway); Linux through the existing libnotify seam. Consequence, said
plainly: an `osascript` banner carries NO click action — "one click →
the shade" waits for the packaged app bundle (174/179). V0 honours
Article III (the body is the count line only unless opted in), the
edge rule, quiet hours, and writes a `heartbeat.notify` receipt per
banner. The needs-you aggregate lives in
`holdspeak/services/needs_you_aggregate.py` (the route reads a
stale-while-refresh cache; `?fresh=1` rebuilds; `computedAt`, `stale`,
`sweepId` on the wire). The brief regenerates once a day after quiet
hours (`runtime/cadence.py::_maybe_regenerate_brief`) before any push.


## Counsel (2026-09-05 07:40): RATIFY-W-C — the rulings

- **M1 mute:** the mute list filters BOTH the notification edge count and
  the aggregate count; muted Rooms still appear in the shade, dimmed,
  with a `MUTED` token, and are NOT counted in the caption — ONE count
  everywhere (badge = shade caption = notification). (M2 ruled with it.)
- **M3:** `needs_you_aggregate.build_aggregate` is the single builder;
  `HeartbeatService.refresh_aggregate` calls it.
- **S1:** the shade caption is the SHORT form `PROJECTS · N NEED YOU`
  (the rows say which Rooms; the notification says `across M projects`).
- **S2:** D2(b)'s click action is DEFERRED to the bundle (174/179); the
  V0 banner is informational only and says so nowhere on the face (no
  promise, no sentence).
- **S3:** the second bubble on the Notification board is a design-only
  reference of what is SWALLOWED in quiet hours — never fired.
- **S4:** `Generate now` is disabled while a brief generates (a
  `GENERATING` token on the row), exactly like `Run now` mid-sweep.
- **S5:** ⌘K's PROJECTS group lists at most 10 Rooms — by needs-you
  count, then name; the rest reach through the Projects surface.
- **N1:** the sweep's rate bound = the per-watch cadence floor (1 min)
  × the tick (15 min); LAN reads are free; documented, no cap in V0.
- **N2:** the sweep receipt summarizes outcomes (counts per state + the
  failures' ids), never the full list.
