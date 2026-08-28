# HS-144-04 — Upcoming rail + doorframe repairs: implementation plan

**Planning ground truth:** committed `feat/hs144-03-kanban-glass` at
`e2e1df79`, inspected 2026-08-27. The working tree has in-progress Story-03
roadmap edits, so this plan deliberately treats the committed tree as fact and
treats the accepted Story-03 plan/disposition as the post-03 composition
contract. In particular, the target Chair is `door → meetings → agents`, with
the full-width Door board first, `FinishThoughtsLane` unmounted, and
`MeetingsLane` retained below it only until this story moves its *upcoming*
scheduled-recording rows into the Door rail.

This is glass and doorframe work. It consumes the established `GET /api/door`
read model and the established schedule/settings verbs; it does not add a
calendar, schedule, settings, or routing backend.

## 0. Non-negotiable boundaries

1. **One aggregate, one timeline.** The rail is a section of Story-03's
   `DoorBoardLane`, consuming its already-fetched `GET /api/door` response.
   It must not independently fetch calendar rows, query schedules, merge or
   sort client-side, or invent a second timeline store. `upcoming` is already
   a stable server sort by `(starts_at, source, id)`.
2. **Truthful kinds.** Render `source: "calendar_event"` as an `EVENT` and
   `source: "scheduled_recording"` as a `SCHEDULED RECORDING` (or the
   equally explicit `RECORDING` label in the compact row). A calendar event is
   never presented as a recording, and a scheduled recording is never
   presented as an invitation. This is the Article VI truth boundary.
3. **The schedule form is reused, not recreated.** The rail's one-click
   create affordance calls the existing `useDesk.getState().openScheduleCreate`
   store verb. It opens the existing globally mounted `ScheduleCreateWindow`,
   whose `StringGadget` title retains its click-to-toggle speak-to-fill mic and
   whose submission remains the existing `createSchedule → POST
   /api/scheduled-recordings` path. No second title/date/cron/duration form,
   no modal, no direct rail POST, and no new endpoint.
4. **No duplicate scheduled rows.** Once the rail owns all future
   `scheduled_recording` entries, `MeetingsLane` returns to live/recent
   meetings only. It remains directly below the Door board, preserving live
   capture and recent-meeting reachability. It must not show the same schedule
   a second time merely because its store also knows about it.
5. **A readiness fact, not timing theatre.** The `/meetings` proof awaits a
   named DOM attribute whose value is set only after `SurfaceWindows` has
   registered its normal-Door surface rows. It must not use a fixed delay,
   retry loop, or snapshot count as a substitute. The direct precedent is
   HS-143-14's `data-assignment-summary-state="loaded"`: the server-backed
   assignment summary has actually landed before the real-hub test measures
   the roster (`web/src/pages/cores/CapabilityAssignmentsCore.tsx:48-50`;
   the test waits for it at `tests/e2e/test_hs143_assignments_glass.py:70-76`).
6. **Calendar source stays in Meetings Settings.** The one source is a future
   meeting input, not a new tile, System RAW debris, a Door-only hidden dial,
   or an integrations platform. The UI reads the backend-derived
   `_calendar_subscription` fact; it never parses the URL or derives an
   egress host in the browser.

## 1. Obligation register

| Story acceptance obligation | Implementation slice(s) | Binding proof |
| --- | --- | --- |
| The Door shows the server-merged ordered `upcoming` timeline with honest event/recording labels, relative time, and designed populated, empty, and calendar-less states. | S1, S5 | `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`; `tests/e2e/test_hs144_door_glass.py::test_upcoming_rail_real_hub_states_and_dimensions` proves real calendar and schedule projections at 1440, 393, and 200%. |
| A schedule is created from the Door in world through the Phase-136 form/verb, its title mic remains present, and its successful create revalidates the rail without a second implementation. | S1, S2, S5 | `DoorBoardLane.test.tsx`; existing `CaptureHero.test.tsx`; `scheduledRecordingSlice.test.ts`; real-hub `test_upcoming_rail_schedule_create_round_trip_and_arming_cancel`. |
| The future schedule appears only in the rail while live/recent meetings remain reachable beneath the board. | S1, S2, S5 | `MeetingsLane.test.tsx` proves no schedule-to-lane projection and preserved live/recent header/footer reachability; Door glass proves one schedule row in one place. |
| The Go menu is visible, opens, and can launch an application at 393px without document overflow. | S3, S5 | New `web/src/desk/components/DeskMenuBar.test.tsx`; `test_hs144_door_glass.py::test_go_menu_is_usable_at_393`. |
| `/meetings` always opens its registered Meetings surface, rather than racing the redirect against registration. | S4, S5 | `web/src/desk/__tests__/surface-windows.test.tsx`, `web/src/desk/__tests__/shell.test.tsx`, and `test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15` (15 serial fresh navigations). |
| One calendar subscription is editable under Meetings Settings with an input mic and one truthful HTTPS-only egress chip; file/disabled input carries no chip. | S2, S5 | New `web/src/pages/cores/__tests__/SettingsCalendar.test.tsx`; existing `settingsFaceRoster.test.tsx`, `SettingsCore.test.ts`, `settingsWriters.test.ts`; Door glass settings legs at both widths. |

