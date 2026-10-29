# Desk object model

This page is for contributors.
It connects object declarations to active openers, verbs, keys, and shared window behavior.
The source is the final authority. Each section names the file that owns the rule.
For the app structure, see [Desk architecture](DESK_ARCHITECTURE.md).

## Object kinds

`PrimitiveKind` in `web/src/lib/primitives.ts` lists the declared shared primitive kinds.
Other service-backed records can have their own opener contract.
For example, `program:<id>` opens a Program through `openObject.ts` and the Programs host.
The `PRIMITIVES` table gives each kind its label, sync class, object verbs, and opening surface.
The descriptor declares static capabilities.
The authorable column records that metadata flag, not every current creation flow.
For example, New Project has an active setup Door although its descriptor flag is false.
The table uses descriptor labels; a host can use another current label, such as Drawer for a `kb`.
The active opener, selected object, and runtime state determine how the current Desk exposes them.
A descriptor alone does not establish a separate app or an available control.

| Kind | Label | Sync class | Descriptor authorable | Object verbs | Opens as |
| --- | --- | --- | :-: | --- | --- |
| `meeting` | Meeting | content | no | ask, send, hand | Meetings host |
| `artifact` | Artifact | content | no | ask, send, hand | pullout |
| `note` | Note | content | yes | ask, edit, rename, duplicate, delete, hand | Note workspace |
| `decision` | Decision | content | yes | duplicate, delete, send, hand | pullout |
| `thread` | Thread | content | yes | delete | current Ask/conversation host |
| `directory` | Zone (drawer) | organization | yes | rename, delete | Directory contents window |
| `kb` | Knowledge | organization | yes | ask, edit, rename, duplicate, delete | pullout |
| `project` | Project | organization | no | send, rename, archive | Project Room (`open-project-memory`) |
| `repository` | Repository | organization | yes | none | repository window |
| `recipe` | Mode | capability | yes | ask, edit, rename, duplicate, delete | pullout |
| `chain` | Sequence | capability | yes | delete | pullout |
| `workflow` | Workflow | capability | yes | ask, edit, rename, duplicate, delete | pullout |
| `workbench` | Automation | capability | yes | duplicate | Automation host, with legacy queue view for an old queue |
| `coder` | Agent | presence | no | none | pullout |
| `roadmap` | Roadmap | organization | no | none | roadmap window |
| `intelligence` | Intelligence | local | no | none | pullout |
| `people` | People | local | no | none | People window |
| `game`, `layout`, `story` | Game, Layout, Story | local | no | none | none |

Directories appear as drawer icons on the current Desk. Root folders open their
stored contents; children appear inside their parent. Filed work stays inside
its drawer. The same root folders are available under Drawers in phone Go.
Directory references use `zone:<id>`; existing member aliases and bare IDs
resolve through the shared object lookup. Missing stored members show an
unavailable row. Missing parents and filing cycles retain a reachable root.
The previous spatial Floor and its list projection remain parked.

An ID resolves as a bare ID or as a qualified `kind:id` reference.

## Floor placement

The previous spatial Floor is parked.
The active Screen and drawers present objects through `web/src/desk/screen/` and the current drawer hosts.
Legacy placement helpers remain in `world.ts` for callers that use them.
They are not a promise that the active Screen exposes free placement for every object.

Icon identity and state come from the shared sprite and component contracts.
A badge must name a real field or stored state.
Object placement, filing, and a registered window's geometry are separate operations.

## Verbs

`VERBS` in `web/src/desk/verbRegistry.ts` is the one verb list.
The menus, the command palette, context menus, window head menus, and dock menus all derive from it.
Each verb has an ID, a label, a menu, an optional key, a `ghost` check, and a `run` function.
A `ghost` check returns the reason a verb is unavailable.
The menu hides a verb when it cannot run for the current selection.

| Menu | Verbs |
| --- | --- |
| **Desk** | **New Note**, **New Decision**, **New Automation**, **New Project**, **New Meeting**, **New Person**, and **New Drawer**. **Reset layout**, **Reset to seed…** and **Refresh from hub** are in Search. |
| **Object** | **Open**, **Get Info**, **Ask about this**, **Write update**, **Hand to agent**, **Edit**, **Rename**, **Duplicate**, **Keep on desk**, **Remove from desk**, **Delete**, **Archive**. The selected object determines which verbs appear. |
| **Go** | Apps from `DESK_APPLICATIONS`, grouped by their `go` entries, plus projects and drawers. An open window gets focus instead of a second copy. |
| **Window** | **Close**, **Minimize**, **Next window**, **Tile left**, **Tile right**, **Zoom**, **To back**, **Overview**, **Stage**, **Arrange all**, **Gather**, **Back**, and the current-work windows |
| System | **Search**, **Keyboard shortcuts** |

**Reset to seed…** opens Settings. You confirm the reset there. The menu never resets by itself.
The compatibility New Thread verb opens Ask but is hidden from menus and Search.
Start a conversation from the first row of Ask's **Recent** rail, or press `⌘N` while Ask has focus.
The separate Thread window is parked.

### Keys

`web/src/desk/keymap.ts` is the one key handler.
A verb `key` field is the binding.
`⌘` means Meta on a Mac and Ctrl elsewhere. A chord that holds both is refused.
A key handler ignores repeats and input method composition.
The chords `⌃W`, `⌃M`, `⌃N`, `⌃B`, and `⌃T` do nothing inside a text field.
The desk runs in a browser tab. The browser keeps `⌘W`, `⌘N`, `⌘⇧N`, `⌘M`, and `⌘1` to `⌘4`, so the menus show `⌃` keys.
The old `⌘` keys stay bound. They work where the browser sends them to the page.

