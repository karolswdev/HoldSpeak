# The desk shell: the recipe

Each slice is one PR in the fast cycle (`CLAUDE.md`). They are ordered so
that each merge leaves the shell better than before and never half-broken on
the owner's desk. Read `DESIGN.md` first; `MODEL.md` has the code map. Paths
are under `web/src/desk/` unless they say otherwise.

Cross-cluster notes:

- S1 is PLAN track T3's "Go ▸ Tools drawn (every app in Go)" and "parked
  rows unmapped". Do it here, once.
- Names follow the owning cluster: a slice uses the manifest label as it is
  at merge time (Conductor until `../agents/` renames it to Agents;
  Workbenches until `../workbench/` A1 renames it to Automations). No slice
  here renames another cluster's app.
- Object verbs per kind (Ask about this, Find the tasks, Prep 1:1, Send…)
  belong to their clusters. The shell slices only make every menu read the
  same list.

---

## S0. Menus and Search show only what works

- **Goal**: every row in every menu and in Search runs when he presses it,
  and the menu-bar Object menu shows the same rows as the right-click menu.
- **Files**: `components/DeskMenu.tsx`, `components/DeskMenuBar.tsx`,
  `objectMenu.ts`, `components/DeskToolShelf.tsx`, `keymap.ts`,
  `components/chrome-menus.css`.
- **Changes**:
  - `WorkMenu` drops an entry whose `ghost` is a string. Remove the ghost
    reason footer and the stipple style. Keep `ghost` in the registry (keys
    and tests read it). Update the header comments of `DeskMenu.tsx:137` and
    `DeskMenuBar.tsx:3-4` to UX-CANON A.11 ("withhold, never ghost").
  - The menu-bar Object menu gets its rows from `objectMenuEntries`. Its
    target is the front window's object (`windowObjectRef(frontWindowId())`)
    or else the one selected icon. Its title is the target's kind in words
    (Note, Meeting, Person, Project, Decision, Drawer). With no target, the
    title is not drawn.
  - The Window menu with no window open shows one line, "No windows open".
  - Search drops every verb row whose `ghost(ctx)` is a string, and the
    launcher rows whose launcher opens no window (`Terminals`) until S1
    moves them to Builder.
  - `dispatchKey` flashes the menu title of the verb it ran (one 120 ms
    inverse flash; none under reduced motion).
- **Done when**: at 1440, with nothing selected, the menu bar reads
  `HoldSpeak Desk Go Window`; select a note and it reads `HoldSpeak Desk Note
  Go Window`, and Note shows the right-click rows, all live. Window with no
  window shows "No windows open". Search "agents" shows no "Select an object"
  row. At 393, Go shows no dead row.
- **Tests**: T2 `__tests__/menus.app.test.tsx` (title by kind; no ghost row
  in any menu; Window empty line), `__tests__/objectMenu.test.ts` (menu bar
  and right-click equal for note, meeting, person, project),
  `__tests__/palette.app.test.tsx` (no ghost rows), `__tests__/keymap.test.ts`
  (flash). T3 the desk sweep picks up the menus.
- **Not in this slice**: changing which verbs exist, the Desk menu's New
  list (S2), Search ranking (S5).

## S1. Go lists every app

- **Goal**: every app opens from Go, on the desktop and the phone, from one
  list; builder tools sit behind one switch.
- **Files**: `applications.ts`, `components/DeskMenuBar.tsx`,
  `screen/GoHome.tsx`, `tools.ts`, `verbRegistry.ts`,
  `pages/cores/settingsPrefs.tsx` (the System section).
- **Changes**:
  - Replace `go: { order, section }` with `go: { group: "daily" | "work" |
    "builder", order }`. Daily: Today, Needs you (the Chair window verb),
    Meetings, People, Projects ▸, Conductor, Ask AI, Speak. Work:
    Workbenches, Memory, Voice commands (`configure-commands`), Drawers ▸.
    Builder: Activity, Processes, Context, Components, Calendar snapshot,
    Delivery board, Terminals, Refresh from hub.
  - Give Today, People and Components a `group` so Search lists them.
  - `deskGo` draws Daily, a separator, Work, and Builder ▸ only when the
    `builderTools` setting is on. `phoneGo` and `GoHome` draw the same groups
    from the manifest; delete the use of `PHONE_GO_CHAIR` and
    `PHONE_GO_PLACES` (park the constants with a pointer to this slice).
    Brief and The week leave the phone list (parked by `../daily/`).
  - Search lists builder rows only when `builderTools` is on.
  - Unmap the parked rows: Engines and Accounts keep their aliases for
    Settings wings, but their HoldSpeak menu rows point at the Settings wing
    verbs, not at parked surfaces. Rhythm gets no Go row: Settings ▸ Rhythm
    is its home; its window stays reachable from Settings until Automations
    absorbs the loops.
  - Settings ▸ System gets one switch, **Builder tools**, default off.
