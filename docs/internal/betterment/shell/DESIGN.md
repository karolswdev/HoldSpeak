# The desk shell: betterment design

Status: draft for the owner. Covers INVENTORY rows 39 (Windows), 40 (Menus),
41 (Dock), 42 (Desk screen and drawers), 43 (Wallpapers) and 44 (Builder
tools). Inputs: `RECON.md` (the live walk, 88 shots, 2026-10-17) and
`MODEL.md` (the code map). It obeys the product model in `../PLAN.md` §2 and
uses the names that the sibling designs settle: Agents (`../agents/`), Ask
and Notes (`../asking/`), Today and Needs you (`../daily/`), Projects and
Decisions (`../projects/`), Automations (`../workbench/`).

## 1. The job

Owner, 2026-10-13: "It still feels more of a gimmick than a fucking OS." The
10-13 recon put the answer in one line: "A real OS is boring: one way to
open, one way to act, one place for each thing, and the verbs always work."

The shell is not a feature he opens. It is how he gets to every feature, all
day. He uses it a hundred times a day without thinking about it: to open
today's meetings, to jump to Mira's prep, to find last week's decision, to
see which agent waits for him, to put two windows side by side. He wants:

- every app in one list he can scan, and each thing in one place;
- his hands on the keyboard: a key for each daily app, and one field that
  finds or does anything by name;
- menus that show only what works on the thing in front of him;
- a desk that holds his things and stays where he put them;
- windows that open where he can see them, at a size that fits;
- a desk that is pleasant to sit at, and never fights his work.

He closes the day without once having to remember where something lives.

## 2. What it is today

The full walk is in `RECON.md`. The window kernel is fast (every app key
opens in under 0.1 s) and the phone grammar (a home list, full-screen panes,
Back) is right. The layer above the kernel disagrees with itself.

| Step | What happens | Shot |
|---|---|---|
| Open the desk | Eleven icons, none his. People and the Conductor are on the floor and in the Dock. "Meetings" is a drawer and an app. | `01-desk-empty-1440.png` |
| Find an app | Go lists 6 of 24 apps. There is no Tools row. 12 windows open only from Search; Components opens from nothing. | `02-menu-go-1440.png` |
| Find Automations | Search "automation": "No matching tools or Desk items." | `03-palette-automation-1440.png` |
| Read the empty Search | First row `New Note`. 18 `PROGRAM` rows, no Today, no People. `Terminals · DRAWER` opens nothing. | `03-palette-empty-1440.png`, `61-enter-terminals-1440.png` |
| Act on a note | Menu bar Object: 13 rows, 3 dead but drawn like live rows. Right-click: 10 rows, all live. Two menus for one note. | `31-object-menu-note-1440.png`, `32-note-context-menu-1440.png` |
| Read the Window menu with no window | 14 rows; none can run. | `02-menu-window-1440.png` |
| Open five apps by key | Five windows in a pile; Speak and the Conductor fully hidden. | `70-keys-five-windows-1440.png` |
| Open Needs you from its icon | 698x672 at (14,42), over the drawer column. | `37-needs-you-icon-1440.png` |
| A morning of work | 3 imports and 3 people made 6 new floor icons by themselves. A new project pushed People and the Conductor into the next column. | `10-working-desk-seeded-1440.png`, `31-object-menu-note-1440.png` |
| Change the wallpaper | A separate app (Change places, ⌘⇧P) and Settings ▸ Wallpaper, with the same 12 cards. On Jupiter, icon names lose contrast. | `50-change-places-1440.png`, `55-settings-wallpaper-1440.png`, `52-scene-jupiter-desk-1440.png` |
| Use a builder tool | Processes: `EXTERNAL.EGRESS · Egress operation c36b0e … CLAIMED`. Activity: `No activity yet` above three records. | `60-tool-processes-1440.png`, `60-tool-activity-1440.png` |
| Phone Dock | Four glyphs, no words (`◈ ▣ ♧ ●`), and the orb cut at the edge. Go repeats the home list. | `40-phone-home-393.png`, `44-phone-go-393.png` |

