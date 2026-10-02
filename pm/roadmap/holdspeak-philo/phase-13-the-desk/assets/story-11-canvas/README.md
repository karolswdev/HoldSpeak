# PHILO-13-11 (C1) canvas: the Workbench look

**Status: DRAFT, round 3d (Astra canvas r3: the overlap waivers narrowed to their exact relationships, with a mutation proof; the boards are unchanged), for Astra's re-check and the owner's ratification** (UX-CANON §A.2: the canvas before the build). Round three pays Astra's check r1 DO-NOT-RATIFY on `1467d9173` (`/Users/karol/dev/tools/HoldSpeak/.tmp/two-brains/20261001-203130-check-p13-canvas-r1/last.md`) with Muad'Dib's rulings R1–R8. Nothing here is built in product code. Every change lives under `harness/`. The review page is `index.html` in this folder: every board at 1440 × 900 (left) and 393 × 852 (right). The settled design for the build is `../../design/workbench-look.md`.

Sources: the story (`../../story-11-c1-the-workbench-look.md`), the charter (`../../current-phase-status.md`, fork 1 "All the way"), the grounding (`docs/internal/philo/phase-13/grounding/faces-jobs.md` §3; before-shots `grounding/shots/surfaces/01-chair-pop-1440.png`, `01-chair-pop-393.png`, `64-room-pop-1440.png`), A1 (`../../story-02-a1-park-never-delete.md`), A2 (`../../story-03-a2-one-meaning-of-needs-you.md`), C3 (`../../story-13-c3-a-live-dock.md`), C7 (`../../story-17-c7-the-phone-desk.md`), `docs/internal/UX-CANON.md`.

## Measurements (generated from `shots/facts.json`, `shots/run.log` and the red-before files by `harness/build_review.py`; never typed by hand)

<!-- generated:measurements:begin -->
| Measure | Value |
|---|---|
| Verdict of this run (`shots/run.log`) | ALL FENCES HELD; EXIT 0 |
| Seat guard (both widths) | PHILO-13-11 SEAT GUARD: 12 files, 16 seats, every anchor met |
| Boards | 50 (24 at 1440, 26 at 393) + the C1-7 comparison |
| Window observations (one gadget set each) | 159 |
| Frame-control observations / lost points | 1294 / 0 |
| Boards with exactly one blue title bar | 50 of 50 |
| Boards whose intended front window is the recorded one, on the glass | 47 of 47 that name one |
| Texts under 4.5:1 (3:1 large), in place | 0 |
| Texts under 12 px | 0 |
| 393: the front window's content (px) | 704 |
| 393: targets under 44 × 44 | 0 on 26 boards |
| Sideways-scrolling strips / clipped texts | 0 / 0 |
| Rendered overlaps | 0 |
| Overlap waivers used (each its exact relationship) | mic: 6 pairs (Item body / Speak Item body); more: 26 pairs (Payments ledger cutover, 3 n / More AppIcons); sticky: 3 pairs (SINCE YOU LOOKED / Ask this project) |
| Mutation proof (injected near misses, each must be CAUGHT) | a_sticky at 1440: CAUGHT (Clear here / MUTANT A); b_mic at 1440: CAUGHT (New item instruction / Speak Item body); c_more at 393: CAUGHT (More AppIcons / STRAY TEXT) |
| Ellipsis lines (recorded, allowed by A.6) | `Check reconciliation timings`, `Draft rollback runbook`, `Ledger cutover bench`, `Material · Workbench Steel`, `Payments ledger cutover`, `Rerun shard benchmark` |
| Needs-you numbers (head, bell, Intelligence, Desk memory) | ('not on the glass', 8, 8, 8) on 5 boards; (8, 8, 8, 8) on 45 boards (the Chair head is off the glass when a window fills the 393 work area) |
| Active projects missing from the Dock / zero badges | 0 / 0 |
| Browser errors | 0 |

Red before, round two: `shots/red-before-r2.json`, 8 boards red.

Red before, round three: `shots/red-before-r3.json`, 28 boards red of 28 measured.

Red before, round 3b (`e23ce53d`): `shots/red-before-r3b.json`, 4 boards red of 50 measured.
<!-- generated:measurements:end -->

## Round 3d: Astra canvas r3 (`/Users/karol/dev/tools/HoldSpeak/.tmp/two-brains/*-p13-canvas-r3/last.md`): the waivers, exactly

The rendered-overlap fence (`harness/shoot.py`, `OVERLAP`) waives a pair ONLY by one of three relationships, each a named function, each waived pair recorded (`overlap_waived` in `shots/facts.json`; summary in the generated block):