- **Done when**: at 1440, Go shows Today, Needs you, Meetings, People,
  Projects ▸, Conductor, Ask AI, Speak, then Workbenches, Memory, Voice
  commands, Drawers ▸. Turning Builder tools on adds Builder ▸ with eight
  rows, each of which opens a window or a list. At 393 the home and Go show
  the same rows in the same order. Search "people" finds People as an App.
- **Tests**: T2 `__tests__/menus.app.test.tsx` (Go equals the manifest
  groups at both widths; Builder gated), `__tests__/palette.app.test.tsx`
  (Today, People found; builder rows gated). T3 the sweep opens every Go row
  at 1440 and 393 (new rows are swept for free; add any honest red to
  `KNOWN_REDS` with its single defect).
- **Not in this slice**: renaming apps, Decisions as an app (`../projects/`),
  the Dock (S3).

## S2. The New list, the HoldSpeak menu and the keyboard sheet

- **Goal**: the Desk menu makes seven kinds of thing, each named once, and
  the HoldSpeak menu holds only setup.
- **Files**: `verbRegistry.ts`, `components/DeskChrome.tsx`,
  `components/window/ShortcutSheet.tsx`, `store/dataSlice.ts` (New Drawer).
- **Changes**:
  - Desk menu: New Note ⌃N, New Meeting, New Decision ⌃⇧N, New Project, New
    Person, New Automation (runs today's New Workbench flow until A1), New
    Drawer. Remove `menu: "desk"` from Write a thought, New Knowledge, New
    Agent, New Workflow, New Workbench, New Thread and Hide the menus; keep
    the verbs (with `palette: false`) and their keys unbound except ⌃T, which
    becomes New Note's alternate.
  - New Drawer: a registry verb that creates a directory through the
    existing `POST /api/directories` route and opens its name for typing.
  - HoldSpeak menu: Settings, Engines, Accounts, Wallpaper (Settings at the
    Wallpaper section), Setup, then Keyboard shortcuts ⌘/. `MARK_VERBS` loses
    `desk.refresh` (it is in Builder ▸ since S1).
  - The keyboard sheet groups: Apps, New, Windows, Desk.
- **Done when**: Desk shows seven New rows; New Drawer puts a drawer on the
  floor with its name ready; HoldSpeak shows six rows and no Refresh. ⌘/
  lists New Note under New.
- **Tests**: T2 `__tests__/menus.app.test.tsx`, `__tests__/creation.app.test.tsx`
  (New Drawer creates and focuses the name). T1 none (the route exists).
- **Not in this slice**: the Automations face, the Note and Thought merge
  (`../asking/`).

## S3. The Dock: five daily apps with their state; the keys follow it

- **Goal**: the Dock holds Today, Meetings, People, Agents and Speak, each
  with its word and its true state, and ⌃1 to ⌃5 open them in that order.
- **Files**: `applications.ts`, `components/window/Dock.tsx`,
  `components/dock.css`, `verbRegistry.ts`, `keymap.ts`.
- **Changes**:
  - Manifest `dock.order`: Today 0, Meetings 1, People 2, Conductor 3, Speak
    4. `dock.phone`: Today 0, Capture 1, Meetings 2, People 3, Conductor 4
    (Capture gets a manifest row or a `dock` entry on its Chair verb). The
    phone tiles in `Dock.tsx:499-534` are drawn from `dock.phone`; delete
    the hand list.
  - Phone labels show (remove `dock.css:590-595`); five tiles of 76 px with
    a 12 px word under the glyph; each owns a 44 px hit.
  - The orb leaves the phone Dock. The Overview and Reset layout buttons
    leave the Dock.
  - Tile states: Today shows the Needs you number (`useNeedsYou`, the bell's
    number); Meetings keeps REC; People shows "1:1 14:00" when a 1:1 is
    today (`useNextOneOnOneRead`); Speak shows a lamp while the mic is open
    (`micPhase`); the Conductor tile shows the worst agent state from the
    agent store the floor reads today (`useAgentFlights`, `agentState`), a
    lamp and count for "ask", a dot for a finished turn not yet seen when
    `../agents/` ships the seen bit. No zero counts.
  - Keys (decision 3): ⌃1 Today, ⌃2 Meetings, ⌃3 People, ⌃4 Conductor (Agents),
    ⌃5 Speak, ⌃J Needs you, ⌃, Settings; ⌘1 to ⌘5 as alternates. Add `j` and
    `,` to the typing guard.
- **Done when**: at 1440 the Dock reads `Today 4 · Meetings · People ·
  Conductor · Speak · (orb)` and nothing else until a window is minimized.
  At 393 it reads `Today · Capture · Meetings · People · Conductor`, every
  word visible, nothing cut at the edge. ⌃1 to ⌃5 open the tiles in order in
  under 0.1 s.
- **Tests**: T2 `__tests__/dock.app.test.tsx` (tiles from the manifest at
  both widths; states from recorded hub answers; no zero), 
  `__tests__/keymap.test.ts` (the new keys). T3 the sweep at 393 checks
  clipping, the 12 px floor and hits.
- **Not in this slice**: the Agents rename and the agent state source
  (`../agents/`), Hand to agent by drop (T4 drag, with `../agents/`).

## S4. The floor holds what he keeps

- **Goal**: the floor shows his drawers, his projects, his notes and what he
  kept, and nothing on it moves by itself.
- **Files**: `screen/compose.ts`, `screen/layout.ts`, `verbRegistry.ts`,
  `objectMenu.ts`, `holdspeak/seeds/fresh-desk.yaml`.
- **Changes**:
  - Seed a directory `hs-seed-desk` named "Desk", never drawn as a drawer.
  - `composeScreen`: loose = notes with content that no project or drawer
    holds (as today) plus any object in `hs-seed-desk`. Meetings, decisions,
    artifacts, repositories, threads and people are no longer loose on their
    own. Drop the People, Conductor and Needs you icons and the live agent
    icons from the floor (decision 1).
  - Keep on desk / Remove from desk: object verbs that `zone.file` /
    `zone.unfile` the object into `hs-seed-desk`. Offered on meetings,
    people, decisions, threads, artifacts; Remove also on notes (it files
    the note into Inbox).
  - `layoutScreen` keeps order: drawers in creation order then projects in
    creation order in the drawer column; loose icons in the order they
    arrived. A new icon appends; nothing reflows.
  - Seed: hide the seed directories "Meetings" and "Decisions" while they
    are empty; file the Weekly update prompt into Inbox for new desks. The
    four `mode` recipes stop being listed as `AGENT` in Search. Existing
    desks: no data changes; ordinary seed never removes records.
- **Done when**: import three meetings and add three people: the floor
  gains no icon. Press Keep on desk on one meeting: it appears at the next
  free place; nothing else moves. Make a project: it appends to the drawer
  column; nothing shifts. A fresh desk shows Inbox, Work, Personal,
  Reference and Archive.
- **Tests**: T2 `screen/__tests__/Screen.test.tsx` (compose rules from a
  recorded world; stable order), `__tests__/objectMenu.test.ts` (Keep on
  desk offered by kind). T1 `tests/unit/test_desk_seed.py` (the desk
  directory, the hidden empty seed drawers, Weekly update filed). T3 the
  sweep.
- **Not in this slice**: drag from a window onto the floor (a T4 follow-up),
  the Needs you window itself (`../daily/`).

## S5. Search is the command line

- **Goal**: ⌘K finds or does anything by name, one ranked list, with the
  row's verbs one key away.
- **Files**: `components/DeskToolShelf.tsx`, `objectMenu.ts`,
  `components/chrome-menus.css`.
- **Changes**:
  - Empty: Recent (the last six objects or apps he opened; keep the list in
    the desk store) then the Go list. No preselected verb.
  - Typing: one ranked list across kinds; a header per kind only when the
    list has more than eight rows; never the same header twice.
  - The kind word at the right in sentence case: App, Note, Meeting,
    Person, Project, Decision, Setting, Do, Ask.
  - → on a row unfolds that row's verbs in place, from `objectMenuEntries`
    (apps: Open; objects: their Object menu). ⏎ on a verb runs it.
  - ⌘⏎ on an object opens Ask with it in About (`openAsk` with the ref).
  - Placeholder "Find, open or ask". The `Ask "…"` row comes from
    `../asking/` (if its slice has merged, reuse it; if not, this slice adds
    it as the last row, opening Ask with the text).
  - The app terms come from the label and the description in full, plus the
    old names as aliases (`automation` finds Workbenches until A1).
- **Done when**: ⌘K "mi" ⏎ opens Mira in 3 presses, under 2 s. ⌘K "mi" → ↓ ⏎
  runs Prep 1:1. ⌘K "automation" puts Workbenches first. The phone sheet
  behaves the same with taps (a tap on → unfolds the verbs).
- **Tests**: T2 `__tests__/palette.app.test.tsx` (ranking, headers, kind
  words, → verbs, ⌘⏎), `__tests__/paletteRankHold.test.tsx` (still holds).
  T4 one keyboard walk in the existing palette browser test if one exists;
  otherwise T2 covers it.
- **Not in this slice**: Ask's face and answers (`../asking/`), memory rows
  (`../asking/`).

## S6. Wallpaper has one home

- **Goal**: he changes the wallpaper in Settings, in one place, and every
  icon name stays readable on every scene.
- **Files**: `applications.ts`, `pages/cores/settingsWallpaper.tsx`,
  `verbRegistry.ts`, `surface/objects/IconGrid.tsx` (or the icon label
  style), `pages/cores/SettingsCore.tsx`.
- **Changes**:
  - Park the Change places row (`parked: "settings wallpaper"`, alias to
    Settings ▸ Wallpaper so old links land there); unbind ⌘⇧P; park "Hide
    the menus" (`desk.settle` loses its key and menu; the settle state code
    stays).
  - Settings ▸ Wallpaper: the head says Wallpaper once; card names in
    sentence case; Motion stays.
  - Icon names on the floor get an ink plate behind the text (the Workbench
    label plate), so the name makes 4.5:1 on any scene.
  - At 393, Settings does not list Wallpaper.
