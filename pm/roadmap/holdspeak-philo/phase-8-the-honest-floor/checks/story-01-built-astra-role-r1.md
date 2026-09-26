# Astra role (Opus 5.5 stand-in, owner ruling 2026-09-25) — check on built + canvas, PR #671 @ f9d0a3da

Branch `feat/philo-8-01-zone-name`, worktree `/Users/karol/dev/tools/wt-philo-8-01` (read only; `git status` empty after the check, HEAD f9d0a3da).
Method: two `git archive` copies in the scratchpad — origin/main 26f7b005 (main has moved past the branch base 267f692a) with the branch's four fence files laid in, and f9d0a3da. Both copies: real `npm ci --ignore-scripts && npm run build` (exit 0). Isolated HOME, `PLAYWRIGHT_BROWSERS_PATH` set, scoped runs only.

## VERDICT

- (a) Merge half A: **RATIFY-WITH-CONDITIONS** (C1, C2).
- (b) Present the canvas to the owner: **RATIFY-WITH-CONDITIONS** (C3–C6).

Seven Tenets: half A passes. The fix is small (one helper module, one in-flight set, one registry flag) and it removes a real dead end (the second New Zone always gave 409). There is no new interface and no ceremony.

## Reproduced

1. **Glass on true main (archive 26f7b005 + the branch fence), run alone and serial:** the two-press cases fail with `[201, 409]` (Floor) and `[201, 201, 409]` (the "new  ZONE 2" skip); the Chair still offers New Zone; list-to-spatial shows `stale rename field: list-to-spatial` 3/3 at both widths. floor-chair-floor is green, which is the expected guard result.
2. **Glass on the branch, run alone:** `12 passed in 81.19s`.
3. **Vitest (3 fence files).** Branch: `Tests 25 passed (25)`. True main: `4 failed | 10 passed (14)`, and `zoneFreeName.test.ts` fails as a whole file because `zoneName.ts` does not exist. The lane's "8 red of 25" comes from its own method, which reverted six files and kept `zoneName.ts` (story-01-half-a-proof.md:10). That is honest as described but it is not a true main run.
4. **The web baseline "2888, zero branch-new"** was not reproduced (full desk vitest, outside scope). UNKNOWN.

## FINDINGS

