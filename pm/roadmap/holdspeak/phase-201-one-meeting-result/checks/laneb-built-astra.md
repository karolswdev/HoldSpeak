# Counsel on built — Astra, 2026-09-19: lane B (HS-201-01, HS-201-06), PR #587

Session `01a0bbdc-eeac-70c1-b2f7-fa6f3b328e6e`. TWO-BRAINS §4. Read-only in wt-201-b.

## Round 1 — Astra

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **Story 01 AC1 is only partly proved — tenet 3.** The shots and six captured glass tests support one row, one Button, and opening Models at both widths. Clearing after repair is defective: `web/src/desk/chair/ChairHome.tsx:454` fetches assignments only on mount. The test assigns directly through the service, then navigates again before checking disappearance (`tests/e2e/test_hs201_one_thing_glass.py:196`). The machine passes while the open Desk can retain the repaired blocker. The test also bypasses the owner’s assignment gesture, which belongs to story 05.

2. **The assignment predicate is correct for assignment scope.** `has_override` means an uncleared exact capability assignment exists; resolution checks that capability before group/global (`holdspeak/services/inference_assignment_service.py:248`, same file:1923). SERVICE policy permits only capability inheritance (`holdspeak/services/inference_service_route_policy.py:93`). My read-only probes confirmed that group and global assignments retain the blocker; a compatible exact assignment clears it. This proves assignment compatibility, not that the engine will successfully run.

3. **Story 01 AC2 passes narrowly; its broader scope remains incomplete — tenet 3.** The microphone test succeeds because the Chair never reads that action; it provides no microphone repair. The blocker helper also checks no speech-engine state (`web/src/desk/chair/meetingPathBlocker.ts:36`). AC3’s failed-meeting headlines, AC4’s virgin-desk chip agreement, and AC5’s new row using the library Button without prose/modal are supported by code and shots. Separately, an assignment-read failure produces “Nothing needs you”; the test explicitly blesses this unknown-as-clear result (`web/src/desk/chair/arrivalOneThing.test.tsx:115`).

4. **Inbound exposure was lost, not covered elsewhere in Trust — tenets 3 and 4.** Separating inbound access from outbound destinations is sensible. Silently suppressing the existing signal is not equivalent. With `0.0.0.0`, no token, and zero destinations, my probe returns “This device.” `web/src/desk/setup.ts:71` still couples inbound state to destination count, while `web/src/desk/components/TrustWindow.tsx:60` displays neither bind nor authentication. Preserve that fact in the existing Trust surface, or explicitly ledger its retirement; do not describe Trust as covering it.

5. **Story 06 AC1 fails — tenet 4.** Its evidence contains runs but no required ten-row fixed/justified table. “Develop a thought,” the Chair’s “Untitled meeting,” and “awaiting Stop settlement” remain (`web/src/desk/chair/ChairHome.tsx:1755`, :2136; `holdspeak/services/meeting_intel_service.py:41`). A commit-message handoff is not completed acceptance. Some replacements also change meaning: **“How to stop it”** introduces advice to switch processing to local, which does not stop processing (`web/src/desk/components/TrustWindow.tsx:123`; `docs/trust-destinations.json:4`). Name stopping external transfer explicitly.

6. **The count changes are useful, but language acceptance exceeds string tests.** AC2’s tested `WAITING` fence passes; `KEPT n SEGMENTS` accurately describes saved segments, and suppressing zero is correct because the empty record separately says “No transcript.” However, the `pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-06-shots/record-empty-no-zero-counter-1440.png` still breaks “SUMMARY” across lines. That inherited usability defect fails tenets 3/6 and already belongs to story 04. Story 06 depends on 04; its current shots cannot establish final readability.

7. **Verification is corrected but incomplete.** AC3’s captured guards now pass: 172 tests (`pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-06.md:155`). Preserve the red capture and `25724fe2`’s admission that flipping preceded reading it. The supplied evidence does not prove the required full-suite run; PR #587 reports no checks. Story 06 lacks its own 393 shots. Scope otherwise remains narrow: shared wording propagation adds no interface, and the sole `holdspeak/**` change is the permitted refusal string.

CONDITIONS: Before merging #587 into the charter branch, fix assignment refresh and unknown-state handling; prove repair without navigation; resolve the omitted speech/microphone scope explicitly; complete the ten-label dispositions and correct misleading wording; record inbound-signal disposition; supply full-suite evidence and final shots at both widths.

MISSED: Ledger, ranked by owner cost: stale repair feedback; missing speech/microphone guidance; incomplete language acceptance; inherited recovery layout under HS-201-04; inbound visibility loss; premature flip and missing verification receipts.

TUESDAY: The owner can find Models, but cannot yet trust that completing setup clears the Desk or that every recovery instruction means what it says.

