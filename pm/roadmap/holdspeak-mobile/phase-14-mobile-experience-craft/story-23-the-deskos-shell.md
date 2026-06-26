# HSM-14-23 — The DeskOS shell: the logical anatomy (organizer · toolbar · drawers · desk · floating)

- **Project:** holdspeak-mobile (canon for both surfaces)
- **Phase:** 14
- **Status:** todo — opened 2026-06-24. The owner's question once the objects, environments, and the
  Living Desk substrate were designed: *"this stuff needs to be logical, and needs to have these drawers
  and the toolbar and what else — how do we incorporate this all?"* This is the answer: one coherent
  shell where every affordance has exactly one logical home.
- **Depends on:** [[story-19-the-desk]], [[story-20-the-desk-object-model]],
  [[story-22-the-living-desk]], [[story-21-desk-environments]].
- **Owner:** unassigned

## The one idea that makes it cohere

There are **two different kinds of side-storage** and conflating them is what makes desk UIs muddy:

- **Your filed world** (the left pane) — *"my stuff, organized."* Navigation: where meetings, KBs,
  directories live. You browse it.
- **The parts bin** (the drawers) — *"the supply of standard pieces I build WITH."* A palette: models,
  sources, blocks, tools. You **pull a piece out of it onto the desk.**

One is *navigation*; the other is a *palette*. Keep them separate and the whole OS reads cleanly.

## The anatomy

```
┌─ TOOLBAR ───────────────────────────────────────────────────────────────────┐
│ ☰  Knowledge › Architecture     ⌘K Search    ⌖ Select   ⤢ Fit   ▦ Tidy        │
│                                            🌗 Environment        ◗ Queue ●     │
├──────────────┬──────────────────────────────────────────────────────────────┤
│  ORGANIZER   │                                                        🗑 Bin   │
│  (left rail) │                                                                │
│              │              THE DESK   — the 3D room at 82°                   │
│  SMART       │                                                                │
│   All · Today│      [cassette]    [✦ KB crystal]    [sticky note]            │
│  LIBRARY     │            lay · lift · stack · drop-on = run                  │
│   Models     │                                          ┌── window ──┐        │
│   Knowledge  │                                          │  Meeting    │        │
│  DIRECTORIES │                                          └─────────────┘        │
│   Atlas …    │                          🎙 Record                              │
├──────────────┴──────────────────────────────────────────────────────────────┤
│  DRAWERS ▸   [ Models ]   [ Sources ]   [ Blocks ]   [ Tools: Ask · ✏ · 🧽 · clay ] │
└──────────────────────────────────────────────────────────────────────────────┘
         (pull a piece UP onto the desk; the drawer is the supply, the desk is the bench)
```

## Where every affordance lives — and why

### A. The Organizer (left rail) — *your filed world*
Smart (All/Today/Week/Pinned), Library (Models, **Knowledge**), Directories (user folders). Navigation +
filing target. Collapsible to a thin rail to give the desk the room. *(Built — HSM-14-19/20.)*

### B. The Toolbar (top) — *view + OS actions*
Left→right: **breadcrumb** (current folder / KB), **⌘K Spotlight** (search + run anything), **Select**
(lasso) toggle, **Fit / Tidy**, **Environment** switcher (the room theme — HSM-14-21), and on the right
the **Queue HUD** pill (running jobs: workflow/Ask runs + syncs — the Phase-15 HUD) and the trust/egress
indicator. The toolbar is *the desk's control strip*, never object actions.

### C. The Drawers (bottom edge) — *the parts bin*
Recessed tabbed trays you pull pieces FROM onto the desk (story-19 pillar 3):
- **Models** — the GGUF cartridges.
- **Sources** — recordings / imports / live inputs.
- **Blocks** — workflow nodes + saved workflows (the Workbench supply).
- **Tools** — **Ask AI** (the atom — HSM-16-09), and the **barrier materials** (pencil / eraser / clay —
  HSM-14-22), stamps. You drag a tool/piece out; it becomes a live object or an active tool on the desk.

The drawers are the *only* place new pieces enter the desk. That's the logic: supply at the edge, work
in the middle.

### D. The Desk (center) — *the workspace*
The 3D room (HSM-14-22). Objects lay/lift/stack; **drop-on = run** (combine); barriers corral; the
environment lights it. This is where everything actually happens.

### E. The Floating layer (over the desk)
- **Windows** — apps open here (meeting detail, output reader, the Workbench, settings) — HSM-14-19
  windowing.
- **Contextual bars** — the **selection bar** (on lasso: Bundle / File / Ask), the **Ask printer tray**
  (the printed result card → keep / bin — HSM-16-09).
- **The Bin** (top-right corner) — drop an object or a printed card to discard. The literal home of
  "bin it."
- **Record** (the mic) — a desk affordance to start a capture.

## The logic in one line

**Left = organize · Top = control · Edges = supply · Center = work · Floating = apps + actions + bin.**
Every affordance has one home; nothing competes for the same job.

## Scope

- **In:** the shell layout as built UI on the Living Desk: the Organizer (exists), the Toolbar (extend
  the existing bar with Spotlight + Environment + Queue), the **Drawers** (new — the bottom tabbed trays
  with Models/Sources/Blocks/Tools and pull-onto-desk), the **Bin**, and the floating layer wiring. Each
  region honors the convention (drawer pieces are DeskObjects; pulling one out spawns it).
- **Out:** the contents' deep behavior (Ask = HSM-16-09; barriers = HSM-14-22; workflows = HSM-16-08) —
  this story is the **shell that houses them**; web parity is HSM-16-04.

## Acceptance criteria

- [ ] The five regions exist and are visually distinct: Organizer (left), Toolbar (top), Drawers
      (bottom), Desk (center 3D), Floating (windows/bars/bin).
- [ ] Drawers open as tabbed trays; **pulling a piece out spawns it on the desk** as a DeskObject/tool.
- [ ] The Toolbar carries Spotlight, Select, Fit/Tidy, Environment, and the Queue HUD.
- [ ] A **Bin** accepts dropped objects + printed cards to discard.
- [ ] The Organizer (filed world) and the Drawers (parts bin) are clearly *different* surfaces, not
      duplicated.
- [ ] Device-proven on the iPad Air M4 ([[feedback_verify_on_device_not_seeded]]).

## Test plan

- On device: pull a model from the Models drawer onto the desk; open the Tools drawer and grab Ask AI;
  switch environment from the toolbar; drop a card in the Bin. Confirm the Organizer still navigates and
  the desk still does objects — each region owns its job.