- **Done when**: HoldSpeak ▸ Wallpaper ▸ a card applies it (3 presses). ⌘⇧P
  does nothing; Search "places" finds the Wallpaper setting. On Jupiter, the
  sweep's contrast check passes for every icon name.
- **Tests**: T2 `gl/__tests__/atmospherePreference.test.tsx` (unchanged
  default `quiet-desk`), a settings app test for the Wallpaper section
  (`__tests__/parked.app.test.tsx` for the parked row). T3 the sweep with the
  Jupiter scene set (contrast, readable).
- **Not in this slice**: new scenes, scene performance work.

## S7. Windows open where he can see them, at the size of their content

- **Goal**: after opening five apps by key, every title bar is in view, and
  each window is as tall as what it shows.
- **Files**: `components/DeskWindow.tsx`,
  `components/window/windowGeometry.ts`, `components/SurfaceWindows.tsx`,
  `applications.ts`.
- **Changes**:
  - A remembered rect is used only when no open window's title bar lies
    under its head strip (`HEAD` 44 px); otherwise `placeWindow` seats it,
    seeded at the remembered place. A rect he set this session is kept.
  - Chair windows go through `placeWindow` like the rest (keeps them off
    the icon column).
  - Application windows get `fitContent` with the working band as the
    maximum and the manifest `minW` / a new `minH` as the minimum. Only on
    first open; a resize by him wins.
