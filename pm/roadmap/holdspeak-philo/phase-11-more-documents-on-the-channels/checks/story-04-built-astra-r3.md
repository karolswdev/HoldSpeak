VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The failed and refused receipts now survive the click that leaves the row.** `ClosedReceipt` renders beside the egress chip when the row is closed, and both hosts have tests that close a FAILED row or pick another row after a refusal (`web/src/desk/surface/send/SendWell.tsx:261`, `web/src/desk/surface/send/SendWell.tsx:576`, `web/src/desk/surface/send/__tests__/SendWell.test.tsx:355`, `web/src/features/channels/__tests__/SendWell.test.tsx:226`). The four transition tests failed on `f4127c441` and pass now (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:624`); my focused run passed 41 tests. The update’s closed-row shot shows `LAST SEND FAILED · NO PERMISSION · NOTHING SENT · THIS DEVICE` at 1440, and the 393 shot keeps the words visible as chips wrap ([1440 shot](</Users/karol/dev/tools/wt-philo-11-04/pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-shots/28b-destination-latest-failed-1440.png>), [393 shot](</Users/karol/dev/tools/wt-philo-11-04/pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/assets/story-04-shots/28b-destination-latest-failed-393.png>)).

2. **The actual outcome producers agree with the UI’s state fields.** On the current head, real Phase 10 atlas cases for FAILED, REFUSED and UNKNOWN passed at both widths. The live hub returned a failed send with reason `github_target_not_found`, a refusal with `destination_parked`, and an unknown send with reason `github_exit_1`; each run used a temporary-HOME database. For example: [failed observation](/tmp/astra-708-atlas-r3/failed-1440/20260930T081101Z-case.p10.send.failed-astra-1440/observation.json), [refused observation](/tmp/astra-708-atlas-r3/refused-1440/20260930T081209Z-case.p10.send.refused-astra-1440/observation.json), [unknown observation](/tmp/astra-708-atlas-r3/unknown-1440/20260930T081353Z-case.p10.send.unknown-astra-1440/observation.json). The SENT and PREPARED face cases at both widths and their operation cases also passed. These walks validate real outcomes and current screens; they do not test closing the row.

3. **The closed-row seat and grammar are ratified; the exact failure sequence is an application of the ratified vocabulary.** A3, B2 and A4c show a destination’s result on the closed row’s second line beside egress, with SAVED or POSTED examples; T1 shows REFUSED and NOTHING SENT while the row is open (`origin/feat/philo-11-03:.../assets/story-03-canvas/README.md:51,57,62,79`). The closed update shot’s exact failure combination is not pictured on those boards. It reuses the existing closed-state `LAST SEND FAILED` chip and the established failure reason and `NOTHING SENT` words. I judge that consistent with the ratified row grammar, but not a literal word-for-word match to a canvas shot.

4. **The UNKNOWN and no-answer closed-row branches lack transition fences.** The implementation adds detailed closed-row rendering for UNKNOWN and for a lost answer (`web/src/desk/surface/send/SendWell.tsx:265`); current tests cover UNKNOWN while open, not after closing or changing rows (`web/src/desk/surface/send/__tests__/SendWell.test.tsx:216`). The four new transition tests cover only FAILED and REFUSED. This leaves the same receipt-loss seam unproved for the other two claimed states.

5. **PR #708 cannot merge against its current base.** GitHub reports it as `CONFLICTING` / `DIRTY`, with no status checks reported. The lane correctly leaves integration until #707 settles ([PR #708](https://github.com/karolswdev/HoldSpeak/pull/708); `pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:33`).

CONDITIONS:

- Add rendered-transition fences for UNKNOWN and a lost/no-answer result on both hosts. Assert the closed row’s result and egress after closing it or selecting another row, and show the fences fail before the fix and pass after it.
- After #707 merges, resolve the stack conflict and run the required integration suite and gate on the resulting tree before merge.

MISSED:

1. Highest cost: UNKNOWN or no-answer detail may disappear when the owner leaves the row; those new branches have no transition test.
2. The PR remains conflicted, so this head cannot merge yet.
3. Chair and picker proof for G4 and the heading-chip rule remains assigned to story 05; story 04 records them as implemented, not proven (`pm/roadmap/holdspeak-philo/phase-11-more-documents-on-the-channels/evidence-story-04.md:31`).

TUESDAY: Yes—the update’s send flow remains, and a closed failed destination keeps its reason, “NOTHING SENT,” and egress on screen.

UNKNOWN: I did not rerun the full web suite on this head; the focused 41-test run and selected real atlas walks passed, while the lane reports a 2,991-test baseline. The atlas GitHub CLI boundary uses a fixture, so no real external GitHub or Slack delivery was verified. The canvas assets I inspected are on `origin/feat/philo-11-03`, outside the #708 checkout. The #708 worktree remains clean at `2ac47c3c6`; I changed nothing in it.