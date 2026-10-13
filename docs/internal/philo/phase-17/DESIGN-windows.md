# Design: windows (R4) and the phone (recon §5)

Cluster: **windows**. Source: `RECON-2026-10-13.md` R4 and section 5. Code
read at main `b50b13a0b` (2026-10-13). Every claim below cites the file and
line it stands on. This is a design, not code.

Seams (named, not designed here): the Runs on face itself and the one engine
chip (`DESIGN-verbs.md`); what the bell counts and what Needs you lists
(`DESIGN-attention.md`); the dock's 1440 content, the seeds, Places and the
final words (`DESIGN-words.md`).

## 1. The problem

Shots 026, 042, 043, 045, 047 and 013 at 1440: every door opens one more
window at the top-left; after five jobs the hub held ten (043). A meeting
opened 24 px over the Meetings list that opened it (026). Settings ▸ Choose
engines opened Runs on as a second window, retitled Settings to
"Settings · Runs on", and Runs on came back after a gadget close, a ⌃W and
a hub-API close (042, 043, 047). A thought is 820×640 for one sentence;
"Nothing needs you" is 700×650 (013). A "Meeting ready" card drew over three
windows at once.

Shots 065 to 082 at 393: every window is a full-screen sheet under a
"Windows: The week ▾" switcher (076); one tap on an icon selects and does
not open, twice (079, 080); the bare desk is an 18-icon grid (078); the dock
shows five of thirteen buttons and a "More" pager; the meeting footer takes a
quarter of the screen (068).

## 2. The cause in the code

### 2.1 Every door is "one more window"

- An application is a window: `SURFACE_APPLICATIONS` in
  `web/src/desk/applications.ts` gives each app a `windowId`;
  `openSurfaceWindow` (`web/src/desk/store/compositorSlice.ts:374`) makes an
  instance under that id. An object (a note, a meeting, a person) opens as
  `pullout:<ref>` through `openPrimitive` (`web/src/desk/shell.ts:136-155`)
  → `openPullout` (`compositorSlice.ts:242`). The hub holds one row per
  window (`holdspeak/services/desk_window_service.py`, `STATIC_WINDOWS`
  line 42, `WINDOW_FAMILIES` line 98).
- A meeting is deliberately split out of the Meetings window: PHILO-17
  (owner 2026-10-10, "A meeting opens in one window") made
  `openSurfaceWindow("review-meetings", "meeting:<id>")` redirect to
  `openPullout("meeting:<id>")` (`compositorSlice.ts:374-385`), and
  `migratedMeeting` moves a saved scoped Meetings row to a meeting window
  (`web/src/desk/compositor/hubWindows.ts:99-111`, applied at `463-477`,
  and at boot `1053-1056`). `openSourceRef` does the same for every
  `meeting:` ref (`web/src/desk/surface/citations.tsx:45-54`). So the list
  stays open and the record opens over it.
- A person does the opposite and it is the shape the recon likes (shot
  036): the person's window hosts `RelationshipPane` with `onBack`
  (`web/src/pages/cores/PeopleCore.tsx:447`, the Back Button at `639`),
  and `Pullout.tsx:63-67` hosts a meeting or a person "as an application
  window does". The grammar for list ▸ detail with Back exists; Meetings
  does not use it.

### 2.2 Where a new window lands

`DeskWindow.tsx:419-456`: a window with no saved rect is seeded by
`measure()` (fallback `{x: MARGIN, y: 64}`, line 332: the CSS home at the
top-left) and seated by `placeWindow`
(`web/src/desk/components/window/windowGeometry.ts:48-128`). The scan
scores every 32 px seat by head occlusion first, then overlap area, then
**distance from the home seat** (line 92), so the first windows all take the
top-left corner beside the icon column (`iconColumnRight`, line 137) and
cover each other's bodies. When every seat hides some title bar
("saturated", line 102) the window cascades `CASCADE_STEP = 24` off the
window placed last (lines 108-117): the "exactly 24 px over the Meetings
list" of shot 026. Nothing steps off the FRONT window by design; the corner
wins until the desk is full.

