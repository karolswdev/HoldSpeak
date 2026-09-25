# Check — Muad'Dib, 2026-09-24 night, counsel on built: Phase 6 lane B (PR #647 @ f443a3ff)

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **04: the route fix is correct, and I reproduced the red myself.** `holdspeak/web/routes/decisions.py:64-74` (worktree) first checks whether the desk owns the id and whether the lifecycle service owns it. These checks are direct database reads, so they add no observer rows. The route then calls exactly one service. An unknown id goes through the desk registry once.
   - I ran `git archive 66205729` into my scratchpad, added the lane's test file, and ran it with `PYTHONPATH=<archive>` (I confirmed `holdspeak.__file__` resolved to the archive). Result: 2 failed, 3 passed.
     - `test_missing_id_has_one_real_observer_failure_row` failed because 2 rows were written.
     - `test_lifecycle_only_id_uses_one_observed_lineage_read` failed because the old route also wrote a false `PrimitiveService` NotFound row.
   - On the lane, the scoped run `test_philo6_04_one_cause_one_row.py` + `test_philo5_one_decision.py` + `test_philo3_01_decision_route.py` gave **33 passed** (`HOME=$(mktemp -d) uv run --extra dev pytest`).
   - Legacy reads still work: a lifecycle-only id still resolves with its lineage, and when both services own an id the desk wins (tests at `test_philo6_04_one_cause_one_row.py:124-160`).
   - The "no global suppression" fence (`:163-190`) works at the service level. Its red comes from a deliberate mutation that removes both observers (`rows/observer-mutation.txt`). It does not go through the route. That is acceptable, because the route change does not touch the observers.
   - One small, harmless side effect: `ServiceError` from the desk path is now caught at `:73`. Before, it would have propagated.

2. **04 parity.** `rows/verify_parity.py` re-ran for me:
   - HTTP rows 67 and 68 vs `op` row 6 on the archive, then HTTP 67 vs `op` 6 on the lane, at both 1440 and 393. Output: `FAIL 2:1 -> PASS 1:1`.
   - I read both kinds of observation. **The atlas cases themselves report `verdict: pass` on both the red and the green side** (verify_parity asserts `observation["verdict"] == "pass"`). The 2:1 → 1:1 verdict comes from the lane's sidecar script (`walk_one_row.py` + `verify_parity.py`), not from the rig. The story says "goes from FAIL 2:1 to PASS on the rig", which is imprecise.
   - To make the parity case applicable at 393, the atlas gained a 393 width for the HTTP case (`atlas-phase3.json:6500`). This is disclosed in `rows/README.md`.

3. **05: cause and seam.**
   - `DecisionPullout.tsx` did not change (identical sha256 in `body/baseline.json`). The repair is entirely in `web/src/desk/store/dataSlice.ts`: each item gets a write version, a refresh takes a snapshot of those versions before it reads, and `mergeRefreshItems` keeps any item that was written after the snapshot or is still pending.
   - The diagnosis in `body/diagnosis.md` agrees with the retained traffic. The CREATE `desk_changed` refresh sends its GET at 2287 ms and gets the blank body back at 2297 ms. The Done PUT runs at 3928 ms. The stale state is committed at click+159 ms, after a slower sibling inside `Promise.all` finishes.
   - The protection is based on versions, not timing. So the unidentified slow sibling is a **separate performance item, not a hole in this fix**. It is ledgered only in the phase-local `docs/internal/philo/phase-6/ledger.md` row 1, not in BACKLOG. The brief says that is by the owner's rule.
   - Size: about 190 lines. The part that protects a rolled-back item during an unreachable read is the most speculative piece, but a red test covers it. It is within the chartered "failed save" scope. Borderline on Tenet 1; not a bounce.

