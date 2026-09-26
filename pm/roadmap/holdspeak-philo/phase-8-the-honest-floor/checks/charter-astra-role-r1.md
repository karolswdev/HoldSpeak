# Astra role (Opus 5.5 stand-in, owner ruling 2026-09-25) — CHECK on the charter draft, PR #668

Branch `docs/philo-8-charter` @ 333abb1b (main 94036242 merged in). Worktree read only. Source lines re-read on origin/main 94036242.
Rig: `git archive origin/main` into the scratchpad; `npm ci --ignore-scripts && npm run build` (exit 0); `uv sync --extra test --extra meeting` (exit 0); each probe ran with `HOME=$(mktemp -d)` and `PLAYWRIGHT_BROWSERS_PATH` set. The owner's HOME and DB were not touched.

## VERDICT: RATIFY-WITH-CONDITIONS on presenting the charter to the owner

The scope is the four verified defects and nothing more. Every cited line is true on main. Two things are wrong. First, story 02's Problem ships a guess and one false sentence. Second, its "mount on both faces" design would carry a third, unnamed drop path to the list. I reproduced and named all three causes (below). Pay C1–C4 before it goes to the owner. C5–C9 are text fixes.

## FINDINGS

F1 — Every cited line is true on main 94036242.
- `web/src/desk/store/dataSlice.ts:322` `zone: ["/api/directories", "directory", { name: "New zone" }]`. `createPrimitive` spans `:298-376`. `:339` Retry re-calls `createPrimitive(kind, overrides)`. `:370` `setRenamingZone(createdId)`.
- `holdspeak/operations.py:655` zone_name_taken, ignoring case. `holdspeak/services/primitive_service.py:365-368` maps ZoneNameTaken to a ConflictError.
- `web/src/desk/gl/WorldStage.tsx:56` the hook. `:138-152` the only OBJECT_DELETE_REQUEST listener, with `revert` `() => undefined` at `:147`. `:206-207` renameZone. `:271-280` the overlay mount. `:343-348` the foot. `:400` `ZoneRenameOverlay`.
- `web/src/desk/DeskApp.tsx:192-207` mounts exactly one of DeskListView, WorldStage or ChairHome.
- `web/src/desk/components/DeskListView.tsx:340` `<AskBar />`, a bare element with no foot wrapper.
- `web/src/desk/hooks/useUndoReceipt.ts:18-21` cleanup. `:23` cleanup on unmount. `:27` `remove()` calls `cleanup()` first.
- `web/src/desk/verbRegistry.ts:546-566` `object.delete`. It only dispatches.
- The BACKLOG ranges `:1243-1247`, `:1249-1253` and `:1269-1274` are correct. So are `DecisionPullout.tsx:115`, `api.ts:259` (no caller), CONSTITUTION `:18-60`, UX-CANON `:23-52` and HANDOVER-XXIX `:33-42`. Phase 7 atlas = 27 cases.

F2 — Story 02 / scope item 4 ships a guess, and one sentence is FALSE. "The face said B was removed" (charter scope 4; story 02 Problem; inherited from the Phase 7 ledger row 4) is not in the checks file (`checks/delete-receipt-astra-role-r1.md:34-37` says only that one delete is lost). My probe, following the checks file's method exactly, shows the face read "Removed Probe A" the whole time. B's Delete never ran. I reproduced it and named the cause:

```
variant checks_method (Shift+Enter A, Delete, 1.5 s, Shift+Enter B, Delete, 12 s):
 sel_before_2nd "2 SELECTED"; receipt_after_2nd "Removed Probe A ... 04s"; A 404; B 200; DELETE requests: [A only]
variant untoggle_a_first (A taken out of the selection before B is selected):
 sel_before_2nd "1 SELECTED"; receipt_after_2nd "Removed Probe B ... 08s"; A 200; B 404; DELETE requests: [B only]
leave-the-Floor (Delete A on the Floor, 1.5 s, back to the Chair, 12 s):
 receipt "Removed Probe A ... 08s"; A 200; DELETE requests: []
```