## 3. Why it fails

1. **There is no one index. There are eight partial lists, and three are
   written by hand.** Go, the phone Go, the phone home, the Dock, the phone
   Dock, the HoldSpeak menu, Search and the floor each decide on their own
   which apps exist (`MODEL.md` §1). The manifest says the faces "must not
   grow parallel application lists" (`applications.ts:4-10`), yet the phone
   Go and the phone Dock are hand lists, and Go draws Tools only for a
   section that no row has. The result: half the product is reachable only
   by typing its internal name, the owner's most wanted job (Automations) is
   not found by its own word, and People has four doors while Components has
   none. (`02-menu-go-1440.png`, `03-palette-automation-1440.png`,
   `03-palette-empty-1440.png`)
2. **The menus show what cannot run, and draw it like what can.** "Ghost,
   never hide" is written into the menu bar and the menu species
   (`DeskMenuBar.tsx:3-4`, `DeskMenu.tsx:137-138`), against UX-CANON A.11.
   The ghost is a faint stipple that the eye cannot see
   (`chrome-menus.css:205-219`). So the menu bar offers "Draft update" on a
   note, the Window menu offers fourteen verbs with no window, Search offers
   "Hand to coder · Select an object", and a key on a ghosted verb does
   nothing, silently (`keymap.ts:125`). The right-click menu already does the
   right thing (`objectMenu.ts:12-14`), so the same note has two Object menus.
   (`02-menu-object-1440.png`, `02-menu-window-1440.png`, `31-*`, `32-*`)
3. **The floor is a view of the database, not his workspace.** Every
   meeting, person, decision, thread and kept answer that no drawer holds
   becomes an icon by itself (`screen/compose.ts:79`, `:303-340`). The system
   puts its own icons (People, the Conductor, Needs you) among his, and the
   layout flows, so one new project moves them. A desktop that changes on its
   own cannot be trusted as a place to put things. (`01-desk-empty-1440.png`,
   `10-working-desk-seeded-1440.png`, `31-object-menu-note-1440.png`)
4. **A window returns to where it was, not to where he is.** A remembered
   place always wins (`DeskWindow.tsx:350-353`), so windows reopen on top of
   each other. Needs you skips the placement scan (`DeskWindow.tsx:451-456`).
   Sizes are constants per app, so "3 people" gets 640x560 and a short list
   gets the same window as a long one. Wings sit in three places (title bar,
   body segment, body tabs). (`70-keys-five-windows-1440.png`,
   `37-needs-you-icon-1440.png`, `15-desk-after-summaries-1440.png`)
5. **The atmosphere is a second app.** Wallpaper has two homes, a key, and a
   "Hide the menus" verb in two places. It costs attention in the menus and
   in Search, and on light scenes it costs legibility. On the phone it is
   never seen. (`50-*`, `55-*`, `52-scene-jupiter-desk-1440.png`,
   `58-phone-wallpaper-393.png`)

## 4. The design

### The concept

**The shell is how he gets to his work: Go lists every app, the Dock holds
the five he uses daily and shows their state, Search (⌘K) finds or does
anything by name, the Object menu acts on the thing in front, and the floor
holds only what he chose to keep.**

One rule makes the shell boring in the good way: **every place is a
projection of one list.** The manifest is the list of apps; the verb registry
is the list of verbs. Go, the phone home, both Docks, the HoldSpeak menu,
Search and the keyboard sheet are drawn from them, and from nothing else. A
new app gets its Go row, its Search row and its sweep check by adding one
manifest row.

Second rule: **a verb that cannot run is not shown.** Not in a menu, not in
Search, not as a dead Dock tile. A key whose verb cannot run does nothing and
says nothing, as on a Mac.

### Each place and what it is for

