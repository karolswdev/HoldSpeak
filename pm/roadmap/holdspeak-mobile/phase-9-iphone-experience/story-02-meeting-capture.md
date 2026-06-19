# HSM-9-02 — Meeting Capture

- **Project:** holdspeak-mobile
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HSM-9-01, HSM-3-02, HSM-4-01
- **Unblocks:** HSM-9-03, HSM-9-04
- **Owner:** unassigned

## Problem

The charter's headline is walking into a meeting with only a phone and leaving
with artifacts. Meeting Capture is the pocket version of the iPad capture loop:
record a real meeting, transcribe it, and queue it for intel — without the phone's
thermal limits blocking capture.

## Scope

- **In:** a Meeting Capture flow on the iPhone — record (Phase 2) → transcribe
  (Phase 3) → persist (Phase 4) → enqueue for intel processing (deferred, so
  capture isn't blocked by inference); the active MIR profile selectable via the
  Phase-7 seam.
- **Out:** the Review Queue surface (HSM-9-03). Building the intel engine (Phases
  5–7). Live (non-deferred) on-device inference if the device can't sustain it
  (phase deferred decision). Sync (Phase 10).

## Acceptance criteria

- [ ] A meeting records, transcribes, and persists from the iPhone, and is
      enqueued for intel processing (processing may be deferred).
- [ ] Capture is never blocked waiting on inference (the queue decouples them).
- [ ] The meeting carries its MIR profile (default Balanced) via the Phase-7 seam.
- [ ] The flow is thin — Runtime-Core seams only, no business logic in the view.

## Test plan

- Unit: the meeting-capture view-model over fakes → record→transcribe→persist→
  enqueue, with inference decoupled.
- Manual / device: record a real short meeting on an iPhone; confirm it persists
  and queues for intel.

## Notes / open questions

- Deferred vs. live intel and the background-audio posture are phase deferred
  decisions — default to deferred processing + Phase-2's posture.
- If the Tier-2 iPhone can't process even deferred locally, this is the signal to
  offer Mode B (homelab) as the iPhone default (phase risk).
