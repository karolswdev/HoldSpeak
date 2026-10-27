# The window grammar — why every window still reads as a web page (2026-10-24)

Owner, 2026-10-24: "I'm disgusted by where we are with the UI. Still look like a
bunch of shitty-ass looking pages inside OS-like containers."

He is right. This note names the concrete causes from the real desk (seeded
isolated hub, every application at 1440, 2026-10-24 16:23) and sets the grammar
every window follows from now on. It is a build direction under the fast cycle,
not a new approval gate. The owner judges the result live on his desk.

## What the shots show (the causes, not the symptoms)

1. **A page headline inside the window.** Meetings opens with a 26 px
   "1 meeting failed"; People with "4 people"; Agents with "1 working"; the Note
   repeats its own title bar name as a 30 px H1. A native window never
   re-announces itself; the title bar IS the name (UX-CANON A.7). The "one big
   fact" (`AppHead`) is a dashboard habit.
2. **Verbs float in blank space.** "New Project", "New automation", "Start an
   agent" sit alone at the top right of an empty band. A native window puts
   its verbs on a **toolbar** directly under the title bar, or in the title bar.
3. **Card-in-card.** Projects draws a bordered card inside the paper inside the
   frame; the Room draws cards inside wells inside the window. Content must
   run **edge to edge**: list rows touch the toolbar rule and the frame.
4. **Lists are stacks of cards, not list views.** Meeting rows are 88 px with
   avatars, chips and a second line; nothing is selectable, nothing is a column.
   A native collection is a **list view**: 28–32 px rows, column headers,
   sortable, one selected row in the selection blue, arrows and Enter.
5. **Chip and mono-caps soup.** `HAS OPEN ACTIONS`, `SAVED`, `NEXT 1:1`,
   `MILESTONE · 23 DAYS LATE`, `SOURCES 2`, stat tiles "5 meetings 4 summaries
   1 to review". That is a dashboard, not a desktop. Metadata is **quiet sans
   12 in muted ink**; a state is a dot and a word; mono is for code and ids.
6. **Dead footers.** Most windows end in a 40 px empty strip. A native window
   ends in a **status bar** that says the count and the state, or in nothing.
7. **Settings is a column of cards.** Eight bordered 56 px icon cards as a
   sidebar, a form with "SAVED" pills per field. A native preference window is
   a plain **rail** of 32 px rows (16–20 px glyph, selected row filled) and a
   **label/control grid**.
8. **The window chrome is weak.** One hairline, a lone square glyph at the
   left, three tiny glyphs at the right, no visible difference between the
   front window and the rest. The frame must carry weight: a title bar with its
   own tint, legible gadgets, a front window that visibly sits above.
9. **The ratified canvas tolerates all of this.** The 2026-10-22 modern-shell
   canvas still puts a 26 px "Speech" headline inside Settings and a 30 px
   "Platform checkpoint" inside Ask. Tokens and material were modernized; the
   page grammar was not. This note supersedes the canvas on grammar; the
   material tokens stand.

## The grammar (every window, from the title bar down)

```
┌ title bar ──────────────────────────────── gadgets ┐   28–32 px, tinted, name once
├ toolbar ─ verbs left · search/filter right ────────┤   36 px, 1 px rule under it
│ content: list view | editor | rail + pane | reader │   edge to edge, no inset for lists
├ status bar ─ count · state · egress ───────────────┤   24 px, sans 12 muted; omitted if nothing to say
└────────────────────────────────────────────────────┘
```

- **Title bar.** The name once, with its 16 px object glyph. Window verbs that
  belong to the whole window (Feedback, Recent, History) may sit in the title
  bar as quiet chrome Buttons. Gadgets: close at the left, zoom and depth at the
  right, 16 px glyphs with real stroke weight. The front window's title bar is
  tinted (`--wb-blue` family), the rest paper; the front window's frame has a
  1 px ink rule and a soft shadow; others a soft rule and no shadow.
- **Toolbar.** `Toolbar` species (kit). Verbs are library Buttons in the quiet
  secondary form; the ONE primary verb is blue. A search well sits at the right
  when the window is a collection. No headline, no count, no stat tiles.
- **Collection content.** `ObjectList` in its dense mode: 30 px rows, headers in
  sans 12/600 muted, cells sans 13, state as dot + word, selection blue on the
  whole row, hover tint, zebra off. Columns are declared by the provider.
  No avatars in list rows (the People detail may keep one). The list fills the
  window and scrolls inside it.
- **Editor content.** The editor fills the window; the title is edited in the
  title bar or as the first line, never duplicated as an H1. Verbs are in the
  toolbar; Saved time in the status bar.
- **Preference content.** A rail (list of rows) at the left, a pane at the right
  with a label/control grid (label sans 13 left, control right, 1 px soft rule
  between rows). Save state in the status bar, not per field.
- **Reader content.** The one place a display-size heading is allowed is a
  document's own first heading in a reader (Ask answers, a filed update).
- **Sections.** Caption sans 12/600 ink, sentence case, a hairline; never
  mono uppercase. Disclosures keep their count at the right as plain sans.
- **Metadata.** Sans 12 muted. Dot + word for state (`● Failed`, `● On track`).
  Mono only for ids, versions, code and times in ledgers.