### 2.3 The Runs on ghost

1. Settings' lead plate presses `onOpen("models")`
   (`web/src/pages/cores/settingsPrefs.tsx:536`), which sets `moduleId`
   (`SettingsCore.tsx:1553`). The window title becomes
   `Settings · Runs on` because `PREF_MODULES` names the module "Runs on"
   (`settingsPrefs.tsx:58`) and the title is the open module's label
   (`SettingsCore.tsx:2449` → `windowName.ts:94`).
2. The module body for `models` is a redirect **inside render**:
   `SettingsCore.tsx:2350-2356` returns `null` and calls
   `openSurface("open-concierge")` as a side effect of rendering. It runs on
   every render of the Settings face.
3. Closing Runs on (gadget, ⌃W, or the hub's `close` verb followed by the
   `desk_changed` frame) changes `windowsById`; `SurfaceWindows` subscribes
   to it (`SurfaceWindows.tsx:96`) and re-renders its cores; Settings
   renders its `models` case again; `openSurface("open-concierge")` opens
   the window again; `hubWindows.sync` sends the open to the hub
   (`hubWindows.ts:802-810`). Three closes, three returns (042, 043, 047).
4. `MORE SETTINGS` stays buried because the ghost is always the newest
   row, so it is always front (`desk_window_service.py:345-346`, open =
   `++highest`).

The same loop waits behind every other door to Runs on: twelve call sites
open `open-concierge` or its alias `configure-runs-on`
(`FirstRun.tsx:406`, `ThoughtWorkspaceWindow.tsx:376`,
`CapabilitySection.tsx:191`, `WorkbenchWindow.tsx:1228`,
`DeskToolInspector.tsx:342`, `ProjectRoomCore.tsx:2306`,
`PreparePosture.tsx:188`, `UpdatePosture.tsx:564`, `SetupCore.tsx:193`,
`DictationSections.tsx:36`, `SettingsCore.tsx:2018`, `routes.tsx:69`).
The alias that once pointed at Settings is parked in
`applications.ts:188-189`.

### 2.4 Sizes

- Thought: `defaultW={820} defaultH={640}`
  (`web/src/desk/thought-workspace/ThoughtWorkspaceWindow.tsx:634-635`).
- Meeting 720×680, person 640×640 (`web/src/desk/pullouts/size.ts:14-18`);
  the Room drawer 900×600 (`web/src/desk/drawer/DrawerWindow.tsx:225-226`);
  Runs on `minW: 900, defaultH: 680` (`applications.ts:378-380`); Settings
  `minW: 560, defaultH: 600` (`applications.ts:194-195`).
- A window that is not `fitContent` and has no `defaultH` grows to its CSS
  `max-height`, capped at 78 % of the band (`DeskWindow.tsx:427-437`).
- Needs you is a Chair window with a CSS seat: half the band wide, 64 % of
  the band tall (`web/src/desk/chair/chair.css:132-182`), whatever it holds.
  "Nothing needs you" fills 700×650 because the seat is CSS, not content.

### 2.5 The toast

The "Meeting ready" aftercare card is one `<aside>` in `AmbientLayer`
(`web/src/components/AmbientLayer.tsx:238-247`), mounted once in
`AppShell.tsx:24`, drawn `ambient-aftercare-fixed` (position fixed) when no
slot takes it. It is one card over the glass; it looks "inside" whichever
window is under it, and three windows were.

### 2.6 The phone

- Compact is `(max-width: 720px)` (`web/src/desk/useCompactViewport.ts:5`).
- One tap selects: `DeskIcon.tsx:120-131` (`onClick` → `onSelect`,
  `onDoubleClick` → `onOpen`, Enter → open), wired by `Screen.tsx:190-191`.
  A phone has no double click in practice.
- The bare desk at 393 is the icon grid: `Screen.tsx:123` skips the free
  layout and draws `data-layout="grid"` (line 142).
- Every window is a sheet: `is-sheet` (`DeskWindow.tsx:1163`; `dock.css:510`
  fixes it full width). The head at 393 keeps close (left) and depth (right)
  only (`DeskWindow.tsx:1238-1250, 1270`).
