# HSM-8-03 — Transcript linking

- **Project:** holdspeak-mobile
- **Phase:** 8
- **Status:** backlog
- **Depends on:** HSM-8-01, HSM-8-02
- **Unblocks:** HSM-8-04
- **Owner:** unassigned

## Problem

A note is far more useful when it remembers *when* it was written. Linking a
handwritten note to the transcript moment it was taken at is the feature that
turns the notebook into a meeting record — and it must anchor on stable contract
identity, not on rendered text that re-flows.

## Scope

- **In:** capturing the transcript position (the active `Segment`/timestamp) when
  a note is made, storing it as a link anchor, and a tap affordance that navigates
  from a note to its transcript moment (and ideally back).
- **Out:** automatic note↔topic association (no ML linking). Artifact review
  (HSM-8-04). Cross-meeting linking. Sync of links (Phase 10 carries them as part
  of the meeting).

## Acceptance criteria

- [ ] Making a note records the transcript moment (a Phase-0 `Segment` identity /
      timestamp), stored as a structured link anchor.
- [ ] Tapping a linked note navigates to that transcript moment, and the link is
      **bidirectional** — from a transcript moment you can reach the note(s) taken
      there.
- [ ] A one-gesture "mark this moment" (a pen tap/star) creates a linked anchor
      without writing a full note, so a live meeting can be flagged at speed (these
      marks are the raw material HSM-8-06 weaves into the intelligence).
- [ ] The link survives reload and re-render of the transcript (anchored on the
      `Segment` contract, not on text offsets).
- [ ] A note made when no transcript exists yet degrades gracefully (no crash, no
      dangling link).

## Test plan

- Unit: link-anchor create/resolve over fixed segments → resolves to the right
  `Segment`; re-render → still resolves.
- Manual / device: write a note mid-meeting, finish, tap it → jumps to the moment.

## Notes / open questions

- Anchor on the Phase-0 `Segment` identity/timing so the link is stable across
  re-render and sync (phase risk: text-offset anchors break).
- The desktop has a transcript-moment-jump in aftercare; keep the anchor concept
  compatible so a synced meeting links the same way on both runtimes.
