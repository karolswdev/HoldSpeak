# Counsel on built — Astra, 2026-09-20: HS-201-09/10/11, PR #590

Session `01a0bd9a-a815-7af1-b6d4-5cb8d89e4f23`. TWO-BRAINS §4. Read-only in wt-201-b.

## Round 1 — Astra

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **SITTING step 2 still breaks — Tenets 2, 3.** “Use this for summaries” saves the assignment but only reloads Models. It neither closes the window nor sends the existing return-to-task signal. The arrival can retain its SETUP row. The [handler](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/useConciergeController.ts:694) omits what ordinary Apply does at line 583. The [walk](/Users/karol/dev/tools/wt-201-b/tests/e2e/test_hs201_09_connect_engine_glass.py:369) checks the assignment through the API, then clicks an additional “Use these”; that does not prove the script’s single-gesture completion. `assets/story-09-shots/models-engine-connected-1440.png` still shows “Choose an engine” behind Models.

2. **OFF works, but the obvious way back ON fails — Tenets 2, 3.** OFF clears the exact `meeting.deferred_analysis` assignment through CAS. Reopening reads its tombstone and correctly retains OFF. However, selecting an existing engine and pressing “Use these” calls [_summary_assignment_revision](/Users/karol/dev/tools/wt-201-b/holdspeak/services/concierge_service.py:1330), which returns zero for that cleared assignment. [Apply](/Users/karol/dev/tools/wt-201-b/holdspeak/services/concierge_service.py:1598) passes zero, while [set_assignment](/Users/karol/dev/tools/wt-201-b/holdspeak/services/inference_assignment_service.py:402) checks the nonzero tombstone revision and refuses. Refresh cannot repair this mismatch. Adding the endpoint again can recover because that path uses the projected revision.

3. **READY survives an address edit — Tenet 3; Article VI.** The address field uses the raw state setter. Editing a checked address leaves READY and its previous model intact; submitting combines the new URL with that old model. Evidence: [field binding](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/ConciergeCore.tsx:471), [draft construction](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/useConciergeController.ts:660). Invalidate the result when the address changes and ignore responses for an earlier address.

4. **The Models face still misses its stated visual bar — Tenets 4, 5, 6.** The first repair remains [primary](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/ConciergeCore.tsx:279) while a READY Add-engine submit also becomes primary at line 510. Existing preset Download buttons at line 82 can likewise compete. The refused-check shots at both widths display `<urlopen error [Errno 61] Connection refused>`, not a plain reason. The new Check row also lacks an egress chip. I found no newly introduced raw button, modal, zero counter, or additional screen. The 393 overlap repair is visible.

5. **09’s contract and assignment changes are otherwise sound — Tenets 1, 3.** [endpointDraft.ts](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/endpointDraft.ts:16) supplies the existing eight-key contract; `model_library_service.py` is unchanged. The declaration, submitted-body test and service acceptance test collectively guard compatibility. Per-group Apply sends READY/OFF rows and preserves service validation. The Meetings row reads `summaryAssignment`, including OFF, rather than replacing it with a proposal. The [LAN capture](/Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-09.md:58) is honest evidence of discovery and assignment against `.43`; it does not establish the complete sitting.

6. **10 removes the automatic summary path — Tenet 3.** The shared import tail no longer enqueues. The decisive fence is [test_import_asks_for_no_summary_and_the_gesture_runs_the_frozen_producer](/Users/karol/dev/tools/wt-201-b/tests/e2e/test_hs201_summary_producer_chain.py:256): lines 367–379 assert no jobs, no drain, no receipt and zero inference-route attempts; afterward the gesture supplies the selection hash and receives the contacted-host receipt. The [browser fence](/Users/karol/dev/tools/wt-201-b/tests/e2e/test_hs201_summary_face_glass.py:704) independently checks the pre-run state and planned host. Imported meetings enter the same summary machinery as recorded meetings. The legacy import, transcript, parity and HS-143 census edits are **(a) lawful posture updates**, not papered regressions. “No contact” means no **summary dispatch**: LAN discovery happens during setup, and transcription is a separate operation.

7. **11’s narrow fixes are appropriate — Tenets 1, 3, 6.** `dw next --json` deliberately emits `{"next_story": null}` at `.githooks/dw:241`; the [consumer guard](/Users/karol/dev/tools/wt-201-b/holdspeak/web/routes/roadmaps.py:147) is the right fix. [SFX_BASE](/Users/karol/dev/tools/wt-201-b/web/src/lib/sfx.ts:193) follows Vite’s configured base for development and built serving; the glass fence checks both audio formats. Treating optional calendar connection as an OFFER is correct: its visible row preserves the information without manufacturing permanent attention debt. The open-actions filter remains available while selected, preserving the way back.