- **Badges and pills.** At most one per row, and only when it says a state
  that changes what you do (`Failed`, `Needs you`). Never for a mode or a
  filter name.
- **Density.** Desktop rows 30 px; narrow (≤520 px content width) rows 44 px.
  Window inset 0 for lists and editors, 12–16 px for forms and readers.
- **Zero counters, prose, raw buttons, modals:** still bounces (UX-CANON A).

## Delight, not sterile (owner, 2026-10-24, same hour)

Owner: "make it look nice and attractive, not boring. Part of delighting the
user is offering up a wonderful interface to work and have fun and experiences
in, not a bore and a sterile piece of shit."

Native grammar is the skeleton; it must NOT produce a grey utility look. The
feel is Amiga Workbench's colour and character with modern craft: an interface
you want to be in. Concrete means, inside canon (no prose, library Buttons,
tokens only):

- **Colour with purpose.** The front window's title bar carries a real tint
  (the deep Workbench blue with paper ink, or the app family's hue); the
  selection is a vivid blue; state words carry saturated friendly colour
  (ok green, ember, red). Paper is warm near-white, not clinical white. The
  desk floor keeps its deep slate gradient.
- **Illustrated objects everywhere they belong.** Every list row leads with
  its 20 px illustrated object glyph (meeting, project, note, person, agent);
  the toolbar's verbs are icon + label (Workbench/Finder style), not bare
  text buttons; the window's own glyph sits in the title bar; an empty list
  shows the app's big illustrated icon with ONE true line.
- **Depth and life.** The front window floats (soft shadow, 1 px ink rule, a
  faint shine on the title bar); rows lift on hover (tint + 1 px ink rule);
  pressed states sink; 120–160 ms eased transitions on hover, selection,
  disclosure; the compositor's open/close motion stays.
- **Typography with character.** The title bar name and section captions set
  in the display face (Space Grotesk 600), body in the sans; numbers in the
  status bar tabular; never everything in one grey 13 px.
- **Friendly facts.** The status bar says the true thing in warm words
  ("5 meetings · 1 needs you", "Saved just now"), with a small lamp, not a
  mono readout.
- **Still no soup.** Delight is colour, objects, depth and motion applied with
  restraint, not more chips, tiles and captions. One accent per row.

Before a lane reports: look at the shot and ask "would I want to work in this
all day, and does it make me smile a little?" If the answer is "it's fine",
it is not done.

## The existing seams this lands on

- `web/src/desk/surface/kit.tsx` / `kit.css`: `AppHead`, `StatusStrip`,
  `FilterBar` (retire from collections; AppHead stays only for readers).
- `web/src/desk/surface/objects/ObjectList.tsx` + `objects.css`: dense mode.
- `web/src/desk/components/window-chrome.css`, `pullout.css`, `DeskWindow.tsx`
  (`desk-pullout-head`, gadgets, `desk-pullout-body` inset).
- `web/src/desk/surface/SurfaceFooter.tsx` / `surface-footer.css`: the status bar.
- Consumers: `web/src/pages/cores/HistoryCore.tsx` (Meetings), ProjectsCore,
  `WorkbenchAutomations.tsx`, ConductorWindow, PeopleCore, DecisionsCore,
  ActivityCore, the Settings cores, ThoughtWorkspaceWindow, ProjectRoomCore.
- Reference: Components (`ComponentsCore.tsx`) gets a "Window" group showing
  the grammar with populated, empty, busy, failed and selected states.

## Delivery

Three lanes in parallel from main 33fdbce59, each its own worktree, each a
small PR under the fast cycle (quick_check, merge, the watcher deploys):

- **Lane grammar**: kit species (`Toolbar`, `StatusBar`, ObjectList dense),
  window chrome weight, body inset, Components "Window" group; exercised on
  Meetings and Projects (the two collection consumers).
- **Lane settings**: the rail and the label/control grid; save state to the
  status bar; Setup and Engines follow the same pane grammar.
- **Lane note**: the Note editor fills its window (no H1), verbs in a toolbar,
  Saved in the status bar; the Room's head compact, sections edge to edge.

Then Automations, Agents, People, Decisions, Activity, Meeting detail adopt
the same species in follow-on slices. The owner judges every slice live.

## The dock, 2026-10-26

Owner 2026-10-26: "Why is the bottom menu so ugly? … Those icons" → the direction canvas
`canvases/dock-direction-2026-10-26.html`; his pick: direction 1 with the D objects ("Yes, I do
like the recommended approach, with D objects"). The dock is a centred plate in the floor's slate
glass, 10 px above the bottom edge, 64 px high, radius 14, as wide as its tiles. Each tile is
56 px wide with a 48 px D icon (`web/public/desk/sprites/system/48/`, 2 px bevel) and no word.
The name and a live fact (REC, 1:1) show on hover and focus as a label above the tile, and the
aria-label says the same. A dot under a tile means the app is running; the front app has a blue
dot and a soft plate; a hollow dot means a seated window. The count sits on the icon's top-right
corner. Record is one tile of the same size. A thin rule comes before the seated windows. The
working band reserves 84 px (`--desk-snap-bottom`); on the phone the plate runs edge to edge with
an 8 px inset and the reserve is 80 px. The same day the floor lost its Talk orb and the Archive
icon that sat in the Trash corner (#1495); Archive opens from Go ▸ Archive and ⌘K.
