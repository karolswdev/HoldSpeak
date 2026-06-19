# HSM-9-04 — Voice Notes + pocket closeout

- **Project:** holdspeak-mobile
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HSM-9-01, HSM-9-02, HSM-9-03
- **Owner:** unassigned

## Problem

The charter's Track J gate is "pocket workflow complete." That's the whole
promise: walk in with only a phone, record, leave, and have artifacts. This story
rounds out Voice Notes and proves the end-to-end pocket workflow on a real iPhone.

## Scope

- **In:** the Voice Notes surface (browse/play/read captured voice notes) and the
  Gate closeout — the full pocket workflow on a real iPhone: quick capture and/or
  meeting capture → deferred processing → review queue → artifacts, end to end,
  evidenced by a device walkthrough.
- **Out:** iPad surfaces (Phase 8). Sync (Phase 10). Engine work (Phases 2–7).
  Hardening scenarios (Phase 11).

## Acceptance criteria

- [ ] Voice Notes lists captured notes with playback and their transcript.
- [ ] **Track J gate:** the pocket workflow runs end to end on a real iPhone —
      capture (quick or meeting) → processing → review queue → artifacts —
      evidenced by a device walkthrough (screens/recording).
- [ ] The walkthrough is on real Tier-2 hardware (iPhone 17 Pro Max), not the
      simulator; the device + mode (A or B) it proves are recorded.
- [ ] No autonomous execution anywhere in the workflow (charter non-goal).

## Test plan

- Manual / device: the full pocket-workflow walkthrough on a real iPhone, captured
  as gate evidence.
- Unit: the voice-notes view-model over fakes → list/playback/transcript.

## Notes / open questions

- This closes Phase 9; on pass write `evidence-story-04.md` + `final-summary.md`.
- If the gate only passes in Mode B (homelab) on iPhone, that's an honest finding,
  not a failure — record which mode the pocket workflow proves on Tier-2.