- The title is the switcher: `DeskChrome.tsx:94-96` renders
  `ScreenSwitcher`, whose menu lists `phoneRing()`
  (`web/src/desk/components/window/phoneRing.ts:30-45`: the open Chair
  windows, then the desk windows in open order). The ring is a set, not a
  history: there is no "previous pane".
- The menu bar at 393 is Go alone (`DeskMenuBar.tsx:307`); Go's rows are
  `phoneGo` (`DeskMenuBar.tsx:56-107`): the four Chair windows, Meetings,
  Ask AI, People, Conductor, the projects, New ▸.
- The dock at 393 is the 1440 dock scrolled by pages with a "More"
  pager (`Dock.tsx:683-697`); its tiles are `DOCK_APPLICATIONS` plus the
  tail (Hide the menus, Places, the orb, Overview, Reset).
- Footers: `SurfaceFooter` (`web/src/desk/surface/SurfaceFooter.tsx`)
  portals egress, receipt and every verb into the frame's foot; at 393 the
  verbs wrap to three rows (shot 068: Open transcript, Send, Add to
  Project ▸, MD, SRT, Park).

## 3. The target behavior

Five window laws, then the phone grammar. The kernel the recon keeps
(drag, zoom, ⌃W, ⌘`, Overview, positions over reload) does not change.

**W1 One app, one window.** An application has one window. An object opened
from its list shows IN that window, with Back. The hub already carries the
window's object as `object_ref` on the row (`hubWindows.ts:216-234`,
`desk_window_service.py:330`); the detail IS the scoped window.
**W2 A settings pane is a pane.** Runs on is the Engines wing of Settings.
Settings is one window, titled "Settings".
**W3 A new window steps off the front window.** 24/24 from the front
window, inside the band, right of the icon column; never the corner while a
window is front.
**W4 A window is the size of its material.** A thought is a sticky; an empty
state is one line under the title.
**W5 One notice, in the menu bar.** Nothing transient draws inside or over a
window.

### 3.1 At 1440, press by press

Job 7, change the model (before: 3 presses, 2 windows + a ghost):
HoldSpeak ▸ Settings (1) → Engines wing (2) → pick the engine for a job
(3). One window. Close it: it stays closed. **3 presses, 1 window, 0 ghosts.**

Job 3, open a meeting (before: the record 24 px over the list):
Meetings (dock, 1) → Ledger standup row (2): the Meetings window shows the
meeting; its title is "Ledger standup"; the head's first verb is Back.
Back (3): the list, the row still selected. Reload: the window is on the
meeting (the row's `object_ref`). **No second window. No toast in the
window**; when the summary lands, the menu bar's bell shows "Ledger standup ·
ready" for six seconds; press it: the meeting.

Opening five doors in a row: Today, Meetings, People, Settings, Ask AI. Each
window opens 24 px right and 24 px down from the one in front, each title
bar in view, none in the icon column. Five windows, a staircase.

Write a thought: the window opens as a sticky, 520×360, and grows with the
text to its cap (820×640); a saved size always wins. Needs you with nothing
in it: the title bar and one line, "Nothing needs you", and its one verb.

### 3.2 At 393, press by press

Home: open the desk. There is no icon grid. The screen IS Go's list:
Needs you, Brief, The week, Capture; Meetings, Ask AI, People, Conductor;
the projects; New ▸. One tap opens any row (the Go menu in the bar keeps the
same rows: from any pane, Go is home).

Job 3 on the phone (before: ~12 presses, 3 panes): Home ▸ Meetings (1) ▸
Ledger standup (2): the Meetings pane shows the meeting. The head reads
`‹ Back · Ledger standup`. The foot shows one verb, Send, and `More ▸`
(Open transcript, Add to project, MD, SRT, Park). Back (3): the list. Back
(4): home. **Nothing is stacked; nothing is switched.**

Job 1 on the phone (before: 4 presses, 2 panes): Home ▸ Today (1); the bell
(2). **2 presses, 1 pane.**

The dock at 393: Today, Capture, Meetings, People. Four tiles, no pager.

### 3.3 The cost table, after

| Job | 1440 presses | 1440 windows | 393 presses | 393 panes |
|---|---|---|---|---|
| 1 Start the day | 6 → 4 (attention cluster owns the rest) | 3 → 2 | 4 → 2 | 2 → 1 |
| 3 Meeting: import, summary, decisions, actions, send | 14 → 13 | 2 + toast → 1 | ~12 → ~10 | 3 → 1 |
| 7 Change the model | 3 → 3 | 2 (+ ghost) → 1 | 3 → 3 | 2 → 1 |
| Open a thought and read it | 2 → 2 | 820×640 → a sticky | 2 → 1 | 1 |

Dead ends removed: "Runs on close" (one of six). Windows after Jobs 1-5:
ten → five (one per app opened, no ghost, no record over its list).

## 4. The design

### 4.1 W2: Runs on is the Engines wing of Settings (the ghost dies)

Component and store:
- `SettingsCore.tsx:2350-2356`: the `models`/`assignments` case renders
  `<RunsOnCore scope={moduleScope} />` (`web/src/features/runson/RunsOnCore.tsx:159`)
  instead of returning null and opening a window. No side effect in render.
- Settings' wings: `SETTINGS_WINGS` (`SettingsCore.tsx:240-243`) gains the
  module as a wing: `Settings | Engines | Accounts | Guide`. The lead plates
  (`settingsPrefs.tsx:518-562`) keep their Buttons; "Choose engines" switches
  the wing. The title stays "Settings" (`SettingsCore.tsx:2449` drops the
  section suffix; the wing names the section).
- `RunsOnCore` draws the form it draws on a phone (the list;
  `applications.ts:379` "a phone draws the list") whenever its host is
  narrower than 900 px, so it fits Settings' `minW: 560`. The content of
  that list (jobs, the engine chip, the catalog behind "Add an engine") is
  the verbs cluster's; this design only hosts it.
- Doors: `applications.ts:188-189` un-parks `{ key: "configure-runs-on",
  scope: "models" }` as a Settings alias and adds `{ key: "open-concierge",
  scope: "models" }`. Every one of the twelve call sites then opens Settings
  on the Engines wing with no edit. A scope they pass today
  ("meetings", "writing_dictation", a resource ref) rides through as the
  wing's focus, as `RunsOnCore`'s `scope` prop takes it now.
- `useConciergeController.ts:784` (Cancel closes `surface-concierge`)
  becomes "back to the Settings wing" (`moduleId = null`).

Hub and rows (additive):
- `desk_window_service.py`: a `RETIRED_WINDOWS: dict[str, str]` beside
  `RETIRED_APPS` (line 115), with `"surface-concierge": "Runs on is the
  Engines wing of Settings (PHILO-17)"`. `open` refuses it with
  `window_retired` (the branch at lines 313-320 reads both tables). A saved
  row still closes.
- `hubWindows.ts`: `RETIRED_PREFIX` (line 114) becomes `isRetired(id)`:
  the `zone:` prefix or an id the registry lists as retired. The registry
  payload gains `retired` (additive; `registry()` line 143). The retire path
  at 475-476 is unchanged: the saved `surface-concierge` row is closed once
  with its revision and never opens here.
- No schema change. No migration.

Parked: the `open-concierge` application entry stays in `applications.ts`
with `dock: undefined`, no `href` in Go, and a `parked: "settings:models"`
mark (so `test_every_window_id_in_applications_ts_is_known`,
`tests/unit/test_desk_window_service.py:291`, still passes and the sweep
skips it). `/models` (`routes.tsx`) routes to `/settings?section=models`.

Words: the wing is "Engines". The plate's verb stays "Choose engines". The
window is "Settings". (Final words: `DESIGN-words.md`.)

### 4.2 W1: a meeting opens in the Meetings window (list ▸ detail, Back)

**OWNER CALL 1.** The owner ruled on 2026-10-10 "A meeting opens in one
window", and the code took it as "its own window" (`Pullout.tsx:63`,
`citations.tsx:47`). The recon now asks for the meeting inside Meetings.
- **Recommended, A:** the Meetings window shows the meeting; one window;
  Back. People already works this way (shot 036) and the phone's Back
  (§4.6) falls out of it.