## 2. Verified inventory and anchors

### 2.1 Door aggregate, post-03 mount point, and timeline truth

| Verified file:line | Fact | Consequence for HS-144-04 |
| --- | --- | --- |
| `holdspeak/services/door_service.py:30-54` | `DoorService.get()` returns one `board`, one `upcoming`, and server-derived counts. | Extend Story-03's one `DoorBoardLane` reader; do not make another request/client store. |
| `holdspeak/services/door_service.py:153-164` | Enabled future recordings and future calendar events join before one `(starts_at, source, id)` sort. | Preserve returned order exactly. No browser sort or kind grouping that changes chronology. |
| `holdspeak/services/door_service.py:167-195` | Reserved row shape is identical across kinds: `id`, `source`, `target_ref`, `title`, `starts_at`, `ends_at`, nullable `location`/`meeting_url`, and `state`; only source distinguishes calendar from schedule. | Give source an explicit visual label; show only supplied location/link facts. Do not infer an invitation, attendee, or recording lifecycle. |
| `assets/story-03-kanban-glass-plan.md:43-49, 81-105` | Accepted post-03 design registers full-width `door`, creates `DoorBoardLane.tsx`, and makes it the Chair's board mount. | The rail is a child/section in `web/src/desk/chair/lanes/DoorBoardLane.tsx`, not a new Chair lane/window. The exact new file has no committed line number yet; this approved target is the authoritative mount point. |
| `assets/story-03-kanban-glass-plan.md:56-58, 301-313` | `FinishThoughtsLane` is unmounted; `MeetingsLane` remains unchanged below the board through Story 03 only. | Do not resurrect active thoughts. Story 04 removes only scheduled rows from Meetings while retaining live/recent duties. |
| `web/src/desk/chair/ChairHome.tsx:38-63`, `web/src/desk/chair/laneContract.ts:26-31`, `web/src/desk/chair/lanes/index.ts:12-17` | Committed pre-03 Chair still owns hero/active slot and four old lane registrations. | These are shared-file regression anchors, not a reason to plan against the obsolete four-lane composition. Story 03 changes them first. |

### 2.2 Existing schedule create control and its actual posting path

| Verified file:line | Fact | Consequence |
| --- | --- | --- |
| `web/src/desk/chair/hero/CaptureHero.tsx:255-263` | The committed Phase-136 visible `Schedule` control calls `useDesk.getState().openScheduleCreate()`. | The Door rail calls this exact store verb. **Anchor surprise:** the committed control is on the capture hero, not on the Cadence surface and not in `MeetingsLane`. The older audit's Cadence click-depth is not a current source anchor. |
| `web/src/desk/DeskApp.tsx:181-184` | Normal Desk mounts one global `<ScheduleCreateWindow />`. | A rail click opens the same in-world DeskWindow; no Door modal/window implementation is needed. |
| `web/src/desk/components/ScheduleCreateWindow.tsx:55-60, 82-120, 136-210` | Existing window owns title, once/recurring, time/cron, duration, error retention, and submit. `StringGadget` is used for title at `:138-145`. | Leave this form and its labels intact. Its title mic comes from the default gadget contract. |
| `web/src/desk/store/scheduledRecordingSlice.ts:41-51` | `createSchedule(input)` is the sole browser writer: `apiFetch("/api/scheduled-recordings", { method: "POST", json: input })`, then `loadSchedules()`. | Rail must never POST. It may use the schedule-store list only as a post-save invalidation signal for its own aggregate `reload()`. |
| `web/src/desk/store/scheduledRecordingSlice.ts:162-168` | `openScheduleCreate`/`closeScheduleCreate` own the chooser lifecycle. | The rail must not duplicate close/open state. |
| `web/src/desk/chair/lanes/MeetingsLane.tsx:84-110, 121-162` | The old lane's `nextFireLabel()` and `scheduleToLaneItem()` make `SCHEDULED` rows; it loads schedules and interleaves them live → schedules → archived. | Relocate the time idiom with its tests, then remove these schedule projections/loading responsibility after the Door rail is real. |

