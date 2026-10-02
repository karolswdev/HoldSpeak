# PHILO-13-11 (C1) canvas: the Workbench look

**Status: DRAFT, round two (Muad'Dib's read of round one, paid), for Astra's check and the owner's ratification** (UX-CANON §A.2: the canvas before the build). Nothing here is built in product code. Every change lives under `harness/`. The review page is `index.html` in this folder: every board at 1440 × 900 (left) and 393 × 852 (right). The settled design for the build is `../../design/workbench-look.md`.

Sources: the story (`../../story-11-c1-the-workbench-look.md`, the seven canvas criteria and the "Parked and Restore" artboard), the charter (`../../current-phase-status.md`, fork 1 "All the way"), the grounding (`docs/internal/philo/phase-13/grounding/faces-jobs.md` §3, before-shots `grounding/shots/surfaces/01-chair-pop-1440.png`, `01-chair-pop-393.png`, `64-room-pop-1440.png`), A1's story (`../../story-02-a1-park-never-delete.md`), `docs/internal/UX-CANON.md`.

## Round two: Muad'Dib's read (2026-10-01)

| Muad'Dib | The canvas now |
|---|---|
| 1 Draw the FIXED Desk: one meaning of "needs you" (story 03, A2) | The Chair's membership (R1 ranked rows + R2 blockers + R3 failed summaries) is the one number: the Chair head, the bell and the Dock's Intelligence and Desk memory icons all read **8** on every board (fact `needs_you`, `(8, 8, 8, 8)` on all 29). The capped list says what it counts: `ACTIONS 5 OF 7` (was `NEEDS YOU 5 OF 7`). Meetings says its narrower count: `All summaries done` (was `Nothing needs you`). The Room says its own: `Clear here`, `OPEN HERE`, `Nothing open` (was `Nothing needs you`). A fence fails a board if any `need(s) you` on the glass is not the Chair's number (the Chair window's name `Needs you` aside) or if the bell or the Dock disagrees. |
| 2 No scratch paths in content | The FILE destination is seeded inside the scratch HOME at `Documents/HoldSpeak/Team updates` and named `Team updates`; the face reads `~/Documents/HoldSpeak/Team updates`, the way the product already shows a home folder as `~` (`web/src/features/channels/channels.ts:347`; the canvas maps its scratch HOME the same way). A fence fails a board that shows `/tmp`, `/private/tmp` or `p13c1-`. |
| 3 The 393 shelf clips an icon | The shelf ends on a whole icon: the daily seats first (Intelligence 8, Meetings REC 12:04, People 1:1 14:30, Payments ledger 3), each 85 px, then a 48 px `More AppIcons` gadget (▸) fixed at the right edge that moves one page; the shelf snaps to whole icons. A fence fails a 393 board if an icon is cut by the edge or the gadget (C1-6a: none cut). At 1440 the icons are 66 px at least, so C1-1 fits with no scroll. |
| In passing: C1-2b's menu covered the front window's title | The right button now lands on the drag bar just past the title; `Payments ledger cutover` stays readable beside the menu. |

Changed boards: every board (the needs-you words, the bell and Dock numbers and the path are on every Desk board); visibly C1-1, C1-2a–d, C1-4a–b, C1-5a–f, C1-6a–b, C1-7 (both widths) and C1-2b (the menu place).

## The recommendation: Workbench Steel

Workbench 2.0's four pens, kept as roles: grey = the frame, black = every line and every word on the frame, white = the screen bar and the menus, blue = the front window. Every window gets the 2.0 gadget set (close at the left; iconify, zoom, depth at the right; the sizing gadget at the bottom right), a striped drag bar, a 4 px frame and a hard drop. The body of every window stays the dark Signal well, so the 19 `DeskWindowFrame` hosts read as they do today, inside a Workbench frame. The Chair is a Workbench screen of four windows. The Dock is a shelf of AppIcons that carry live state.

**The one alternative (board C1-7): Honest 2.0** — the four pens on every body too (grey bodies, black text). It is the most literal Amiga. It costs contrast on inherited body colours: on the Chair at 1440 the contrast scan finds 8 texts under 4.5:1 (lowest 1.56:1, the ember display on grey) against 2 for Steel: the ember `--accent` display on `--surface-1` at 4.26:1 (26 px, large text) and an inherited `Add` primary at 3.79:1, tokens this material does not change (not measured on main) (`shots/facts.json`, `_cmp_*`).

## The boards

