# Astra role (Opus 5.5 stand-in, owner ruling 2026-09-25) — CHECK on built, PR #673

PR #673 @ `590bdff8` (`feat/philo-8-01-half-b`, from main `808a9c30`). Worktree `/Users/karol/dev/tools/wt-philo-8-01` read only; `git status` clean and HEAD `590bdff8` after the check. Every run was in clean `git archive` copies (fresh dirs `a673-main`, `a673-head`, `a673-merge` under the session scratchpad), real `npm ci --ignore-scripts && npm run build` in each, isolated `HOME=$(mktemp -d)`, `PLAYWRIGHT_BROWSERS_PATH` set, scoped only.

## VERDICT: RATIFY-WITH-CONDITIONS (merge after C1–C3; all are small: records, one ledger row, one test case)

The build matches the ratified canvas. The reds reproduce on main and the greens reproduce on the PR. The Floor failed-save case that was missing HOLDS (I wrote it: 4 red on main, 4 green on the PR). No duplicate chip and receipt. The merge with #672 has one trivial code conflict (an import line) and two records conflicts. The merged tree builds, typechecks and passes the scoped vitest.

## Reproduction

| Run | main 808a9c30 + PR tests | PR 590bdff8 |
|---|---|---|
| vitest `zoneRenameRefusal.test.ts` + `DeskApp.test.tsx` | `Tests 6 failed / 12 passed (18)`, all 6 refusal cases × | `Tests 18 passed (18)` |
| glass: list-rename (14) + zone-name (12) + my Floor failed-save (4), `-n 4` | `19 failed, 11 passed`: 14/14 list-rename red, 4/4 Floor failed-save red, plus `test_two_new_zone_presses_make_two_zones[1440-spatial]` (load; green serially, 4 passed) | `1 failed, 29 passed`: `test_two_new_zone_presses_make_two_zones[1440-list]` timed out on the POST response under two parallel runs; serial rerun `4 passed in 58.96s` |
| tsc `--noEmit` | 0 errors | 0 errors |
| whole desk vitest (by accident, an empty file glob) | — | `Test Files 320 passed (320)`, `Tests 2898 passed (2898)` |

The two-press flake is load, on both sides, and serial is green on both. The main reds are for the causes the evidence names: no list field; the Floor shows the sentence, not the chip; no receipt; for my case, a 422 or network failure reverts without a word.

## Question by question

