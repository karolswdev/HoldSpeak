# Astra role (Opus 5.5 stand-in, owner ruling 2026-09-25) — CHECK on built, PR #665 @ 9fa8dda8

VERDICT: RATIFY-WITH-CONDITIONS on MERGE (the conditions are backlog items, not blockers).

Rig: `git archive origin/main` (3d3f1748) and `git archive 9fa8dda8`, each extracted to scratchpad; real `npm ci --ignore-scripts && npm run build` in each copy (both exit 0); `uv sync --extra test --extra meeting` in each; every run used an isolated `HOME=$(mktemp -d)` + `PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright`. The worktree was not touched (`git status` clean, HEAD 9fa8dda8).

## FINDINGS

F1 (claim 1, reproduced). The glass fence is red on main and green on the branch.
- main (fence copied in): `2 failed in 45.46s`
  `AssertionError: 'Removed': not in the viewport: {'x': 1055.71875, 'y': -12, 'w': 372.28125, 'h': 27}` (1440)
  `AssertionError: 'Removed': not in the viewport: {'x': 8.71875, 'y': -12, 'w': 372.28125, 'h': 27}` (393)
- branch: `2 passed in 71.57s`
  `1440: pending {x 533.9, y 698, w 372.3, h 27} committed {x 650.9, y 748} shown 6388 ms`
  `393: pending {x 12, y 598, w 369, h 27} committed {x 127.4, y 676} shown 6081 ms`

F2 (claim 2). Taking `desk-next` off the wrapper removes nothing the receipt needs. The receipt still renders inside the `#desk-next` root (`web/src/desk/DeskApp.tsx:178`), so every `.desk-next .undo-receipt*` rule (`web/src/desk/surface/surface-footer.css:152-215`) still matches. Computed styles, main compared with the branch at 1440x900 (probe):
- label 11px rgb(155,162,176) / committed rgb(139,147,163); Undo button 13px; time 10px rgb(139,147,163). The two are IDENTICAL.
- The only change is the receipt ground: main `rgba(255,255,255,0.035)`, branch `rgb(28,31,39)` (`--surface-2`, `desk.css:236-238`). The text colours on that ground come to about 7:1 and 5.9:1 by my estimate (computed from the RGB, not measured with a tool).
- The 11px label and 10px time are under a 12px floor, but main has the same sizes. Nothing new. I did not find a `.desk-next .surface-state-chip` floor that applies to `.undo-receipt`.

F3 (claim 3). No test or face depended on 1.2 s or 1.6 s. `grep -rn "1200|1600|Removal committed"` across every file that names `useUndoReceipt`/`undo-receipt` finds only the hook and the new fence. Workbench effect: the footer's priority chain `writeReceipt || undoReceipt || copyReceipt || status` (`web/src/desk/components/WorkbenchWindow.tsx:1893-1897`) now hides the "N ITEMS · last run" status for 6 s after a delete, not 1.2 s. For those 6 s it also hides a Copy receipt that happens in the same window. The copy still runs; only its receipt does not show. This is a minor change in behaviour and does not block.

F4 (claim 4). The move from z 60 to z 30 did not put anything over the receipt. On the branch at every probed size, `elementFromPoint` gave 9/9 for both phases (the fence). The dock is z 80 fixed, but the foot is lifted clear of it: at 393x700 the dock top is 575 and the AskBar bottom is 503. Floor objects draw on the GL canvas (z 0). The rename row and lasso sit at 25 (`tokens.css:247`), and the mic sits fixed at z 20 in the bottom-left corner. None of these covers the foot. With 40 decisions on the Floor (1440 and 393x700) the page does not scroll (`scrollH == innerHeight`), so the absolute foot stays in the viewport. A consequence the owner has already accepted: the opaque receipt now covers Floor object labels in the row behind it. At 1440 with 40 items it covers the "Probe decision 31" row. At 393 it sits on the tile being deleted. The AskBar already covers the same row.

F5 (claim 5). One baseline run on the branch was clean: `Suite totals: 2873 passed, 0 failed, 0 skipped` / `VERDICT: baseline-subset, zero branch-new` (HEALED 5). The two intermittent failures did not come back, so I cannot name them.

F6 (claim 6). The phone lift works. `--desk-dock-h` = 125px at 393 (53px at 1440), and the foot inherits it.
- 393x900: receipt y 598-625, AskBar 633-703, dock 775.
- 393x700: receipt y 398-425, AskBar 433-503, dock 575.
- 393x600: receipt y 298-325, AskBar 333-403, dock 475.
At every size there is no overlap and everything stays in the viewport.

F7 (new, pre-existing on main, outside this PR). Two Floor deletes inside one 8 s window lose one of the deletes without a word. Probe: select+Delete decision A, wait 1.5 s, select+Delete decision B, wait 12 s, then GET both.
- branch `{"decision_a11e69fa08e8": 404, "decision_2fdcb41e0e28": 200}`
- main `{"decision_35e36cf6898e": 404, "decision_b705e353e8e5": 200}`
The second decision is still on the server. Where I think it comes from: `remove()` calls `cleanup()` and drops the earlier pending `fire` (`web/src/desk/hooks/useUndoReceipt.ts:27-29`), and the Floor's `revert` is a no-op (`web/src/desk/gl/WorldStage.tsx:144-148`). I have not confirmed why A commits and B is the one lost; see UNKNOWN.

F8 (cosmetic). When the AskBar leaves, the receipt moves. At 393 the committed receipt drops 78px (598 to 676) when the selection clears. Whether the AskBar is still there when "Removal committed" appears is a race. At 1440 it showed "1 SELECTED" (for the deleted object) in 1 of 1 branch runs, but 0 of 1 on main at n1 and 1 of 1 at n40. The same race exists on main, so this PR did not cause it.

## CONDITIONS
C1. Put F7 in the backlog: a second delete inside the undo window must commit (or keep) the first one, never drop it without a word. The bug is on main already; this PR does not have to fix it.
C2. Optional: take the Workbench footer's 6 s linger (F3) to the next Workbench sitting. It follows the one-constant law, so it is a note, not a bounce.

## MISSED
- F7 (above). No fence covers two deletes inside one window.
- The fence does not check an open window over the receipt, which is the stated design, and it does not check a short phone height. My probe covered 393x700 and 393x600.

## TUESDAY
The owner deletes a decision on the Floor and now reads "Removed … Undo 07s" above his selection, then "Removal committed" for 6 s, at both widths. On main he saw nothing. If he deletes two decisions quickly, one of them comes back (F7, pre-existing).

## UNKNOWN
- F7 mechanism: why the first delete commits and the second does not (not traced; one guess is that the selection still holds A when Delete is pressed on B).
- The atlas case `case.p7.decision_delete.gone` (on the PHILO-7-03 branch) was not re-run here.
- The earlier intermittent 2 baseline failures (did not recur in one run).