### 2.3 Relative time, menu, route race, and readiness precedent

| Verified file:line | Fact | Consequence |
| --- | --- | --- |
| `web/src/desk/chair/lanes/MeetingsLane.tsx:84-99` | The existing relative-time idiom is `nextFireLabel`: future under 24h is `in Hh Mm`/`in Mm`; later time is local `MMM DD HH:MM`. | Extract/rename this behavior into a narrow Door upcoming-time helper instead of introducing `Intl.RelativeTimeFormat`, an ambiguous "soon", or a second formatting dialect. The row supplies the semantic prefix (`NEXT`/`STARTS`) so it does not read `Next: Next`. |
| `web/src/desk/components/DeskMenuBar.tsx:20-25, 72-114` | `Go` is the third member of one registry-derived `DeskMenuBar`; each button owns a portal `WorkMenu`. | Do not add a parallel Go registry/menu. Add a stable `data-menu-id` hook and retain only the Go item at compact width. |
| `web/src/desk/components/chrome-menus.css:736-773` | At `max-width: 720px`, `.desk-verbbar { display: none; }`. At 393px this hides Go together with Desk/Object/Window. | This is the actual Go-menu diagnosis. Replace blanket hiding with a compact rule that hides Desk/Object/Window but preserves the real Go title and its WorkMenu; prove it has no page overflow. |
| `web/src/App.tsx:16-35` | A demoted `/meetings` route effect queues `openSurfaceWhenReady("review-meetings")` and redirects to `/`. | The route itself is not a separate Meetings page; test the real demotion path, not a direct Zustand open. |
| `web/src/desk/shell.ts:10-33` | Surface openers register in a module map; an early deep-link queues until `registerSurface` flushes it. | Preserve this one dispatcher. Expose its completed normal-Door registration as a testable fact at the `SurfaceWindows` boundary; do not sleep around it. |
| `web/src/desk/components/SurfaceWindows.tsx:308-353` | Normal rows are registered in an effect at `:330-351`; the component's current `ready` only gates first-value recovery and says nothing about completed normal registry registration. | Add an explicit normal registry readiness state/attribute after all normal rows and aliases are registered. This closes the audit-B observation gap rather than waiting for a generic shell node. |
| `tests/e2e/test_hs143_assignments_glass.py:64-76`; `web/src/pages/cores/CapabilityAssignmentsCore.tsx:46-50` | HS-143's fixed 393 hydration race waits for `data-assignment-summary-state="loaded"`, a server-summary fact, heading, and complete row roster. | Apply the same discipline: the deep-link e2e awaits a named registered-surface fact and the actual Meetings frame. It must not use a timer or `count()` before the underlying fact exists. |

### 2.4 Settings tile and egress derivation

| Verified file:line | Fact | Consequence |
| --- | --- | --- |
| `web/src/pages/cores/settingsPrefs.tsx:28-46` | Phase 139's roster is authored and the Meetings tile currently owns `keys: ["meeting"]`. | Add `"calendar"` to the existing Meetings tile; do not create an eighth Calendar tile. |
| `web/src/pages/cores/SettingsCore.tsx:435-452, 747-853` | Settings is the sole full-document writer; the authored Meetings module is the future glass slot. `StringGadget` is its standard text well. | Add a concise `Calendar` group above the operator RAW fold: `Subscription` at `calendar.subscription`, saved through existing `update`, not another route/writer. Keep blank as `""` rather than converting it to `null`, because the backend validates a string. |
| `web/src/desk/surface/gadgets.tsx:215-280` | `StringGadget` defaults `mic = true` and renders `Speak ${label}`. | Use it with no `mic={false}`. The Settings proof must assert `Speak Calendar subscription` exists. |
| `holdspeak/services/settings_service.py:110-129` | `GET/PUT /api/settings` includes the nonpersisted `_calendar_subscription` summary. | UI reads this fact rather than parsing its own input into an egress claim. |
| `holdspeak/config/integrations.py:72-103` | Summary is `{kind, host, refresh_seconds, egress}`: HTTPS alone has `egress: true`; file, disabled, and invalid are false. | Render exactly one EgressChip only when `egress === true`, derived from host/cadence. Never show a URL chip for local files or disabled calendar. |
| `web/src/desk/surface/gadgets.tsx:714-758` | `EgressChip` is the single permitted badge species and accepts explicit label/title/scope. | Use this component with `scope="cloud"`, for example `FETCHES CALENDAR.EXAMPLE · 15 MIN`; title names the host/cadence and the established no-credentials/no-headers constraint. |

## 3. Target implementation shape

### 3.1 Door rail