| Board | Shows | Criteria |
|---|---|---|
| C1-1 the Desk | screen title bar naming the front window + time; the Chair as four windows; the AppIcon shelf with REC, 1:1 and project counts | 2, 3, 4, 7 |
| C1-2a window gadgets | Meetings + the Payments ledger Room (real hosts): one gadget set each; ONE front window | 1, 2, 3 |
| C1-2b window menu | right button on the title bar: the window's menu with the Amiga-key column; Desk ▸ open | 1, 5 |
| C1-2c depth | depth pressed: the Room goes behind; the screen bar follows | 1, 2 |
| C1-2d zoom (1440) | zoom pressed: the window fills the work band | 1 |
| C1-3 material | the tokens and the species that wear them, read back from the live `:root` | 3, 5 |
| C1-4a / C1-4b the Chair | Needs you, Brief, The week, Capture: the Arrival's real sections in windows; a window zoomed (1440) / opened (393) | 4 |
| C1-5a–f Parked and Restore | Meetings: Park → `PARKED <time>` + Restore → the `PARKED 1` filter → restored; the Workbench window: Remove parks the item, the filter | A1-F |
| C1-6a / C1-6b the phone (393) | one line of screen bar; one Chair window open, the rest title bars; one-row shelf; a window as a sheet with 44 px gadgets | 6 |
| C1-7 comparison | Steel vs Honest 2.0, the Chair and two windows | — |

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs` against a REAL hub (`scripts/graph_walk.py serve`) on `HOME=tempfile.mkdtemp(dir="/tmp")`, removed when the run ends. Each width runs on its own hub and HOME.
- **The seed:** the Phase 13 grounding seed (`harness/seed_db.py`, from `grounding/probes/faces-surfaces-seed.py.txt`, with Priya Nair as the peer): three projects, four meetings with summaries, Avery Chen, Jordan Patel and Sam Rivera as reports with 1:1s and requests, two decisions, a brief; then through the real routes a Workbench with four items and a FILE destination `Team updates` at `~/Documents/HoldSpeak/Team updates` inside the HOME (`harness/rig.py`).
- **The seats** (`vite.config.mjs`, the `SEATS` table): each product file the look touches gets one named hook into `harness/p13.tsx` at a named anchor. A missing or doubled anchor stops the server. Files: `DeskWindow.tsx` (the gadget set, the head menu), `DeskChrome.tsx` (the screen title; the bell reads the one needs-you number), `ChairHome.tsx` (the Arrival's sections routed into windows; publishes its needs-you count; the `ACTIONS` caption), `window/Dock.tsx` (AppIcon state and icons; the needs-you badges), `HistoryCore.tsx` and `WorkbenchWindow.tsx` (Park, the PARKED filter and receipt), `history/helpers.ts` (`All summaries done`), `ProjectRoomCore.tsx` (`Clear here`, `OPEN HERE`), `features/channels/channels.ts` (the scratch HOME read as `~`). The guard line of the run: `PHILO-13-11 SEAT GUARD: 9 files, 12 seats, every anchor met` (`shots/facts.json`, `_seat_guard_*`).
- **The material:** `harness/canvas.css`, injected last; each section names the product file the build moves it into.
- **The stand-ins** (stated in `p13.tsx`'s header): the depth gadget reorders `panelOrder` in the harness (C2 builds it); `REC 12:04`, `1:1 14:30` and the project counts are fixed values (C3 reads them from the bus; A3 makes REC honest); Park and Restore keep the parked set in the harness and send no request (H-A1 builds the routes); the real Delete is never called. The one needs-you number is the Chair's own count, published by the harness to the bell and the Dock (H-A2's `needsYou.ts` is what the build reads).
- **One front window:** the product marks two windows `is-front` today (grounding `faces-surfaces.md:219`). The canvas marks the one top window (`data-p13-front`), and the screen title reads its name from the same mark, so the bar cannot disagree with the glass.

## Measurements (`shots/facts.json`; the default run, both widths, exit 0)

- 29 boards + the comparison; fences: `ALL FENCES HELD` (`shots/run.log`), both widths, each on its own hub and HOME, both HOMEs removed.
- One needs-you number on every board: Chair head, bell, Dock Intelligence, Dock Desk memory = 8, 8, 8, 8 (29 of 29). No `/tmp` path on any board.
- Every window on every board: one close at the left, one depth at the right, one zoom at 1440; the old traffic lights never visible: **147 window observations**.
- Gadgets probed at nine points each: **448**; every gadget on top owns its points; at 393 every gadget is 44 × 44 px.
- The screen title names the front window on every board; the clock is on every board.
- The Dock box stays inside the viewport on every board (left 0, right = width). C1-1 at 1440 fits with no scroll. With windows open at 1440 the shelf scrolls inside itself (C1-2a–d, C1-5a–f: their window chips); nothing leaves the screen (red on main: −35 to 1475). At 393 the shelf ends on whole icons (fact `shelf`: `cut` empty; whole: Intelligence, Meetings, People, Payments ledger cutover; More 48 × 63 px).
- The phone frame (C1-6a): screen bar 28 px + shelf 68 px = **96 px** (C7's budget 142); the open window 579 px.
- Text under 12 px in the proposal: **0**. Raw `<button>` in the proposal: **0**. Inherited, not changed here: the Chair's ranking tokens and row details at 11 px (`RANKED`, `DUE TODAY`, `DOOR`, `4 WORDS`, …: C8's sweep); the EgressChip species and the Workbench `Run` chip are raw buttons.
- Modals 0; horizontal overflow 0; browser errors 0; no counter of zero (no `PARKED` token until something is parked).
- Contrast of the pens: ink on steel 7.81:1, ink on blue 5.40:1, ink on paper 17.12:1, REC on paper 5.73:1, text on the ember ink 5.24:1.
- The run fails if the page reloads during a board (a fence; a cold vite server re-optimizes on the first lazy window, so the run warms every window first).

## Reproduce

```bash
# from the worktree root; both widths, each on its own hub and HOME (removed when it ends)
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright npm_config_cache=$HOME/.npm \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/shoot.py
python3 pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/build_review.py
```

`harness/dev.py` holds one stack up for design iteration (`STACK_STATE=` reuses it); it is not part of the proof.

## Questions for the owner

1. **The direction:** Workbench Steel (grey frame, blue front window, dark bodies) or Honest 2.0 (grey bodies too)? **Recommended: Steel.**
2. **Park is one press:** no confirm, because Restore undoes it (Tenet 1). **Recommended: yes.**
3. **The Chair's fourth window, Capture:** the capture bar becomes a window, not a bar over the content. **Recommended: yes.**