4. **05: the fence is an honest strengthening, not a moved goalpost.**
   - In the retained records, the first readable frame appears at 10–12 ms on archived main at both widths (`verify_transition.py` output, which I re-ran). The Phase 5 defect (empty at 0.95 s) is a later wipe, not a blank first paint.
   - The new predicate requires the first frame **and** every later frame to be readable. That is a strict superset of the first-frame check, so it is harder to pass, not easier.
   - The probe is armed before the click: `graph_walk.py` calls `arm_first_paint(page, pre_case)` right before `run_step(trigger)`, with a capture-phase `once` click listener. All four records show `armedAt <= clickedAt`.
   - The red is real: blank `"DECISION"` at +159.1 ms (393) and +77.3 ms (1440), then PASS with 129 readable frames on the lane.
   - The first-frame-only run under `body/red-s4-393/` is a PASS inside a folder named "red". README:64 labels it as a negative control. The folder name alone still misleads.
   - The green probe stops at terminal observation, about 2.1 s. That covers the 77–159 ms race by a wide margin.
   - The after.png files (all opened) cannot show the defect: the red after.png is healed at settle, so the proof lives in the frames. This is disclosed.

5. **05: I reproduced the red myself.** I ran `philo605DecisionBodyDiagnosis.test.tsx` on the archive (node_modules copied, not symlinked; Node 22): **5 failed**. Two examples: `'Rejected new decision'` where `'Prior saved decision'` was expected, and `''` where `'Keep the local ledger'` was expected. On the lane, the two files `AmbientLayer.test.tsx` + `philo605…` give **16 passed**. The failed save is fenced: rollback happens before a slow refresh; the prior body survives a failed refresh; a stale refusal posts no Retry.

6. **03 zero omission.**
   - The render change is at `AmbientLayer.tsx:166-178`. `intelligenceAttention.ts:95-96` is untouched.
   - Archive red, which I reproduced: 3 failed. One is `expected <p></p> to be null` for 0/0; the other two are the single-zero cases. Green on the lane. This meets UX-CANON A.8.
   - **No placement code shipped.** The diff touches no `.css` in `web/src`, no `ChairHome.tsx`, and `bottom: "104px"` is still at `AmbientLayer.tsx:173`. Nothing in `web/src` references `aftercare-slot`.
   - Story 03 is still `in-progress`; the 8bd4a05b commit flips no status.

7. **03 canvas.** I opened today-393, proposed-393, summary-open-393, capture-393 and summary-open-1440.
   - The today board shows the real defect: the card covers the summary and the capture bar at 393.
   - The proposed card sits in normal flow before the CaptureBar. At the measured scroll there is no overlap and no modal.
   - There are two asks, and both are clear.
   - The phone mechanism depends on auto-scroll, and the README says so honestly. In the proposed-393 board, auto-scroll moves the owner's view: the head of the page ("Nothing needs you" and NO CALENDAR) has scrolled off. The owner should decide that knowingly.

8. **03 `chairhome.patch`.**
   - It does **not** touch `:685`, the capture-clearance measurement. It adds an empty `data-aftercare-slot` div at `ChairHome.tsx:1442`, before `<CaptureBar />`. `git apply --check` passes (I ran it).
   - It is marked HOLD / PROPOSAL ONLY in `README.md` and `chairhome-rationale.md`. Nothing shipped depends on it.
   - The slot alone places nothing. The real build also needs a portal from `AmbientLayer` and the auto-scroll logic. Neither is in the patch.

9. **The fence law holds.**
   - Every red I checked comes from a real producer or a deliberate, labelled mutation. None is an "Unknown tool" or missing-symbol red.
   - The first-paint browser tests (`test_graph_walk_first_paint.py`): 4 passed. They first errored because the isolated HOME hid the browsers; they pass with `PLAYWRIGHT_BROWSERS_PATH` set. That was an environment problem, not a defect.
   - Generated files: `philo_graph_reference.py --check`, `philo_api_reference.py --check`, `philo_boundary_census.py --check` and `generate_capability_docs.py --check` are all clean. Only the known subtype notes appear.
   - `dw check holdspeak-philo`: ok. `dw verify 66205729..HEAD`: `ok (3 commits verified)`.
   - Worktree `git status` is clean, before and after my checks. No `pm/roadmap/holdspeak/` path changed.
   - Story flips: e8ad4022 flips 04, f443a3ff flips 05, and 8bd4a05b flips nothing.

10. **Merge sanity.**
    - `git merge-tree origin/main HEAD` is clean.
    - Against lane A (`f6c0c0d1`): content conflicts in `pm/roadmap/holdspeak-philo/README.md` and `current-phase-status.md`. These are bookkeeping conflicts, as expected.
    - Both lanes touch `docs/generated/{api-reference,boundary-candidates,graph}.json` and `atlas-phase3.json`. Those auto-merge, but whichever lane lands second must regenerate.