`DoorBoardLane` already owns an aggregate-local `reload()` under the Story-03
contract. Add an `UpcomingRail` presentation section there (a local component
is fine; a second fetch component is not):

- Read `upcoming` only from the same typed Door response as the board.
- Keep server order. For every row, render a terse kind label, title, existing
  relative/absolute timestamp idiom, and only supplied `location`/meeting URL
  facts. Never expose raw `target_ref` or claim a capture will auto-start.
- **Populated:** use one dense chronological rail with kind-first rows, not
  calendar and recording sublists. `EVENT` and `SCHEDULED RECORDING` make the
  mixed timeline scanable.
- **Calendar-less but scheduled:** a schedule row renders normally and no
  empty calendar heading/chrome appears. The calendar source is optional, so
  its absence is not an error.
- **Truly empty:** retain a designed, in-flow `UPCOMING` empty well with the
  schedule affordance rather than removing the rail and leaving a visual
  hole. It states no future time is scheduled; it does not pretend a calendar
  is broken.
- **Fetch failure:** use the Door lane's established in-flow `SurfaceState` /
  retry treatment. Do not hide a failure behind an empty rail.
- The rail's `Schedule recording` button calls `openScheduleCreate()` once.
  Because the reused form updates `scheduledRecordings` after a successful
  POST, DoorBoardLane observes that existing store list only as invalidation
  and reloads its aggregate after the first post-mount schedule-list change.
  It never renders that list or posts itself. This makes the new row appear
  after the existing form closes while canceling a form can only cause a
  harmless reread.

### 3.2 Meetings lane after the move

Remove `ScheduledRecording`, `loadSchedules`, `nextFireLabel`,
`scheduleToLaneItem`, enabled-schedule filtering, and schedule interleaving
from `MeetingsLane`. Retain live-first/recent ordering, its header and footer
open to `review-meetings`, and `null` only when there are no live/recent
meetings. The real Door rail is now the schedule's one Chair appearance.

### 3.3 Settings row

Within existing `case "meetings"`, place a `Calendar` group immediately after
`Capture + export` and before `Actuators`:

- `Subscription` is a `StringGadget` for `calendar.subscription`, placeholder
  `ICS file path or HTTPS URL`, input mic intact.
- Read `_calendar_subscription` as a small typed view local. It provides only
  the derived fact. If it says HTTPS/egress, show one `EgressChip`; otherwise
  show no egress chip. The label/tip name the returned host and 15-minute
  cadence, not the source pathname or a browser-derived host.
- Let the existing debounced full-document Settings writer send the existing
  revision and existing `PUT /api/settings`. Do not add a save button, manual
  refresh, credentials UI, headers UI, or a calendar-specific endpoint.

### 3.4 Doorframe repairs

- **393 Go:** add `data-menu-id={m.id}` to the existing menu item wrapper and
  change the compact CSS rule so its `nav` remains present but only
  `[data-menu-id="go"]` displays. The preserved button stays the existing
  keyboard/pointer/WorkMenu implementation. The Desktop menu set is unchanged.
- **Meetings route:** give normal `SurfaceWindows` an explicit registration
  state. A wrapper/landmark such as
  `data-surface-registry-state="registered"` may turn true only after the
  `rows.map(registerSurface)` plus alias registrations finish. The e2e starts
  from `/meetings`, awaits that fact, then awaits the real
  `#surface-meetings` window. Keep first-value recovery truthful: it must not
  claim normal surface registration while only Setup is registered.

## 4. Delivery slices

### S1 — Put one truthful upcoming rail in the post-03 Door lane

**Files**

- Modify `web/src/desk/chair/lanes/DoorBoardLane.tsx` (created by Story 03).
- Create `web/src/desk/chair/lanes/upcomingTime.ts` and
  `web/src/desk/chair/lanes/upcomingTime.test.ts`.
- Modify `web/src/desk/chair/lanes/DoorBoardLane.test.tsx` (created by Story
  03).
- Modify `web/src/desk/chair/lanes/MeetingsLane.tsx` and
  `web/src/desk/chair/lanes/MeetingsLane.test.tsx`.

**Work**

1. Move the committed `nextFireLabel` semantics into the tiny named helper so
   it is testable without the retired schedule projection; use it for either
   upcoming source.
2. Render the rail under the Door board headline from the one already-loaded
   aggregate, preserving the server timeline's order and exact source truth.
3. Add the populated, empty, initial-error/retry, calendar-less-with-schedule,
   source-label, timestamp, nullable detail, and no-client-sort tests.
4. Remove scheduled-recording rows from MeetingsLane while keeping real
   meeting behavior/reachability. Assert a schedule-only store no longer makes
   a Meetings lane and a rail fixture owns the schedule exactly once.

