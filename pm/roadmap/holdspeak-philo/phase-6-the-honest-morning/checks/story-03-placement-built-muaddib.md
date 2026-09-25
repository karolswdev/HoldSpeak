# Check — Muad'Dib, 2026-09-24 night, counsel on built: PHILO-6-03 placement (PR #649 @ 50472836)

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:
1. **The build matches what was ratified.**
   - **ChairHome.** The only change in `ChairHome.tsx` is the 4-line empty slot div placed right before `<CaptureBar />`. It is at `ChairHome.tsx:1443-1446` on the branch and moves to `:1450-1453` after the merge. I confirmed this with `git diff origin/main...HEAD -- web/src`.
   - **Portal.** `AmbientLayer.tsx:235` portals the card into the slot. `:238 findAftercareSlot` checks the slots in this order: the front surface window, then any visible surface window, then the Arrival, then the Floor list.
   - **Off-Arrival slots.** `SurfaceWindows.tsx:187` adds `data-aftercare-window-slot="top"` and `DeskListView.tsx:278` adds `data-aftercare-floor-slot="top"`.
   - **The fixed offset.** The inline `bottom:104px` is gone. It now lives in the class `.ambient-aftercare-fixed` (`react-app.css:270`), which applies only when no slot is found (`AmbientLayer.tsx:209`). The spatial Floor keeps it.
   - **Strings and buttons.** The card still uses the library Button, and the strings are unchanged (the removed lines are only the import, `return (`, className and style).
   - **Zero counts and 0/0.** The 0/0 guard on `Open proposals` was already on main (`origin/main AmbientLayer.tsx:180`). It is fenced in `AftercareNote.test.tsx:110-116`, which I ran: 5/5 pass. The zero-token fence is `AmbientLayer.test.tsx:195-226`.
2. **No overlap: confirmed by the logs and by my own rig run.**
   - **Arrival 393.** Final run `052820Z`: the card, the summary text and the CaptureBar each own 9/9 points, and the CaptureBar is the real one at 138 px.
   - **All six closure runs pass.** I opened every after.png. The card sits in flow above the capture bar on the Arrival, at the top inside the Meetings window, and at the top of the Floor list, at both widths.
   - **Dismiss.** At both widths the card leaves and the CaptureBar owns 9/9 points in `dismissed.png`.
