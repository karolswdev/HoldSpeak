# Counsel on built — Astra (Codex `gpt-6-astra`, xhigh): PR #725 faces lane wave 1, r2

Session `01a0fa6d-1a34-7691-9a65-c14aa074fbc9`. Verbatim.

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The r1 fixes are paid, and the A4 seam is right.** I reproduced the new A3 fences against `07aa76e3`: 8 failed, 25 passed; against `82353f48`, the two new A4 child-close tests failed. The current A4 test passes 7/7, and the A3 capture reports 61 files and 484 tests passing with typecheck and baseline green. The Settings words and fence changed together in `07aa76e3`; the Mic failure-title wording and fence changed together in `667c110a` and are stronger assertions, not loosened ones. Evidence: [A3 baseline failures](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Oom2AARnw3/a3.log), [A4 baseline failures](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.Oom2AARnw3/a4.log), `pm/roadmap/holdspeak-philo/phase-13-the-desk/evidence-story-04.md:31`, `web/src/pages/cores/__tests__/settingsSummaryName202.test.tsx:45`, `web/src/desk/components/MicButton.test.tsx:397`.

   A4 closes by the stored pullout ID through the card’s `onClose`. No render mount is omitted: the glass matrix covers the Chair, list and Floor mounts, plus the Thought frame; it records representative openers rather than every call site. The actual atlas close case passed at both sizes, with isolated DB provenance and the Desk beneath the closed window receiving the hit test: [1440 after](</var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.sh3Jc6d9ho/20261002T031740Z-case.p13.close.intelligence_gone-muaddib-1440/after.png>), [393 after](</var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.DEmw4lO4Xn/20261002T031824Z-case.p13.close.intelligence_gone-muaddib-393/after.png>). Coverage note: `pm/roadmap/holdspeak-philo/phase-13-the-desk/story-05-a4-close-means-gone.md:64`.

2. **Tenet 4: the unsupported-browser Mic branch still exposes prose.** It puts `reason` in both the title and accessible name; the existing test expects that sentence. The tightened fence starts at the later `.desk-mic-failure` branch and does not cover this return path. Evidence: `web/src/desk/components/MicButton.tsx:195`, `web/src/desk/components/MicButton.test.tsx:53`, `web/src/desk/__tests__/philo13FacesDoNotLie.test.tsx:64`.

3. **Tenet 3 / A4 proof: the Meeting close fence bypasses the producer and has no rendered walk.** The unit test replaces `MeetingConflictRecovery` and directly supplies `{ deleted: true }`; it never exercises the child’s real API response or proves the rendered close transition. The “no route seeds a meeting conflict” ledger is incomplete: an existing integration test creates a tombstone through the meeting repository and verifies the real resolve route returns `deleted: true`. Evidence: `web/src/desk/__tests__/pulloutCloseQualified.test.tsx:20`, `web/src/desk/__tests__/pulloutCloseQualified.test.tsx:125`, `tests/integration/test_meeting_conflict_recovery.py:132`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/story-05-a4-close-means-gone.md:64`. I ran the producer test: 1 passed.

4. **Tenet 5: the Coder button deferral is misrouted.** `Watch live` remains a raw `<button>`, alongside four other raw actions in the component. The standing library-Button rule applies; C8 is scoped to type sizes and typography, not component conversion. Evidence: `web/src/desk/pullouts/CoderPullout.tsx:173`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/story-18-c8-the-12-px-floor.md:26`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/story-05-a4-close-means-gone.md:64`.

5. **Tenet 7 / A.10: A3 is correctly marked in progress, but the Meetings list rail still lies.** The detail face says `SUMMARY STORED`; the list rail still derives `OFF` from `intel_status: disabled` even when a summary is stored. Evidence: `web/src/pages/cores/history/helpers.ts:82`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/story-04-a3-faces-that-do-not-lie.md:68`. The Chair’s availability label, Settings’ configured label and Trust’s egress label are honest in the reviewed shots; this list-rail state is the exception.

CONDITIONS:

1. Replace or remove the unsupported-browser sentence and fence that rendered branch’s title and accessible name in the same change.
2. Fence the Meeting tombstone close through the real producer and rendered transition. Coder’s no-glass limitation may stay ledgered only as a clearly scoped limitation; it does not replace fixing the raw Button violation on `Watch live`.
3. Do not mark A3 done until H-A3’s list-row field is derived from persisted summary data, the rail says `SUMMARY STORED`, and the real-producer route fence passes. **I accept H-A3 for Astra’s lane** on that contract; add it to the phase status handoff table, where it is currently absent (`pm/roadmap/holdspeak-philo/phase-13-the-desk/current-phase-status.md:204`).
4. Record the orchestrator’s full-suite result and investigate the failed Documentation Navigation check before the merge record is complete.

MISSED:

1. **Highest owner cost:** the stored-summary list rail remains `OFF`; the amendment acknowledges this and keeps A3 in progress, but the shared handoff register omits H-A3.
2. **Medium:** the unsupported-browser Mic sentence sits outside the new fence and is still asserted by an existing test.
3. **Medium:** the Meeting glass ledger overlooks the existing real tombstone-resolution producer test; the new UI fence fabricates the exact field it reads.
4. **Lower:** `evidence-story-05.md` has no captured run for the 994 follow-up. I independently verified the old test fails and the current seven-test unit file passes, but that rerun is not in the story evidence.

TUESDAY: Not yet—the retry, Setup and close paths work, but the Meetings list can still say `OFF` for a stored summary.

UNKNOWN: The local full suite is still running. PR checks show Documentation Navigation failed, Unit Tests pending, and E2E/Integration queued; its failure log is unavailable while the run is active. The phase status says CI is not a merge gate. The atlas walks used source `667c110a` with `dirty=true` from the known concurrent canvas work and uncommitted A3 evidence; each DB was under the rig’s isolated temporary HOME. I made no changes to the worktree.