- **B:** keep the meeting's own window, but open it beside the list (W3)
  and never over it; the list's row stays selected. Two windows per
  meeting read; the phone keeps a pane per meeting.

Design for A:
- `compositorSlice.ts:374-385`: the redirect goes. `openSurfaceWindow
  ("review-meetings", "meeting:<id>[?view=…]")` opens or fronts
  `surface-meetings` with `scope = "meeting:<id>"`; the view/segment request
  rides as today (`meetingWindowRef`, `objectWindows.ts:45-69`, keeps its
  request map; only the returned ref changes to the Meetings scope).
- `citations.tsx:50-54` and `openPrimitive` for a `meeting:` ref call
  `openSurface("review-meetings", ref)`.
- The Meetings application (`web/src/pages/cores/history/index.ts`) renders
  `MeetingDetail` (`history/MeetingDetail.tsx`) when scoped, with Back
  (clears the scope: the window's `object` adapter sends `object_ref: ""`,
  `hubWindows.ts:229-233, 818-823`), and the list when not. The meeting's
  wings (OUTCOMES · REVIEW · ARTIFACTS) and foot publish into the frame as
  they do in the hosted pullout today (`Pullout.tsx:63-70`): the host moves,
  the face does not.
- The window's title is the meeting's name while scoped (`useWindowTitle`,
  as Settings does at `SettingsCore.tsx:2449`).