3. **The phone scroll happens once, and each guard is fenced except one.**
   - **Guards.** The width guard is `AmbientLayer.tsx:175` (above 720 px, no scroll). The once-per-signal-and-slot key is at `:198`. The focused-field guard is at `:186`. The Arrival "is it covered" check is at `:196`.
   - **Mutation check.** I ran mutations on a copy of the branch:
     - Removing the focus guard turns the focus test red.
     - Removing the once-guard turns the "obscured phone slot once" test red.
     - Removing the width guard turns the same test red.
     - Removing the portal turns 5 tests red.
     - Removing the covered-slot check at `:196` leaves everything green. No fence covers it. The harm is small because `block:"nearest"` does not move a slot that is already in view.
   - **Slot changes.** The once-key includes the slot element, so the card moving to another surface's slot allows one more scroll. That is once per slot, not once per render.
   - **Scroll anchoring.** The mechanism is `chair.css:651-658`: while the Arrival slot holds the card, the rows above it are excluded from anchoring (`overflow-anchor:none`) and the slot is kept as the anchor. Its only fence is the rig. Diagnostic run `045018Z` was red with the old CSS (the capture bar and the dock owned the card's points), and `045707Z` plus both final runs are green. No unit fence exists, and jsdom cannot provide one.
4. **Fences reproduced.**
   - **Red before the fix.** I ran it on a `git archive` of the fork base `d8f608c8`, which is what `baseline.json` pins, not `e64114df`: `Tests 8 failed | 10 passed (18)`, the exact eight named tests.
   - **Green on the branch.** Focused frontend: `Test Files 3 passed (3) / Tests 30 passed (30)`. Python: `104 passed in 4.44s`. That needs `PLAYWRIGHT_BROWSERS_PATH`; without it, 4 errors in `test_graph_walk_first_paint.py` because Chromium is missing, which is the environment, not the code.
   - **The inherited fixture error.** `TypeError: currentBucket is not iterable` from `arrivalSummaryRun.test.tsx` reproduces on a `git archive origin/main` (`e64114df`) copy. It is inherited, and it is logged in the phase ledger (`ledger.md:32`).
5. **My rig run.** I ran `case.philo603.toast.arrival` at 393 with `--brain muaddib`, a fresh HOME, `--no-build` against a bundle I confirmed has the final CSS and classes, and `--out` to my scratchpad.
   - Result: `PASS: live`, `SOURCE: 50472836 dirty=False`.
   - The scroll count is 1 (`scrollIntoView` at 215 ms, scrollTop 0→479). Before the trigger the count was 0.
   - The card, the summary and the capture bar each own 9/9 points.
   - My after.png shows the card readable and not covered.
   - The BRIEF row scrolls off screen (0/9). That is the scroll the owner accepted.
6. **Records.**
   - Story status is `done` (story header and `current-phase-status.md:64`). The flip belongs to the lane, so it is lawful while the conflicts block integration.
   - `evidence-story-03.md` ships in the diff.
   - The WebGL fallback is recorded in `ledger.md:33`, with a shot.
   - All five generated `--check` scripts exit 0. `dw check holdspeak-philo` is ok. `dw verify origin/main..HEAD` is ok (2 commits).
   - The worktree is clean (0 changed files), and nothing under `pm/roadmap/holdspeak/` changed.
   - **Stale line.** The committed `voice.json:1049` (and `capabilities.yaml:2568`) says "the Phase 6 placement still needs its live 1440/393 atlas validation". This PR is that validation, so the line is now false.
7. **The five conflicts** (from `git merge-tree`, read-only):
   - The files are `docs/generated/boundary-candidates.json`, `docs/generated/graph.json`, `docs/internal/philo/graph/atlas.json`, `pm/roadmap/holdspeak-philo/README.md` and `phase-6.../current-phase-status.md`.
   - `ChairHome.tsx` and `test_philo_graph_atlas.py` merge on their own; the slot lands at `:1450-1453`. `AmbientLayer.tsx` was not changed on main.
   - None is a code conflict. The `atlas.json` hunks are ChairHome line numbers that moved (738 vs 745, 713 vs 720, 2309 vs 2322). The branch side also re-serialized the text with `\u` escapes.
8. **Tenet 1: not over-built.** The product change is about 110 lines in AmbientLayer plus small CSS. The rig adds about 361 lines to `graph_walk.py`. About 50k lines of evidence JSON is heavy, but it is the lane's evidence standard, not product weight.

CONDITIONS:
1. Correct `voice.json:1049` `meeting.aftercare.status_reason` so it no longer says the placement "still needs its live 1440/393 atlas validation", then regenerate `capabilities.yaml` and `CAPABILITIES.md`.
2. When reconciling, do not pick either side of the `atlas.json` anchor hunks. Regenerate the line numbers against the merged tree (the ChairHome slot moves 1442→1450), then re-run the generated `--check` scripts, `test_philo_graph_atlas.py` and the focused vitest on the combined tree.

MISSED (highest owner cost first):
1. **Empty band after Dismiss on the phone.** Because of the one scroll, the page stays scrolled to the bottom. After Dismiss this shows about 300 px of empty space above the capture bar (`052820Z/dismissed.png`, and my own run's scrollTop 413). It is the chair's existing end-of-scroll clearance, now visible to the owner. It is not a defect of the ratified design, but the owner will see it.
2. **Spatial Floor at 393 still covered.** The fixed fallback card covers the WebGL items and the top edge of the dock (`050750Z/after.png`). This is ledgered as out of scope and was already this way on main.
3. **Focused field on the phone.** If the owner is typing in the capture bar when the card arrives, it never scrolls. The card can then sit under the sticky bar until the owner scrolls. This is intended and fenced, but not visible to him.
4. **Unfenced covered-slot check** (finding 3).
5. **Stale BACKLOG row.** `pm/roadmap/holdspeak/BACKLOG.md` still says "product follow-up owed" for this item. The lane was not allowed to touch that roadmap, so Muad'Dib closes it.

TUESDAY: After a summary, the "Meeting ready" card now sits in the page directly above the capture bar and covers nothing. On a phone the page scrolls to it once, and he loses the brief at the top, which he accepted. Inside the Meetings window and above the Floor list, the card is the first thing on the surface. Dismiss removes it cleanly, but on a phone it leaves an empty band where it was. On the spatial Floor at phone width the old floating card still covers furniture and part of the dock. That is recorded and will not surprise him in a sitting. Nothing here adds a screen or a question; it only stops the card from hiding his summary.

UNKNOWN:
- Safari, physical-phone behavior and engines without scroll anchoring. Every run, including mine, is Chromium only.
- Whether my rig run opened a visible browser window. The rig has no headed flag; it ran in its default Page mode.
- The combined tree (branch merged with `e64114df`) is untested. I did not run any merge in a working copy.
- The multi-window case with a pull-out in front, which is ledgered as not walked (`ledger.md:35`).
- I did not re-run the meetings_window or floor_list cases or the 1440 Arrival. For those I read their observations and shots only.
