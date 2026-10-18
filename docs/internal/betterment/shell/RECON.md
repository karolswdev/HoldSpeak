# The desk shell: what it is today (recon, 2026-10-17)

This is the "What it is today" input for `DESIGN.md` section 2. I walked the
shell as a first-time user: the menus, Go, the Dock, Search (⌘K), the Object
menu, windows, the desk floor and its drawers, the wallpapers and the builder
tools. Two hubs: an empty desk and a working desk with three meetings, two
notes, three people and one project. 1440x900 and 393x852. I fixed nothing.
All shots are in `shots/` (88 files). The rig is in the footnote.[^rig]

The jobs I walked, in the owner's frame ("one way to open, one place for each
thing, keyboard first, fast, and verbs that always work"):

1. Open each app he uses every day.
2. Find a thing that is not on the Dock: Automations (today "Workbenches"),
   Rhythm, Memory, a builder tool.
3. Act on a note from the menu bar and from a right-click.
4. Work with several windows at once, by keys.
5. Keep the desk floor tidy after a morning of real work.
6. Change the wallpaper.
7. Do the same on the phone.

## What I saw, in short

- **Speed is good.** Every app key (⌃1 to ⌃4, ⌘I) opened its window in under
  0.1 s. Overview, ⌘` and ⌃W work. A meeting now opens inside the Meetings
  window (list, then detail, then Back), which the 10-13 recon asked for.
  The phone home is now the Go list, with one tap to open, and Back works.
- **Go lists six apps.** Speak, Meetings, Today, Ask AI, People, Conductor.
  There is no Tools row at all. Twelve windows (Rhythm, Workbenches, Memory,
  Activity, Processes, Context, Commands, Setup, Change places, Delivery,
  Terminals, Calendar snapshot) open only from Search, and Components opens
  from nothing.
- **The menus show what cannot run, and it looks the same as what can.**
- **The floor fills by itself.** Three imports and three people put six new
  icons on the floor in two minutes, and the system icons moved.
- **Wallpaper has two homes** (a Change places window and Settings ▸
  Wallpaper) with the same twelve cards.

## Friction log

"Presses" counts clicks, taps and key chords; typing is not counted. "Wait"
is measured. "Est." is my estimate for a first-time user who reads the
screen.

| # | Step | What I pressed | What I saw (exact text) | What a newcomer expects | Where I got stuck | Presses | Wait / est. | Shots |
|---|---|---|---|---|---|---|---|---|
| 1 | Open the desk (empty) | Load, `Continue later` | `Get ready` card, then the floor: drawers `Decisions` `Inbox` `Meetings` `Personal` `Reference` `Work`, app icons `People` `Conductor` `Needs you` `Archive`, the seed note `Weekly update`, the bell `1`, a `TALK` button, the Dock `Today Speak Meetings People Conductor` and an orange orb | An empty desk with my apps in a Dock | Eleven icons and none is mine. `People` and `Conductor` are on the floor and in the Dock. `Meetings` is a drawer and an app | 1 | 2 s / 20 s | `00-first-open-*`, `01-desk-empty-1440.png` |
| 2 | Read the menus | HoldSpeak, Desk, Object, Go, Window | HoldSpeak: `Refresh from hub`, `Settings ⌃4`, `Engines`, `Accounts`, `Setup`. Desk: nine `New …` rows (`New Note`, `Write a thought`, `New Decision`, `New Knowledge`, `New Agent`, `New Workflow`, `New Workbench`, `New Thread`, `New Project`) and `Hide the menus`. Go: six rows. Window: fourteen rows | One way to open each app; a short New list | Go has no Rhythm, Memory or Workbenches. Four New rows mean "write something" (Note, thought, Knowledge, Thread). Three mean "automate" (Agent, Workflow, Workbench) | 5 | – / 60 s | `02-menu-*-1440.png` |
| 3 | Object menu with nothing selected | Object | Thirteen rows (`Open`, `Get Info`, `Ask this project · Select a Project`, `Draft update · Select a Project`, `Ask AI`, `Hand to coder`, … `Archive · Select a Project`) and a foot `Select an object` | A short menu or none | Every row is dead, and they look the same as live rows | 1 | – / 10 s | `02-menu-object-1440.png` |
| 4 | Window menu with no window | Window | `Overview`, `Close window`, `Iconify`, `Cycle windows`, `Tile left`, … `Stage · Needs two windows`, `Gather · No Room has two windows`, `Back · Nothing arranged`, `Desk »`, foot `No window open` | Nothing to do: few rows | Fourteen rows that cannot run | 1 | – / 10 s | `02-menu-window-1440.png` |
| 5 | Find Automations | Go (not there), Search, typed `automation` | Go: six rows. Search: `No matching tools or Desk items.` | Automations in Go, or Search finds it | The word he would use finds nothing. Only `workbench` finds `Workbenches · PROGRAM` | 4 | – / 60 s, stuck | `02-menu-go-1440.png`, `03-palette-automation-1440.png` |
| 6 | Find Rhythm, Memory, Activity | Search, typed each | `Rhythm · PROGRAM` and `Rhythm · SETTINGS`; `Memory · PROGRAM`; `Activity · PROGRAM` | The same in Go | Only Search reaches them. Rhythm has two rows (a window and a Settings section) | 3 each | 1 s / 15 s | `03-palette-rhythm-1440.png`, `03-palette-memory-1440.png`, `03-palette-activity-1440.png` |
| 7 | Read the empty palette | ⌘K | `VERBS`: `New Note`, `Write a thought`, `New Decision`, `New Knowledge`, `New Agent`, `New Workflow`. `PROGRAMS`: 18 rows (`Speak`, `Ask AI`, `Meetings`, `Settings`, `Change places`, `Conductor`, `Rhythm`, `Setup`, `Context`, `Workbenches`, `Activity`, `Memory`, `Processes`, `Commands`, `Engines`, `Accounts`, `Delivery · DRAWER`, `Terminals · DRAWER`). `SETTINGS`: … | My recent things and my apps | Today and People are not programs here. The first, preselected row is `New Note`. Every row carries a caps kind word (`VERB`, `PROGRAM`, `DRAWER`) | 1 | – / 30 s | `03-palette-empty-1440.png` |
| 8 | Search "agents" | ⌘K, `agents` | `OBJECTS`: `Chase`, `Desk`, `Draft`, `Interview`, `Plan`, each `AGENT`. `VERBS`: `Hand to coder · Select an object`, `New Agent`, `New Workbench`. `PROGRAMS`: `Context`, `Workbenches`, `Conductor` | The agents app | Four seed "modes" show as agents. A dead verb row is listed | 2 | – / 30 s | `03-palette-agents-1440.png` |
| 9 | Seed the working desk | (three imports, two notes, a project, three people through the hub) | Six new floor icons: `Event bus archi… review`, `1:1 with Mira`, `Platform sync`, `Ledger migrat… risks`, `On-call handbook idea`, then `Mira Kovacs`, `Theo Brandt`, `Jun Park` after People was set up. The project `Ledger migration` took the first column, so `People` and `Conductor` moved to the second | My meetings in Meetings, my people in People | Every new record became an icon. The system icons moved when a project appeared | 0 | – | `10-working-desk-seeded-1440.png`, `15-desk-after-summaries-1440.png`, `31-object-menu-note-1440.png` |
| 10 | Act on a note, menu bar | Click `On-call handbook idea`, then Object | Thirteen rows. `Ask this project`, `Draft update` and `Archive` are dead (`aria-disabled`), but drawn like the others; the foot says `Select a Project` | Only what a note can do | Three dead rows that look live | 2 | – / 15 s | `30-note-selected-1440.png`, `31-object-menu-note-1440.png` |
| 11 | Act on the same note, right-click | Right-click the icon | Ten rows, all live: `Open`, `Get Info`, `Ask AI`, `Hand to coder`, `Continue in thread`, `Edit`, `Rename F2`, `Duplicate`, `Move to Zone`, `Delete` | The same menu as the menu bar | Two menus for one object, with different rows. The note's Object menu works now (the 10-13 recon saw 7 of 11 dead); the menu bar copy still lists project verbs | 1 | – / 10 s | `32-note-context-menu-1440.png`, `34-object-menu-note-window-1440.png` |
| 12 | Open many windows by key | ⌃1, ⌃2, ⌃3, ⌃4, ⌘I | Each in under 0.1 s. Speak 640x560, Meetings 720x600, Conductor 720x600, Settings 640x600, Ask AI 740x620. Ask covers Settings, Settings covers Conductor and Speak | Windows side by side, or a clean cascade | Two windows hidden behind three others. Settings came back near its remembered place (706,220), over the others | 5 | 0.01–0.06 s each | `70-keys-five-windows-1440.png` |
| 13 | Open from the Dock and Go | Dock Today, Dock Meetings, a meeting row, Go ▸ Ask AI, HoldSpeak ▸ Settings | Today 880x700 at (408,64); Meetings 720x600 at (264,220) over Today; the meeting opens IN the Meetings window; Ask 740x620 at (520,124) over both; Settings at (648,220) over all three | Each new window beside the front one | Four overlapping windows, no pattern. Each window has a fixed size, not the size of its content | 5 | ~0.5 s each | `21-door-today-1440.png` … `26-door-settings-1440.png` |
| 14 | Find a buried window | ⌘⇧E | Overview shows two windows side by side, readable | – | Works (keep) | 1 | – / 5 s | `24-overview-1440.png` |
| 15 | Open from floor icons | Double-click `1:1 with Mira`, `Theo Brandt`, `Needs you` | Meeting 720x600 at (264,220); person 640x560 at (648,28); Needs you 698x672 at (14,42), over the icon column | Windows clear of my icons | Needs you covers the drawers | 3 | ~2.5 s each | `35-*`, `36-*`, `37-needs-you-icon-1440.png` |
| 16 | Change the wallpaper | ⌘⇧P (or Search ▸ `Change places`) | A window `Change places`, strip `Quiet Desk · All places · Favorites · Hide the menus`, twelve cards with `CHOOSE` | A Wallpaper row in Settings | It is a separate app. Settings ▸ Wallpaper shows the same twelve cards, and its head says `Wallpaper` twice | 1 | 2.5 s / 20 s | `50-change-places-1440.png`, `55-settings-wallpaper-1440.png` |
| 17 | Try three scenes | `NIGHT TRAIN`, `IN JUPITER'S ORBIT`, `RAINY CITY` | Night Train: a warm lit compartment; windows stay readable. Jupiter: the planet fills the right half; white icon names on the pale planet are hard to read. Rainy City: dark, readable | A pleasant desk that never fights my work | Labels on light scenes lose contrast. Headless frame rate was 2.5 to 9 per second, but headless Chromium has no GPU here, so I could not measure real cost | 3 | 6 s each / – | `51-scene-*`, `52-scene-*`, `53-scene-*` |
| 18 | Open builder tools from Search | Activity, Processes, Components, Context, Commands, Rhythm, Memory, Workbenches, Setup, Delivery, Terminals | Activity: `No activity yet` above three records. Processes: `EXTERNAL.EGRESS · Egress operation c36b0e`, `Node:inference-bbe847…`, `CLAIMED`. Components: not in Search (`No matching tools or Desk items.`). Context: a briefing page. Delivery: `Companion repo · owner/repo · ✕ NO LIVE SOURCE`. Terminals: Enter opened no window | Tools that say what they are for, or nothing | Only Memory and Rhythm help him. The rest are kernel views. Terminals is a dead row | 3 each | ~3 s each | `60-tool-*`, `61-enter-*` |
| 19 | Read the keyboard sheet | ⌘/ | `APPLICATIONS`: `⌃1 Speak`, `⌃2 Meetings`, `⌃3 Conductor`, `⌃4 Settings`, `⌘⇧P Change places`, `⌘I Ask AI`. `WINDOWS`: `⌃N New Note`, `⌃T Write a thought`, `⌃⇧N New Decision`, `⌘⇧F Hide the menus`, `⌘⇧E Overview`, … | Keys for my daily apps | No key for Today, People or Needs you. New Note sits under WINDOWS | 1 | – / 20 s | `71-shortcut-sheet-1440.png` |
| 20 | Phone: start | Load at 393 | The home is a list: `Apps` (`Needs you`, `Brief`, `The week`, `Capture`, `Meetings`, `Ask AI`, `People`, `Conductor`), `Projects`, `Drawers`, `New`. The Dock: four glyphs `◈ ▣ ♧ ●` and the orb, no words | My apps, with names | The Dock has no labels; `♧` is People. The orb is cut at the right edge | 0 | – / 15 s | `01-desk-empty-393.png`, `40-phone-home-393.png` |
| 21 | Phone: open a meeting | `Meetings`, `Platform sync`, `‹ Back` | Full-screen Meetings, then the meeting, then back to the list | – | Works: 2 taps in, 1 out (keep) | 3 | 2.5 s each | `41-*`, `42-*`, `43-phone-after-back-393.png` |
| 22 | Phone: Go | `Go` | The same list as the home screen | Something new | Go repeats the home list | 1 | – / 5 s | `44-phone-go-393.png` |
| 23 | Phone: HoldSpeak menu | The mark | `Refresh from hub`, `Settings`, `Engines`, `Accounts`, `Setup` | – | `Refresh from hub` is a builder verb | 1 | – / 5 s | `46-phone-holdspeak-menu-393.png` |
| 24 | Phone: Search | The magnifier, typed `mira` | `PEOPLE Mira Kovacs`, `OBJECTS 1:1 with Mira: decisions and actions`, `MEETINGS 1:1 with Mira`, `VERBS Prep 1:1 with Mira Kovacs`, `MEETINGS Platform sync`, `PROJECTS`, `OBJECTS`, `VERBS`, `MEMORY` | One section per kind | `MEETINGS`, `OBJECTS` and `VERBS` each appear twice | 1 | 1 s / 10 s | `45-phone-search-mira-393.png`, `56-phone-search-empty-393.png` |
| 25 | Phone: wallpaper | HoldSpeak ▸ Settings ▸ Open Wallpaper | Twelve cards | – | On the phone the home list covers the desk, so a wallpaper is never seen | 3 | 2.5 s / – | `57-*`, `58-phone-wallpaper-393.png` |