- **Done when**: on a desk with remembered rects, ⌃1 to ⌃5 and ⌘I leave six
  title bars in view at 1440. Needs you opens clear of the drawer column.
  "Nothing needs you" opens as a short window.
- **Tests**: T2 `components/window/__tests__/cascade.a1.test.ts` and
  `workBand.test.ts` (pure placement: remembered rect refused when it
  covers a head). T1 `tests/unit/test_desk_windows.py` (a hub-opened
  window keeps its rect rule). T4 one geometry relation in the sweep or one
  browser case: six windows, every head visible (an exact geometry
  relation, which the diet allows).
- **Not in this slice**: moving wings into title bars (each cluster's face
  rebuild), materials (the sweep's material check already reports).

## S8. The Window menu

- **Goal**: the Window menu arranges, in plain words.
- **Files**: `verbRegistry.ts`, `compositor/useCompositor.ts`,
  `components/DeskMenuBar.tsx`.
- **Changes**: Iconify → Minimize; Cycle windows → Next window; Cascade and
  Reset layout → one verb, Arrange all (cascade from the front window,
  keep sizes); Window ▸ Desk leaves; Stage, Gather, To back and Back show
  only when runnable (S0 already withholds them). Order as in `DESIGN.md`.
- **Done when**: with three windows, the Window menu matches the design
  drawing; Arrange all cascades them with every head in view.
- **Tests**: T2 `__tests__/menus.app.test.tsx`, `__tests__/windows.test.tsx`.
- **Not in this slice**: new window verbs.

## S9. Ask can arrange the desk (gated)

- **Goal**: he types "put Mira's prep beside the platform sync" into Search
  or Ask, and the windows move.
- **Gate**: `../mcp/` M1 (the desk's tools reach a tool-capable engine) and
  `../engines/` E1 have merged, and Ask runs with tools (`../asking/`).
- **Files**: `holdspeak/mcp/families/desk_windows.py` (tool descriptions
  written for an engine), the Ask window's Wrote line, and an Undo record
  for window moves. The window tools are already WORK, so no press is
  needed (`holdspeak/mcp/tool_authority.py:290-295`).
- **Changes**: the engine gets `desk_window.open`, `.arrange`, `.raise`,
  `.close`, `.list` and `desk.list`; Ask shows what it did under Wrote
  ("Opened 2 windows · Tiled") with Undo (restore the previous rects).
- **Done when**: on his desk, with an engine that has tools, the sentence
  above opens both windows tiled in under 10 s, and Undo puts them back.
- **Tests**: T1 `tests/unit/test_desk_windows_mcp.py` (authority class,
  Undo record). Live proof on the real engine (no faked replies).
- **Not in this slice**: any other tool family.