CONDITIONS: Fix findings 1–4 within the existing Models flow. Prove direct selection → arrival refresh without “Use these”; OFF → existing-engine selection → ON; address-edit invalidation; and primary-button arbitration with repairs/presets present. Capture both widths. Correct SITTING’s speech-engine precondition: a completely unassigned desk says “No engine yet,” not “No engine for summaries.” Complete and classify the quiet-tree suite and CI before reconsidering merge.

MISSED: Ranked by owner cost: failed setup return; failed re-enable; stale Check truth; conditional visual failures. Ledger the first four findings as **(b) product defects under HS-201-09**. Record the four import-test migrations as **(a)**. Update the stale import-enqueue debt at `current-phase-status.md:157`. Correct story 10’s “six, all red first”: its capture shows four failed, two passed. Preserve the named sync/Record transcription-state limitations.

The [PR documentation check](https://github.com/karolswdev/HoldSpeak/actions/runs/35495031870/job/106036373825) and [fork-point check](https://github.com/karolswdev/HoldSpeak/actions/runs/35490970756/job/106025713310) both fail on API-reference drift; that establishes inherited redness, not an identical drift delta.

TUESDAY: Import can now wait for the owner’s summary gesture, but Models still prevents a reliable cold sitting at step 2.

UNKNOWN: No tests or live product actions were run during this review; the tree was unchanged. Full-suite completion, remaining CI results, actual dictation into another app, and useful real-meeting output remain unverified. No owner-state write was identified; story 10’s captured commands omit the parent HOME value, so its complete isolation envelope cannot be certified from those records.
## Round 1 — Muad'Dib's response

Accepted in full. Findings 1–4 are (b) product defects under HS-201-09 and go back to its worker as one fix round: the summary selection fires the return signal like ordinary Apply and the walk proves the single gesture refreshes the arrival; OFF→ON uses the projected revision; an address edit invalidates READY; one filled primary with repairs and presets present, a plain reason instead of the raw urlopen text, an egress chip on the Check row. Stories 10 and 11 stand as ratified; the four import-test migrations are recorded (a). The three doc corrections (SITTING step 1 "No engine yet"; the paid import-enqueue debt line; story 10's "six red" sentence) ride with the fix round. The documentation drift on the PR and at the fork point is checked on main separately. Quiet-tree suite and CI are read before the merge.

## Round 2 — Astra

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Finding 3 remains partly open — Tenet 3.** Start Check, edit the address before it returns, then let the old request finish. Both stale-response branches return before clearing `addEngineChecking`: [controller:657](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/useConciergeController.ts:657). Check consequently stays disabled by [Core:536](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/ConciergeCore.tsx:536). The new [test:478](/Users/karol/dev/tools/wt-201-b/web/src/features/concierge/__tests__/connectAnEngine.test.tsx:478) verifies that stale results disappear, but never attempts another Check. Correcting an address can still strand step 2.

2. **Findings 1, 2 and 4 are paid — Tenets 3–6.** The real-LAN walk now proves one gesture clears SETUP and OFF→ON advances revision 3→4. The re-shots at 1440 and 393 support the plain refusal, egress chip and primary arbitration. Mixed presets remain honestly identified as Vitest coverage, not glass evidence: [counsel evidence:322](/Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-09.md:322). The three doc corrections and Philo refresh do not widen product scope.

3. **Every-step stranger walkability is not established — Tenets 2, 3, 7.** Step 2’s direct path is proved, with the correction defect above. [Step 7:48](/Users/karol/dev/tools/wt-201-b/pm/roadmap/holdspeak/phase-201-one-meeting-result/SITTING-07.md:48) still says only “Dictate one sentence into another app”; it supplies no starting gesture and remains unobserved.

CONDITIONS: Quiet-tree suite success alone does **not** clear #590. Restore Check recovery after an in-flight address edit; prove the replacement address can be checked after stale success and failure. Then read the suite and CI against main, distinguishing inherited failures from new regressions.

MISSED: Keep the Check defect as **(b)** under 09. Close the other accepted defects. Keep import-test migrations **(a)** and import enqueue debt paid. Retain capture-recovery, sync/Record state limitations, parked follow-through and reproduced baseline failures in the ledger.

TUESDAY: The normal setup path now works; correcting an address can still stop the stranger.

UNKNOWN: Full-suite completion and remaining CI results; owner-observed usefulness, restart retrieval and dictation; story 10’s parent-HOME provenance. I ran no tests or live product actions and changed nothing.
## Round 2 — Muad'Dib's ruling

Finding 1 is a (b) under 09 and is paid before the merge: the in-flight flag clears on every stale branch and the replacement address is proven checkable after a stale success and a stale failure. Step 7 of SITTING-07.md gains its starting and stopping gesture. Findings 2 and 3 are accepted as recorded. Under TWO-BRAINS §3 the lane owner rules after one round each: #590 merges on verification when CI's failure set reads as main's own (the local suite cannot run on this machine tonight; CI is the full run), with this record beside it. The ledger stays as Astra lists it.