## Counts

| Measure | Value |
|---|---|
| Apps in Go (desktop) | 6 of 24 manifest rows |
| Windows reachable only by Search | 12 (Rhythm, Workbenches, Memory, Activity, Processes, Context, Commands, Setup, Change places, Delivery, Terminals, Calendar snapshot) |
| Windows reachable by nothing | 1 (Components) |
| Search rows that do nothing | 2 (`Terminals`, `Hand to coder · Select an object`) |
| Rows in the Object menu on a note (menu bar / right-click) | 13 / 10 |
| Rows in the Window menu with no window | 14, none runnable |
| `New …` rows in the Desk menu | 9 |
| Floor icons on a fresh desk / of them his | 11 / 0 |
| New floor icons after 3 imports, 2 notes, 3 people | 8 |
| Places that hold the same 12 wallpapers | 2 |
| Doors to People | 4 (Dock, floor icon, Go, Search) |
| Time to open an app by key | under 0.1 s |

Words a newcomer would not understand: `PROGRAM`, `VERB`, `DRAWER` (on
Terminals and Delivery), `Iconify`, `Stage`, `Gather`, `To back`, `Desk »`,
`Hide the menus`, `Change places`, `Move to Zone`, `Continue in thread`,
`Hand to coder`, `Conductor`, `Refresh from hub`, `Write a thought`,
`New Knowledge`, `New Agent`, `New Workflow`, `New Workbench`, and in the menu
bar, after the engine was added, `→ LAN-SCAN:7310B8C8…` (a raw id in the egress
chip, `12-used-1440.png`).

