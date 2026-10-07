# PHILO Phase 14 canvas: The Desk Is Objects

**Status: DRAFT, for the owner's letter.** Nothing in product code changes. Every change is in `harness/`.

The page: `page.html` (one row per moment: the control, then A, B, C at 1440; the 393 shots under them; "Your call" at the top; the new species at the bottom). The charter: `docs/internal/philo/phase-14/PROPOSAL.md` (branch `philo-14/charter`).

## The alternatives (they differ in the shape of the desk)

| | Shape | 1 Floor | 2 Drawer open | 3 Drop to hand | 4 Lane | 5 Needs you |
|---|---|---|---|---|---|---|
| **A Workbench** | A screen of icons; windows open and stack | drawers, loose objects, an asking agent, the Conductor drawer, Needs you, Parked | drawer window (icons) + Get Info window; `A-2L`: the list view | the item dragged from the drawer onto the Conductor drawer; the confirm line in the drawer | the lane window (vertical rail) over the Conductor drawer | the smart drawer window |
| **B Bench** | A Shelf of drawers (left), stacked windows, the Conductor as a Pit of agent bays (bottom) | shelf + pit + two stacked windows | the tray: one icon row per kind, Info as a column | dragged onto the pit's free bay; the confirm line above the pit | the lane over the pit (two columns) | the tray, rows grouped by Agents / Due / To review |
| **C Stage** | Places on a floor; agents stand at their item, trails to the garage | zones per Project, Desk, Conductor garage | enter the place: the zone fills the stage; Get Info beside it | dragged onto the automaton in the garage; the confirm line in the garage | the lane window, stations on a horizontal track | the smart drawer window over the stage |

At 393 every alternative opens one window at a time (C7); a drawer is its list; the lane is one column.

## The control

The product on `origin/main` `c1a6ce50b`, served with `CANVAS_MODE=today` (no seat, no shim) on the same seed: `control-1` the Chair, `control-1b` the Floor today, `control-2` the Room, `control-2b` the Floor list (40 `[ ]` marks counted, `facts.json`), `control-3` the Hand to agent sheet (Launch never pressed), `control-4` the session window, `control-5` the Needs you coder row.

## The method (reused from `docs/internal/conductor-canvas/harness/`)

- **Stack** (`harness/p14stack.py`, `rig.py`): a real hub (`scripts/graph_walk.py serve`) on `HOME=/tmp/p14canvas-*`, the conductor seed (`seed_db.py`: Projects, the runbook item, the decision, people, two hook-reported sessions: Claude Code waiting with "The runbook needs a rollback owner. Jordan or Avery?", Codex working) plus `seed_f2.py` (a clone, worktrees, three launches bound to the sessions, a `cat` pane each on a private tmux socket) and a fake `gh` on the hub's PATH (PR #412 open, its checks passing). Each width has its own hub and HOME; the run removes every scratch dir. The owner's DB is never read. No agent starts.
- **Seat** (`harness/seats.mjs`): one named anchor in `web/src/desk/DeskApp.tsx` (the `<ChairHome>` render). With no alternative chosen the product renders exactly as on main. A missing anchor stops the server: `P14 CANVAS SEAT GUARD (p14): 1 files, 1 seats, every anchor met`.
- **Proposal** (`harness/p14.tsx`, `p14.css`): library species (Button, FilterTokens, LampGadget, StringGadget with its mic, EgressChip, SurfaceSection, SurfaceFooter, DeskWindowFrame) plus the proposed species listed on the page. Sprites from the mold (`web/public/desk/sprites`) through `sprites.ts`.
- **Fences** (`harness/board.py`): C1's JS_LIB, CONTRAST_ALL, CLIP, OVERLAP, TARGETS44 and C5's laws, imported unchanged from the ratified story-11 and story-15 harnesses. A board with no window open (A-1, C-1, C-3, B-1 at 393, control-1b, control-2b) is held to "no blue title bar".

## Fences: `ALL FENCES HELD`

Run of 2026-10-06, both legs, both widths (`shots/facts.json`, `_fails: []`). 45 shots.
- Recorded as main's, not failed: the Dock chip under `More` at 393 (every 393 board); the session window's xterm well scrolls sideways inside itself (`control-4`, as the Conductor F2 proof recorded); every small target on the control boards (they are main's face).
- At 393 the screen behind a window is hidden (`data-covered`): the window fills the work area (C7), so the screen leaves the glass instead of standing under it.

## Stand-ins (named in `harness/p14.tsx`'s header)

- **S1** The drawers' contents are composed in the shim from the seeded records' names; "Write the cutover comms" is a canvas item.
- **S2** The agent objects, their states and lamps (ASKS, WORKS, PR #412) are the shim's; the hub holds the same two sessions and three launches.
- **S3** The lane's timeline (tool calls, the agent's words, commit `a1c9e02`, PR #413, the held `psql` call, files changed) is canvas data. The hub keeps most of it and serves none (PROPOSAL §2; lane C0).
- **S4** The drafted answer "Jordan owns it. Avery reviews." is canvas text.
- **S5** The drag is drawn (a ghost sprite at the target, a dotted path, the target lit); no drop handler runs. Hand, Answer, Approve, Deny, Stop, Re-brief, Open PR do nothing.
- **S6** The Needs you rows are composed from the seed and S2/S3.
- **S7** Sprite gaps: no sprite for an action item (the note family), a PR (paper), a person (the one people-ledger), a smart drawer or the Conductor drawer (the drawer with an automaton badge); a project and a repository share the drawer.

## Not drawn honestly / limits

- The list has Name, Kind, When and State; **Where** is not a column (every object in one drawer has the same place). Needs you rows name their Project in the fact line.
- At 393 the selected list row's second line (`TODAY`) is cut at the row's foot.
- The screen bar's title reads `Chair` on the windowless boards (main's name for the surface; no seat changes it).
- The Dock is main's in every alternative (it still shows `Agents`, which the charter folds into the Conductor).
- Drag at 393 is drawn as the confirm line over the list; a phone drag gesture is not drawn.
- Not verified: the owner's browser and screen; a real touch device.

## Reproduce

```bash
uv sync --python 3.13 --extra test; (cd web && npm ci)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python docs/internal/philo/phase-14/canvas/harness/shoot.py
```

`ONLY_WIDTH=393`, `LEG=control|proposal`, `ONLY=B-` limit the run. `harness/dev.py proposal p <statefile>` holds one stack up; `window.__p.set({alt: 'B', moment: 4})` draws a board.