- **(a) sticky** (`waiveSticky`): one element is in a sticky or fixed bar of its window; the other is that window's scrolling content passing beneath it. Fixed bar: the other element's scroll container is its ancestor and NOT the bar's. Sticky bar: CSS makes a sticky bar stick INSIDE its scroll container, so the rule is that the bar sticks to the other element's scroll container, the other element is not in the bar, and the overlap lies inside the bar's box.
- **(b) mic** (`waiveMic`): an input or textarea and a mic button whose nearest common ancestor is that field's wrapper (its parent or grandparent), the wrapper holds no other text field, and the mic's box is inside the input's box.
- **(c) More** (`waiveMore`): the Dock's More gadget and an AppIcon of the same shelf that begins left of More and runs on under it.

**The mutation proof** (`MUTATE`; facts `_mutation_1440`, `_mutation_393`; the boards are shot before it runs and it removes what it injected): three near misses, one per waiver, each must be CAUGHT. (a) a Button that lives in the Room's sticky Ask bar, moved over a body row that is NOT beneath the bar; (b) a mic button placed over a DIFFERENT text field of the Workbench window (no shared field wrapper); (c) a stray text element of the shelf placed under More (not an AppIcon). The result is in the generated block. Red before for the boards stays `shots/red-before-r3b.json`.

## Round 3c: Astra canvas r2 (`/Users/karol/dev/tools/HoldSpeak/.tmp/two-brains/*-p13-canvas-r2/last.md`)