- Rows: a saved `pullout:meeting:<id>` row migrates once to
  `surface-meetings` with `object_ref = "meeting:<id>"`, the mirror of
  `migratedMeeting` (`hubWindows.ts:99-111`): the row is retired at its
  revision and the Meetings window opens on the meeting. The old migration
  code is parked (not deleted) under a `MEETING_IN_OWN_WINDOW = false`
  flag, so a revert is one line.
- The size: Meetings keeps its rect; the detail needs what the list needs
  (`minW: 640`, `applications.ts:126`); `PULLOUT_SIZE.meeting` is parked.
- The Room (a project) already opens as one drawer per project with its
  postures inside (`DrawerWindow.tsx`); nothing to do. A person stays as it
  is (shot 036).

### 4.3 W3: cascade from the front window

`windowGeometry.ts:48-128`, `placeWindow` gains a `front?: PanelRect`
argument (the front window's rect, `DeskWindow.tsx:400-416` already sorts
`others` back to front; the last is the front). The seed becomes
`{x: front.x + 24, y: front.y + 24}` when a front window exists and the
seat is inside the band and right of `iconColumnRight()`; the distance term
of the score (line 92) measures from THAT seed, so the scan keeps the
staircase and still moves off a hidden title bar. With no front window the
home seat stays. The saturated branch (lines 102-117) is unchanged. A saved
rect still wins (line 395-401). Chair windows keep their CSS seats
(line 449-456).

Pure function, pinned by `web/src/desk/components/window/__tests__/cascade.a1.test.ts`
(extend) and `compositor/__tests__/geometry.test.ts`.

### 4.4 W4: sizes

A size table in `pullouts/size.ts` (one place; it exists):

| Window | Opens at | Grows |
|---|---|---|
| Thought / note (sticky) | 520×360, `fitContent` | with the text, to 820×640 |
| Needs you, Brief, The week (Chair) | CSS seat width; height `fitContent` with `min-height` = head + one row | with rows |
| Meetings | 720×600 | saved rect |
| Person | 640×560 | saved rect |
| Room (drawer) | 760×480 | saved rect |
| Settings | 640×600 | saved rect |

Mechanism: `ThoughtWorkspaceWindow.tsx:634-635` reads the table;
`chair.css:132-182` height rules become `min-height` with the window
`fitContent` (`DeskWindow.tsx:427` already skips the max-height inflation
for `fitContent`). The empty states ("Nothing needs you", "Nothing open",
"No updates yet") are then one line tall by construction. The cap of 78 %
of the band (`DeskWindow.tsx:432-434`) stays.