| Place | It is for | It holds | It never holds |
|---|---|---|---|
| **Go** (menu bar; on the phone, the home screen) | Finding any app | Every app, grouped: daily, work, then Builder ▸ when builder tools are on | Objects, verbs, settings |
| **The Dock** | The five daily apps, one press, with their state | Today, Meetings, People, Agents, Speak; the record orb; a tile for each iconified window | Tools, drawers, Overview and Reset buttons |
| **Search (⌘K)** | Finding or doing anything by name | Recent things, apps, objects by name, verbs that can run now, settings, and **Ask "…"** | Dead verbs, raw ids, duplicated section headers |
| **The HoldSpeak menu** | Setting the machine up | Settings, Engines, Accounts, Wallpaper, Setup, Keyboard shortcuts | Daily apps, builder verbs |
| **The Desk menu** | Making a new thing | New Note, New Meeting, New Decision, New Project, New Person, New Automation, New Drawer | View toggles, second names for Note or Automation |
| **The Object menu** (title = the kind: "Note", "Meeting") | Acting on the thing in front | Only the verbs that work on that kind, the same rows as the right-click menu | Verbs of other kinds |
| **The Window menu** | Arranging windows | The arranging verbs that can run now, then the open windows | Rows that need a window when none is open |
| **The bell** | The number that needs him | The Needs you count; one press opens Needs you | Anything else |
| **The floor** | His own things, where he put them | His drawers, his project drawers, his notes, anything he kept on the desk, Archive | Records the machine made by itself, app icons that are in the Dock |

### The words

| He sees | We stop using |
|---|---|
| **Go** | Tools ▸ (it was never drawn) |
| **Search** (the chip), placeholder **Find, open or ask** | "Search tools and Desk items" |
| Kind words in Search, sentence case: **App**, **Note**, **Meeting**, **Person**, **Project**, **Decision**, **Setting**, **Do**, **Ask** | `PROGRAM`, `VERB`, `DRAWER`, `OBJECTS`, `PROGRAMS`, `VERBS` |
| **Agents** (Dock, Go, key) | Conductor, Hand to coder |
| **Ask**, **Ask about this** | Ask AI, Ask this project, Continue in thread |
| **Automations**, **New Automation** | Workbenches, New Workbench, New Workflow, New Agent |
| **New Note** | Write a thought, New Knowledge, New Thread |
| **New Drawer**, **Move to drawer** | Move to Zone, zone |
| **Keep on desk**, **Remove from desk** | (new) |
| **Minimize** | Iconify |
| **Next window** | Cycle windows |
| **Arrange all** | Cascade, Reset layout |
| **Wallpaper** (a Settings row) | Change places, Places, Places to think, Hide the menus, Back to Desk |
| **Builder tools** (a Settings switch and a Go group) | Refresh from hub on the HoldSpeak menu |
| The Dock tile's word under every glyph, on the phone too | Icon-only tiles |

### The desktop (1440): the menu bar and Go

```
 HoldSpeak  Desk  Note  Go  Window                     ● 4   Search ⌘K   Sat 17 Oct 20:20
                         ┌───────────────────────────────┐
                         │ ◈ Today                    ⌃1 │
                         │ ● Needs you            4   ⌃J │
                         │ ▣ Meetings                 ⌃2 │
                         │ ⊕ People                   ⌃3 │
                         │ ▤ Projects                  ▸ │
                         │ ◉ Agents         1 asks    ⌃4 │
                         │ ✦ Ask                      ⌘I │
                         │ ⌁ Speak                    ⌃5 │
                         │ ───────────────────────────── │
                         │ ⚙ Automations            NEW  │
                         │ ◆ Decisions                   │
                         │ ▤ Memory                      │
                         │ ◰ Drawers                   ▸ │
                         │ ───────────────────────────── │
                         │ ⚒ Builder                   ▸ │  ← only when Builder tools is on
                         └───────────────────────────────┘
```

- The third menu is titled by the kind of the object in front: **Note**,
  **Meeting**, **Person**, **Project**, **Decision**. With no object in front
  and none selected, the title is not drawn.