| Astra r2 | The canvas now |
|---|---|
| 1 C1-5a-393: the `NO SUMMARY ROUTE · NO ASSIGNMENT` warning ran under `MD` / `SRT` | The footer at 393 is two rows by explicit grid areas: the egress chip, then the receipt and the verbs (round three's rule set columns but kept the inherited one-row areas, so it never took). **New fence: rendered overlap** — no two visible interactive or text elements of one window (or bar, shelf, menu) intersect by more than 2 × 2 px where the glass at the centre shows one of them, a parent and its descendant excepted. Three waivers, narrowed to their exact relationships in round 3d (above). The fence also found the Dock's state tag sitting on its count (`SENT 14:02` over `8`, 1440) and `SEND FAILED` running into the next icon (393): at 1440 the tag takes the icon's top-left and the count its top-right; at 393 the Meetings tag reads `FAILED` (the icon's name says Meetings). Red before: `shots/red-before-r3b.json` (`e23ce53d`'s harness, fence code identical). |
| 2 Stale proof text | Every count is generated (the block above). The ranking-strip and wings rules in `harness/canvas.css` no longer scroll and their comments say so; the stale R3 line is corrected below; the design doc carries no totals and points here. |

## Round 3b: nothing clips, nothing scrolls sideways (Muad'Dib's ruling; HS-200-12 stands)

Every strip of choices (the window tabs and the Chair's ranking filters):

- **1440:** a strip must fit. The ranking strip has its own line in the Needs-you window; `● 9 OF 9 AVAILABLE`, `CHECKED …` and the calendar state wrap to the next line, off the strip (C1-1).
- **393:** a strip that does not fit is ONE library menu Button in its row, with the current choice and ▾ (`RANKED ▾`, `OUTCOMES ▾`), 44 px tall; it opens the DeskMenu species with every choice and a check on the current one; a gear door joins after a separator (C1-2e: the Meetings tabs menu open; C1-6a: `RANKED ▾`). A strip that fits stays a strip (the Room's ROOM · HISTORY). The canvas draws "does not fit" as "more than two choices at 393"; the build measures it. Seats: `web/src/desk/surface/FilterTokens.tsx`, `web/src/desk/surface/wings.tsx`.
- Also paid: the 393 title bar's −4 px frame overlap (the window was 397 px wide); the phone mark's word (it was clipped; it now rides only the accessible name); the material sheet at 393 (it was 476 px wide).

**The fence (new): no horizontally scrolling element, and no text node whose box runs past its clipping ancestor or spills out of its own control.** Ellipsis truncation of a single line (`text-overflow: ellipsis`, UX-CANON A.6 "titles shrink first") is recorded, not failed; the Dock is outside the rule by name (the AppIcon shelf, paged by More at 393).

| | Round three (`_r3harness/`: this harness with the 3b CSS block and the two 3b seats removed; fence code identical) | Round 3b |
|---|---|---|
| Boards red | **28 of 28 measured** (`shots/red-before-r3.json`). C1-1-1440: the ranking row scrolled (1153 px in 658) and clipped `9 OF 9 AVAILABLE`, `CHECKED JUST NOW`, `NO CALENDAR`, `Connect calendar`. C1-2c-393: `NOT RUN`, `9 OF 9 AVAILABLE`, the Meetings tab `Artifacts` and the mark's `HoldSpeak` clipped; the Chair 397 px in 393. The replica's 393 run stops at C1-2e (round three had no strip menu to open), so C1-6a-393 itself was not measured there; its `NOT R` is the same ranking strip that is red on C1-1/C1-2a–c-393 | the generated block |
| Ellipsis (recorded, allowed) | — | the list is in the generated block |

## Round three: Astra r1 + Muad'Dib's rulings

| Ruling / finding | The canvas now | Boards |
|---|---|---|
| **R1 one window lifecycle** (Astra 4) | Close CLOSES a Chair window; depth sends it back; two gadgets, two functions. A closed Chair window comes back from `Window ▸ Chair` (393: `Go ▸ Chair`), which lists Needs you / Brief / The week / Capture with a check on each open one; at 1440 the Chair's screen holds one compact reopen Button where the window was. | C1-4c, C1-4d, C1-4e |
| **R2 the phone is one window at a time** (Astra 2) | No stack of bars (round 3b: strips that do not fit are menu Buttons). One window fills the work area: screen bar 44 + window head 44 + shelf 56 leaves the content the generated block reports (C7: ≥ 700). Switch from the Dock or `Go ▸ Chair`. Capture is on demand (the Speak AppIcon is a daily seat; the pop-key is C6). Every target at 393 owns a 44 × 44 box: the screen bar's controls, the head's gadgets and wings, the shelf's icons, the menu rows, the body's controls. The first `Done` is whole on the first screen. The Meetings footer: egress on its own row (round 3c made it hold: see above). | C1-6a, C1-6b, every 393 board |
| **R3 steroids where it counts** (Astra missed 1) | The first screen leads with the work: `8 need you`, the ranking strip on its own line and whole (393: `RANKED ▾`, round 3b), then `ACTIONS 5 OF 7`; SETUP drops below the actions. The Brief window is taller: SEND and `Team updates` are on the first screen at 1440. | C1-1 |
| **R4 one front window** (Astra 5) | Exactly one blue title bar on every board (fenced). The inherited `.is-front` head (`web/src/desk/components/window-chrome.css:337`) is neutralised at the canvas layer by `.desk-window-shell.is-front:not([data-p13-front]) > .desk-pullout-head` (canvas.css, "ROUND THREE"). | C1-2a–d, all |
| **R5 contrast where hosts use it** (Astra 5) | `--desk-window-head-fill` and `--gadget-fill` are no longer re-pointed to steel: body strips wear them (People's `.surface-verbs` read `--text-muted` on steel at 1.02:1). Every word in a title bar is ink. Ember TEXT uses a new `--accent-text` (#bc8058, 5.43:1; `--accent` text read 4.26:1). The inherited 10–11 px texts are drawn at 12 px (`.arrival-source-emblem`, `.arrival-why-token`, `.surface-filter-token`, `.surface-disclosure-*`, `.meetings-stream-fact`, `.meetings-stream-compact-facts`, `.transcript-speaker`, `.surface-ledger-remainder-count`, `.wb-workspace-path`, the menu ghost hint). Contrast is measured IN PLACE on every board, every text node. | C1-6b, C1-1, all |
| **R6 outcomes** (Astra 6, 8) | Restore: `RESTORED hh:mm` and the row comes into view, marked. Restore refused: `NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE` + Retry. Claimed by a run: `NOT PARKED · CLAIMED BY A RUN`. Workbench Restore. Bulk park: `Clear done` → `PARKED 2 · hh:mm` + Restore. C3 states on the icons: `READY 1`, `SENT 14:02`, `SEND FAILED`, `UNKNOWN`, and disconnected: `OFFLINE · AS OF 20:24` heads the shelf, no tag or count claims freshness. Every active project keeps its AppIcon; Staff hiring has no count and no badge. | C1-5a–j, C1-8a–c, C1-1 |
| **R7 honest comparison** (Astra 7) | Round two's Honest 1.56:1 headline came from the alternative's own `--accent` override (blue-on-grey, canvas.css), not from grey bodies. Round three makes Honest a complete palette (every text tone ≥ 4.5:1 on its greys): on the Chair, two windows and People, both directions now measure **0** texts under the threshold. The recommendation is Steel for coherence and preference, not contrast. | C1-7 |
| **R8 fences that fail on these defects** (Astra 3) | Below, each with its red on the round-two boards. | — |

### R8: the fences, red before, green after

Red before = round two's harness (`1467d9173`, copied unchanged into `_r2harness/`, measured by round three's fence code with `_r2harness/red.py`; result `shots/red-before-r2.json`). Green after = this run (`shots/facts.json`, `shots/run.log`).

| Fence | Red on round two | Green now |
|---|---|---|
| Ownership: every one of nine points of each frame control is that control's (or under a window in front) | `Close Meetings`, `To back Meetings`, `Close/To back Payments ledger cutover` own 6/9 at 1440 (the resize edge took their outer column); `Close People`, `To back People`, `ROOM` 6/9 at 393 | see the generated block |
| Visible state: the intended front window is the recorded front window, on the glass | C1-6a-393: intended `Needs you`, recorded `Ledger cutover bench`, not on the glass | see the generated block (C1-4c-1440 and C1-4d name no single front window: a menu or a closed window) |
| Exactly one blue title bar | C1-2a: `Meetings` and `Payments ledger cutover` both blue (1440 and 393); C1-6a-393: none | see the generated block |
| In-place contrast ≥ 4.5:1 (≥ 3:1 large) | `DUE TODAY`, `NO DUE DATE · UNASSIGNED` 4.26 (1440, 393); `8 need you` 4.26 at 22 px (393); `Encrypted`, `Local storage`, `Notes only` 1.02 and `Manual` 3.08 (C1-6b-393) | see the generated block |
| 393: the front window's content ≥ 700 px | 530 (C1-1), 560 (C1-2a), 0 (C1-3: the sheet was blank), 639 (C1-6a), 469 (C1-6b) | see the generated block |
| 393: no target under 44 × 44 | the screen bar: `HoldSpeak` 30 × 22, `Go` 31 × 26, the egress chip 26 × 22, the bell 59 × 22, `Search` 32 × 22; `Manual` 69 × 27 | see the generated block |
| No active project missing from the Dock | round two drew a project only while its count was not zero: Staff hiring absent (C1-1). The red file lists all three because round two's icons carry no `data-project`; the defect on the glass is Staff hiring | see the generated block |
| No zero badge | not red on round two (no zero was drawn); kept as the guard for the rule above | 0 |

"ALL FENCES HELD" in `shots/run.log` means every fence above held on every board at both widths, plus the earlier ones: one gadget set, the screen bar names the front window and shows the time, no text under 12 px on the whole board, one needs-you number, no scratch path, no modal, no horizontal overflow, the Dock in the viewport, the 393 shelf ends on a whole icon, no page reload during a board, (3b) no strip scrolls sideways and no text clips, and (3c) no rendered overlap.

## The recommendation: Workbench Steel

Workbench 2.0's four pens as roles: grey = the frame, black = every line and word on the frame, white = the screen bar and menus, blue = the ONE front window. Every window wears the 2.0 gadget set, a striped drag bar, a 4 px frame and a hard drop; its body stays the dark Signal well, so the 19 `DeskWindowFrame` hosts read as they do today. The Chair is a Workbench screen of windows; the Dock is a shelf of AppIcons with live state.

**The alternative, Honest 2.0** (C1-7): the four pens on every body too. With its palette completed, it meets the same contrast. Steel is recommended for coherence (the hosts keep their dark material and every ember and state colour) and preference. Steel's limits, stated: under the inherited `--accent` the large `8 need you` headline reads 4.26:1 (large text: 3:1 passes) and round two's `Add` primary read 3.79:1 (small text: fails). Round three draws ember text on `--accent-text` (5.43:1) and every filled verb on `--accent-ink` (5.24:1); in place, no text on any board is under its threshold. The build must adopt both tokens (tokens.css, global.css).

## The boards

| Board | Shows |
|---|---|
| C1-1 the Desk | the one front window named; the work first; the Brief's SEND on the first screen; 8 = 8 = 8 = 8; every project's AppIcon |
| C1-2a–e window gadgets | the gadget set on real hosts; the right-button menu with Amiga keys; depth; zoom (1440); the strip menu open (393) |
| C1-3 material | the tokens and species, read from the live `:root`; at 393 the sheet fills the work area |
| C1-4a–b the Chair as windows | 1440: four windows, one zoomed; 393: one window at a time |
| C1-4c–e lifecycle (R1) | close closes; the reopen Button; `Window ▸ Chair` with checks; reopened |
| C1-5a–j Parked and Restore (A1-F) | Park, PARKED, the filter, RESTORED in view, Restore refused, the Workbench item parked / filter / restored, claimed by a run, Clear done |
| C1-6a–b the phone (393) | one window, 704 px of content, first Done whole, 44 px targets; People at 393 |
| C1-8a–c C3 states | ready + sent; failed + unknown; disconnected |
| C1-7 comparison | Steel vs Honest 2.0 in three states |

## What the boards are, exactly

- **The app:** the PRODUCT app (`web/`), served by vite with `harness/vite.config.mjs` against a REAL hub (`scripts/graph_walk.py serve`) on `HOME=tempfile.mkdtemp(dir="/tmp")`, removed when the run ends. Each width runs on its own hub and HOME.
- **The seed:** the Phase 13 grounding seed (`harness/seed_db.py`, Priya Nair as the peer), then through the routes (`harness/rig.py`) a Workbench with five items (two DONE, for Clear done) and a FILE destination `Team updates` at `~/Documents/HoldSpeak/Team updates`.
- **The seats** (`vite.config.mjs`): one named hook per anchor in each product file below (the count is in the guard line); a missing or doubled anchor stops the server. Guard line: in the generated block. Files: `DeskWindow.tsx`, `DeskChrome.tsx`, `DeskMenuBar.tsx` (Window ▸ Chair), `ChairHome.tsx`, `window/Dock.tsx`, `HistoryCore.tsx`, `WorkbenchWindow.tsx` (Park, bulk Clear done), `history/helpers.ts`, `ProjectRoomCore.tsx`, `features/channels/channels.ts`, `surface/FilterTokens.tsx` and `surface/wings.tsx` (the strip menu).
- **The rehearsal:** each width walks every board once with no shot, then draws the boards on a fresh page (a cold vite server re-optimizes on a lazy window and reloads; a fence fails any board drawn across a reload).
- **The stand-ins** (stated in `p13.tsx`): depth reorders `panelOrder` (C2); the AppIcon tags and project counts are fixed values (C3; A3 makes REC honest); Park, Restore, the refused Restore and the claimed refusal keep their state in the harness and send no request (H-A1); the one needs-you number is the Chair's own count published to the bell and Dock (H-A2's `needsYou.ts`); the Chair windows are canvas windows, not yet `DeskWindowFrame` hosts (the C1 build).

## Inherited raw buttons, assigned

Measured on the boards (`shots/facts.json`, `raw_buttons`); each repaired by its owning story, none hidden:

| Raw button | Where | Owner |
|---|---|---|
| `Remove`, `Dismiss` (`desk-chip quiet`) | Workbench item card (`WorkbenchWindow.tsx`) | A1-F (Remove becomes the Park verb there) |
| `▸ Run · Bind an agent first` (`desk-chip`) | Workbench title bar actions | C8 |
| `Add` (`desk-chip is-primary`), `P3` (`wb-priority-cycle`), `No agent · Manual ▾` (`wb-config-strip`), the item heads (`wb-card-head`) | Workbench window | C8 |
| `⌂ THIS DEVICE` (EgressChip, `gadget-chip`) | screen bar | C8 (the species, `web/src/desk/surface/gadgets.tsx`) |

## Limits

- The strip menu's "does not fit" is drawn as "more than two choices at 393"; the build measures the fit.
- At 1440 the shelf scrolls inside itself when window chips join it (C1-2a–d, C1-5); nothing leaves the screen.
- Not verified: the owner's browser; a real touch device (393 is a touch-enabled viewport); the right button at 393 (a long-press on a device).

## Reproduce

```bash
# from the worktree root; both widths, each on its own hub and HOME (removed when it ends); ~20 minutes
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright npm_config_cache=$HOME/.npm \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/shoot.py
python3 pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/harness/build_review.py
# red before: round two's harness measured by round three's fences
PLAYWRIGHT_BROWSERS_PATH=$HOME/Library/Caches/ms-playwright \
  .venv/bin/python pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/_r2harness/red.py
```

`harness/dev.py` holds one stack up for iteration (`STACK_STATE=`, `NO_REHEARSE=1` on a warm stack); it is not part of the proof.

## Questions for the owner

1. **The direction:** Workbench Steel or Honest 2.0? **Recommended: Steel.**
2. **Park is one press:** no confirm; Restore undoes it. **Recommended: yes.**
3. **Capture:** a window at 1440; on demand at 393 (Speak, the pop-key). **Recommended: yes.**
