Reading is done and the scoped fences reran green here. Here is the check.

**VERDICT: RATIFY-WITH-CONDITIONS** — story 05 is ready to flip done, commit, and open the lane PR once the three small conditions below are paid. Nothing I found invalidates the evidence.

**FINDINGS (with evidence)**

1. **Every prior condition is paid, verified in the tree.**
   - Exact CREATE-refresh cause: `diagnosis.md` names the CREATE `desk_changed` refresh, GET 2287.1→2297.1 ms, PUT at 3928.3 ms, blank at click+159.1 ms, the pre-PUT-snapshot hypothesis refuted. The after-snapshot `decision_traffic` in both continuous red traces carries exactly those six requests, so the numbers are read from the record, not asserted.
   - Held-prop control labelled: test file header lines 1–5 and the inline comment on the third test say "synthetic negative control … must not be cited as the production cause."
   - Unreachable retention scoped: `mergeRefreshItems` only protects by rollback when kind, id, version and token match and `status[kind] === "unreachable"`. Other unreachable buckets keep the old empty-bucket behaviour (README says so explicitly).
   - Stale refusal: `refused` returns before `reportWriteFailure` when `state.version !== writeVersion`, so no old Retry closure is posted. Test 7 now resolves the newer success before the older refusal and asserts no receipt.
   - Continuous criterion: amended in story 05 criterion 2 and, as of this reading, in `current-phase-status.md` "Decisions made" (the parent's concurrent edit landed while I read; my first grep predated it). The first-frame-only probe is called green-on-main in story, README and design.

2. **The rig observer is sound.** `arm_first_paint` runs after the before-snapshot (graph_walk.py:4359 vs :4378), registers a capture-phase once-listener, and records every RAF with a sticky `firstUnreadableReadFrame`. `check_predicate` fails on either a non-readable first read frame or any later unreadable frame. The four rig unit cases exercise both directions (delayed fill, covered, heal-after-blank). I reran them: 4 passed.

3. **The retained traces prove the transition.** `verify_transition.py` reran here: red FAIL at both widths (143/148 unreadable read frames after +159.1/+77.3 ms), green PASS at both with 129 read-mode frames to ~1.07 s and no unreadable frame. The stale commit in red landed at click+77–159 ms; the green window covers that moment with margin. Both green `after.png` shots show the full sentence in the DECISION section, unobscured, at 393 and 1440. Console errors empty in all four.

4. **Store fence: no regression found.** I traced the version map through the seven orderings. Success after a newer write skips `clearWriteFailure`/`keptAt` correctly; `createPrimitive` never touches the map, so the CREATE refresh (snapshot version 0) correctly yields to the Done write (version 1); once a write settles, a refresh started afterwards sees equal, non-pending versions and the hub's row wins. The map is per store instance, so tests do not share state. Typecheck and build passed in the final DW capture. The probe file reran here: 7 passed.

5. **Provenance is honest.** Red traces carry rig 1.2.0 and index `83e4803…`; green carry 1.3.0 and index `19fcdcf…` at e8ad4022 dirty. `baseline.json` hashes show `dataSlice.ts` changed and `DecisionPullout.tsx`/`DeskApp.tsx` identical. The `--atlas` CLI miss and the exit-2 typecheck capture are retained and named as excluded, not hidden.

6. **Generated docs regenerated and fenced.** `voice.json`/`capabilities.yaml` now carry the story-05 claim anchored at `createDataSlice` (dataSlice.ts:174, verified) and the five fence tests. `test_philo_architecture.py` reran: 9 passed.

Tenets: this is the minimal repair (no pullout shadow, no new verb, no framework change), uses the existing SAVE FAILED/Retry idiom, and helps the Tuesday sitting. No over-engineering.

**CONDITIONS (before the flip)**

- **Test 2 asserts before the rollback refresh commits.** "keeps the prior body when a refused save's refresh fails" checks store and body right after the SAVE receipt appears, then only awaits `save` with no assertion after. The unreachable-retention branch in `mergeRefreshItems` is therefore not proven by a post-commit assertion; it may pass by timing. Add one line after `await save` asserting `items.decision[0]?.decisionMarkdown === "Prior saved decision"` and rerun the scoped file. Cheap, and it is the only fence for the one rollback item.
- **Roadmap README "Last updated" line** still names only 6-04 and 6-03; the operating cadence requires it to name 05 at done.
- **Commit scope.** The worktree now also carries `docs/generated/*` and `voice.json` regenerations plus the phase-status lines. Stage them with the story so the contract's index tree is the one the evidence was captured against; regenerate the contract after any restage.

**MISSED (ledger, not this story)**

- A newer write refused after an older write also failed restores the older *optimistic* text as "prior" (captured at the second write), not the durable value, until its rollback refresh lands. Self-heals on that read; one row in `ledger.md`.
- `probe.complete` is only set after the after-screenshot, so green traces read `complete: false`. Cosmetic; the frame list is what the verifier checks.

**TUESDAY:** Yes. Done keeps the sentence on screen at both widths; a refused save shows the old sentence with the existing receipt. Nothing new to learn.

**UNKNOWN:** Which `loadAll` sibling holds the commit for ~1.8 s (ledgered). The green rig runs used `--no-build`; the bundle hash differs from red and passes, but no record ties `index-CvfCFuGX.js` to the green `dataSlice.ts` hash. I ran no hub and no full suite; scoped fences only, per the brief.

Recommendation: pay the three conditions, flip 05 done, commit under the gate, open the lane PR. Do not merge; story 03 placement stays unratified and the phase stays open.

Claude session: `a843dd1c-2c5c-4b31-ad65-8fa9e225ac3a`. Raw response: `docs/internal/philo/phase-6/body/built-check-response.json`.

## Conditions paid — Astra, 2026-09-24 night

- Test 2 now asserts the store body, rendered body and SAVE FAILED receipt
  after `await save` has completed the failed rollback refresh. Final archive
  overlay remains `5 failed | 2 passed (7)` (`body/origin-main-red-final.log`).
  Parent DW rerun: `7 passed (7)` at `2026-09-25T03:32:01Z`.
- README Last updated and status name 05 at completion. Generated metadata,
  references, atlas, phase status, evidence and ledger ship with this story.
  Contract is generated only after explicit-path staging.
- Both MISSED findings are in the phase-local `ledger.md`.

The bundle unknown is narrowed by `body/build-identity.json`: Astra recomputed
the Vite source digest before the final test-only assertion change, matched
the emitted build ID, and matched both green observations' index SHA and
asset SHA. It records the unchanged green dataSlice hash. No product source
changed after those S4 runs. The final additional assertions change the test
source digest only; they are not shipped runtime code.
