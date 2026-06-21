# HSM-8-01 — iPad shell + meeting capture

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** done (2026-06-21 — the `MeetingCapture` view-model (record → windowed live
  transcript → persist → reopen) + the `MeetingCaptureApp` iPad shell ship; host-tested
  and run live on a physical iPad. See [evidence-story-01](./evidence-story-01.md))
- **Depends on:** HSM-1-01, HSM-2-01, HSM-3-02
- **Unblocks:** HSM-8-02, HSM-8-03, HSM-8-04
- **Owner:** unassigned

## Problem

The runtime has no face on iPad. The flagship experience starts with the simplest
high-value loop: open the app, press Record, watch the transcript appear. That
screen is the spine the notebook and review hang off, and it must drive the
Runtime Core without absorbing business logic.

## Scope

- **In:** the iPad SwiftUI app shell (navigation, the meeting list/entry point)
  and the meeting-capture screen — record/stop, a live transcript view fed by the
  Phase-3 transcriber over the Phase-2 capture, persisted via Phase-4 storage. All
  through Runtime-Core seams / view-models.
- **Out:** PencilKit notebook (HSM-8-02), transcript linking (HSM-8-03), artifact
  review (HSM-8-04). The engines themselves. The iPhone shell (Phase 9). Sync.

## Acceptance criteria

- [ ] The app launches on an iPad, presents a meeting list, and opens a capture
      screen.
- [ ] Record/stop drives the Phase-2 capture and the live transcript view updates
      from the Phase-3 transcriber as speech is recognized.
- [ ] The meeting + its segments persist via the Phase-4 store and reopen intact.
- [ ] The screen depends only on Runtime-Core seams/view-models — no engine or
      provider concrete types in the view layer (proven by the view's imports /
      a dependency check).

## Test plan

- Unit: the view-model layer over fake providers (capture/transcribe/store) →
  record→transcript→persist flow without UIKit.
- Manual / device: record a short meeting on an iPad; confirm live transcript +
  reopen-intact.

## Notes / open questions

- This is the loop everything else extends; keep it clean and thin so HSM-8-02/03
  add to it without rework.
- Depends on Phases 2–3 being callable; the artifact-bearing parts wait for
  Phase 6 (review is HSM-8-04).