### 4.5 W5: one notice, in the menu bar

`AmbientLayer.tsx:238-247`'s aftercare card is parked. The signal it reads
(`signal.title`, `proposalTotal`) goes to the menu bar's attention Button
(`DeskMenuBar.tsx`, the bell): for six seconds the bell reads
"Ledger standup · ready"; a press opens the meeting (`openSurface
("review-meetings", "meeting:<id>?view=review")`); then the bell is its
count again. One place, one line, never over a window. What the bell counts
is the attention cluster's; this slice only gives it the transient line.

### 4.6 The phone

P1 **One tap opens.** `Screen.tsx:190-191`: at `compact`, `onSelect` opens
(`openTarget(o.target)`); `onOpen` stays for Enter. `DeskIcon` is unchanged
(a desk icon still selects on one click at 1440).

P2 **Go is home.** `Screen.tsx:123, 142`: at `compact` the Screen draws
`<GoHome />` in place of the grid: `phoneGo`'s rows
(`DeskMenuBar.tsx:80-107`, the same pure function) as a list of library
Buttons, one per row, 44 px targets, the separators as gaps, New ▸ last.
The grid branch is parked behind `PHONE_ICON_GRID = false`. The Go menu in
the bar stays and lists the same rows: Go is "home" from any pane.

P3 **Back, not a switcher.**
- The sheet's head (`DeskWindow.tsx:1238-1250`): at `compact` the left
  gadget is `‹ Back` (a library Button). Back does the first of: clear the
  window's scope (a meeting → the Meetings list, §4.2; a person → the
  roster, `PeopleCore.tsx:447`); else close the pane. The pane under it is
  the next in the ring by open order (`phoneRing.ts:30-45`, already
  ordered by `openedSeq`); with none, home (P2). The stack is the open
  order: no new history store.
- `DeskChrome.tsx:94-96`: the title at 393 is the pane's name, plain;
  `ScreenSwitcher` is parked (`components/window/_parked/`). The ring's
  swipe (`usePhoneSwipe`) moves to `DeskChrome` and stays: a power move,
  not the door.
- ⌃W at 393 is Back.

P4 **Footers: one primary, the rest under More.** `SurfaceFooter.tsx`: at
`compact`, the verbs slot shows the first `variant="primary"` Button and a
`More ▸` menu Button (the library menu, `DeskMenu.tsx`) with the rest in
order. Faces change nothing: they pass the same `verbs`. The meeting foot
(`history/MeetingReview.tsx`, `MeetingRecord.tsx`) reads Send · More ▸.

P5 **The dock at 393 is four.** `applications.ts` `dock` entries gain
`phone?: number` (order on the phone); `Dock.tsx` at `compact` draws the
tiles with `phone` set, in that order: Today (`intelligence:desk`),
Capture (`chair:capture`, a Chair tile), Meetings, People; no tail (Hide
the menus, Places, Overview, Reset), no pager (`Dock.tsx:683-697` parked at
393). The 1440 dock is the words cluster's.

### 4.7 Data and API

Additive only:
- `registry.retired` in `GET /api/desk/windows` (§4.1).
- `window_retired` refusal for a static id (`desk_window_service.py`,
  the branch at 313-320).
- No table, no column, no migration. `object_ref` on `surface-meetings`
  rows is already allowed (`desk_window_service.py:330`).

### 4.8 Parked

| What | Where it goes |
|---|---|
| The Runs on window (`open-concierge` as a window) | `applications.ts` entry marked `parked`; the id stays in `STATIC_WINDOWS` as retired |
| `migratedMeeting` and the meeting-in-own-window redirect | behind `MEETING_IN_OWN_WINDOW = false` in `objectWindows.ts` |
| `PULLOUT_SIZE.meeting` | `pullouts/size.ts`, commented with the flag |
| The aftercare card | `web/src/components/_parked/AmbientAftercare.tsx` |
| `ScreenSwitcher` | `web/src/desk/components/window/_parked/ScreenSwitcher.tsx` |
| The 393 icon grid | `Screen.tsx` behind `PHONE_ICON_GRID = false` |
| The dock pager at 393 | `Dock.tsx` behind the same `compact` branch, not drawn |

