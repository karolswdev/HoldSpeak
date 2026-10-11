# Desk object model

This page is for contributors.
It lists the Desk object kinds, the verbs and keys, the drag rules, and the window geometry.
The source is the final authority. Each section names the file that owns the rule.
For the app structure, see [Desk architecture](DESK_ARCHITECTURE.md).

## Object kinds

`PrimitiveKind` in `web/src/lib/primitives.ts` lists every kind.
The `PRIMITIVES` table gives each kind its label, sync class, object verbs, and opening surface.
A verb that the table does not list is not available for that kind.

| Kind | Label | Sync class | Create | Object verbs | Opens as |
| --- | --- | --- | :-: | --- | --- |
| `meeting` | Meeting | content | no | ask, send | pullout |
| `artifact` | Artifact | content | no | ask, send | pullout |
| `note` | Note | content | yes | ask, edit, rename, duplicate, delete | pullout |
| `decision` | Decision | content | yes | duplicate, delete, send | pullout |
| `thread` | Thread | content | yes | delete | pullout |
| `directory` | Zone | organization | yes | rename, delete | Zone window |
| `kb` | Knowledge | organization | yes | ask, edit, rename, duplicate, delete | pullout |
| `project` | Project | organization | no | send | Project Room (the `open-project-memory` surface) |
| `repository` | Repository | organization | yes | none | repository window |
| `recipe` | Agent | capability | yes | ask, edit, rename, duplicate, delete | pullout |
| `chain` | Sequence | capability | yes | delete | pullout |
| `workflow` | Workflow | capability | yes | ask, edit, rename, duplicate, delete | pullout |
| `workbench` | Workbench | capability | yes | duplicate | workbench window |
| `coder` | Coder session | presence | no | none | pullout |
| `roadmap` | Roadmap | organization | no | none | roadmap window |
| `intelligence` | Intelligence | local | no | none | pullout |
| `people` | People | local | no | none | People window |
| `game`, `layout`, `story` | Game, Layout, Story | local | no | none | none |

A Zone is a drawer, not a card.
At the root of the Floor, filed objects leave the Floor and a coder session stays.
Inside a Zone, the Floor shows only its members.
`world.ts` leaves the Zone, game, layout, intelligence, and People kinds out of the ordinary Floor.
It also leaves out roadmaps.
The list view shows the same objects as the spatial view.

An ID resolves as a bare ID or as a qualified `kind:id` reference.

## Floor placement

`objUnit` in `web/src/desk/world.ts` returns a saved position when one exists.
Otherwise it places the object on a grid.
Dragging an object saves its position and removes it from the grid.
Positions are normalized from 0 to 1.
A compact screen is a screen 720 pixels wide or less.

Icon art is 64 by 64 pixels in a uniform cell.
Selected and stale states are separate image files, not CSS filters.
A state badge needs a named live field.

## Verbs

`VERBS` in `web/src/desk/verbRegistry.ts` is the one verb list.
The menus, the command palette, context menus, window head menus, and dock menus all derive from it.
Each verb has an ID, a label, a menu, an optional key, a `ghost` check, and a `run` function.
A `ghost` check returns the reason a verb is unavailable.
The menu shows an unavailable verb dimmed, with that reason.

| Menu | Verbs |
| --- | --- |
| **Desk** | **New Note**, **Write a thought**, **New Decision**, **New Knowledge**, **New Agent**, **New Workflow**, **New Workbench**, **New Zone**, **New Thread**, **New Project**, **Hide the menus** (Settle in), **List view** or **Spatial view**, **Arrange desk**, **Overview**, **Reset layout**, **Reset to seed…**, **Refresh from hub**, **Open Intelligence**, **Open People** |
| **Object** | **Open**, **Get Info**, **Ask this project**, **Ask AI**, **Continue in thread**, **Edit**, **Rename**, **Duplicate**, **Move to Zone**, **Delete**, **Focus** (Zone) |
| **Go** | One entry for each tool in `DESK_APPLICATIONS`. An open window gets focus instead of a second copy. |
| **Window** | **Close window**, **Iconify**, **Cycle windows**, **Cycle windows (reverse)**, **Snap left**, **Snap right**, **Zoom**, **To back**, and the four Chair windows |
| System | **Search**, **Keyboard shortcuts** |
| Thread slash commands | **Keep as note**, **Fork from here**, **Stop generation**, **New thread**, **Switch mode**, **Insert prompt**, **Show tools**, **Add todo**, **Compact thread**, **Toggle guardrail** |