- A Go row carries a count or NEW only when it is true (no zeros).
- Builder ▸ holds Activity, Processes, Context, Components, Calendar
  snapshot, Delivery board, Terminals and Refresh from hub.

The HoldSpeak menu and the Desk menu:

```
 ┌ HoldSpeak ──────────────────┐   ┌ Desk ───────────────────────┐
 │ Settings                 ⌃, │   │ New Note                 ⌃N │
 │ Engines                     │   │ New Meeting                 │
 │ Accounts                    │   │ New Decision            ⌃⇧N │
 │ Wallpaper                   │   │ New Project                 │
 │ Setup                       │   │ New Person                  │
 │ ─────────────────────────── │   │ New Automation              │
 │ Keyboard shortcuts       ⌘/ │   │ New Drawer                  │
 └─────────────────────────────┘   └─────────────────────────────┘
```

Engines, Accounts and Wallpaper open Settings at that wing. Setup opens the
first-run checks.

The Object menu on a note, and on a person (the same rows as the right-click
menu and the window's own menu):

```
 ┌ Note ───────────────────────┐   ┌ Person ─────────────────────┐
 │ Open                     ⏎  │   │ Open                     ⏎  │
 │ Ask about this              │   │ Ask about Mira              │
 │ Find the tasks              │   │ Prep 1:1                    │
 │ Hand to agent               │   │ Remove from desk            │
 │ Send…                       │   │ Get Info                    │
 │ Rename                   F2 │   └─────────────────────────────┘
 │ Duplicate                   │
 │ Move to drawer            ▸ │
 │ Remove from desk            │
 │ Get Info                    │
 │ ─────────────────────────── │
 │ Delete                   ⌫  │
 └─────────────────────────────┘
```

The rows for each kind come from the clusters that own the kind (`../asking/`
for notes, `../projects/` for projects, `../agents/` for Hand to agent,
`send/` for Send). The shell only promises that the menu bar, the
right-click menu, the window menu and Search show the same rows.

The Window menu, with three windows open:

```
 ┌ Window ─────────────────────┐
 │ Minimize                 ⌃M │
 │ Zoom                    ⌘⇧Z │
 │ Tile left               ⌘⌥← │
 │ Tile right              ⌘⌥→ │
 │ Arrange all                 │
 │ Overview                ⌘⇧E │
 │ Next window              ⌘` │
 │ ─────────────────────────── │
 │ Close                    ⌃W │
 │ ─────────────────────────── │
 │ ✓ Meetings                  │
 │   Ask                       │
 │   Settings                  │
 └─────────────────────────────┘
```

With no window open, the Window menu holds one line: "No windows open."
Stage (⌘⏎), Gather (⌘G) and To back (⌘⇧`) keep their keys and the keyboard
sheet; they appear in the menu only when they can run.

### The desktop: the Dock and the floor

```
┌────────────────────────────────────────────────────────────────────────────┐
│ ▤ Inbox     ▤ Ledger migration                                   (bell 4)  │
│ ▤ Work                                                                     │
│ ▤ Personal  ▢ On-call handbook idea   ▢ Ledger migration risks             │
│ ▤ Reference                                                                │
│                                                                            │
│                                                                            │
│                                                                  ▥ Archive │
├────────────────────────────────────────────────────────────────────────────┤
│  ◈ Today 4   ▣ Meetings   ⊕ People   ◉ Agents ●1   ⌁ Speak      (●) Record │
└────────────────────────────────────────────────────────────────────────────┘
```

- **The floor holds his things.** His drawers (Inbox, Work, Personal,
  Reference, and the ones he makes), his project drawers, his notes, anything
  he kept on the desk, and Archive. A meeting, a person, a decision, a thread
  or an automation result appears on the floor only when he presses **Keep
  on desk** (or drops it there). It lives in its app either way.
- **Icons never move by themselves.** A new drawer or project takes the next
  free place in the drawer column; a new note takes the next free place
  after the last loose icon. Nothing already on the floor shifts.
