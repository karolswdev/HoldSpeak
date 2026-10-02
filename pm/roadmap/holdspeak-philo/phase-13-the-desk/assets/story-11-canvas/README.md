# PHILO-13-11 (C1) canvas: the Workbench look

**Status: DRAFT, round 3b (round three + Muad'Dib's ruling on strips), for Astra's re-check and the owner's ratification** (UX-CANON §A.2: the canvas before the build). Round three pays Astra's check r1 DO-NOT-RATIFY on `1467d9173` (`/Users/karol/dev/tools/HoldSpeak/.tmp/two-brains/20261001-203130-check-p13-canvas-r1/last.md`) with Muad'Dib's rulings R1–R8. Nothing here is built in product code. Every change lives under `harness/`. The review page is `index.html` in this folder: every board at 1440 × 900 (left) and 393 × 852 (right). The settled design for the build is `../../design/workbench-look.md`.

Sources: the story (`../../story-11-c1-the-workbench-look.md`), the charter (`../../current-phase-status.md`, fork 1 "All the way"), the grounding (`docs/internal/philo/phase-13/grounding/faces-jobs.md` §3; before-shots `grounding/shots/surfaces/01-chair-pop-1440.png`, `01-chair-pop-393.png`, `64-room-pop-1440.png`), A1 (`../../story-02-a1-park-never-delete.md`), A2 (`../../story-03-a2-one-meaning-of-needs-you.md`), C3 (`../../story-13-c3-a-live-dock.md`), C7 (`../../story-17-c7-the-phone-desk.md`), `docs/internal/UX-CANON.md`.

## Round 3b: nothing clips, nothing scrolls sideways (Muad'Dib's ruling; HS-200-12 stands)

