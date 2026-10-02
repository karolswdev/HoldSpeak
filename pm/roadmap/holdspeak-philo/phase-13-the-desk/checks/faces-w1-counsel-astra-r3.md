# Counsel on built — Astra (Codex `gpt-6-astra`, xhigh): PR #725 faces lane wave 1, r3

Session `01a0fa6d-1a34-7691-9a65-c14aa074fbc9`. Verbatim.

VERDICT: RATIFY-WITH-CONDITIONS — I would not merge #725 at `41ebe0ee`; I would ratify it after the conditions below. PHILO-13-04 and PHILO-13-11 remain honestly in-progress.

FINDINGS:

1. **The A4 fix is at the right seam.** `web/src/desk/components/Pullout.tsx:73` closes using the store’s `pulloutId`; the `DeskApp`, `WorldStage`, and `DeskListView` mounts pass each card’s store ID (`web/src/desk/DeskApp.tsx:261`, `web/src/desk/gl/WorldStage.tsx:270`, `web/src/desk/components/DeskListView.tsx:412`). I found no opener bypass. The new meeting glass uses the real meeting repository and resolution route; it checks the 200 response, deleted DB row, removed card, and Desk hit at 1440 and 393 (`tests/e2e/test_philo13_05_close_glass.py:215`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-05-shots/meeting-tombstone-after-1440.png`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-05-shots/meeting-tombstone-after-393.png`). I also walked the actual atlas cases `case.p13.close.intelligence_gone` and `case.p13.record.refused_not_recording` at both widths; all four passed. The observations are under `/private/tmp/philo13-r3-counsel/`.

2. **The targeted A3 corrections and fences are paid.** The six focused test files pass, 49 tests total. Commit records report the changed fences red before and green after: `667c110a` records the A3 fences red on `07aa76e3`; `e0eaa3e6` records the mic fence red 3 / green 31; `41290806` records the Coder close and raw-button fences red before and green after. The Settings, Trust, Chair, and Meetings faces name configured state, egress, availability, and stored state respectively; the Settings exact-word test remains intact (`web/src/pages/cores/__tests__/settingsSummaryName202.test.tsx:45`). The targeted Brief, Room-publish, People, and Ask failures have short failure copy and no raw server text in their tested branches (`web/src/desk/__tests__/philo13FacesDoNotLie.test.tsx:52`). MicButton now names the unsupported-browser failure, and its title fence covers that branch. The Coder card uses library Buttons; its source fence is in `web/src/desk/__tests__/pulloutCloseQualified.test.tsx:133`.

3. **H-A3 is an acceptable handoff, not a delivered route change.** The register names the stored-summary field, its source, the list/search route fence, and the A3-W consumer; it keeps A3 in-progress until both halves merge (`pm/roadmap/holdspeak-philo/phase-13-the-desk/current-phase-status.md:213`). I accept that contract.

4. **The full-suite triage is documented, but the current Documentation Navigation check fails.** Commit `41ebe0ee` records 11 failures, 13,766 passes, and 1 error, with the branch reds and inherited failures triaged. The current DocNav failure is a separate, reproducible boundary-census drift: the generated candidate lists AskPanel at line 122, while the current source is at line 123 (`docs/generated/boundary-candidates.json:6946`, `web/src/desk/components/AskPanel.tsx:123`).

5. **Yes, I require a new A4 follow-up capture appended before merge.** The existing capture is timestamped before the Coder and meeting follow-ups, uses `tail` pipelines without `pipefail`, and reports the earlier test counts (`pm/roadmap/holdspeak-philo/phase-13-the-desk/evidence-story-05.md:9`). Its coverage note also still says there is no meeting glass and that Coder has five raw buttons (`pm/roadmap/holdspeak-philo/phase-13-the-desk/story-05-a4-close-means-gone.md:64`); both statements are stale.

6. **The C1 ratification is valid, but its README is stale.** The owner’s ratification and status record agree that the canvas is ratified and the build remains in-progress (`pm/roadmap/holdspeak-philo/phase-13-the-desk/story-11-c1-the-workbench-look.md:76`, `pm/roadmap/holdspeak-philo/phase-13-the-desk/current-phase-status.md:248`). The canvas README still calls it a draft awaiting ratification (`pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-11-canvas/README.md:3`).

CONDITIONS:

1. Append a post-follow-up A4 capture covering the current close tests and glass, with `pipefail`; update the coverage note to reflect the meeting glass and Coder Button fence.
2. Regenerate `boundary-candidates.json` and make the boundary-census / Documentation Navigation check pass.
3. Correct the canvas README’s status to record the owner’s ratification while keeping story 11 in-progress.

MISSED:

1. **Room load failures still display `ctrl.error`.** The load controller uses `readableError(reason)`, which returns an `Error` message, and the Room renders it directly (`web/src/features/project-room/useProjectRoomController.ts:108`, `web/src/features/project-room/ProjectRoomCore.tsx:2302`). The amendment explicitly parks this separate load path to B1 (`pm/roadmap/holdspeak-philo/phase-13-the-desk/story-04-a3-faces-that-do-not-lie.md:68`). The tested Room *publish* failure is clean; the whole Room face is not yet free of raw error text. This remains a Tenet 4 issue, but it is recorded as out-of-scope debt for these in-progress acceptance branches.

2. **Coder Watch live has no browser glass.** Its test seeds a `coder:s1` card in the store and checks that the card leaves the DOM; it does not prove a live-session producer or rendered destination (`web/src/desk/__tests__/pulloutCloseQualified.test.tsx:113`). The stated absence of a route that seeds a live coder session explains the limit. I accept this as a disclosed coverage gap for the shared store-ID seam; I do not count it as real-producer glass.

TUESDAY: Yes for the tested A3/A4 flows—the close returns to the Desk and refusal says what happened—but a Room load failure still exposes raw error text.

UNKNOWN: The macOS unit, integration, and E2E checks were still pending, and #725 was still draft at review time. The phase status says CI does not gate merge; I did not treat pending checks as a gate. I reviewed the recorded full-suite triage rather than rerunning the full suite.