- Cause 1 (the checks file's observation): the listener does not take the deleted object out of the selection, and nothing hides it (`WorldStage.tsx:138-149`). Selecting B makes 2 selected. `keyContext()` gives `selectedRef: null` when there are 2 (`web/src/desk/keymap.ts:71-74`). `object.delete` ghosts "Select an object" (`verbRegistry.ts:554-556`), and `dispatchKey` "refuses quietly" (`keymap.ts:84`). So Delete on B does nothing, with no sign.
- Cause 2 (the true "face lied" case): with the selection right, `remove()` calls `cleanup()` (`useUndoReceipt.ts:27`), which clears A's interval, so A's `fire` never runs. The face said "Removed Probe A". The hub keeps A.
- Cause 3 (NEW, not in the charter): unmount drops the pending delete. `useUndoReceipt.ts:23` runs `cleanup` on unmount. WorldStage unmounts on every face change (`DeskApp.tsx:192-207`). If he leaves the Floor inside the 8 s window, A stays 200 and zero DELETE requests go out.
- The no-op `revert` (`WorldStage.tsx:147`) is NOT a cause. Only `undo()` calls it.

F3 — The story 02 design "one handler, mounted on both faces" (story 02 Scope; AC "mounted on both faces") keeps cause 3. A list-to-Chair switch inside the window would drop the list's delete the same way. It also does not cover the Chair, where a stale selection plus the Delete key (the keymap is global) still dispatches to no listener. That last point comes from reading the code; I did not exercise it.

F4 — The story 01 free-name rule "ignoring case" is incomplete. The hub normalizes by strip, collapse whitespace, NFC and casefold (`holdspeak/db/primitives.py:60-68`, used at `:1119`). The Retry closure (`dataSlice.ts:339`) picks again from the same store. If the store is stale (a zone made by MCP or in another tab and not yet refreshed), Retry posts the same name and gets 409 again. The risk row "Retry picks the next free name again" holds only if Retry refreshes the store first.

F5 — Q2 is honest but has no recommendation. It leaves out one fact: `desk.new-zone` is declared `scope: "floor"` (`verbRegistry.ts:203-212`, per FINDING), yet the Chair's palette offers it. So option (c) is lawful under UX-CANON §A.11 (`UX-CANON.md:50-52`, "withhold it … rather than ship it dead") and consistent with the verb's own declaration. Against Tenet 3 it costs one extra step (go to the Floor), where zones can be seen anyway.

F6 — The rename work should hang off `renamingZoneId`, not off the New Zone verb. `object.rename` (F2) also sets it (`verbRegistry.ts:502`). On a face without WorldStage it is dead the same way. Story 01 should state that the one rename-where-he-is covers F2 as well.

F7 — The list's AskBar is placed by itself: `.desk-askbar` is `position: absolute; bottom: 84px` (`web/src/desk/components/mission-control.css:285-289`). It is not inside `.desk-world-foot` (`desk.css:208-238`). The #665 seat can be reused by wrapping the list's AskBar and receipt in the same foot class, so no canvas is needed. But the #665 fence proved only a page that does not scroll. Exit 3 must also prove the receipt with a long list scrolled to the end.

F8 — The README "Last updated" line lost main's entries in the merge. On main, the line held "Phase 7 CLOSED …" and "PHILO-7-04 DONE … 'Reviewed — it's right'". The new line goes from the Phase 8 draft straight to PHILO-7-03 (`git diff origin/main...HEAD -- pm/roadmap/holdspeak-philo/README.md`).

F9 — Story 04(b) is not a Floor item. Its BACKLOG home is "the Arrival lane" (`BACKLOG.md:1281`), and its producer line is untraced (story 04 admits this). Story 04(a) is homed to the Floor lane (`:1280`). But the same empty heading shows for "Decision context" and "Decision" (`DecisionPullout.tsx:113-114`), not only for Consequences at `:115`.

F10 — The Out list skips Phase 7 ledger rows 9 (the ToolSearch confound) and 14 (the privacy note). The charter says only "rows 11–13", while rows 5–8 are homed. Name them "report only, no home" so the ledger is closed out in full.

F11 — Estimate. "4–6 engineering days" is honest as a unit but does not help him plan. On Phase 7's own calibration, story 01 took about 25 agent-minutes (`phase-7…/current-phase-status.md:372`). The whole 11–15-day phase closed in about two elapsed days, and most of that was check rounds and the owner's word. The repairs here are small: a free-name helper, a hook flush, a selection drop, a hoisted listener, a foot wrapper, one rename composition. The charter should add a forecast of elapsed time (about 1–2 days, gated by the canvas word and the checks). I would also cut the effort figure to 2.5–4 d. Not a blocker.

F12 — The exits are measurable and each is red on main. Exit 1 is red by FINDING S1. Exit 2 is red by FINDING Finding 1. Exit 3 is red by FINDING Finding 2. Exit 4 is red by my probe (both variants fail "A 404, B 404"). Exit 5 is red by construction. Exit 6 is a proof act, not a red. Exit 4's "Undo on the pending one keeps only that one" is ambiguous with a one-slot receipt. See RULING (5).

## RULINGS

(3) The 409. The store picks the next free "New zone N" inside `createPrimitive`, and the hub rule stays. This is the smallest lawful fix, and it hides no real conflict.
- A zone he named "New zone 2" himself is his name. The picker skips it and never renames an existing zone.
- Two clients creating at once still meet the hub's unique index, and the 409 stays the named failure row. That risk is honest at one owner.
- A hub-side answer (the hub picks the name when the name is absent) would be atomic. But it changes a declared contract: the `operations.py` descriptor and its "zone name is required" refusal, the generated docs, the MCP args schema. The charter puts the hub's zone-name rule Out, rightly. That is more files and more fences for one owner (Tenet 1). Rejected.
- Conditions: mirror `normalize_zone_name` (strip, collapse whitespace, casefold). Never replace an explicit `overrides.name`. On a `409 zone_name_taken`, Retry refreshes the store before it picks.

(5) The two-deletes bug. The cause is named, not guessed. There are three causes (F2): the stale selection (the checks file's observation), the flush dropped in `remove()` at `useUndoReceipt.ts:27`, and the flush dropped on unmount at `:23`. The smallest repair:
- (i) `remove()` fires the pending `fire` before it replaces the state (flush, not drop).
- (ii) Unmount flushes a pending delete, or the listener and hook are hoisted to one always-mounted place.
- (iii) The listener takes the queued ref out of `selectedIds`.

The receipt stays one slot. A second delete commits the first at once and takes its Undo away. That is honest, and there is no new species (Tenet 1). The lane decides it, and it is recorded. It is not an owner question. List reuse: one listener and one hook, hoisted to DeskApp (or the hook's flush on unmount plus one mount per face). The receipt sits in the `.desk-world-foot` seat around the list's AskBar, with no canvas.

## CONDITIONS (before the charter goes to the owner)

- C1. Rewrite story 02 Problem, scope item 4 and risk row 4. Replace the three "suspected causes" with the three verified causes and their lines (F2). Strike "the face said B was removed". Add cause 3 to the ledger row wording.
- C2. Story 02 Scope and AC. Hoist the listener and hook, or flush on unmount. Change "mounted on both faces" to "one mount, which survives a face change". Add to exit 4: "leave the face inside the window → the object 404". Check `WorkbenchWindow.tsx`, the other user of `useUndoReceipt`, under the flush semantics.
- C3. Story 01's free-name rule: `normalize_zone_name` parity; `overrides.name` is never replaced; Retry refreshes on 409. Add these to the unit plan.
- C4. Q2 gets a recommendation and the fact that the verb is declared `scope:"floor"`. Story 01 states that `object.rename` (F2) is covered by the same rename.
- C5. Exit 3: the list receipt stays readable with a long list scrolled to the end, at 393.
- C6. Restore the README entries the merge dropped (F8).
- C7. Projects: give it a home line (README phases table note or a BACKLOG row, "the owner's second job, deferred by his word 2026-09-26"). "Unchartered" with no home is how it gets lost.
- C8. The Out list names ledger rows 9 and 14 (F10).
- C9. The estimate adds a forecast of elapsed time from the Phase 7 calibration (F11).

## MISSED
- Cause 3: leaving a face inside the undo window drops the delete (probe above).
- The object stays drawn and selected during the window (no optimistic hide). This is the root of cause 1. Hiding it would be a face change. Taking it out of the selection is not.
- F2 Rename on non-Floor faces (`verbRegistry.ts:502`).
- The empty "Decision context" and "Decision" headings (`DecisionPullout.tsx:113-114`), if 04(a) is kept.
- The Chair plus a stale selection plus the Delete key (from reading the code, not exercised).

## TUESDAY
He opens the Chair, presses New Zone twice and gets two zones, named where he is. On the list at 393 he deletes a decision and reads "Removed … Undo". He deletes two quickly, or flips to the Chair during the countdown, and both are really gone. Today all three of those lose a delete, and the first one says nothing.

## RECOMMENDATIONS TO MUAD'DIB (not conditions)
- Q1 is close to a lane call ("New zone 2" is the Finder convention). Keep it only as "(a) unless you object", so it is not one more interface (Tenet 3).
- Q3(b) belongs to the Arrival lane (BACKLOG:1281). Offer to drop it from this phase.

## UNKNOWN
- Whether the list at 393 with more than 16 objects scrolls the document or an inner box. This decides whether the foot seat stays in the viewport (C5 fences it).
- Whether the Chair can reach `object.delete` with a stale selection (not exercised).
- Whether any atlas case captures the zone by the name "New zone" across repeated creates in one hub (the 27-case re-run in exit 5 will show it).
- Whether the lane will choose hoisting or flush-on-unmount. Either pays cause 3.