Every strip of choices (the window tabs and the Chair's ranking filters):

- **1440:** a strip must fit. The ranking strip has its own line in the Needs-you window; `● 9 OF 9 AVAILABLE`, `CHECKED …` and the calendar state wrap to the next line, off the strip (C1-1).
- **393:** a strip that does not fit is ONE library menu Button in its row, with the current choice and ▾ (`RANKED ▾`, `OUTCOMES ▾`), 44 px tall; it opens the DeskMenu species with every choice and a check on the current one; a gear door joins after a separator (C1-2e: the Meetings tabs menu open; C1-6a: `RANKED ▾`). A strip that fits stays a strip (the Room's ROOM · HISTORY). The canvas draws "does not fit" as "more than two choices at 393"; the build measures it. Seats: `web/src/desk/surface/FilterTokens.tsx`, `web/src/desk/surface/wings.tsx`.
- Also paid: the 393 title bar's −4 px frame overlap (the window was 397 px wide); the phone mark's word (it was clipped; it now rides only the accessible name); the material sheet at 393 (it was 476 px wide).

**The fence (new): no horizontally scrolling element, and no text node whose box runs past its clipping ancestor or spills out of its own control.** Ellipsis truncation of a single line (`text-overflow: ellipsis`, UX-CANON A.6 "titles shrink first") is recorded, not failed; the Dock is outside the rule by name (the AppIcon shelf, paged by More at 393).

| | Round three (`_r3harness/`: this harness with the 3b CSS block and the two 3b seats removed; fence code identical) | Round 3b |
|---|---|---|
| Boards red | **28 of 28 measured** (`shots/red-before-r3.json`). C1-1-1440: the ranking row scrolled (1153 px in 658) and clipped `9 OF 9 AVAILABLE`, `CHECKED JUST NOW`, `NO CALENDAR`, `Connect calendar`. C1-2c-393: `NOT RUN`, `9 OF 9 AVAILABLE`, the Meetings tab `Artifacts` and the mark's `HoldSpeak` clipped; the Chair 397 px in 393. The replica's 393 run stops at C1-2e (round three had no strip menu to open), so C1-6a-393 itself was not measured there; its `NOT R` is the same ranking strip that is red on C1-1/C1-2a–c-393 | **0 strips, 0 clipped texts on all 50 boards** |
| Ellipsis (recorded, allowed) | — | window titles in a narrow title bar: `Ledger cutover bench` (10), `Payments ledger cutover` (2), `Material · Workbench Steel` (1); Workbench item titles in the item card: `Draft rollback runbook`, `Rerun shard benchmark`, `Check reconciliation timings` |

## Round three: Astra r1 + Muad'Dib's rulings

| Ruling / finding | The canvas now | Boards |
|---|---|---|
| **R1 one window lifecycle** (Astra 4) | Close CLOSES a Chair window; depth sends it back; two gadgets, two functions. A closed Chair window comes back from `Window ▸ Chair` (393: `Go ▸ Chair`), which lists Needs you / Brief / The week / Capture with a check on each open one; at 1440 the Chair's screen holds one compact reopen Button where the window was. | C1-4c, C1-4d, C1-4e |
| **R2 the phone is one window at a time** (Astra 2) | No stack of bars (round 3b: strips that do not fit are menu Buttons). One window fills the work area: screen bar 44 + window head 44 + shelf 56 → **704 px of content** on 852 on every 393 board. Switch from the Dock or `Go ▸ Chair`. Capture is on demand (the Speak AppIcon is a daily seat; the pop-key is C6). Every target at 393 owns a 44 × 44 box: the screen bar's controls, the head's gadgets and wings, the shelf's icons, the menu rows, the body's controls. The first `Done` is whole on the first screen. The Meetings footer no longer overlaps (egress on its own line). | C1-6a, C1-6b, every 393 board |
| **R3 steroids where it counts** (Astra missed 1) | The first screen leads with the work: `8 need you`, the ranking strip on ONE line (it scrolls inside itself), then `ACTIONS 5 OF 7`; SETUP drops below the actions. The Brief window is taller: SEND and `Team updates` are on the first screen at 1440. | C1-1 |
| **R4 one front window** (Astra 5) | Exactly one blue title bar on every board (fenced). The inherited `.is-front` head (`web/src/desk/components/window-chrome.css:337`) is neutralised at the canvas layer by `.desk-window-shell.is-front:not([data-p13-front]) > .desk-pullout-head` (canvas.css, "ROUND THREE"). | C1-2a–d, all |
| **R5 contrast where hosts use it** (Astra 5) | `--desk-window-head-fill` and `--gadget-fill` are no longer re-pointed to steel: body strips wear them (People's `.surface-verbs` read `--text-muted` on steel at 1.02:1). Every word in a title bar is ink. Ember TEXT uses a new `--accent-text` (#bc8058, 5.43:1; `--accent` text read 4.26:1). The inherited 10–11 px texts are drawn at 12 px (`.arrival-source-emblem`, `.arrival-why-token`, `.surface-filter-token`, `.surface-disclosure-*`, `.meetings-stream-fact`, `.meetings-stream-compact-facts`, `.transcript-speaker`, `.surface-ledger-remainder-count`, `.wb-workspace-path`, the menu ghost hint). Contrast is measured IN PLACE on every board, every text node. | C1-6b, C1-1, all |
| **R6 outcomes** (Astra 6, 8) | Restore: `RESTORED hh:mm` and the row comes into view, marked. Restore refused: `NOT RESTORED · THE HUB DID NOT ACCEPT THE CHANGE` + Retry. Claimed by a run: `NOT PARKED · CLAIMED BY A RUN`. Workbench Restore. Bulk park: `Clear done` → `PARKED 2 · hh:mm` + Restore. C3 states on the icons: `READY 1`, `SENT 14:02`, `SEND FAILED`, `UNKNOWN`, and disconnected: `OFFLINE · AS OF 20:24` heads the shelf, no tag or count claims freshness. Every active project keeps its AppIcon; Staff hiring has no count and no badge. | C1-5a–j, C1-8a–c, C1-1 |
| **R7 honest comparison** (Astra 7) | Round two's Honest 1.56:1 headline came from the alternative's own `--accent` override (blue-on-grey, canvas.css), not from grey bodies. Round three makes Honest a complete palette (every text tone ≥ 4.5:1 on its greys): on the Chair, two windows and People, both directions now measure **0** texts under the threshold. The recommendation is Steel for coherence and preference, not contrast. | C1-7 |
| **R8 fences that fail on these defects** (Astra 3) | Below, each with its red on the round-two boards. | — |

### R8: the fences, red before, green after

Red before = round two's harness (`1467d9173`, copied unchanged into `_r2harness/`, measured by round three's fence code with `_r2harness/red.py`; result `shots/red-before-r2.json`). Green after = this run (`shots/facts.json`, `shots/run.log`).

| Fence | Red on round two | Green now |
|---|---|---|
| Ownership: every one of nine points of each frame control is that control's (or under a window in front) | `Close Meetings`, `To back Meetings`, `Close/To back Payments ledger cutover` own 6/9 at 1440 (the resize edge took their outer column); `Close People`, `To back People`, `ROOM` 6/9 at 393 | 1294 control observations, 0 lost points |
| Visible state: the intended front window is the recorded front window, on the glass | C1-6a-393: intended `Needs you`, recorded `Ledger cutover bench`, not on the glass | 47 of 47 boards that name one (the three menu/closed boards name none: C1-4c-1440, C1-4d at both widths) |
| Exactly one blue title bar | C1-2a: `Meetings` and `Payments ledger cutover` both blue (1440 and 393); C1-6a-393: none | 50 of 50 |
| In-place contrast ≥ 4.5:1 (≥ 3:1 large) | `DUE TODAY`, `NO DUE DATE · UNASSIGNED` 4.26 (1440, 393); `8 need you` 4.26 at 22 px (393); `Encrypted`, `Local storage`, `Notes only` 1.02 and `Manual` 3.08 (C1-6b-393) | 0 texts on 50 boards |
| 393: the front window's content ≥ 700 px | 530 (C1-1), 560 (C1-2a), 0 (C1-3: the sheet was blank), 639 (C1-6a), 469 (C1-6b) | 704 on every 393 board |
| 393: no target under 44 × 44 | the screen bar: `HoldSpeak` 30 × 22, `Go` 31 × 26, the egress chip 26 × 22, the bell 59 × 22, `Search` 32 × 22; `Manual` 69 × 27 | 0 on 26 boards |
| No active project missing from the Dock | round two drew a project only while its count was not zero: Staff hiring absent (C1-1). The red file lists all three because round two's icons carry no `data-project`; the defect on the glass is Staff hiring | 3 of 3 projects on every board |
| No zero badge | not red on round two (no zero was drawn); kept as the guard for the rule above | 0 |

"ALL FENCES HELD" in `shots/run.log` means every fence above held on every board at both widths, plus the earlier ones: one gadget set, the screen bar names the front window and shows the time, no text under 12 px on the whole board, one needs-you number, no scratch path, no modal, no horizontal overflow, the Dock in the viewport, the 393 shelf ends on a whole icon, no page reload during a board, and (3b) no strip scrolls sideways and no text clips.

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
- **The seats** (`vite.config.mjs`): 10 product files, 14 seats; a missing or doubled anchor stops the server. Guard line of this run: `PHILO-13-11 SEAT GUARD: 12 files, 16 seats, every anchor met` (both widths). Files: `DeskWindow.tsx`, `DeskChrome.tsx`, `DeskMenuBar.tsx` (Window ▸ Chair), `ChairHome.tsx`, `window/Dock.tsx`, `HistoryCore.tsx`, `WorkbenchWindow.tsx` (Park, bulk Clear done), `history/helpers.ts`, `ProjectRoomCore.tsx`, `features/channels/channels.ts`, `surface/FilterTokens.tsx` and `surface/wings.tsx` (the strip menu).
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
