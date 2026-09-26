# PHILO-8-02 — one delete everywhere: the reds, the repair, the decisions

Lane: Fedaykin (Opus 5.5) for Muad'Dib, 2026-09-26. Branch `feat/philo-8-02-one-delete` from main `267f692a`.

## Where the reds ran

A `git archive origin/main` copy in the lane's scratchpad, with `uv sync --extra test` and a real `npm ci --ignore-scripts && npm run build`. The archive holds origin/main `26f7b005`. That is `267f692a` plus PR #669 (PHILO-8-04, the decision window's empty headings). #669 does not touch any file of the delete path (`git diff --stat 267f692a 26f7b005`: `DecisionPullout.tsx`, `surface.css`, docs, tests). Each glass case boots a real `MeetingWebServer` on an isolated HOME and reads the hub (`GET /api/decisions/{id}`). No test double.

## The reds on main (verbatim, from the files in this folder)

| Fence | Red on main | File |
|---|---|---|
| The list's Delete: row menu, Delete key, palette, at 1440 and 393 | `Page.wait_for_function: Timeout 5000ms exceeded.` (no receipt; no DELETE request) | `red-main-glass.log`, `red-main-palette.txt` |
| Undo on the list | the same timeout (no receipt, so there is no Undo) | `red-main-glass.log` |
| The receipt on a long list (20 rows) at 393, scrolled to the end | the same timeout | `red-main-glass.log` |
| Two deletes, Floor, A left selected (cause 1), 1440 and 393 | `AssertionError: ({'A': 404, 'B': 200}, '1 SELECTED', 'Removed Probe A …'` | `red-main-two-deletes-serial.txt` |
| Two deletes, Floor, A taken out first (cause 2), 1440 and 393 | `AssertionError: ({'A': 200, 'B': 404}, '', 'Removed Probe B …'` | `red-main-glass.log` (serial reruns: `red-main-two-deletes-serial.txt`) |
| Two deletes on the list, both orders | `AssertionError: B came after A's window: ''` (the list shows no receipt for A) | `red-main-two-deletes-serial.txt` |
| Undo keeps only the pending object | `Page.wait_for_function: Timeout 5000ms exceeded.` waiting for "Removed Probe B" (B's Delete is ghosted: cause 1) | `red-main-leave-chair-undo-serial.txt` |
| Leave the Floor inside the window (cause 3), 1440 and 393 | `AssertionError: (200, [])` (200, zero DELETE requests) | `red-main-leave-chair-undo-serial.txt` |
| Leave the list inside the window | the receipt timeout (the list never queued it) | `red-main-leave-chair-undo-serial.txt` |
| The Delete key on the Chair with a selection left from the Floor | `AssertionError: (200, [])` | `red-main-leave-chair-undo-serial.txt` |
| Vitest: the hook's flush, the Workbench window's Remove, the listener module | 6 failed, and `Failed to resolve import "../deleteReceipt"` | `red-main-vitest.txt` |

The two-delete probe checks that it is still inside A's window before B's Delete ("Removed Probe A" must be on the receipt). Without that check, a slow run can press B after A committed and pass on main. The first parallel run saw this once (`floor-a_taken_out-1440` passed on main under load).

## The repair

- `web/src/desk/hooks/useUndoReceipt.ts`: a pending removal is never dropped. A second `remove()` commits the pending one first (`flush()`); an unmount commits a pending one; `undo()` clears it. The receipt keeps one slot. `flush` is returned.
- `web/src/desk/deleteReceipt.tsx` (new): `DeskDeleteHost` holds the ONE `OBJECT_DELETE_REQUEST` listener and the ONE hook. It takes the queued object out of `selectedIds` (cause 1). `DeskDeleteSeat` is the receipt where a face seats it. When the last seat unmounts (a face change), a pending delete commits. A delete asked for where no seat is mounted (the Chair) commits at once.
- `web/src/desk/DeskApp.tsx`: mounts `DeskDeleteHost` once. It survives every face change.
- `web/src/desk/gl/WorldStage.tsx`: the listener and the hook are gone; the foot seats `DeskDeleteSeat` above the AskBar.
- `web/src/desk/components/DeskListView.tsx`: the AskBar is wrapped in the Floor's foot (`.desk-world-foot`) with `DeskDeleteSeat` above it (#665 seat).
- `web/src/desk/components/list-view.css`: on the list the foot is `position: fixed`. The list grows with the page and the page scrolls. With the Floor's `position: absolute` the receipt sat at the bottom of the list's content, not of the viewport (M4 below: `y 1565` at 393 with a viewport height of 852).

`grep -rn OBJECT_DELETE_REQUEST web/src` after the repair: the constant and the dispatch (`verbRegistry.ts`), the one listener (`deleteReceipt.tsx`), and the tests.

## The lane's decisions (recorded, not owner questions)

1. **One slot.** A second delete commits the first at once and takes its Undo away (the Astra-role ruling, RULING (5)).
2. **A face change commits.** When no face seats the receipt, no Undo is in reach, so a pending delete commits right away. Floor → list is a face change too (the seat leaves and comes back in one commit), so a pending delete commits there as well, and the list shows "Removal committed".
3. **The Chair.** The keymap is global, so a selection left from the Floor reaches the Chair. On main, the Delete key there sent nothing (200). Now the one listener takes it. The Chair has no receipt seat, so the delete commits at once and nothing on the Chair shows it. That is honest to the key, but the face is silent. A seat on the Chair is a face change (canvas first), so it goes to the BACKLOG ("PHILO-8-02 follow-ups").
4. **The Workbench window** (the same hook) changes on purpose: a second Remove commits the first at once, and closing the window commits a pending Remove. Before, both dropped the removal without a word; the footer said "Removed" and the item stayed. Undo is unchanged. Fenced in `web/src/desk/components/__tests__/workbenchUndoFlush.test.tsx`.

## The list's delete paths (recorded)

The row menu (right-click, or `ContextMenu` / `Shift+F10`), the Delete key after Space selects the row, and the palette's `Delete` verb with a row selected. All three are fenced at 1440 and 393. `list-paths-probe.txt` shows the palette offers `desk-palette-option-object.delete` on the list, and the delete reaches the hub (404).

## FINDING S2 (measured)

At 393 the row menu's Delete row is cut at the bottom edge: `{'top': 839, 'bottom': 867, 'vh': 852}` (15 px below the viewport) for a row near the top of a one-item list. At 1440: `{'top': 847, 'bottom': 875, 'vh': 900}` (inside). It reproduces at 393. BACKLOG row filed; not repaired here (story 02 Out).

## The mutations (each cause restored turns its fence red)

`mutations-glass.txt` (glass, real hub) and the vitest rows below.

- M1 (cause 1, the selection drop removed): glass `({'A': 404, 'B': 200}, '1 SELECTED', 'Removed Probe A …'`; vitest `takes the queued object out of the selection (cause 1)` fails.
- M2 (cause 2, `remove()` no longer flushes): glass `({'A': 200, 'B': 404}, '', 'Removed Probe B …'`; vitest 4 fail (the hook's two, the listener's, the Workbench window's).
- M3 (the seat flush and the hook's unmount flush removed, the host still hoisted): glass PASSES. That was the wrong mutation: with the listener hoisted, the timer keeps running after a face change, so the hoist alone repairs cause 3. It is recorded, not hidden.
- M3b (cause 3 restored: the host mounts only on the Floor faces, `{showFloor && <DeskDeleteHost />}`, and nothing commits on the way out): glass `floor 1440: 200; DELETE 0`, both leave-face cases at 1440 fail; vitest 4 fail.
- M4 (the list foot's `position: fixed` removed): the long-list fence fails, `'Removed': not in the viewport: {… 'y': 1565 …}`.