**Named proofs**

- `web/src/desk/chair/lanes/upcomingTime.test.ts`
- `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`
- `web/src/desk/chair/lanes/MeetingsLane.test.tsx`
- `web/src/desk/chair/ChairHome.test.tsx`
- `web/src/desk/chair/Chair.test.tsx`

```bash
cd /Users/karol/dev/tools/HoldSpeak
(cd web && npx vitest run \
  src/desk/chair/lanes/upcomingTime.test.ts \
  src/desk/chair/lanes/DoorBoardLane.test.tsx \
  src/desk/chair/lanes/MeetingsLane.test.tsx \
  src/desk/chair/ChairHome.test.tsx \
  src/desk/chair/Chair.test.tsx)
```

### S2 — Reuse schedule creation and give calendar its rightful Settings home

**Files**

- Modify `web/src/desk/chair/lanes/DoorBoardLane.tsx` and
  `web/src/desk/chair/lanes/DoorBoardLane.test.tsx` only for the launch and
  existing-store invalidation seam.
- Modify `web/src/pages/cores/settingsPrefs.tsx`.
- Modify `web/src/pages/cores/SettingsCore.tsx`.
- Modify `web/src/pages/cores/core-types.ts` for the explicit `calendar` and
  `_calendar_subscription` wire views.
- Create `web/src/pages/cores/__tests__/SettingsCalendar.test.tsx`.
- Extend `web/src/pages/cores/__tests__/SettingsCore.test.ts` and
  `web/src/pages/cores/__tests__/settingsFaceRoster.test.tsx`.

**Work**

1. Rail create is a single `openScheduleCreate()` call. Do not touch
   `ScheduleCreateWindow.tsx` or `scheduledRecordingSlice.ts`; their untouched
   existing POST and mic prove it is reuse.
2. Test the post-save Door revalidation through the existing schedule-list
   change and prove no rail code calls `/api/scheduled-recordings`.
3. Make Meetings own `calendar` in the authored tile registry. Add the
   Subscription well and read the server-provided egress fact.
4. Prove the mic, full-document/revision writer, URL-only single badge, no
   file/disabled badge, and settings refusal/reconciliation behavior. The UI
   must not introduce a second persistent writer.

**Named proofs**

- `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`
- `web/src/desk/chair/hero/CaptureHero.test.tsx` (existing Phase-136 launch
  path remains intact)
- `web/src/desk/store/__tests__/scheduledRecordingSlice.test.ts` (existing
  POST/reload authority remains intact)
- `web/src/pages/cores/__tests__/SettingsCalendar.test.tsx`
- `web/src/pages/cores/__tests__/SettingsCore.test.ts`
- `web/src/pages/cores/__tests__/settingsFaceRoster.test.tsx`
- `web/src/pages/cores/__tests__/settingsWriters.test.ts`

```bash
cd /Users/karol/dev/tools/HoldSpeak
(cd web && npx vitest run \
  src/desk/chair/lanes/DoorBoardLane.test.tsx \
  src/desk/chair/hero/CaptureHero.test.tsx \
  src/desk/store/__tests__/scheduledRecordingSlice.test.ts \
  src/pages/cores/__tests__/SettingsCalendar.test.tsx \
  src/pages/cores/__tests__/SettingsCore.test.ts \
  src/pages/cores/__tests__/settingsFaceRoster.test.tsx \
  src/pages/cores/__tests__/settingsWriters.test.ts)
```

### S3 — Restore the compact Go menu without a parallel navigator

**Files**

- Modify `web/src/desk/components/DeskMenuBar.tsx`.
- Modify `web/src/desk/components/chrome-menus.css`.
- Create `web/src/desk/components/DeskMenuBar.test.tsx`.
- Extend `tests/e2e/test_hs144_door_glass.py` (created by Story 03).

**Work**

1. Mark the registry-derived menu wrappers by ID, then at compact width retain
   Go alone rather than applying `display: none` to the entire verb bar.
2. Preserve all four desktop titles, keyboard activation, outside-dismissal,
   portal positioning, and registry-derived Go entries. The repair is layout
   visibility, not a menu rewrite.
3. At 393, click Go, assert a real Go entry is visible, invoke `Meetings`, and
   observe the registered Meetings surface. Assert document width stays within
   viewport and capture the shot.

**Named proofs**

- `web/src/desk/components/DeskMenuBar.test.tsx`
- `web/src/desk/__tests__/verbRegistry.test.ts`
- `web/src/desk/__tests__/workMenu.test.tsx`
- `tests/e2e/test_hs144_door_glass.py::test_go_menu_is_usable_at_393`

