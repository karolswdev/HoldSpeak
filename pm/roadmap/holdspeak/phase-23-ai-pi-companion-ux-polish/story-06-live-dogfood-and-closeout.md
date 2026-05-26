# HS-23-06 — Multi-Agent Live Dogfood and Closeout

- **Status:** done
**Opened:** 2026-05-26.
**Closed:** 2026-05-26.
**Owner:** Codex.

## Problem

Phase 23 changes are meaningful only if the real AI PI loop is understandable
under pressure: multiple waiting agents, long questions, selected answer
targets, tmux delivery, and transient voice-reply feedback all have to agree on
the physical display.

## Scope

### In

- Dogfood at least two waiting sessions with distinct identities.
- Confirm single-tap preview and double-tap session cycling on hardware.
- Confirm right-button voice reply into a tmux-backed Claude/Codex target.
- Fix small UX defects found during dogfood when they are clearly in Phase 23
  scope.
- Record final observed gaps and close the phase when the loop is trustworthy.

### Out

- New firmware widgets beyond the current top/middle/bottom labels.
- Hosted orchestration or autonomous agent replies.
- A full web companion dashboard.

## Acceptance Criteria

- [x] AI PI can cycle between multiple waiting sessions.
- [x] A tmux-backed agent reply can be delivered from AI PI.
- [x] Transient status flashes are not overwritten by the companion poller
      before their TTL expires.
- [x] The final dogfood pass records remaining UX gaps.
- [x] Phase 23 final summary is written.

## Notes

Live dogfood exposed one immediate UX defect: after a spoken reply, the
transcript status flashed only briefly before the agent waiting display
returned. The bridge now coordinates status flash TTLs with the companion
poller so middle-zone flashes remain readable.

## Closeout

Implemented 2026-05-26. See [evidence-story-06.md](./evidence-story-06.md)
and [final-summary.md](./final-summary.md).