- **The seed** keeps Inbox (with Start here), Work, Personal and Reference.
  The seed drawers "Meetings" and "Decisions" are hidden while empty, because
  the apps have those names. The Weekly update prompt is filed into Inbox.
  The four seed modes leave Search (they are Ask's modes, not agents).
- **The Dock** has five tiles, in key order, then the record orb:
  - **Today** carries the Needs you number (the same number as the bell,
    `../daily/DESIGN.md`).
  - **Meetings** shows `REC 12:04` while recording (as today).
  - **People** shows the next 1:1 time when it is today ("1:1 14:00").
  - **Agents** carries the worst agent state (`../agents/DESIGN.md`): an amber
    lamp and a count for "Asks you" and "Wants to run", a dot for a New
    result, nothing when all are quiet. A drop on the tile is Hand to agent.
  - **Speak** shows a lamp while the mic listens.
  - An iconified window gets its own seat tile after the orb (as today).
  - The Overview and Reset layout buttons leave the Dock (the Window menu and
    the keys keep them).
  - The Dock never grows a tile by itself. An automation's NEW result shows
    on Go ▸ Automations and in Today. (This replaces the "Automations dock
    entry" line of `../workbench/DESIGN.md`.)
- The bell stays in the menu bar. The Needs you desk icon leaves the floor
  (decision 1).

### The desktop: Search (⌘K), the command line

```
 ┌ Search ──────────────────────────────────────── ⌘K ┐
 │ [ Find, open or ask…                          🎙 ] │
 │ Recent                                             │
 │ ▣ Platform sync               Oct 17     Meeting   │
 │ ⊕ Mira Kovacs                            Person    │
 │ ▢ On-call handbook idea                  Note      │
 │ Apps                                               │
 │ ◈ Today                          ⌃1      App       │
 │ ▣ Meetings                       ⌃2      App       │
 │ …every Go row…                                     │
 └────────────────────────────────────────────────────┘

 typed "mira", then → on the first row:
 ┌────────────────────────────────────────────────────┐
 │ [ mira                                        🎙 ] │
 │ ⊕ Mira Kovacs                            Person  → │
 │     Open · Ask about Mira · Prep 1:1 · Keep on desk│
 │ ▸ Prep 1:1 with Mira                     Do        │
 │ ▣ 1:1 with Mira               Oct 17     Meeting   │
 │ ▣ Platform sync               Oct 17     Meeting   │
 │ ✦ Ask "mira"                             Ask       │
 └────────────────────────────────────────────────────┘
```

- **Empty**: Recent (the last six things he opened: objects and apps), then
  the Go list. No verbs are preselected.
- **Typing**: one ranked list. The best match is first, whatever its kind.
  A row shows one kind word at the right. Each kind has at most one header,
  or none when the list is short.
- **Keys**: ↑ ↓ move; ⏎ opens; **→** shows that row's verbs in place (the
  same rows as its Object menu); **⌘⏎** asks about it (Ask with that thing in
  About); Esc closes.
- **Ask "…"** is the last row, or the first when the text reads as a question
  (`../asking/DESIGN.md`). An engine that has the desk's tools answers
  through Ask; when it can also arrange windows, "put Mira's prep beside the
  platform sync" works (slice S9, gated on `../mcp/` M1).
- Settings rows open Settings at that section.
- Builder tools are listed only when Builder tools is on.
- On the phone: the same, as a full-screen sheet.

### Windows

- **A new window opens where he can see it**: beside or 24 px below the front
  window, clear of every title bar and of the icon columns (the placement
  scan that exists). This now holds for Needs you and the other Chair
  windows too.
- **A remembered place is used only if it is clear.** A window that reopens
  goes back to its last place when no other title bar is under it.
  Otherwise the scan finds a clear place. A window he moved this session
  stays where he put it.
- **A window fits its content on first open.** It opens at the height of
  what it shows, between its minimum and the working band. "Nothing needs
  you" is a short window; a list of 40 meetings fills the band. When he
  resizes a window, his size wins from then on.
- **One wing grammar.** Wings sit in the title bar, as in Meetings and
  Settings. Faces that put wings in the body (a person's Prep, Context,
  History, Info) move them up when their cluster rebuilds the face. The
  desk sweep checks it.
- **One material.** A window is the steel frame and the paper body; rows
  are the library ledger. The desk sweep's material check names any window
  that mixes its own card colours (the Automations recon found mixed
  materials; `../workbench/DESIGN.md` §3.5).
- **The phone** stays as it is: each window is a full-screen pane with
  `‹ Back`; the stack is the history.

### The phone (393)

```
┌───────────────────────────────┐
│ ◌  Go   Today         ●4   ⌕ │
├───────────────────────────────┤
│ ◈ Today                       │
│ ● Needs you                 4 │
│ ▣ Meetings                    │
│ ⊕ People                      │
│ ◉ Agents              1 asks  │
│ ✦ Ask                         │
│ ⌁ Speak                       │
│ ───────────────────────────── │
│ ⚙ Automations             NEW │
│ ◆ Decisions                   │
│ ▤ Memory                      │
│ PROJECTS                      │
│ ▤ Ledger migration            │
│ DRAWERS                       │
│ ▤ Inbox   ▤ Work   ▤ Personal │
│ NEW                           │
│ Note · Meeting · Project ·    │
│ Person                        │
├───────────────────────────────┤
│  ◈      ●       ▣     ⊕    ◉  │
│ Today Capture Meetings People │
│                         Agents│
└───────────────────────────────┘
```

- The home screen **is** Go. The Go button in the bar folds the open panes
  and shows this list; it never opens a copy of it.
- The rows are the desktop Go rows, from the same manifest. Speak opens
  Capture on the phone (Talk, Write, Record), as today.
- The Dock has five tiles, each with its word: Today, Capture, Meetings,
  People, Agents. The orb leaves the phone Dock: Capture holds Record.
- Settings hides the Wallpaper row on the phone (the home list covers the
  desk).

### Wallpaper

- **One home**: Settings ▸ Wallpaper. HoldSpeak ▸ Wallpaper opens it. The
  Change places window, its ⌘⇧P key, its Search row and "Hide the menus" are
  parked.
- **Quiet Desk is the default**: a still, dark, textured desk.
- **The eleven scenes are opt-in**: Rainy City, Lantern Garden, After-Hours
  Radio, Midnight Archive, Night Train, Deep-Sea Station, Storm Greenhouse,
  Last Laundromat, and the orbits of Jupiter, Mars and Saturn. Each card is a
  still preview with its name once. The Motion switch stays. Room sound stays
  off unless he turns it on.
- **A scene may only show what is true.** It reacts to recording, the mic
  and a new arrival (as `gl/atmosphereActivity.ts` does); nothing else moves
  for attention. It pauses on a hidden tab (as today).
- **Icon names stay readable on any scene**: each name sits on a small ink
  plate (the Workbench label plate), so names make 4.5:1 on Jupiter as on
  Quiet Desk.

What makes it delight and not a gimmick: it costs no press in his day (it is
not in Go, the Dock or Search), it never hides a word, and when it moves, it
tells him something true ("recording").

### Builder tools

- One switch, Settings ▸ System ▸ **Builder tools**, default off.
- On: Go gains **Builder ▸** (Activity, Processes, Context, Components,
  Calendar snapshot, Delivery board, Terminals, Refresh from hub), and Search
  lists them. Off: they are in neither.
- Components gets its manifest `group` so Search finds it when on. Terminals
  opens a real window or leaves the list.
- Rhythm leaves as a window: its settings are Settings ▸ Rhythm; its loops
  fold into Automations (`../PLAN.md` §2). Voice commands opens as a wing of
  Speak (capture cluster, `capture/`, may refine). Setup is in the HoldSpeak
  menu. Memory is a Go row (`../asking/`). Workbenches is Automations.

So every one of the twelve Search-only windows has one home.

### Keys

| Key | Does |
|---|---|
| ⌃1 … ⌃5 | Today, Meetings, People, Agents, Speak (the Dock order) |
| ⌃J | Needs you |
| ⌘I | Ask |
| ⌘K | Search |
| ⌃, | Settings |
| ⌃N, ⌃⇧N | New Note, New Decision |
| ⌃W, ⌃M, ⌘⇧Z | Close, Minimize, Zoom |
| ⌘`, ⌘⇧E | Next window, Overview |
| ⌘⌥← / → | Tile left / right |
| ⌘/ | Keyboard shortcuts |

A key opens its app or brings its window to the front. When it runs, its
menu title flashes once (as on a Mac), so he sees where the verb lives. The
keyboard sheet groups keys as Apps, New, Windows, Desk.

### What one press does

| Verb | One press |
|---|---|
| Go ▸ an app | Opens it, or brings its window to the front if it is open. |
| Go ▸ Projects ▸ a project | Opens that project's window. |
| Go ▸ Drawers ▸ a drawer | Opens the drawer window. |
| Go ▸ Builder ▸ a tool | Opens that tool (only when Builder tools is on). |
| A Dock tile | Opens the app, brings it to the front, or restores it when minimized. |
| Agents tile (drop) | Hand to agent with the dropped thing. |
| Record (orb) | Starts recording a meeting; the Meetings tile shows REC. |
| The bell | Opens Needs you. |
| Search ⏎ | Opens the row's thing; on a Do row, runs the verb; on Ask, asks. |
| Search → | Shows the row's verbs in place. |
| Search ⌘⏎ | Opens Ask with that thing in About. |
| Object menu row | Runs that verb on the thing in front. |
| Keep on desk | Puts the thing on the floor at the next free place (files it into the desk). |
| Remove from desk | Takes the icon off the floor; the thing stays in its app. |
| New Drawer | Makes a drawer on the floor, its name ready to type. |
| Arrange all | Cascades the open windows from the front one, keeping their sizes. |
| Overview | Shows every window side by side; a press brings one to the front. |
| HoldSpeak ▸ Wallpaper | Opens Settings at Wallpaper. |
| A wallpaper card | Applies it at once; the card shows "In use". |
| Builder tools (switch) | Adds or removes Go ▸ Builder and the builder rows in Search. |

### What is removed or parked (nothing is deleted)

- **Go ▸ Tools** (the empty branch in `deskGo`) is replaced by the Go groups
  and Builder ▸.
- **The hand lists** `PHONE_GO_CHAIR`, `PHONE_GO_PLACES`, `PHONE_NEW` and the
  phone Dock list are replaced by manifest fields. Their code is parked with
  a pointer.
- **"Ghost, never hide"** leaves the menu doctrine. The `ghost` reason stays
  in the registry (keys, tests and the rig read it); faces withhold a ghosted
  row.
- **Desk menu rows**: Write a thought, New Knowledge, New Agent, New
  Workflow, New Workbench, New Thread, Hide the menus. Their verbs stay in
  the registry without a menu; their data and MCP tools stay.
- **HoldSpeak menu**: Refresh from hub moves to Builder ▸.
- **Window menu**: Cascade and Reset layout become Arrange all; Window ▸
  Desk (Brief, The week, Capture, Needs you) leaves (Brief and The week are
  parked by `../daily/`; Needs you and Capture are in Go and the Dock).
- **Dock**: the Overview and Reset buttons; the phone orb.
- **Floor**: the People, Agents (Conductor) and Needs you icons; the live
  agent icons (`../agents/` moves them into Agents); records the machine made
  that he did not keep. Their data stays; they are in their apps.
- **Wallpaper**: the Change places window (manifest row `parked`), ⌘⇧P, its
  Search row, "Hide the menus" in its strip and in the Desk menu.
- **Search**: the `Terminals · DRAWER` row until Terminals opens a window;
  the seed modes as `AGENT` rows; every ghosted verb row.
- **Builder tools** leave Search unless Builder tools is on.

### What has to change underneath

- **The manifest grows the fields the faces need**, and every face reads
  them: `go: { group: "daily" | "work" | "builder", order }`, `dock: { order,
  phone }` (the phone Dock from the same field), and `group` on Today,
  People, Components so that Search sees them. `PHONE_*` hand lists go.
- **One function lists an object's verbs**: `objectMenuEntries` (today the
  right-click menu) also feeds the menu-bar Object menu, the window menu and
  Search's → row. Ghosted rows are dropped in the shared menu species.
- **The floor reads a desk directory.** A seed directory (`hs-seed-desk`,
  not drawn as a drawer) holds what he kept. `composeScreen` draws loose
  notes as today, and other kinds only when they are in that directory.
  Keep on desk and Remove from desk are `zone.file` and `zone.unfile` on it,
  so an agent can do them too (MCP parity, no new tool).
- **Stable floor order**: system icons leave, drawers append, loose icons
  append; `layoutScreen` never reorders what is there.
- **Placement**: `DeskWindow` uses a remembered rect only when no other
  title bar is under it; Chair windows go through `placeWindow`; app windows
  get `fitContent` with a maximum of the working band.
- **A Builder tools setting** in Settings ▸ System, read by Go and Search.

## 5. Decisions for the owner

1. **The floor shows only what you keep.** Meetings, people, decisions,
   threads and results stay in their apps and drawers, and come on the floor
   only when you press Keep on desk. The People, Agents and Needs you icons
   leave the floor, because the Dock and the bell are their homes. This
   changes one line of `../daily/DESIGN.md`: the Needs you number shows on
   the bell, the Today tile and Go, not on a desk icon. Recommended: **yes**.
   A desktop that fills by itself is the first thing that reads as a stage
   set (10-13 recon, R7).
2. **Wallpaper is a Settings row, not an app.** Quiet Desk stays the
   default. The eleven scenes stay, opt-in, in Settings ▸ Wallpaper. Change
   places, ⌘⇧P and Hide the menus are parked. Recommended: **yes**. The
   alternative is to also cut the set to a curated five; the cost of keeping
   eleven is zero presses in his day once they leave the menus and Search.
3. **The keys follow the Dock**: ⌃1 Today, ⌃2 Meetings, ⌃3 People, ⌃4 Agents,
   ⌃5 Speak, ⌃J Needs you, ⌃, Settings. Today ⌃1 is Speak and Settings is ⌃4.
   Recommended: **yes**. He has not built habits on the old keys yet (Tenet
   2), and one rule (the Dock order is the key order) is easier to learn
   than a list. ⌘1 to ⌘5 stay bound where the browser passes them.

## 6. How we know it worked

On his desk, in a normal working day:

- **One map.** He opens any app from Go in **at most 2 presses**, or its
  key in **1**. No window is reachable only by Search: the sweep counts
  every manifest row in Go (target **0** Search-only apps, today 12).
- **He finds Automations** by Go in **2 presses**, or by typing "automation"
  in Search, where it is the **first row**.
- **Verbs always work.** Every row in every menu and in Search runs when
  pressed: **0** dead rows (today 13 in the Object menu with nothing
  selected, 14 in the Window menu with no window, 2 in Search). The menu-bar
  Object menu and the right-click menu show **the same rows**.
- **Keyboard first.** He opens Today, Meetings, People, Agents and Speak with
  ⌃1 to ⌃5, finds Mira by ⌘K "mi" ⏎ in **3 presses and under 2 s**, and asks
  about her with ⌘K "mi" ⌘⏎.
- **Windows.** After ⌃1 to ⌃5 and ⌘I, **every title bar is in view**, and no
  window covers the drawer column.
- **The floor.** After a day with four meetings and three new people, **0**
  icons appeared that he did not keep, and **0** icons moved.
- **Wallpaper.** He changes it in **3 presses from one place**, and every
  icon name is readable on every scene.
- **Phone.** Every Dock tile has its word; Go never shows a copy of the home.
- **The gimmick test.** He works a full morning and never opens Search to
  find an app, only to find a thing or to ask.