### 4.9 Product words

Short, as he would say them: **Back**, **More**, **Engines**, **Settings**,
**Home** (the phone's Go list has no title; the bar reads "HoldSpeak"),
"Nothing needs you", "Ledger standup · ready". No "switcher", no "ring", no
"pane" on any face.

### 4.10 Owner calls

- **OWNER CALL 1** (§4.2): a meeting inside the Meetings window (A,
  recommended) or its own window opened beside the list (B).
- **OWNER CALL 2** (§4.6 P3): Back at 393 closes the pane (recommended: a
  pane is cheap, the hub reopens it where it was; nothing piles up) or
  iconifies it (the ring keeps every pane he opened; the dock shows them).

## 5. The slices

Each is one PR on the fast cycle (`scripts/quick_check.sh`, merge, the
watcher runs the suite). Order matters only where said.

### S1 The ghost dies: Runs on is the Engines wing (first to build)

- Files: `SettingsCore.tsx` (the `models` case, the wings, the title),
  `settingsPrefs.tsx` (the plate verb switches the wing), `applications.ts`
  (aliases, the parked entry), `routes.tsx` (`/models`),
  `useConciergeController.ts:784`, `RunsOnCore.tsx` (list form under
  900 px), `desk_window_service.py` (`RETIRED_WINDOWS`, `registry()`),
  `hubWindows.ts` (`isRetired`).
- Tests: T1 `tests/unit/test_desk_window_service.py` (a retired static id
  is refused on open and still closes; the registry lists it),
  `tests/unit/test_desk_runs_on.py` (unchanged, must stay green);
  T2 `web/src/desk/__tests__/settings.app.test.tsx` (press Choose engines →
  the Engines wing shows the jobs, `windowsById` has no `surface-concierge`;
  close Settings → nothing reopens after a store change), `hubWindows.test.ts`
  (a saved `surface-concierge` row is retired once); T3 the sweep drops the
  Runs on case by itself and sweeps Settings' new wing at 1440 and 393.
- Risk: the twelve doors' scopes; `RunsOnCore` at 560 px (its list form is
  the phone's today and is swept at 393, so it exists).
- Judge LIVE: HoldSpeak ▸ Settings ▸ Choose engines. One window. Close by
  gadget, by ⌃W, reload. It stays closed. MORE SETTINGS is reachable.

### S2 Cascade from the front window; sizes to content

- Files: `windowGeometry.ts` (`placeWindow(front)`), `DeskWindow.tsx:419-456`,
  `pullouts/size.ts`, `ThoughtWorkspaceWindow.tsx:634-635`,
  `chair.css:132-182`, `DrawerWindow.tsx:225-226`.
- Tests: T2 `cascade.a1.test.ts` (five opens step 24/24 from the front;
  the icon column stays clear; a saved rect wins), `geometry.test.ts`; a
  thought test in `thoughtDoorAndReceipt.test.tsx` (opens at the sticky size); T3 the
  sweep's fit, overlap and clipped fences at 1440 (the empty Needs you, the
  Room, the thought).
- Risk: the sweep's `KNOWN_REDS` for windows that depended on the corner
  seat; chair seats at 1440 (`clampIntoBand` path unchanged).
- Judge LIVE: open Today, Meetings, People, Settings, Ask AI: a staircase.
  Write a thought: a sticky. Needs you empty: one line.

### S3 A meeting opens in the Meetings window (after OWNER CALL 1)

- Files: `compositorSlice.ts:374-385`, `citations.tsx:45-54`, `shell.ts:136`,
  `objectWindows.ts` (the flag, `meetingWindowRef`), `hubWindows.ts`
  (the mirror migration), `history/index.ts` + `MeetingDetail.tsx` (Back),
  `Pullout.tsx:63-70` (hosted meeting parked), `pullouts/size.ts`.