| Key | Verb |
| --- | --- |
| `⌃N` | **New Note** |
| `⌃⇧N` | **New Decision** |
| `⌃T` | **New Note** |
| `⌘⇧E` | **Overview** |
| `F2` | **Rename** |
| `Delete` | **Delete** (Backspace on a Mac) |
| `⌘I` | **Ask** |
| `⌃1` to `⌃5` | Today, Meetings, People, Agents, Speak |
| `⌃7` | **Programs** |
| `⌃,` | **Settings** |
| `⌃W` | **Close** |
| `⌃M` | **Minimize** |
| `⌘⇧Z` | **Zoom** |
| ``⌘⇧` `` | **To back** |
| `⌘⌥←` and `⌘⌥→` | **Tile left** and **Tile right** |
| `⌘⏎` | **Stage** |
| ``⌘` `` | **Next window** |
| ``⌃⇧` `` | Reverse cycle compatibility binding |
| `⌘K` | **Search** |
| `⌘/` | **Keyboard shortcuts** |

## Selection

`selectedIds` holds the selection. `toggleSelected`, `setSelected`, and `clearSelection` change it.
An object verb works only when exactly one object is selected.
With more than one selected object, an object verb is unavailable. **Ask** still uses the whole selection.

| Gesture | Result |
| --- | --- |
| Click | Select the object. |
| Double click | Open the object. A Zone opens its window. |
| Tap (touch or pen) | Open the object. |
| Context menu | Show the object menu. |
| Drag | Move the object. A valid target lights up. |

## Drag and drop

`DROP_MATRIX` in `web/src/desk/dropMatrix.ts` lists the valid drops.
Any pair not in the table does nothing.

| Target | Accepted kinds | Label | Result |
| --- | --- | --- | --- |
| Mode, Sequence, Workflow | Note, Knowledge, Meeting, Artifact | **Hold as source** | The record becomes held context. Nothing runs. |
| Knowledge | Note, Meeting, Artifact, Mode | **Add to Knowledge** | The record joins the Knowledge. You can undo it. |

The old Floor file-drop host is parked in the active Desk composition.
The matrix describes supported internal object pairs, not a general file-ingestion promise.
Meetings import and calendar snapshot review have their own active controls and API routes.
Read [Meeting mode](MEETING_MODE_GUIDE.md) for supported import steps.

## Window geometry

`web/src/desk/components/window/windowGeometry.ts` holds the geometry functions.
`DESK_WINDOW` comes from `web/design-tokens.json` through `web/src/lib/tokens.gen.ts`.

The work area comes from shell CSS properties and the measured Dock height.
Token defaults come from `web/design-tokens.json` and `web/src/lib/tokens.gen.ts`.
Read the geometry module for placement steps, title-occlusion scoring, and minimum-size defaults.
Each app can declare its own window constraints.

### Placement

`placeWindow` starts near the front window or the app's default position.
It fits the candidate within the usable band and avoids the icon columns when the window fits.
Its scan gives title-bar overlap a higher cost than body overlap.
A saturated layout uses the bounded cascade logic in the geometry module.

### Snap and resize

`snapForPointer` snaps a window when you release it near an edge or corner.
Near the left or right edge, the window takes half the work area.
In a corner, it takes a quarter.
A resize works from the right, bottom, left, bottom-left, and bottom-right handles.
The result stays inside the work area and above the minimum size.

### Overview

**Overview** lays out the open windows in a grid.
The grid has `ceil(sqrt(count))` columns.
It centers an incomplete last row.
Press `Escape` to leave it.

## Window lifecycle

Each window has one ID, one rect, one place in the stacking order, and an iconified or zoomed flag.
Opening a window puts it in front. Focusing a window moves it to the front.
Closing a window removes its ID.
The front registered window is derived from the greatest shown depth.
Raising a window advances the shared depth counter.
`services/desk_window_service.py` and `compositor/hubWindows.ts` own the hub and browser sides.

A window opens as a region and takes focus.
Closing it returns focus to the element that opened it.
Windows do not trap focus.
`Escape` closes an open head menu first. A later `Escape` requests window close when that host enables `escapeCloses`.
A host can disable Escape closing, and an editor can require its own close handling.
Dragging the head moves the window. Double-clicking the head zooms it.

### Saved layout

The hub owns registered window rows in `desk_windows` and desk-level counters in `desk_window_desk`.
Each window write takes the desk's next revision.
Stale expected revisions are refused and followed by a read of current state.
Share-plus-pixel geometry resolves against each view's usable band.

The browser saves `hs.desk.workspace.v1` for initial presentation, local drafts, places, and preferences.
Hub rows overwrite the registered-window cache when loaded.
Context-dependent windows listed in `NOT_ON_HUB` remain local to their browser host.
The loader validates local entries and drops corrupt or unknown data.

A window cache does not own the Note, Meeting, or output shown inside it.

## Motion and states

A face shows one of seven states: `idle`, `active`, `working`, `success`, `warning`, `failure`, or `unreachable`.
Every state shows an icon and text, not color alone.
Window motion uses transform and opacity.
`prefers-reduced-motion` removes it.

`SurfaceLedgerRow` is a `div` with `role="button"`.
It cannot be a `button` because its trailing action would nest inside it.
Do not copy this pattern. New faces use the library Button.


## See also

- [Desk architecture](DESK_ARCHITECTURE.md): rendering and state ownership.
- [Domain model](DOMAIN_MODEL.md): retained records and execution evidence.
- [The Desk](WEB_DESK.md): user procedures.