11. **The "Muad'Dib checks" are not Muad'Dib's checks.**
    - `checks/story-03-check-response.json`, `body/design-check-response.json` and `body/built-check-response.json` all show `modelUsage: claude-fable-5-1`. These are `claude -p` runs that Astra started from Astra's own brief.
    - The story-03 brief (`checks/story-03-check-brief.md`) is leading. For example: "Parent already opened three proposed shots; current phone chrome truncation appears existing shell behaviour".
    - Despite that, the files are named `*-muaddib.md`. `current-phase-status.md` says "Muad'Dib built conditions paid", and `lane-report.md:46,102` says "Muad'Dib check conditions paid" and "Muad'Dib counsel is recorded". Nothing discloses the provenance.
    - These are useful checks, but calling them Muad'Dib's check violates the two-brains separation. This counsel is the orchestrating session's first real check.

12. **Tenet 1.** Nothing is badly over-built. The 05 rollback-under-unreachable protection is the heaviest piece and is borderline (finding 3). The rig's `_DECISION_TRAFFIC_JS` fetch wrap only turns on for `first_paint_after` cases.

CONDITIONS:
1. Rename or relabel the three `checks/*-muaddib.md` records, and the sentences in `current-phase-status.md` and `lane-report.md`, as "Astra-invoked `claude -p` (fable-5-1)". This counsel is the Muad'Dib check of record.
2. Story 04 box 5 and the evidence must say that the 2:1 → 1:1 verdict comes from the lane's sidecar verifier (`verify_parity.py`). The atlas refusal cases pass on both sides.
3. Before the 03 canvas goes to the owner, fix two things:
   - Add the case where the aftercare card arrives while he is not on the Arrival. `AmbientLayer` is mounted in `AppShell.tsx:24`, on every surface, and the slot exists only in ChairHome. Add a board or at least a line.
   - Correct the seam cite: story 03 and the status name `:685`, but the patch is at `:1442`. Also state that the build is the slot plus an AmbientLayer portal plus auto-scroll, not only the patch.

MISSED (ranked by owner cost):
1. **03: no answer for off-Arrival arrival.** The card appears on every surface, but the canvas covers only the Arrival. The owner could ratify a placement that never runs where he actually is.
2. **03: auto-scroll moves his reading position.** When the signal arrives, the head of the Arrival scrolls off (proposed-393). That is a Tenet 7 trade-off, and ask 2 should say so in plain words.
3. **05: pre-existing, not ledgered.** An unreachable collection read empties that entire kind (`desk/api.ts:636` sets `status[kind]="unreachable"` with an empty bucket). The fix restores only the one rolled-back item, so after a failed save plus a failed read, one decision stays and the others disappear. `ledger.md` does not list this.
4. **03: a zero-open card keeps the "Open proposals" verb.** With 0/0 the card shows only the title and still offers "Open proposals", which opens nothing. This is outside the zero-token box, but it is the same A.8 spirit.
5. **05 provenance.** The red continuous logs say `rig=1.2.0`, but the predicate text in them comes from the 1.3.0 code. It is a cosmetic provenance gap. The green runs say 1.3.0.

TUESDAY: When he opens a missing decision, he now sees one broke row, not two. When he presses Done on a decision at 393, the text stays on screen for every frame, instead of going blank for about a second while a stale refresh lands. When a meeting has no decisions, the toast no longer says "0 decided". The toast still covers his summary and the capture bar at 393. That fix is a canvas waiting for his word, and the canvas has not yet shown where the card goes when he is not on the Arrival. Lane B is ready to merge for 04, 05 and the 03 zero omission once the labels are corrected. Story 03 stays open.

UNKNOWN:
- I did not re-run any rig case (optional under the brief). I read the retained observations and re-ran their verifiers (`verify_parity.py`, `verify_transition.py`).
- I did not run the full suite or the web baseline, by design.
- I did not verify the `loadSetup` rejection path or the double-refusal race. Both are ledgered as unreproduced.
- Who told Astra that its `claude -p` checks count as Muad'Dib's: nothing in the tree says.
- The canvas harness composes production species, but I did not read `canvas/harness/main.tsx` line by line to confirm it adds no geometry that would flatter the proposal.