1. **Build vs the boards.** Crop comparison, board 1 vs `list-field-open-1440.png`: the same pixels on the field border `(168,110,74)`, the same monospace bold text, the same selection tint, the same mic well, the same Name-cell width (the field ends at x≈626, the mic at ≈665, the Kind column at 686 in both). Board 5 vs `list-name-taken-393.png`: the chip is on its own line under the field, `✗ NAME TAKEN`, and the columns do not move (the glass asserts the Kind head's x before and after, `test_philo8_01_list_rename_glass.py`). The CSS is the canvas CSS moved into the product: `speak-to-fill.css:95-113` = `harness/canvas.css`. Differences: the product board 5 keeps the accent focus border, and the canvas 393 board lost it. The product matches the canvas text ("the field stays open with focus"). The name reads `New zone`, not `New zone 2`, because the isolated hub starts with no zone of that name. Boards 2, 4, 8 and 9 have no product shot, and 10 has one (`two-zones-list-*`). 4 and 9 are fenced. 8 (the long name) is neither fenced nor shot (see MISSED).
2. **Reds and greens.** Reproduced (table above). Floor failed-save: the case holds on the PR. Chip `✗ NOT SAVED`, focus kept, `not inListRow`, no text under 12 px, no sentence, and the hub still lists `New zone`. My file: `scratchpad/astra-673-floor-failed-save.py`. It subclasses the PR's glass class. Shots: `scratchpad/floor-not-saved-{422,network}-{1440,393}.png`.
3. **The changed half-A wait** (`test_philo8_01_zone_name_glass.py:214`): not weakened. On half B the row's name button no longer exists while the field is open. The `input.desk-zone-rename` inside `.desk-listmode` appears only when the row exists (after the post-create refresh) AND `renamingZoneId` is that row (`DeskListView.tsx:218`). It proves the same "create landed" fact, and it also proves the field was open before the face change, which is a stronger precondition for the no-stale assert. The `.or_` with the button keeps the leg valid on main.
4. **Refusal moves on a face change**: correct, and there is no duplicate. `DeskApp.tsx:144-147` reads the standing refusal, clears the chip, then reports once. The in-flight path (`dataSlice.ts:618-621`) goes to the receipt only when `renamingZoneId !== id`, and by then the chip is empty. Normal case, a click on another face: the blur `commit()` first clears the chip (`useZoneRenameField.ts:17`) and sends the PUT again. The face change then finds no chip, and the late 409 goes to the receipt exactly once. The vitest `DeskApp.test.tsx` "moves to the write receipt" and `zoneRenameRefusal.test.ts` "no field open" fence both paths.
5. **Get Info and the 500**: in scope. Get Info (`InfoWindow.tsx:28`) is unchanged. Its zone rename calls `renameZone` with no field open, so a refusal now reaches the receipt. On main it set a string nobody drew, so the refusal was silent. The 500 is a failed save under the owner's answer 2, so the revert is lawful (`dataSlice.ts:633-648`). No regression: `InfoWindow.tsx` has no diff, and the whole desk vitest passes 2898/2898 on the PR copy.
6. **The Floor opens the name selected**: see RULING.
7. **Size, verbs, words.** The glass scans every text node in the row for font-size < 12 px on the list, on the Floor and in my Floor failed-save case: `small == []` everywhere. The `.desk-zone-rename-error` 11 px rule is gone (`desk.css`). The diff adds no raw `<button>`: the MicButton is the library one, and the receipt's Retry and OK are the library `Button` (`useWriteReceipt.ts:22,91,102`). Strings: `NAME TAKEN`, `NOT SAVED`, `RENAME ZONE FAILED · NAME TAKEN`, `Retry`. These are STE-clean (approved verbs, no prose). The chip `title` holds the hub's reason (a tooltip, not face text). The raw `<button className="info-name">` in `InfoWindow.tsx:43` is inherited and not in this diff.
8. **Merge with #672** (`git merge-tree --write-tree HEAD origin/feat/philo-8-02-one-delete` → `3ef0b4c1`, exit 1). CONFLICTS: `web/src/desk/components/DeskListView.tsx` is ONE hunk, the imports (`ZoneRenameRow` vs `DeskDeleteSeat`): keep both. `pm/roadmap/holdspeak-philo/README.md` has the "Last updated" line. `phase-8-the-honest-floor/current-phase-status.md` has "Last updated", the story-table rows (take 8-01 `done` from #673 and 8-02 `done` from #672) and the "Where we are" paragraph (keep both). `DeskApp.tsx`, `WorldStage.tsx` and `docs/generated/api-reference.json` auto-merge. Merged tree, with the import hunk resolved: `npm run build` exit 0, `tsc --noEmit` 0 errors, vitest `deleteReceipt` + `zoneRenameRefusal` + `DeskApp` + `philo801ZoneVerbs` + `zoneFreeName` → `Tests 39 passed (39)`.
9. **Records.** Story `done`; the phase row is `done` with a link to the evidence; the acceptance boxes are flipped; the README "Last updated" is set. The evidence records the failed `-n 6` capture (exit 1) and the `-n 4` rerun (26 passed). This is honest, with one wording fault (C1).

## FINDINGS

- F1 (records, `evidence-story-01.md:34`): it calls both `-n 6` failures "load timeouts". The half-A leg's failure (`waiting for get_by_role("button", name="New zone zone")`, evidence :157) was DETERMINISTIC. Half B replaces that button with the field, so the leg could not pass until it was changed. Only the two-press POST wait was load.
- F2 (records, the story's acceptance "Shots at 1440 and 393 beside the canvas artboards", flipped `[x]`): no board-to-shot map exists. The evidence never names a board, and the canvas README only points at `../story-01-shots/`.
- F3 (Floor face, inherited, now in the story's reach): the Floor field is still clipped. My `floor-not-saved-network-393.png` shows `ıe zone` for `Offline zone` in a field about 62 px wide. The PR's `floor-name-taken-1440.png` shows `Inbox` in a field about 60 px wide. The story's Out line excludes "the clipped field width at 1440 ('ew zone') unless the canvas's field is the same element", and after this PR it IS the same element (`ZoneRenameRow`). The width comes from the Floor overlay (`WorldStage.tsx` `width={renameZone.width}`), not the row. Also on the Floor: the chip has no backing, so sprites show through it (`NAME TAKEN` / `NOT SAVED` at 393), and it is about 8 px wider than the field + mic at 1440. The canvas drew only the list, so this is not "as drawn" either way. No BACKLOG row names it (`pm/roadmap/holdspeak/BACKLOG.md:1290-1296`).
- F4 (minor, from reading the code, not observed): after a refusal, every blur sends the SAME refused name again (`useZoneRenameField.ts:19` compares to `title`, which was reverted), and `:22` takes focus back after each 409. A click elsewhere on the list with `Inbox` refused costs one PUT per click, and the field keeps pulling focus until Escape. This is inherited from main's hook (the Floor did the same), but the list now exposes it on every row.
- F5 (minor): the late-refusal receipt for a 422 or network failure reads `RENAME ZONE FAILED · NOT SAVED`. That is a tautology, and the hub's reason (kept in `detail`) is dropped from the receipt (`dataSlice.ts:621`, `DeskApp.tsx:147` pass `label`, not `detail`).

## CONDITIONS (before merge)

- C1: Correct `evidence-story-01.md:34`. Only the POST wait was load. The half-A leg failed on the removed button, and that was deterministic.
- C2: Add the Floor failed-save case to `tests/e2e/test_philo8_01_list_rename_glass.py`. Either parametrize `test_a_failed_save_shows_in_the_chip_slot` over `face` ∈ {list, spatial}, or lift my case. It is proved red on main (4/4) and green on the PR (4/4). Answer 2 of the ratified canvas ruled "a failed save … in the same slot" on both faces, and today only the list is fenced.
- C3: Add a BACKLOG row under "PHILO-8-01 follow-ups" for F3: the Floor rename field's width comes from the zone label (text clipped at both widths), and the chip on the Floor has no backing and is wider than the row. Cite the shots. Also add a board → product-shot map (F2) to the evidence, or reword the acceptance note to name which boards have product shots (1, 3, 5, 6, 10) and which are fenced without one (4, 9) or neither (8).

At merge (Muad'Dib): resolve the #672 conflicts as in question 8, in either order.

## RULING on (6): lawful, no owner word needed; disclose it

The owner ratified ONE field ("Chip on the list and the Floor", one species on both faces). The canvas README defines the field as composed "from the ONE rename behaviour `useZoneRenameField.ts`", with "the name opens selected, so typing replaces it" as part of that field's ratified behaviour. The half-A acceptance line demands "one Enter/blur/Escape commit path". Keeping the select only on the list would split the one behaviour by face, and that would break the ratified law, not build it. "Build what was ratified" binds the field's behaviour, and the field is the same element on both faces. A default name `New zone` that typing replaces is also what Tenet 3 asks for. The Floor glass fences it implicitly: `test_a_taken_name_shows_the_chip_on_the_floor` types `Inbox` with no clear and expects the 409, so it would get `New zoneInbox` if the name were not selected. Condition: one line in the PR body and the sitting notes ("the Floor field now opens with the name selected, as the list does"). He sees it, but no ask is needed.

## MISSED

- Board 8 (the long name) has no fence and no shot. The in-field scroll is native input behaviour (low risk). The 393 column push after a commit is inherited and already in the BACKLOG.
- F4: sending the refused name again on every blur, and focus reclaimed after each 409.
- F5: the late receipt's reason is the label, not the hub's reason.
- The late-refusal glass leaves the Floor (spatial) only. The list-to-Chair path runs the same code but is not fenced at the glass level.
- The glass's late-refusal case cannot tell apart "409 before the face change, moved by DeskApp" and "409 after, routed by `renameZone`". The two vitest cases cover each path.

## UNKNOWN

- Whether a Chromium blur fires on the field's unmount during a face change with no click (a keyboard or voice face change). React does not dispatch blur for a removed node, and the DeskApp path covers the standing chip. I did not observe a keyboard-only face change with the field open.
- Why `test_two_new_zone_presses_make_two_zones` times out on the POST response under about 8 parallel browsers. It happens on main and on the PR alike, and it is green serially on both.

Commands and logs: `scratchpad/a673-{main,head}-e2e.log`, `a673-merge-build.log`. Floor case: `scratchpad/astra-673-floor-failed-save.py`.