## Seen, but not in this cluster

- Meetings says `All summaries done` while each row says `REFUSED`
  (`22-door-meetings-1440.png`). Capture cluster.
- Settings ▸ Engines: `Default engine` set, but `Meeting summaries` still
  `no engine` until a second press (`13-default-assigned-1440.png`). Engines
  cluster.
- The brief asked about "only one of three meetings got an icon". In my walk
  all three got icons. By `web/src/desk/screen/compose.ts:303-326`, a meeting
  that is filed in a project or a drawer is not drawn on the floor, which
  would explain it if two were filed. I did not reproduce it: unknown.

## The verdict

The window kernel is fast and solid, and the phone grammar (a home list,
full-screen panes, Back) is right. What makes the desk read as a gimmick is
the layer above the kernel: the ways in do not agree with each other. Go
lists six of twenty-four apps; the Dock, the floor and Go each name People and
the Conductor; Search is the only way to half the product and cannot find the
word "automation"; the menus list verbs that cannot run and draw them like
verbs that can; the floor grows an icon for every record the machine makes;
and the wallpaper is a separate app. An architect who lives in this all day
learns four maps, not one.

[^rig]: Two isolated hubs through `scripts/graph_walk.py serve --scheduler`
    with `_isolated_hub_env` (scratch `HOME` from `mktemp -d`, every isolation
    switch from `CLAUDE.md`), run from the code of the owner's desk worktree
    (`wt-daily-delight-delivery-20261017`, `217001b2e`; `web/` and
    `holdspeak/web` match `main` at `b746549b8` except one setup route).
    Port 8851: the empty desk. Port 8852: the working desk. Seed through the
    hub's own routes: three transcripts through `POST /api/meetings/import`
    (Platform sync; 1:1 with Mira; Event bus architecture review), two notes
    through `POST /api/notes`, one project through `POST /api/projects`,
    People set up with the face's `Set up People` and three people through
    `POST /api/people/relationships`. The LAN engine `qwen3.8-27b` at
    `192.168.1.43:8080` was added with the face (Settings ▸ Engines ▸ Find on
    LAN ▸ Use it ▸ Default engine, then Meeting summaries) and the three
    summaries ran on it for real (6 s, 20 s and about 30 s). Chromium headless
    via Playwright, 1440x900 and 393x852 (mobile, touch, scale 2). The scripts
    are in `rig/`. Both hubs stopped and both scratch HOMEs removed
    afterwards.
