# PHILO-13-11 (C1) close: board beside shot, on main

Every C1 board in `../story-11-canvas/shots/` (ratified 2026-10-02, "Ratify, build it", "Steel") is shot again on the real product. Base: main `23a6c137f` (with #730, C2, C8, #744 and #750 merged). Real hub, isolated HOME, 1440 x 900 mouse and 393 x 852 touch. The shots are in `shots/`, named for the board they answer.

Sources of the shots:

- The glass tests: `tests/e2e/test_philo13_11_frame_glass.py`, `test_philo13_11_chair_glass.py`, `test_philo13_12_gadgets_glass.py`, `test_philo13_13_dock_glass.py`, `test_philo13_02_park_glass.py`.
- `shoot_close.py` (this folder): the Chair states that no glass test shoots (C1-4b, C1-4d at 393, C1-4e). It re-uses the Chair glass rig and its fences.
- The atlas walks `case.p13.dock.send_failed`, `case.p13.dock.send_unknown` and `case.p13.dock.needs_you_week` (`docs/internal/philo/graph/atlas-phase13-astra.json`), one case per run, at both widths. All six pass (`dock-walks.txt`).

The seed is not the canvas seed in every rig. Counts (`7 need you`, `ACTIONS 5 OF 6`) and rows differ from the boards for that reason; this is not a face difference. The rigs file to a scratch HOME, so a FILE destination shows that scratch path where the canvas drew `~/…` (known since slice two of the build).

## The boards

| Board | Shot | Result |
|---|---|---|
| `C1-1-the-desk-1440` | `shots/C1-1-the-desk-1440.png` | MATCH |
| `C1-1-the-desk-393` | `shots/C1-1-the-desk-393.png` | MATCH with the later ratified C7-1 board (story 17, owner 2026-10-03). The screen bar carries the switcher `▾` and Search, so the name reads `Need…`. Home: PHILO-13-17 (ratified there) |
| `C1-2a-window-gadgets-1440` | `shots/C1-2a-window-gadgets-1440.png` | MATCH |
| `C1-2a-window-gadgets-393` | `shots/C1-2a-window-gadgets-393.png` | MATCH |
| `C1-2b-window-menu-amiga-keys-1440` | `shots/C1-2b-window-menu-amiga-keys-1440.png` | MATCH (the submenu opens to the left at the screen edge) |
| `C1-2b-window-menu-amiga-keys-393` | `shots/C1-2b-window-menu-amiga-keys-393.png` | MATCH |
| `C1-2c-depth-to-back-1440` | `shots/C1-2c-depth-to-back-1440.png` | MATCH |
| `C1-2c-depth-to-back-393` | `shots/C1-2c-depth-to-back-393.png` | MATCH |
| `C1-2d-zoom-1440` | `shots/C1-2d-zoom-1440.png` | DEVIATION on main, FIXED here. See F1 |
| `C1-2e-strip-menu-open-393` | `shots/C1-2e-strip-menu-open-393.png` | MATCH |
| `C1-3-material-tokens-1440` / `-393` | none | NOT A STATE: the specimen sheet. The tokens are fenced in `web/src/desk/__tests__/workbenchFrame.test.tsx:59-85` |
| `C1-4a-chair-windows-1440` | `shots/C1-4a-chair-windows-1440.png` | MATCH |
| `C1-4a-chair-windows-393` | `shots/C1-4a-chair-windows-393.png` | MATCH |
| `C1-4b-chair-window-zoomed-1440` | `shots/C1-4b-chair-window-zoomed-1440.png` | DEVIATION on main, FIXED here. See F1. Zoom now fills the screen (design §5, board C1-2d) |
| `C1-4b-chair-week-open-393` | `shots/C1-4b-chair-week-open-393.png` | MATCH |
| `C1-4c-chair-window-closed-1440` | `shots/C1-4c-chair-window-closed-1440.png` | MATCH |
| `C1-4c-chair-window-closed-393` | `shots/C1-4c-chair-window-closed-393.png` | MATCH |
| `C1-4d-window-menu-chair-1440` | `shots/C1-4d-window-menu-chair-1440.png` | MATCH |
| `C1-4d-window-menu-chair-393` | `shots/C1-4d-window-menu-chair-393.png` | MATCH. Each open window has a check. In this walk all three are open, so Brief has a check too |
| `C1-4e-chair-window-reopened-1440` | `shots/C1-4e-chair-window-reopened-1440.png` | DEVIATION, OPEN. See O1. Home: fix/philo-13-b0-reds (same seam), else BACKLOG |
| `C1-4e-chair-window-reopened-393` | `shots/C1-4e-chair-window-reopened-393.png` | MATCH |
| `C1-5a-meeting-selected-park-1440` / `-393` | `shots/C1-5a-…-{1440,393}.png` | MATCH (story 02 glass) |
| `C1-5b-meeting-parked-receipt-1440` / `-393` | `shots/C1-5b-…` | MATCH |
| `C1-5c-meetings-parked-filter-1440` / `-393` | `shots/C1-5c-…` | MATCH |
| `C1-5d-meeting-restored-1440` / `-393` | `shots/C1-5d-…` | MATCH |
| `C1-5e-meeting-restore-failed-1440` / `-393` | `shots/C1-5e-…` | MATCH |
| `C1-5f-workbench-item-parked-1440` / `-393` | `shots/C1-5f-…` | MATCH |
| `C1-5g-workbench-parked-filter-1440` / `-393` | `shots/C1-5g-…` | MATCH |
| `C1-5h-workbench-item-restored-1440` / `-393` | `shots/C1-5h-…` | MATCH |
| `C1-5i-workbench-claimed-refused-1440` / `-393` | `shots/C1-5i-…` | MATCH |
| `C1-5j-workbench-clear-done-parked-1440` / `-393` | `shots/C1-5j-…` | MATCH |
| `C1-6a-phone-desk-393` | `shots/C1-6a-phone-desk-393.png` | MATCH |
| `C1-6b-phone-window-sheet-393` | `shots/C1-6b-phone-window-sheet-393.png` | MATCH |
| `C1-7-comparison-1440` / `-393` | none | NOT A STATE: Steel against Honest 2.0. The owner ruled Steel |
| `C1-8a-dock-ready-and-sent-1440` / `-393` | `shots/C1-8a-…-{ready,sent}.png` | MATCH, one state for each shot. The canvas drew all the states on one shelf |
| `C1-8b-dock-send-failed-unknown-1440` / `-393` | `shots/C1-8b-…-{failed,unknown}.png` | MATCH. `SEND FAILED` and `UNKNOWN` are on Intelligence, the icon the send left from (design §6). The board drew them on Meetings |
| `C1-8c-dock-offline-1440` | `shots/C1-8c-dock-offline-1440.png`, `…-outage-receipt.png` | DEVIATION on main, FIXED here. See F2 |
| `C1-8c-dock-offline-393` | `shots/C1-8c-dock-offline-393.png`, `…-outage-receipt.png` | MATCH |

Total: 52 boards. 44 match on main. 4 do not show a product state (C1-3 and C1-7, both widths). 3 deviated on main and are fixed here (C1-2d-1440, C1-4b-1440, C1-8c-1440). 1 is open (C1-4e-1440).

Out-of-board deviations, by Muad'Dib's note. The fix/philo-13-b0-reds lane has them; this close did not observe them or fix them:

- B0-F3, `repository.window` at 1440. Home: fix/philo-13-b0-reds.
- `roadmap.window` opens again off the screen. Home: fix/philo-13-b0-reds.

## Fixes (faces lane, red then green)

**F1: zoom fills the screen.** On main a zoomed window took the shell work band: top 54 px (the screen bar ends at 28) and bottom 52 px. The C3-W shelf is 76 px high, so the foot and the sizing gadget were under the Dock. The zoomed state could not be resized, and `G2 the zoomed state resizes` was red on main. Fix: `web/src/desk/components/DeskWindow.tsx:835-842`. The top is `var(--wb-screen-h)` and the bottom is the shelf's measured `--desk-dock-h`. Fence: `tests/e2e/test_philo13_12_gadgets_glass.py:250-266`. It checks that the head is flush under the bar, the foot is clear of the Dock, and the sizing gadget owns its point. Red on main: `red-zoom-band-main-23a6c137f-1440.txt` (`top 54, bottom 848, dock_top 824, grip_owned false`). Green: `green-gadgets-after-fix.txt`. `close-facts-1440.json` `zoom-geometry` gives `Brief [10, 28, 1430, 824]`, `dock [0, 824, …]` and `owns: true`.

**F2: the screen bar stays one line under an outage receipt.** On main, at 1440, `READ MEETINGS FAILED · HUB UNREACHABLE` + Retry/OK in the bar pushed the clock plate below the bar (top 24, bottom 42, bar 28), onto the windows. Fix: `web/src/desk/components/chrome-menus.css:686-704` (1440 only; 393 has its own row). The status cluster does not wrap. The receipt seat is a flex box, so its label can shorten while its verbs keep their size. Fence: `tests/e2e/test_philo13_13_dock_glass.py:324-336`. Red on main: `red-screen-bar-wrap-main-23a6c137f.txt`. Green: `green-dock-frame-after-fix.txt`. A cost to know: at 1440 with a long front-window name, the receipt label now ends in an ellipsis (`HUB UNREACH…`). The exact words stay in the DOM text; the fence reads them.

## Open

**O1 (C1-4e-1440):** a Chair window that you close and then open again comes back at the top of the shell work band (`--desk-work-top` 54 px, `web/src/styles/tokens.css:259-261`, read by `workBand()` in `web/src/desk/components/window/windowGeometry.ts:24`). Its tile place is 42 px, so it shows 12 px lower than on the board. Design §2 says the work band starts at the screen bar. This change moves every window's open and clamp band. fix/philo-13-b0-reds is working on the same placement seam, so this close did not change it. Home: fix/philo-13-b0-reds, else BACKLOG.

## The seven criteria

| # | Criterion | Proof |
|---|---|---|
| 1 | One gadget set on every window: close, depth, zoom | `DeskWindow.tsx:959` close, `:979` iconify, `:988` zoom, `:1000` depth, `:524` sizing. Fences: frame glass F2 (`test_philo13_11_frame_glass.py:131`), `workbenchFrame.test.tsx:116-136`, gadget glass G1 to G4 |
| 2 | The screen title bar names the front window and the time | `DeskChrome.tsx:96-107` (ScreenTitle). Fences: frame glass F1 (`:122`), Chair glass C2, `workbenchFrame.test.tsx:184-204` |
| 3 | One material as tokens on every DeskWindowFrame host | `web/src/styles/tokens.css:336-352` (`--wb-*`), `:101` (`--accent-text`). Fence: `workbenchFrame.test.tsx:85` (every host uses the `--wb-*` frame) |
| 4 | The Chair is windows, not one scrolling page | `web/src/desk/chair/ChairDesk.tsx:44` (DeskWindowFrame), `chairWindows.ts:29-30`. Fence: Chair glass C1 (four windows, tiled, `:153`), C3 (close and reopen), C4 (393, one at a time) |
| 5 | 12 px floor and library Buttons throughout | `tests/unit/test_philo13_18_type_floor_static.py:91-122`, `tests/e2e/test_philo13_18_type_floor_glass.py` (every state at both widths), frame glass F5, `tests/unit/test_ux_canon_ratchet.py:61-136` (raw buttons ratchet and hard zeros) |
| 6 | Both widths | Every board above at 1440 and 393. Frame glass F4 (393: content 700 px or more, targets 44 x 44), Chair glass C4, `test_philo13_17_phone_desk_glass.py` |
| 7 | Live state on the AppIcons, no status window | `web/src/desk/components/window/Dock.tsx:416` (1:1), `:504` (count, never zero), `:521-524` (SEND FAILED / FAILED), `:436` (OFFLINE · AS OF), `:568` (project count only when not zero). Fences: `test_philo13_13_dock_glass.py` (READY, SENT, REC on confirmation only, OFFLINE), the three dock walks (failed, unknown, needs-you week), `Dock.test.tsx:196-260` (1:1) |

## Runs (isolated HOME, PLAYWRIGHT_BROWSERS_PATH set)

- On main before the fixes: `glass-run-main-23a6c137f.txt`. Result: 1 failed (`test_gadgets_1440`, G2), 70 passed.
- After the fixes: `glass-run-final.txt`. Result: 71 passed. The run had the frame, Chair, gadget, Dock, type-floor (glass and static), the readers, park and phone suites, plus the shared `test_philo13_c3_dock`, `test_philo13_c3_ready`, `test_ux_canon_ratchet` and `test_philo13_muaddib_atlas`.
- Web unit: `web-baseline.txt`. Result: 3209 passed, zero branch-new.
- `shoot_close.py`: 2 passed (both widths).

## Not verified

- The `1:1 hh:mm` tag on People and a project AppIcon with a count are not on glass in any rig here. They are fenced in unit tests only (`Dock.test.tsx:196`).
- The owner's own browser and screen, and a real touch device (393 uses a touch-enabled viewport).
- The atlas walks ran before F1 and F2. Neither fix touches the Dock states that they shoot.
