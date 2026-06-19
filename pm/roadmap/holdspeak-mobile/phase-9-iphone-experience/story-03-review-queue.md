# HSM-9-03 — Review Queue

- **Project:** holdspeak-mobile
- **Phase:** 9
- **Status:** backlog
- **Depends on:** HSM-9-02, HSM-6-02
- **Unblocks:** HSM-9-04
- **Owner:** unassigned

## Problem

On a phone, intel processing is deferred, so the user needs a place that shows
what's captured, what's still processing, and what's ready — and lets them open a
finished meeting's artifacts. The Review Queue is that surface.

## Scope

- **In:** a Review Queue listing captures (quick notes + meetings) with their
  processing state (captured / processing / ready), and a path into a ready
  meeting's artifacts (the Phase-6 outputs) for review/approve.
- **Out:** the iPad PencilKit/notebook surfaces (Phase 8). Building the artifact
  engine (Phase 6). Connector execution. Sync (Phase 10).

## Acceptance criteria

- [ ] The queue lists captures with an honest processing state that updates as
      deferred intel completes.
- [ ] Opening a ready item shows its artifacts (Phase-6 outputs), grouped by type.
- [ ] Proposals can be reviewed/approved; nothing executes autonomously.
- [ ] Egress on actionable surfaces is shown as the egress badge, not privacy
      prose (positioning canon).

## Test plan

- Unit: the queue view-model over fake captures in each state → correct listing +
  state transitions; open-ready → artifacts.
- Manual / device: capture a meeting, watch it move captured→processing→ready,
  open its artifacts.

## Notes / open questions

- Depends on Phase 6 for real artifacts; until then show processing/ready state
  honestly without faking artifacts (phase risk).
- Keep state language honest (the desktop convention): the queue reflects reality,
  it doesn't imply work that didn't happen.
