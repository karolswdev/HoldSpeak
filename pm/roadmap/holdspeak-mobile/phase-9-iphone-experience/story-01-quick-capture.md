# HSM-9-01 — Quick Capture

- **Project:** holdspeak-mobile
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HSM-1-01, HSM-2-01, HSM-3-02
- **Unblocks:** HSM-9-04
- **Owner:** unassigned

## Problem

The fastest value on a phone is capturing a thought before it's gone. Quick
Capture is one tap → recording → a voice note in the runtime, with no setup. It's
the lightest entry into the pocket workflow and the lowest-friction reason to open
the app.

## Scope

- **In:** a one-tap Quick Capture entry point on the iPhone host that records a
  short voice note via the Phase-2 capture, transcribes it (Phase 3), and stores
  it as a note/dictation entry through the Runtime-Core seam.
- **Out:** full Meeting Capture (HSM-9-02). The Review Queue (HSM-9-03). Intel
  artifacts. Business logic in the view.

## Acceptance criteria

- [ ] One tap starts a voice-note recording; stopping it persists the note +
      transcript via the runtime.
- [ ] The capture works from a cold app open within a couple of taps (no
      configuration gate).
- [ ] The note reopens with its transcript intact.
- [ ] The flow goes through Runtime-Core seams/view-models, not engine concrete
      types in the view.

## Test plan

- Unit: the quick-capture view-model over fake capture/transcribe/store →
  record→note flow.
- Manual / device: one-tap capture on an iPhone; confirm persist + reopen.

## Notes / open questions

- Keep it genuinely one-tap; this is the friction floor of the pocket workflow.
- Reuse the dictation/note shape the desktop uses so a synced note is the same
  entity on both runtimes.
