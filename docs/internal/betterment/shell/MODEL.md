# The desk shell: the code map

Read from `main` (`b746549b8`). Paths are under `web/src/desk/` unless they say
otherwise. This is the map `DESIGN.md` builds on: what the shell is in data,
which doors and verbs are dead or doubled, and the constraints a build must
keep.

## 1. What the shell is in data

The shell has two sources of truth and eight faces that project them.

**Source 1: the application manifest** (`applications.ts:57-480`). 24 rows.
Each row may carry a `dock` place, a `go` row (`app` or `tools` section), a
`mark` place (the HoldSpeak menu), a `shortcut`, a `group` (`app` or `tool`,
which puts it in Search) and `parked`. Its header says: "Window hosts, the
Dock, Go commands, keyboard bindings, aliases, and the mark menu are
projections of this table; they must not grow parallel application lists"
(`applications.ts:4-10`).

**Source 2: the verb registry** (`verbRegistry.ts`, 1,051 lines). Each `Verb`
has an id, a label, an optional `menu` (desk, object, go, window), a `key`, a
`ghost(ctx)` that returns `null` (runnable) or a reason string, and `run`
(`verbRegistry.ts:63-98`). One binder runs keys from it (`keymap.ts`).

**The faces, and where each gets its rows:**

| Face | Built from | Rows today |
|---|---|---|
| Go, desktop | manifest `go` (`DeskMenuBar.tsx:115-145`) | 6: Speak, Meetings, Today, Ask AI, People, Conductor. Projects ▸ when projects exist. Tools ▸ only when a row has `go.section: "tools"`; none has (`grep 'section: "tools"' applications.ts` finds nothing) |
| Go, phone, and the phone home | **hand lists** `PHONE_GO_CHAIR`, `PHONE_GO_PLACES`, `PHONE_NEW` (`DeskMenuBar.tsx:58-77`), drawn by `phoneGo` and by `screen/GoHome.tsx` | Needs you, Brief, The week, Capture; Meetings, Ask AI, People, Conductor; Projects; Drawers; New (4) |
| Dock, desktop | manifest `dock` (`applications.ts:494-497`, `Dock.tsx:425-497`) | Today, Speak, Meetings, People, Conductor; then the record orb (`DeskApp.tsx:305`); then Overview and Reset layout buttons when a window is open (`Dock.tsx:600-620`) |
| Dock, phone | **a hand list** in `Dock.tsx:499-534` | Today, Capture, Meetings, People, and the orb. Labels hidden by `dock.css:590-595` ("eleven doors fit the screen", now four) |
| HoldSpeak menu | `MARK_VERBS = ["desk.refresh"]` plus manifest `mark` (`DeskChrome.tsx:38`, `applications.ts:505-512`) | Refresh from hub, Settings, Engines, Accounts, Setup. Engines and Accounts are `parked` rows that still have a `mark` (`applications.ts:457-478`) |
| Desk menu | verbs with `menu: "desk"` | nine `New …` rows and Hide the menus (`verbRegistry.ts:165-322`) |
| Object menu, menu bar | verbs with `menu: "object"`, **not filtered by kind** (`DeskMenuBar.tsx:225-280`) | 13 rows on any object |
| Object menu, right-click and window menu | `objectMenuEntries`, **filtered by kind** (`objectMenu.ts:12-72`) | 10 rows on a note |
| Window menu | verbs with `menu: "window"`, plus Window ▸ Desk (the Chair windows, `chair/chairWindows.ts:36-41`), plus the open windows | 14 verbs, then Desk ▸, then windows |
| Search (⌘K) | `DeskToolShelf.tsx` (1,081 lines): `DESK_TOOLS` = manifest rows with `group` app or tool (`tools.ts:4-10`), the drawer launchers (`launcherRegistry.ts`), objects, settings, memory, the week's verbs | Sections in fixed order PROJECTS, PEOPLE, OBJECTS, MEETINGS, VERBS, PROGRAMS, SETTINGS, MEMORY (`DeskToolShelf.tsx:50-59`) |
| The floor | `screen/compose.ts` `composeScreen` | every project drawer, the People drawer, the Conductor, Needs you, Archive, root directories, and every **loose** object (below) |
| Keyboard sheet | verbs with a key, grouped by scope (`ShortcutSheet.tsx:13-17`) | Applications, Windows (holds `floor` too), Desk |

So the manifest rule is broken in three places: the phone Go, the phone home
and the phone Dock are hand lists, not projections.

## 2. Where each application can be reached