```bash
cd /Users/karol/dev/tools/HoldSpeak
(cd web && npx vitest run \
  src/desk/components/DeskMenuBar.test.tsx \
  src/desk/__tests__/verbRegistry.test.ts \
  src/desk/__tests__/workMenu.test.tsx)

HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q \
  tests/e2e/test_hs144_door_glass.py::test_go_menu_is_usable_at_393
```

### S4 — Make the Meetings deep-link test await actual registration

**Files**

- Modify `web/src/desk/components/SurfaceWindows.tsx`.
- Extend `web/src/desk/__tests__/surface-windows.test.tsx`.
- Extend `web/src/desk/__tests__/shell.test.tsx`.
- Extend `tests/e2e/test_hs144_door_glass.py`.

**Work**

1. Separate current render readiness from completed normal-surface registry
   readiness, and expose the latter on a stable Door DOM anchor. Registration
   remains the existing `registerSurface` / pending-open mechanism.
2. Regression-test early queued `review-meetings` opens against the actual
   registration fact, including normal-Door versus first-value-recovery
   distinction.
3. Add a single serial e2e test that seeds/dismisses arrival, enters
   `/meetings` through the real route 15 times in one test, awaits
   `data-surface-registry-state="registered"` and `#surface-meetings` each
   time, and asserts no page errors. It must not hide a failure with retries
   or sleeps.

**Named proofs**

- `web/src/desk/__tests__/surface-windows.test.tsx`
- `web/src/desk/__tests__/shell.test.tsx`
- `web/src/routes.test.ts`
- `tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15`

```bash
cd /Users/karol/dev/tools/HoldSpeak
(cd web && npx vitest run \
  src/desk/__tests__/surface-windows.test.tsx \
  src/desk/__tests__/shell.test.tsx \
  src/routes.test.ts)

HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q \
  tests/e2e/test_hs144_door_glass.py::test_meetings_deep_link_waits_for_registered_surface_x15
```

### S5 — Real hub, dimensions, states, and beauty pass

**Files**

- Extend `tests/e2e/test_hs144_door_glass.py` rather than creating a parallel
  Door test file.
- Refresh the existing Story-03 shot directory or create the clearly scoped
  `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/story-04-shots/`
  only for Story-04 outputs.
- Modify `web/src/desk/chair/chair.css` only if shots show a real rail layout
  defect; re-run its neighboring tests if touched.

**Work**

1. Use production `MeetingWebServer` composition and real database
   repositories/services to seed a calendar event and an enabled scheduled
   recording. The browser consumes `/api/door`; it must not mock the client
   response.
2. Prove at 1440 and 393: populated mixed order, schedule-only calendar-less
   state, truly empty state, controlled Door-service error state, source labels,
   local relative/absolute times, one source of the schedule row, schedule
   create round-trip, and the preserved arming/cancel behavior.
3. Prove Meetings Settings: URL field with mic and one host/cadence egress chip;
   file/disabled state without a chip. Capture both widths and a 200% populated
   Door state (720×450 CSS viewport at device scale 2), with zero console errors
   and no document horizontal overflow.
4. Run the compact Go action and the 15-serial `/meetings` route leg in this
   same production file. Review shots only after functional proof; check the
   opaque/beveled material, rail scan order, touch targets, contained board
   scroller, and no duplicated active thought or schedule. Owner sees the
   refreshed shots before any merge claim.

**Named proofs and focused commands**

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q tests/e2e/test_hs144_door_glass.py