- **F1 (fence, C1): the list-to-spatial fence can pass on main when the machine is under load.** In the first run, main and branch ran in parallel (8 browsers), and `[393-list-to-spatial]` PASSED on main. `test_philo8_01_zone_name_glass.py:216-217` waits a fixed 600 ms and then checks that the field is absent. The field on main shows only after the post-create refresh (about 4.7 s on the rig). If the refresh is late, the check runs before the field can show, and the test goes green on buggy code. This breaks the lying-double law ("prove every fence FAILS pre-fix"). In the same loaded run, the branch had 2 timeouts (`_ensure_view` and `expect_response`, both 10 s). Run alone, the branch is green 12/12.
- **F2 (merge, C2): the branch does not merge clean with main.** `git merge-tree origin/main f9d0a3da` reports CONFLICT in `pm/roadmap/holdspeak-philo/README.md` (the "Last updated" line, from #669). All code merges clean.
- **F3 (in-flight set, (2)): no leak.** Probes on the archive copy (astraProbe.test.ts, 4/4) showed these results:
  - A 409 frees the name, so the next press posts it again.
  - A network throw frees the name.
  - A refresh that throws frees the name (`dataSlice.ts:354`, `:373-384`, `:395-399`).
  - Retry refreshes before it picks again (`:363-367`).
  - One narrow opposite case is real: out-of-order refreshes. A late, stale refresh of press A can overwrite the store after press B's refresh has landed and released B's name, so a third press posts B's name again. The hub answers 409, which shows with Retry, and Retry refreshes first and recovers. This is low severity and no work is needed now. Recorded.
- **F4 (`needsZones`, (3)): lawful and complete.** A declarative field on the Verb (`verbRegistry.ts:71`, `:227`) plus `offeredHere` (`:84-85`) follows the registry's existing pattern (`palette?: boolean`). An id check (`v.id === "desk.new-zone"`) would need the same two call sites and would hide the rule. Tenet 1 is met.
  - Surfaces:
    - The palette: `DeskToolShelf.tsx:378`.
    - The menu bar and the 393 "go" door: `DeskMenuBar.tsx:81`.
    - The floor right-click: `floorMenu.ts:33`, mounted only in WorldStage (`WorldStage.tsx:328`).
    - Voice: the grammar is mounted only in WorldStage.
    - The HoldSpeak mark menu (`DeskChrome.tsx:32`) does not list the verb.
    - Keyboard: `desk.new-zone` has no `key` (keys at `verbRegistry.ts:157,169,268,306,507,…`), so no shortcut exists to leak.
  - Keyboard F2 respects the ghost: `keymap.ts` returns without action when `verb.ghost(ctx)` is set.
- **F5 (face change, (4)): no stale field, and typed text is saved.** Probe on the real product (branch archive, real hub): on the spatial Floor, press New Zone, type "Typed then left", then click the Chair toggle. The result is `PUT 200`, and the hub lists "Typed then left". The click blurs the field, and the blur commits before `DeskApp.tsx:138-140` clears the rename. This matches the canvas rule "leaving the field writes". UX-CANON sets no rule for this case, and saving on leave is what Q1 of the canvas asks him to ratify. Lawful.
- **F6 (silent failure, (6); ruling below): the silent revert has a second way in.** On the Floor, type a taken name ("Inbox") and click to the Chair. The result is `PUT 409`, and the zone goes back to "New zone" with no alert on the Chair (`ALERTS_ON_CHAIR []`). By then the field has unmounted and the face-change effect has cleared the error. The same silence applies to `renameZone` on 422 and on a network failure (`dataSlice.ts:626-640`, "revert"). All of this is pre-existing and half A does not make it worse.
- **F7 ((5)): F2 greyed "Open the Floor" is acceptable.**
  - STE: "open" is an approved verb, and "the Floor" is the face's proper name. The string reads as an instruction in the ghost slot, which is the registry's grammar ("Select an object", `verbRegistry.ts:511`).
  - §A.11 forbids a verb that does nothing while it looks live. A ghost with a reason is not a lie. Rename cannot be withheld as a whole because it serves notes and other kinds.
  - Wording drift: AC line 34 says "withheld where the face shows no zone". Amend the AC to "ghosted with its reason" when the story closes.
- **F8 (canvas, board 7): the board shows a zone the hub has already deleted.** `shoot.py:183-186` deletes "New zone 2" through the API, and the app store is not refreshed. The Chair palette on board 7 then lists OBJECTS "New zone" and "New zone 2" (393 shot). The caption does not say this. The board also shows that the Chair palette still lists zones as objects (`DeskToolShelf.tsx:425-434`, `run: diveInto`), which the owner may read as against Q2 (c). Q2 (c) covers only New Zone, so this is not a defect, but it must be named.
- **F9 (canvas, board 1): the caption says "the name selected", but the shot shows no selection highlight.** Board 2 proves the selection indirectly: typing replaced the value, and facts give `field: "Platform team"`. `facts.json` records no selectionStart/End.
- **F10 (canvas, board 5): the chip moves the table.** At 1440, the KIND column is at x≈757 on board 1 and at x≈859 on board 5, on every row. The chip widens the Name column, and the whole table shifts when a refusal shows. At 393 the Zone column is off screen on that board. The fence sketch does not cover this.
- **F11 (canvas, inherited): the Limits line misquotes the face.** The face reads `17 SHOWNS OF 17`, a bad plural from `countToken(visible.length, "SHOWN")` at `DeskListView.tsx:289`. The README says "17 SHOWN of 17". The 4 raw sort-header `<button>`s (`DeskSortableTable.tsx:96`, a §A.1 bounce) are in the README, but they are missing from the review page's Limits.
- **F12 (canvas): the field is monospace bold, but the row names are sans.** Boards 1, 5 and 6 show this. It is the Floor's `.desk-zone-rename` style carried into the row. It is a beauty question for the owner, not a canon breach.
- **F13 (canvas scope, (8)): the Floor chip change is lawful to present.** Replacing the Floor's 11 px sentence (`desk.css:245-252`, below the 12 px floor, and prose) with the same StateChip follows §D ("the same object never drawn two ways") and the story's "compose, not copy" (story:20). It is small, and the owner is asked about it by name (canvas Q2). It is in scope if he says yes.
- **F14 (canvas, (7)): the board labels are honest.** `shoot.py:101-115` boots a real hub through `scripts/graph_walk.py serve` on an isolated HOME and serves the product with vite, with one module aliased (`harness/vite.config.mjs`). Boards 0 and 7 open `hub_url` (`:171`, `:238`), which is the built product. All writes and statuses are in facts.json. The one exception is the stale store on board 7 (F8).

## RULING on (6)

It is in scope for half B, and it does not block half A. Once the rename is the ratified path, a refusal the owner cannot see goes against Tenet 3 and §A.10. Half B shows a failed rename in the same chip slot as NAME TAKEN: 422 and a network failure get a StateChip `failure` with the hub's reason or `NOT SAVED`, and the field keeps focus. A refusal that arrives after the field has unmounted (F6) goes to the existing write-receipt line (`reportWriteFailure`, `RENAME ZONE`, with Retry). One fence covers each case.

## CONDITIONS

- **C1 (before merge):** Make the list-to-spatial fence wait for the create to land before it checks absence (for example, wait for the new zone's row, or wait for the first GET `/api/directories` after the POST). Then prove it red on true main with the machine under load.
- **C2 (before merge):** Merge origin/main and resolve the `holdspeak-philo/README.md` "Last updated" conflict.
- **C3 (before the owner sees it):** Re-shoot or re-caption board 7. Either refresh the store after the API delete, or say that the palette lists existing zones as objects (open, not create).
- **C4 (before the owner sees it):** Correct the Limits on the review page. Quote `17 SHOWNS OF 17` exactly, and name the 4 raw sort-header `<button>`s. File the 10 px census line, the bad plural, the cut Zone column at 393 and the raw headers in BACKLOG.md as one list-face repair entry. These are inherited and must not block the ratification.
- **C5 (before the owner sees it):** On board 5, fix the column jump in the proposal (fixed Name column or a chip that does not widen it), or show it and add it to Q2. Add a selection fact to board 1 (selectionStart/End), or remove "the name selected" from the caption.
- **C6 (before the owner sees it):** Add one line to Limits: "a failed rename (422, network, or refused after you leave the field) will show in the same chip slot (half B)". This is the ruling above, so the owner does not ratify a canvas that is silent on it.

## MISSED (not on the boards)

- A long zone name at 393. The field is 125 px there (board 1) and 97 px with the chip (board 5). Show how the committed long name truncates in the row.
- A name of only spaces: `useZoneRenameField.ts` trims it to empty, sends no PUT and closes the field, so the old name stays with no word. This is acceptable because it acts like Escape, but draw it or state it.
- Two fast New Zone presses on the list with the proposed field: which row holds the field? The second create's `setRenamingZone` replaces the first.
- The ~4.7 s from press to field (the post-create full `loadAll`). The field waits for the whole refresh. Tenet 3 says this delay should be recorded as a follow-up (open on the created id at once).

## UNKNOWN

- The web baseline (2888, zero branch-new) was not reproduced.
- What `diveInto` does when a zone is picked from the Chair palette.
- CI load behaviour of the 10 s timeouts in the new glass (2 timeouts seen only under 2× parallel load).