| Manifest row (`applications.ts`) | Dock | Go | Search | HoldSpeak | Floor icon | Key |
|---|---|---|---|---|---|---|
| Today `open-intelligence` (:74) | yes | yes | **no** (no `group`) | – | – | – |
| Speak `dictate` (:84) | yes | yes | yes | – | – | ⌃1 |
| Ask AI `ask` (:105) | – | yes | yes | – | – | ⌘I |
| Meetings `review-meetings` (:115) | yes | yes | yes | – | drawer "Meetings" is a **different thing** (a seed directory) | ⌃2 |
| Conductor `open-conductor` (:142) | yes | yes | yes | – | yes | ⌃3 |
| People `open-people` (:421) | yes | yes | **no** (no `group`) | – | yes | – |
| Settings `configure-settings` (:176) | – | – | yes | yes | – | ⌃4 |
| Setup `configure-setup` (:248) | – | – | yes | yes | – | – |
| Engines, Accounts (:357, :457, :468; parked) | – | – | yes | yes | – | – |
| Change places (:58) | – | – | yes | – | – | ⌘⇧P |
| Rhythm (:221), Context (:269), Workbenches (:286), Activity (:319), Memory (:337), Processes (:387), Commands (:404) | – | – | yes | – | – | – |
| Components (:303), Calendar snapshot (:440) | – | – | **no** | – | – | – |
| Live meeting (:205), New Project (:370), Agents `inspect-personas-and-coders` (:159) | – | – | – | – | – | – |
| (launchers) Delivery, Terminals (`DeliveryBoard.tsx:390`, `SessionPullout.tsx:266`) | – | – | yes, as `DRAWER` | – | – | – |

Live meeting and New Project are opened by verbs (record, New Project), which
is right. The old Agents row is parked in all but name (INVENTORY §3).

## 3. Dead, ghosted and doubled verbs

