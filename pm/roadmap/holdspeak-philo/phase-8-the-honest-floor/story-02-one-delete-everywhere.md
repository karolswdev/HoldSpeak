# PHILO-8-02 - One delete everywhere

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter (no canvas: the list reuses the #665 seat)
- **Unblocks:** PHILO-8-03
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 final summary, THE LEDGER rows 3–4; `docs/internal/philo/phase-7/floor-diag/FINDING.md` Finding 2; `../phase-7-the-desk-on-the-contract/checks/delete-receipt-astra-role-r1.md` F7; `checks/charter-astra-role-r1.md` F2, F3, F7 and RULING (5); BACKLOG "PHILO-7-03 follow-ups" row 3 and "The Floor delete receipt follow-ups" row 1
- **Canvas:** none. The list wraps its AskBar and the receipt in the same foot class as the Floor (`.desk-world-foot`, `web/src/desk/desk.css:208-238`), the seat the owner ratified in #665

## Problem

**The list Delete.** `object.delete` does not delete; it dispatches `OBJECT_DELETE_REQUEST` (`web/src/desk/verbRegistry.ts:559-564`). The only listener, and the only undo receipt, are in `WorldStage` (`web/src/desk/gl/WorldStage.tsx:56`, `:138-152`, the seat `:343-348`). `WorldStage` never mounts with `DeskListView` (`web/src/desk/DeskApp.tsx:192-207`). On the list at 1440 and 393 the row menu shows an enabled Delete with a keycap; pressing it sends no request, shows no receipt, and the object stays (FINDING Finding 2). UX-CANON §A.11: a verb that does nothing is a lie.

**Deletes that do not happen: three VERIFIED causes** (reproduced by the Astra-role check through the real hub on main, `checks/charter-astra-role-r1.md` F2):

1. **The deleted object stays selected.** The listener queues the delete but does not take the object out of the selection (`WorldStage.tsx:138-149`). Selecting B then makes 2 selected; `keyContext()` passes no target when 2 are selected (`web/src/desk/keymap.ts:71-74`); `object.delete` ghosts, and `dispatchKey` refuses quietly (`keymap.ts:84`). Result: A 404, B 200; B's delete is never sent, and the receipt reads "Removed Probe A" throughout.
2. **A second queued delete drops the first.** With the selection right, `remove()` calls `cleanup()` first (`web/src/desk/hooks/useUndoReceipt.ts:27`), which clears A's timer, so A's `fire` never runs. Result: A 200, B 404. The face said "Removed Probe A"; the hub keeps A.
3. **Leaving the face drops the pending delete.** The hook runs `cleanup` on unmount (`useUndoReceipt.ts:23`), and `WorldStage` unmounts on every face change (`DeskApp.tsx:192-207`). Delete A on the Floor, go to the Chair inside the window: A 200, zero DELETE requests.

The Floor's no-op `revert` (`WorldStage.tsx:147`) is not a cause: only `undo()` calls it.

## Scope

- **In (the repair shape, ruled by the Astra-role check, RULING (5)):**
  - The first delete COMMITS when a second is queued: `remove()` fires the pending `fire` before it replaces the state. A delete is never dropped.
  - A pending delete COMMITS on a face change: either the hook flushes a pending `fire` on unmount, or the listener and the hook move to one always-mounted place (for example `DeskApp`). Either way it is ONE listener that survives a face change; "one handler mounted on each face" is not enough, because it carries cause 3 to the list.
  - The queued object leaves the selection (`selectedIds`), so the next select-and-Delete targets only the next object.
  - The receipt keeps ONE slot: a second delete commits the first at once and takes its Undo away. This is the lane's decision, recorded in the evidence; it is not an owner question.
  - The list reuses the Floor's receipt seat by wrapping its AskBar (`web/src/desk/components/DeskListView.tsx:340`; placed by itself today, `.desk-askbar` `position: absolute; bottom: 84px`, `web/src/desk/components/mission-control.css:285-289`) and the receipt in the same foot class. No canvas.
  - A record of which delete paths the list offers (row menu, Delete key, palette); a measure of FINDING S2 (the Delete row cut at the bottom edge at 393), with a BACKLOG row if it reproduces.
- **Check list (the other users of the hook, under the flush semantics):** the Workbench window (`web/src/desk/components/WorkbenchWindow.tsx:38`, `:968` — the same `useUndoReceipt`); its remove, undo and unmount behaviour is fenced unchanged or changed on purpose, and recorded.
- **Out:** a new receipt species; hiding the object during the window (a face change; not needed once it leaves the selection); the Workbench footer linger (BACKLOG "The Floor delete receipt follow-ups" row 2); F8, the receipt moving when the AskBar leaves; the Chair plus a stale selection plus the Delete key (read from code by the check, not exercised) — the lane exercises it, and the always-mounted listener covers it if it reproduces.

## Acceptance criteria

- [ ] The list Delete (every path the list offers) removes the object: "Removed … Undo", then "Removal committed", `readable_text` in the viewport at 1440 and 393; `GET` the object → 404 after the window; Undo inside the window → 200 and the row stays. Red on main (no request, 200).
- [ ] At 393 with a long list (more than 16 objects) scrolled to the end, the receipt is still readable in the viewport (the list's AskBar is placed on its own; the #665 fence proved only a page that does not scroll).
- [ ] Two deletes in one window, on the spatial Floor and on the list, with both selection orders of the check's probe (A left selected; A taken out first): A 404 and B 404 after the window. Red on main (A 404 / B 200, and A 200 / B 404).
- [ ] Leave the face inside the window (Floor → Chair, list → Chair): the object is gone (404). Red on main (200, zero requests).
- [ ] Undo inside the window keeps the one pending object (200); a delete already committed by a second delete stays gone.
- [ ] Each of the three causes has a mutation that restores it and turns its fence red.
- [ ] One listener, one hook mount: `grep -rn OBJECT_DELETE_REQUEST web/src` shows one handler, and it survives a face change.
- [ ] The Workbench window's delete and Undo behave as recorded (fenced).
- [ ] `case.p7.decision_delete.gone` (`docs/internal/philo/graph/atlas-phase7.json`) still passes at 1440 and 393.
- [ ] Shots at 1440 and 393.

## Effort (not a promise)

PROVISIONAL: 0.75–1.25 engineering days of effort (calibrated from Phase 7's record, `checks/charter-astra-role-r1.md` F11).

## Test plan

- **Unit (vitest):** `useUndoReceipt` with two `remove()` calls in one window (the first fires at once); unmount with a pending delete (it fires); the listener removes the ref from `selectedIds`; the Workbench window's use of the hook.
- **Integration (glass, the real hub, isolated HOME):** the FINDING's Finding 2 reproduction at 1440 and 393; the check's three probes (`checks/charter-astra-role-r1.md` F2) on the Floor and on the list; the long-list scroll at 393.
- **Web baseline:** `uv run python scripts/check_web_baseline.py --run`, zero branch-new (read vitest's `Errors` line, handover XXIX law 1); every `scripts/philo_*.py --check` exits 0 before push.

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib from the owner's word closing Phase 7; unratified.
- 2026-09-26 — round two: the Astra-role check (`checks/charter-astra-role-r1.md`, RATIFY-WITH-CONDITIONS) paid: C1 the three verified causes replace the guesses, and the false sentence "the face said B was removed" is struck; C2 the repair shape (flush, not drop; one listener that survives a face change; the selection drop; one receipt slot; the list's foot seat; the Workbench window checked); C5 the long-list receipt at 393.
