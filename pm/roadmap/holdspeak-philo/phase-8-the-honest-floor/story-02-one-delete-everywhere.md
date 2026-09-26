# PHILO-8-02 - One delete everywhere

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** backlog
- **Depends on:** the owner's ratification of the charter (no canvas unless the list cannot use the #665 seat)
- **Unblocks:** PHILO-8-03
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 final summary, THE LEDGER rows 3–4; `docs/internal/philo/phase-7/floor-diag/FINDING.md` Finding 2; `../phase-7-the-desk-on-the-contract/checks/delete-receipt-astra-role-r1.md` F7; BACKLOG "PHILO-7-03 follow-ups" row 3 and "The Floor delete receipt follow-ups" row 1
- **Canvas:** none if the list's receipt sits in the seat the owner ratified in #665 (directly above the AskBar); a small canvas otherwise

## Problem

**The list Delete.** `object.delete` does not delete; it dispatches `OBJECT_DELETE_REQUEST` (`web/src/desk/verbRegistry.ts:559-564`). The only listener, and the only undo receipt, are in `WorldStage` (`web/src/desk/gl/WorldStage.tsx:56`, `:137-152`, the seat `:343-348`). `WorldStage` never mounts with `DeskListView` (`web/src/desk/DeskApp.tsx:192-206`). On the list at 1440 and 393 the row menu shows an enabled Delete with a keycap; pressing it sends no request, shows no receipt, and the object stays (FINDING Finding 2). UX-CANON §A.11: a verb that does nothing is a lie.

**Two deletes in one window.** Delete A, wait 1.5 s, delete B, wait 12 s: A 404, B 200, on main (`delete-receipt-astra-role-r1.md:34-37`). The face said B was removed; the hub kept it. The cause is not verified. Candidates: `remove()` calls `cleanup()`, which clears the earlier pending timer without firing it (`web/src/desk/hooks/useUndoReceipt.ts:18-29`); the Floor's `revert` is a no-op (`WorldStage.tsx:144-148`); or the second Delete still targets A through the selection (`delete-receipt-astra-role-r1.md:53`).

## Scope

- **In:** one delete path for the spatial Floor and the list: the same `OBJECT_DELETE_REQUEST` handling and the same `useUndoReceipt`, mounted wherever `object.delete` can run, the receipt in the #665 seat above the list's AskBar (`web/src/desk/components/DeskListView.tsx:340`); the trace of F7's cause, named with its source line; the repair so that every delete the face announces reaches the hub unless the owner presses Undo on it; a record of which delete paths the list offers (row menu, Delete key, palette); a measure of FINDING S2 (the Delete row cut at the bottom edge at 393), with a BACKLOG row if it reproduces.
- **Out:** a new receipt species or copy; the Workbench footer linger (BACKLOG "The Floor delete receipt follow-ups" row 2); F8, the receipt moving when the AskBar leaves; the Chair's delete (the Chair has no object menu: `objectMenuEntries` is used only by `floorMenu.ts`, `DeskListView.tsx` and `WorldStage.tsx`), unless the trace shows `object.delete` can run there.

## Acceptance criteria

- [ ] The list Delete (every path the list offers) removes the object: "Removed … Undo", then "Removal committed", `readable_text` in the viewport at 1440 and 393; `GET` the object → 404 after the window; Undo inside the window → 200 and the row stays. Red on main (no request, 200).
- [ ] The receipt on the list sits directly above the AskBar, the same species as the Floor's; if it cannot, the lane stops and a canvas goes to the owner first.
- [ ] Two deletes in one window, on the spatial Floor and on the list: A 404 and B 404 after the window; Undo on the pending one keeps only that one. Red on main (B 200).
- [ ] F7's cause named in the evidence with its source line, and a mutation that restores it turns the fence red.
- [ ] One listener and one receipt hook: `grep -rn OBJECT_DELETE_REQUEST web/src` shows one handler, mounted on both faces.
- [ ] `case.p7.decision_delete.gone` (`docs/internal/philo/graph/atlas-phase7.json`) still passes at 1440 and 393.
- [ ] Shots at 1440 and 393.

## Effort (not a promise)

PROVISIONAL: 1–1.5 engineering days.

## Test plan

- **Unit (vitest):** `useUndoReceipt` with two `remove()` calls inside one window (both fire, or the first fires at once); the list mounting the delete handler.
- **Integration (glass, the real hub, isolated HOME):** the FINDING's Finding 2 reproduction at 1440 and 393; the F7 probe on the Floor and the list.
- **Web baseline:** `uv run python scripts/check_web_baseline.py --run`, zero branch-new; every `scripts/philo_*.py --check` exits 0 before push.

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib from the owner's word closing Phase 7; unratified.