- Tests: T1 `tests/unit/test_desk_windows_routes.py` (a `surface-meetings`
  row opens with `object_ref: "meeting:<id>"`, then `""` on Back; one row
  throughout); T2 `meetings.app.test.tsx` (a recorded hub: press the row →
  the detail in the same window, the title, Back → the list; a saved
  `pullout:meeting:` row migrates once); T3 the sweep's Meetings case gains
  the scoped state at 1440 and 393.
- Risk: the 2026-10-10 ruling; every `meeting:` door (Today, Needs you, the
  bell, ⌘K, Follow-through's Open transcript) goes through
  `openSourceRef`/`openPrimitive`, which is why those two are the change.
- Judge LIVE: Meetings ▸ Ledger standup ▸ Back ▸ reload on the meeting.

### S4 One notice in the menu bar

- Files: `AmbientLayer.tsx` (park the card), `DeskMenuBar.tsx` (the bell's
  six-second line), `AppShell.tsx:24`.
- Tests: T2 `bell.app.test.tsx` (a `meeting_ready` signal → the bell reads
  the title for the window of time, then the count; a press opens the
  meeting's review); T3 the sweep's overlap fence sees no card over any
  window.
- Risk: the Chair's `data-aftercare-slot` (`ChairHome.tsx:1463`) loses its
  card; the seam with the attention cluster's bell content.
- Judge LIVE: import a meeting; the bell says ready; no card anywhere.

### S5 Phone: one tap opens; Go is home

- Files: `Screen.tsx` (compact: open on select; `GoHome`), a new
  `web/src/desk/screen/GoHome.tsx` (reads `phoneGo`), `screen.css`.
- Tests: T2 `web/src/desk/__tests__/phoneDoors.test.tsx` (extend) at 393
  (matchMedia compact: the home list's rows are `phoneGo`'s; a tap on
  Meetings opens `surface-meetings`; the grid is not drawn); T3 the sweep's
  `desk` case at 393 (44 px targets, fit, no overlap).
- Risk: none on the hub; the sweep's 393 `KNOWN_REDS` for the bar.
- Judge LIVE on his phone: open the desk; tap Meetings; it opens.

### S6 Phone: Back, footers, the four-tile dock

- Files: `DeskWindow.tsx:1238-1250` (Back gadget at compact),
  `DeskChrome.tsx:94-96`, `phoneRing.ts` (previous pane), `SurfaceFooter.tsx`
  (More ▸), `Dock.tsx` + `applications.ts` (`phone` order), `dock.css`.
- Tests: T2 `dock.app.test.tsx` (393: four tiles, no pager), `phoneDoors.test.tsx`
  (Meetings → meeting → Back → list → Back → home; the foot shows one
  primary and More); T4 one browser case in `tests/e2e/test_windows_glass.py`
  for the touch swipe staying alive after the switcher is parked (touch is
  T4 by the doctrine); T3 the sweep at 393 for every window's foot.
- Risk: faces whose only verb is not `primary` (More alone): the first verb
  is then the primary.
- Judge LIVE on his phone: Home ▸ Meetings ▸ Ledger standup ▸ Back ▸ Back.
  The foot: Send · More.

## 6. What not to do

- **No window manager.** No tiling modes, workspaces, groups or "window
  mode per app". The kernel works (the recon's keep list); the fault is
  what opens, where, and how many. Three small rules fix it.
- **No navigation router on the phone.** No history store, no routes per
  pane, nothing on the hub. The open order IS the stack
  (`openedSeq`), and Back is close. A "real" stack would be a second truth
  beside the hub's rows (COMPOSITOR.md L1).
- **No new window family for "detail".** A scoped application window is the
  detail; the row's `object_ref` exists. A `detail:` family would double
  every opener.
- **No rebuild of Runs on.** It is hosted, not redesigned. Its words and its
  diagram are the verbs cluster's.
- **No preference to keep the Runs on window.** Two homes for one pane is
  the bug again.
- **No responsive framework.** `compact` is one media query and it is
  enough; the phone gets five rules, not a second app.
- **No schema change.** The retired id and the mirror migration are the
  same mechanisms the desk already runs for `zone:` and for the meeting
  window.