**Reset to seed…** opens Settings. You confirm the reset there. The menu never resets by itself.
The composer runs the Thread slash commands.

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
| `⌃T` | **Write a thought** |
| `⌘⇧F` | Settle in |
| `⌃↑` | **Overview** |
| `F2` | **Rename** |
| `Delete` | **Delete** (Backspace on a Mac) |
| `⌘I` | **Ask AI** |
| `⌃1` to `⌃4` | Speak, Meetings, Agents, Settings |
| `⌘⇧P` | Change places |
| `⌃W` | **Close window** |
| `⌃M` | **Iconify** |
| `⌘⇧Z` | **Zoom** |
| `⌃B` | **To back** |
| ``⌃` `` and ``⌃⇧` `` | Cycle windows, forward and reverse |
| `⌘K` | **Search** |
| `⌘/` | **Keyboard shortcuts** |

## Selection

`selectedIds` holds the selection. `toggleSelected`, `setSelected`, and `clearSelection` change it.
An object verb works only when exactly one object is selected.
With more than one selected object, an object verb is unavailable. **Ask AI** still uses the whole selection.

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
| Agent, Sequence, Workflow | Note, Knowledge, Meeting, Artifact | **Hold as source** | The record becomes held context. Nothing runs. |
| Knowledge | Note, Meeting, Artifact, Agent | **Add to Knowledge** | The record joins the Knowledge. You can undo it. |

`GlassDropLayer` accepts files from outside the browser.
It refuses unknown file types and names the reason.
A transcript or audio file goes to `POST /api/meetings/import`.
A calendar screenshot goes to `POST /api/calendar/snapshot`.

## Window geometry

`web/src/desk/components/window/windowGeometry.ts` holds the geometry functions.
`DESK_WINDOW` comes from `web/design-tokens.json` through `web/src/lib/tokens.gen.ts`.

| Constant | Value |
| --- | --- |
| Margin from the viewport edge | 10 px |
| Top of the work area | 54 px |
| Bottom of the work area | 52 px, or the dock height when the dock is taller |
| Cascade step | 26 px |
| Title strip used to score overlap | 44 px |
| Placement scan step | 32 px |
| Default minimum size | 320 by 220 px |
| Snap edge | 26 px |
| Snap corner | 150 px |
| Overview gap | 18 px |
| Re-clamp delay after a resize | 150 ms |

### Placement

`placeWindow` picks a position for a new window.
It scans the work area in 32 px steps and scores each candidate.
A title strip overlap costs more than any body overlap.
A candidate must beat the best score to win.
When every candidate covers a title, the window cascades by 26 px for each open window, up to 8.

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
`windowRegistry.ts` defines the front window as the last open window that is not iconified.

A window opens as a region and takes focus.
Closing it returns focus to the element that opened it.
Windows do not trap focus.
`Escape` closes an open head menu first. A second `Escape` closes the window.
Dragging the head moves the window. Double-clicking the head zooms it.

### Saved layout

The browser saves one document, `hs.desk.workspace.v1`.
It holds the open tool windows, rects, stacking order, zoomed windows, iconified windows, open Zones, Zone view preferences, Chair window state, drafts, and window places.
Window IDs match `^[A-Za-z0-9:_-]+$`.
The loader drops invalid entries and caps ordered IDs at 100.
An unknown version or damaged data gives an empty layout.

## Motion and states

A face shows one of seven states: `idle`, `active`, `working`, `success`, `warning`, `failure`, or `unreachable`.
Every state shows an icon and text, not color alone.
Window motion uses transform and opacity.
`prefers-reduced-motion` removes it.

`SurfaceLedgerRow` is a `div` with `role="button"`.
It cannot be a `button` because its trailing action would nest inside it.
Do not copy this pattern. New faces use the library Button.