# Shared Chair/First-Sentence geometry neighbor; this is not a full suite.
HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q tests/e2e/test_hs141_chair_geometry.py
```

## 5. Required [ORCH-CALL]s

| [ORCH-CALL] | Recommendation | Why / implementation consequence |
| --- | --- | --- |
| **Calendar Settings placement** | **Accept existing Meetings tile, with a visible Calendar group immediately after Capture + export.** | Story 02 already ruled it, Phase 139 protects an authored compact tile roster, and a subscription is a future-meetings source. It is discoverable without turning the Door into a configuration room or inventing an eighth tile. The group uses `StringGadget` with mic and one derived URL-only EgressChip. |
| **Rail versus MeetingsLane final shape** | **Move all future SCHEDULED rows into the Door rail; MeetingsLane owns live/recent meetings only. Do not duplicate.** | The aggregate timeline is the canonical future chronology. Keeping schedule rows beneath it makes the Door lie by presenting the same future event twice, while removing the whole Meetings lane would make live/recent history less reachable. |
| **Relative-time formatting** | **Preserve/extract Phase-136's `in Hh Mm` under-24-hour and local `MMM DD HH:MM` otherwise behavior; add a semantic row prefix rather than inventing vague time prose.** | It is an existing scanned-on-Chair idiom and meets “Next in 45 min” without a browser locale/time-authority rewrite. The helper receives the server UTC instant and must render invalid input as no time fact, never “now” fiction. |
| **≤1-click schedule-create affordance** | **One plainly labeled `Schedule recording` Button in the rail header/empty well opens the existing ScheduleCreateWindow in one click.** | It remains an in-world DeskWindow, keeps the title mic and Phase-136 POST/cancel/countdown machinery, avoids a second form, and gives the empty rail a useful first action. There is no pre-dialog or Cadence detour. |
| **Route readiness fact shape** | **Expose `data-surface-registry-state="registered"` from normal `SurfaceWindows` only after its real surface/alias registrations complete, then await it before asserting `#surface-meetings`.** | It mirrors HS-143's successful factual-ready barrier rather than timing the React effect. The attribute must name what it knows—registered surfaces—not falsely say that HistoryCore's content has loaded. |
| **393 Go compact grammar** | **Keep Go visible as the one compact verb-bar title; hide Desk/Object/Window at compact width, not the bar itself.** | Go is the app-navigation menu and the audit's missing direct path. It remains the same registry/WorkMenu species, preserves desktop menus, and fits beside existing trust/search/clock chrome when the other three titles are absent. |

## 6. Shared-file net and stop signals

### Mandatory shared-file net

The following are named because Story 04 consumes Story 03's Chair reforge;
passing only new rail tests would not prove the shared doorway remains intact.

**Post-03 Door/Chair Vitest net**

- `web/src/desk/chair/lanes/DoorBoardLane.test.tsx`
- `web/src/desk/chair/lanes/MeetingsLane.test.tsx`
- `web/src/desk/chair/Chair.test.tsx`
- `web/src/desk/chair/ChairHome.test.tsx`
- `web/src/desk/chair/FinishThoughtsLane.test.tsx`
- `web/src/desk/chair/ThoughtEntry.test.tsx`
- `web/src/desk/chair/hero/CaptureHero.test.tsx`
- `web/src/desk/chair/lanes/AgentsLane.test.tsx`
- `web/src/desk/chair/lanes/BriefLane.test.tsx`
- `web/src/desk/chair/lanes/FollowThroughLane.test.tsx`
- `web/src/desk/DeskApp.test.tsx`
- `web/src/desk/components/FirstWords.test.tsx`
- `web/src/desk/pullouts/IntelligencePullout.test.tsx`
- `web/src/desk/pullouts/IntelligenceTruth.test.tsx`
- `web/src/desk/pullouts/IntelligenceWalk.test.tsx`
- new `web/src/desk/chair/lanes/upcomingTime.test.ts`
- new `web/src/desk/components/DeskMenuBar.test.tsx`
- new `web/src/pages/cores/__tests__/SettingsCalendar.test.tsx`
- existing settings net: `SettingsCore.test.ts`, `settingsFaceRoster.test.tsx`,
  `settingsWriters.test.ts`
- route/registry net: `surface-windows.test.tsx`, `shell.test.tsx`,
  `routes.test.ts`

**Real-hub e2e net**

- `tests/e2e/test_hs144_door_glass.py` — Story 03's new Door glass file,
  extended rather than forked for all rail/settings/Go/deep-link state shots.
- `tests/e2e/test_hs141_chair_geometry.py` — shared Chair geometry/overflow
  and First-Sentence neighbor.
- The retained Story-03 fresh-arrival neighbors:
  `tests/e2e/test_hs14104_refinement_glass.py`,
  `tests/e2e/test_hs14105_context_glass.py`, and
  `tests/e2e/test_hs14105a_default_context_glass.py`.

Run this bounded net after focused slices, never as a substitute for them:

```bash
cd /Users/karol/dev/tools/HoldSpeak
(cd web && npx vitest run \
  src/desk/chair/lanes/DoorBoardLane.test.tsx \
  src/desk/chair/lanes/MeetingsLane.test.tsx \
  src/desk/chair/Chair.test.tsx \
  src/desk/chair/ChairHome.test.tsx \
  src/desk/chair/FinishThoughtsLane.test.tsx \
  src/desk/chair/ThoughtEntry.test.tsx \
  src/desk/chair/hero/CaptureHero.test.tsx \
  src/desk/chair/lanes/AgentsLane.test.tsx \
  src/desk/chair/lanes/BriefLane.test.tsx \
  src/desk/chair/lanes/FollowThroughLane.test.tsx \
  src/desk/DeskApp.test.tsx \
  src/desk/components/FirstWords.test.tsx \
  src/desk/pullouts/IntelligencePullout.test.tsx \
  src/desk/pullouts/IntelligenceTruth.test.tsx \
  src/desk/pullouts/IntelligenceWalk.test.tsx \
  src/desk/chair/lanes/upcomingTime.test.ts \
  src/desk/components/DeskMenuBar.test.tsx \
  src/pages/cores/__tests__/SettingsCalendar.test.tsx \
  src/pages/cores/__tests__/SettingsCore.test.ts \
  src/pages/cores/__tests__/settingsFaceRoster.test.tsx \
  src/pages/cores/__tests__/settingsWriters.test.ts \
  src/desk/__tests__/surface-windows.test.tsx \
  src/desk/__tests__/shell.test.tsx \
  src/routes.test.ts)

HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright" \
  uv run --python 3.13.11 pytest -q \
  tests/e2e/test_hs144_door_glass.py \
  tests/e2e/test_hs141_chair_geometry.py \
  tests/e2e/test_hs14104_refinement_glass.py \
  tests/e2e/test_hs14105_context_glass.py \
  tests/e2e/test_hs14105a_default_context_glass.py
```

### Stop signals

| Stop signal | Required correction |
| --- | --- |
| Rail makes a second `/api/door` fetch, merges/sorts kinds client-side, or pulls calendar data directly. | Return to the existing DoorBoardLane aggregate; server chronology is the sole timeline authority. |
| `EVENT` looks like a capture or a schedule looks like an invitation. | Restore exact source label and remove fabricated semantic metadata. |
| A schedule is visible in both rail and MeetingsLane. | Delete its MeetingsLane projection; retain only live/recent meetings there. |
| Door code posts to `/api/scheduled-recordings` or reproduces title/cron/duration controls. | Use only `openScheduleCreate`; leave the Phase-136 form/slice as writer. |
| URL egress chip is shown for a file/disabled source, or host/cadence is browser-parsed. | Consume only `_calendar_subscription.egress/host/refresh_seconds` and render no chip otherwise. |
| Calendar becomes another Settings tile, a System RAW row, or a Door-hidden setting. | Return it to Meetings' authored group and existing one-writer save path. |
| Go is replaced with a hand-maintained menu, disappears at 393, or horizontal page overflow appears. | Preserve `DeskMenuBar → menuVerbs → WorkMenu`; repair compact CSS only. |
| `/meetings` test uses `wait_for_timeout`, retries, or checks a generic wrapper before the actual registry fact. | Await named normal surface registration then `#surface-meetings`, as the HS-143 readiness precedent requires. |
| First-value recovery says normal surfaces are registered. | Keep the readiness attribute scoped to actual normal registry completion; recovery has Setup only. |

## 7. Evidence checklist

- [ ] Record the two anchor surprises honestly: schedule create is committed on
  `CaptureHero`, not Cadence; Story-03's DoorBoardLane is an accepted target
  file rather than a committed source line at planning time.
- [ ] Capture focused Vitest output after reading it; no full suite command is
  authorized by this plan.
- [ ] Capture each real-hub e2e with the isolated-HOME commands above; the
  `/meetings` proof contains 15 serial attempts in its named test.
- [ ] Save populated, empty, error, and calendar-less schedule-only rail shots
  at 1440 and 393, plus 200% populated; include Settings URL/file states and
  compact Go proof.
- [ ] Verify zero page errors and zero document horizontal overflow on all
  Door/Go/Settings width legs.
- [ ] Review material/scanability after functional green and show the owner
  the updated shots before making a merge claim.

## Orchestrator dispositions (ruled 2026-08-28)

All five recommendations ACCEPTED as written:

1. Calendar settings live under the EXISTING Meetings Settings tile —
   no new tile, no Door-only control (the seven-tile reckoning
   stands); egress badge + mic on the input per house law.
2. The Door rail is the SOLE Chair location for future
   scheduled-recording rows; MeetingsLane keeps live/recent meetings —
   the non-duplicating shape.
3. The Phase-136 relative-time grammar is preserved and extracted
   narrowly — one idiom, not a second clock vocabulary.
4. One `Schedule recording` rail action calling the existing
   `openScheduleCreate()` path — reuse, never re-implementation.
5. The `/meetings` repair uses the awaited
   `data-surface-registry-state="registered"` server-rendered fact,
   modeled on the HS-143 readiness barrier; proof bar is 15 serial
   green runs of the real route.

The Go-menu repair note: the fix is a designed 393 presence for the
verb bar, not a bare `display:block` — it goes through the beauty
pass with the rest of the story's glass.

Build order: after HS-144-03 closes (single-writer tree).
