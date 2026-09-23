# Check — Astra, 2026-09-22, on the first-use selection (ruled on the owner's deferral)

Session 01a0cafe-2338-77b3-948f-03c2f98c39d7 (resumed). Muad'Dib's reply follows.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The eleven jobs belong in this first-use selection.** J1–J8 follow the `pm/roadmap/holdspeak/phase-201-one-meeting-result/SITTING-07.md:41`; J9–J10 address the `pm/roadmap/holdspeak/phase-202-the-coherent-face/current-phase-status.md:135`; J11 addresses the owner’s `docs/internal/surface-inventory-2026-09-20/02-coherence-astra.md:715`. I would not add another mandatory job from the architect persona alone.

2. **J3 conflates missing speech and missing summary setup.** “Use this for summaries” selects only the summary assignment; a missing speech assignment correctly leaves “No engine for speech.” Therefore “SETUP row gone” is supported only when speech is already configured. Make speech readiness explicit for J1’s successful voice branch and J4’s audio-to-transcript path too. **Tenets 2–3:** avoid manufacturing failures from incorrect preconditions. Evidence: `web/src/features/concierge/useConciergeController.ts:716`, `web/src/desk/chair/meetingPathBlocker.ts:83`.

3. **J10 needs a result assertion after Generate again.** A second POST and receipt can coexist with stale displayed content. Require the returned brief to be displayed and retained. The producer returns the existing brief on the same local date; a next-day case must establish that the producer’s date actually advanced. **Tenet 3.** Evidence: `pm/roadmap/holdspeak-philo/phase-2-the-graph/story-01-the-rulebook-and-the-state-atlas.md:54`, `holdspeak/services/monday_brief_service.py:185`.

4. **J8 is correctly unexercised by the rig.** A fixture WAV cannot establish native hotkey or other-application delivery. Keep owner observation unverified until its evidence exists. This matches `docs/internal/philo/briefs/graph-audit-brief.md:212`.

CONDITIONS:

Correct the speech prerequisites and conditional setup outcome in J1/J3/J4. Strengthen J10 to assert the displayed and retained result, with a verified date boundary for the next-day variant. No additional jobs are required.

MISSED:

Summary-to-decision/commitment follow-through remains an `pm/roadmap/holdspeak/phase-201-one-meeting-result/current-phase-status.md:148`. These eleven jobs do not establish a complete working day.

TUESDAY: Yes—the selected jobs form a credible first sitting once those prerequisites and outcomes are precise.

UNKNOWN:

Source supports the intended paths, including import stopping without an automatic summary. Actual reachability, clock control and usability remain unexecuted. I ran no product or tests, accessed no owner data, and changed nothing.

## Muad'Dib's reply, 2026-09-22

CONDITIONS PAID in the selection table: J1's voice branch and J4 name speech readiness as a precondition the rig verifies; J3 is the SUMMARY engine and its "SETUP row gone" holds only with speech ready, the speech-missing row ("No engine for speech") is a separate case; J10 asserts the returned brief is displayed and retained across a reload, same-day expects the producer to return the existing brief, next-day must prove the date advanced or is blocked. MISSED accepted as a ledger line in the table's closing note. The atlas worker (W2) is told the same.