- **Ghost, never hide, is the menu doctrine.** `DeskMenuBar.tsx:3-4` ("a verb
  that cannot run now is GHOSTED with its reason, never hidden") and
  `components/DeskMenu.tsx:137-138` ("ghosting over hiding"). UX-CANON A.11
  says the opposite: "A verb that does nothing is a lie. Withhold it". The
  right-click menu already withholds by kind (`objectMenu.ts:12-14`); the
  menu bar does not.
- **A ghost looks live.** The ghost style is a 2 px paper stipple at 0.6
  opacity over ink of the same colour (`components/chrome-menus.css:205-219`).
  In the shots the ghosted rows cannot be told from live ones
  (`31-object-menu-note-1440.png`).
- **A ghosted key does nothing, silently** (`keymap.ts:125`).
- **Doubled create verbs:** New Note and Write a thought (one record),
  New Knowledge (a drawer), New Thread (Ask), New Agent, New Workflow and
  New Workbench (three ways to automate) (`verbRegistry.ts:165-271`).
- **Doubled window verbs:** Cascade (`window.cascade`) and Reset layout
  (`desk.reset-layout`, also a Dock button); Overview is a menu row, a key
  and a Dock button.
- **Dead rows in Search:** Terminals (`SessionPullout.tsx:266-276` toggles a
  pane list; in the walk Enter opened nothing) and object verbs with a ghost
  reason (`Hand to coder · Select an object`).
- **Parked rows still on a face:** Engines and Accounts (`mark: 2`, `mark: 3`
  on parked rows, `applications.ts:465`, `:476`); Hide the menus
  (`verbRegistry.ts:309-322`, also a button in Change places).
- **Two homes for the wallpaper:** `pages/cores/ChangePlacesCore.tsx` (52
  lines, the window) and `pages/cores/settingsWallpaper.tsx` (132 lines, the
  Settings section). Both list the same registry
  (`gl/atmosphereRegistry.ts`, 12 entries, default `quiet-desk` at :173).

## 4. Windows

- **Placement** (`components/window/windowGeometry.ts:48-128`): a new window
  is seeded at its home, or 24 px off the front window, then a scan moves it
  off other title bars and clear of the icon columns. This is good.
- **But a remembered rect wins** (`components/DeskWindow.tsx:350-353`, "the
  arrangement is sacred"). A window that was ever placed comes back to that
  place, over whatever is open now. That is why five keys made a pile.
- **Chair windows skip the scan** (`DeskWindow.tsx:451-456`): Needs you opens
  at its CSS seat (14,42), over the drawer column.
- **Sizes are constants per app**: `defaultW` / `defaultH` in the manifest
  (Meetings 720x600, Settings 640x600, Rhythm `defaultH: 520`) or the CSS
  default (640x633 for most tools). A content-sized mode already exists,
  `fitContent` (`DeskWindow.tsx:140-143`, `:510-554`), used by pullouts,
  thoughts and zones, but not by application windows
  (`components/SurfaceWindows.tsx`).
- **Windows are hub-owned** (Phase 16 B): `/api/desk/windows` and the six
  `desk_window.*` MCP tools (open, close, raise, arrange, seat, list), all
  classed WORK (`holdspeak/mcp/tool_authority.py:290-295`). An
  agent can already open and arrange his windows.
- **Wings** sit in the title bar in Meetings and Settings (`has-wings`,
  `DeskWindow.tsx:1246`), in the body as a segment in Today, and in the body
  as tabs in a person window. Three grammars for one thing.
- **Phone**: every window is a full-screen sheet with `‹ Back`
  (`DeskWindow.tsx:1265`). It works.

## 5. The floor

- `composeScreen` (`screen/compose.ts:215-345`) draws, in order: the project
  drawers, the People drawer, the Conductor, Needs you, Archive, the root
  directories, then **loose** objects, then live agents.
- **Loose** means "a meeting, note, decision, artifact, repository or thread
  with content, that no project and no directory holds", plus **every person
  no project holds** (`compose.ts:79`, `:303-340`). So every import, every
  person added, every kept Ask answer and every thread with a turn becomes an
  icon by itself.
- `layoutScreen` (`screen/layout.ts`, 74 lines) flows icons in columns, so a
  new project drawer pushes People and the Conductor to the next column.
- **The seed** (`holdspeak/seeds/fresh-desk.yaml`): six directories (Inbox,
  Personal, Work, Meetings, Decisions, Reference), Start here (filed in
  Inbox), Weekly update (a `prompt`-tagged note, loose on the floor) and four
  `mode` recipes (Desk, Chase, Draft, Plan) that Search lists as `AGENT`.
- **The phone has no floor**: at 393 the Screen draws `GoHome`, the Go list
  (`screen/Screen.tsx:154`). Loose objects are reached by Search or drawers.

## 6. Wallpaper

- 12 atmospheres (`gl/atmosphereRegistry.ts:19-150`): Quiet Desk (default,
  `:173`), Rainy City, Lantern Garden, After-Hours Radio, Midnight Archive,
  Night Train, Deep-Sea Station, Storm Greenhouse, Last Laundromat, and the
  three orbits. 4.3 MB of scene code and textures in `gl/`.
- The choice is per browser (`gl/atmospherePreference.ts:27`, localStorage).
- The runtime already pauses on a hidden tab and under reduced motion
  (`gl/atmosphereRuntime.ts:97-150`).
- Scenes react to real desk events: the mic level, recording, a new arrival
  (`gl/atmosphereActivity.ts`). This is the one way a scene tells something
  true.
- No MCP tool sets the wallpaper (`settings.update` may; not checked).

## 7. Builder tools

Activity, Processes, Components, Context and Calendar snapshot are kernel and
design views. Rhythm is a settings face for the heartbeat (its loops fold into
Automations, `../PLAN.md` §2). Delivery and Terminals are agent tools that
`../agents/DESIGN.md` puts behind RAW. There is no global RAW switch today:
"RAW" is a per-window disclosure (`surface/Surface.tsx:521`).

## 8. Constraints for a build

- Menus must derive from the registry; a guard census enforces it
  (`DeskMenuBar.tsx:2-3`). Keep it: the fix is to make the phone faces
  projections too.
- The manifest feeds the generic desk sweep (`tests/e2e/test_desk_sweep.py`:
  every app in `applications.ts`, every wing, the palette, at 1440 and 393).
  A row that gains a `go` place is swept for free.
- Hub-owned windows: one hub is one desk; a placement change must hold for
  windows the hub or an agent opens (`desk_window.open`).
- 393 stacks under the `surface` container query; the 44 px hit rule applies
  to Dock tiles and menu rows (UX-CANON C, D).
- Existing tests to extend: `__tests__/menus.app.test.tsx`,
  `__tests__/objectMenu.test.ts`, `__tests__/dock.app.test.tsx`,
  `__tests__/palette.app.test.tsx`, `__tests__/keymap.test.ts`,
  `components/window/__tests__/cascade.a1.test.ts`,
  `screen/__tests__/Screen.test.tsx`, `gl/__tests__/atmospherePreference.test.tsx`,
  `tests/unit/test_desk_seed.py`.

## 9. MCP parity

Shell verbs an agent can do today: open, close, raise, arrange, seat and list
windows (`holdspeak/mcp/families/desk_windows.py`), create, update and delete
desk objects (`desk.*`), file into a drawer (`zone.file`, `zone.unfile`).
Missing: the wallpaper (a settings field at most), "keep on the desk"
(it becomes `zone.file` into the desk, see the design).