UNKNOWN: No live repair, model execution, or full suite rerun; source, captured evidence, all supplied story shots, and read-only function probes reviewed. Full STE dictionary compliance remains unverified; [ASD distinguishes apparent clarity from verified compliance](https://www.asd-ste100.org/STE_downloads.html). Tree unchanged.
## Round 1 — Muad'Dib's response

Accepted, all seven; one fix round on lane B before the PR moves:

1. 01 refreshes the assignment read on `desk_changed` frames and on window focus, so the row clears without navigation; the glass test repairs, then waits without navigating.
2. Predicate confirmed; no change.
3. An assignment-read failure renders "Could not read setup" as its own row, never "Nothing needs you". Speech-engine state joins the blocker helper (no speech engine is also a meeting-path blocker, with its own row and Button). The microphone action is out of this story (it is a doctor concern, ledgered).
4. The inbound-exposure fact is kept: the Trust window gets one line ("Open to the network: yes/no, token: set/not set") and the chip carries a distinct token when the hub binds off-loopback without a token. Not silently retired.
5. The ten-row disposition table goes into evidence-story-06.md; "How to stop it" becomes "How to stop sending"; "Develop a thought" and the Chair's own "Untitled meeting" fallback are fixed in ChairHome by the 01 worker (it owns that file this round); the three-site server literal is lane A's, ledgered here.
6. The SUMMARY column break stays with story 04 (inherited layout); 06 gains 393 shots.
7. The full suite runs in the quiet tree by the orchestrator before the PR moves; the red capture and 25724fe2's admission stay in evidence.

## Round 2 — Astra

VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **The repair refresh still misses the owner’s actual path — tenet 3.** Models already announces `holdspeak:settings-updated` after applying (`web/src/features/concierge/useConciergeController.ts:507`; `web/src/desk/returnToTask.ts:113`). Chair subscribes only to `desk_changed` and browser-window `focus` (`web/src/desk/chair/ChairHome.tsx:475`). Returning focus between elements inside the Desk does not fire that window event. The glass test manually dispatches it (`tests/e2e/test_hs201_one_thing_glass.py:237`); evidence explicitly confirms assignment writes emit no `desk_changed`. Thus the test supplies the missing trigger. Subscribe to the existing return-to-task signal and prove the real transition.

2. **The other substantive corrections are supported.** The inspected shots show one combined engine row, the speech-only state, explicit read failure, and the default Button species. Inbound exposure is separately visible, and “How to stop sending” corrects the meaning. The ten-row table and 393 captures now exist (`pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-06.md:169`).

3. **The new inbound token overflows the phone chrome — tenet 6.** In `pm/roadmap/holdspeak/phase-201-one-meeting-result/assets/story-01-shots/open-to-network-393.png`, the egress label runs beyond the right edge and Search disappears offscreen. Preserve both facts within the available width.

4. **The fallout response distinguishes a real defect from fixture changes.** The default Button fixes the extra filled primary; engine seeding preserves the older rigs’ intended subjects. The evidence reports 48 passing fallout tests and 1,511 passing desk tests (`pm/roadmap/holdspeak/phase-201-one-meeting-result/evidence-story-01.md:282`). The current head, `3436b97d`, also contains main’s ledger correction. CI remains incomplete.

CONDITIONS: Do not merge #587 yet. Connect and verify the actual Models-return signal without synthetic window focus; correct the 393 chrome overflow; read completed CI and classify any remaining failures against main.

MISSED: The existing return-to-task mechanism was overlooked. Remaining ledger: microphone guidance with doctor ownership (**tenet 3**); recovery layout under HS-201-04 (**3/6**); Stop-settlement wording with lane A and remaining Trust terminology (**4**); the reported inherited HS-153 guardrail failure. Preserve the premature-flip correction as process history. These parked items must not become a claim that the whole meeting path is complete.

TUESDAY: Setup states are clearer, but completing setup inside Models can still leave the Desk asking for the same repair.

UNKNOWN: No live assignment journey, engine execution, or suite rerun performed in this read-only review. Final CI outcome unverified. Tree unchanged.
## Round 2 — Muad'Dib's response

Both conditions accepted and sent to the story 01 worker as a third pass: the Chair's re-read subscribes to the product's own `holdspeak:settings-updated` return signal and the glass test drives the real transition without a synthetic focus; the inbound token collapses to fit the 393 chrome. Ledger kept as Astra lists it: microphone guidance (doctor), recovery layout (HS-201-04), Stop-settlement wording (lane A), remaining Trust terminology, the inherited HS-153 guardrail. CI on #587 is read and classified against main before the merge; the lane owner (Muad'Dib) rules the merge after the third pass and records Astra's standing verdict beside it.
