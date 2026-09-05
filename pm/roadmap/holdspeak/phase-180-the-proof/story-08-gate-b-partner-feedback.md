# HS-180-08 — Gate B partner feedback

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** HS-180-01
- **Unblocks:** HS-180-09
- **Owner:** unassigned

## Problem

The arc's paragraph says "Gate B partner feedback." A second pair of
eyes on the shipped product validates that the owner's verdict is not
self-confirming. The partner (a colleague, a peer, someone who manages
a team) uses HoldSpeak for a defined session and gives feedback.

## Scope

- In:
  - One partner session: a person who is NOT the owner uses HoldSpeak
    on the owner's desk (or a configured instance on their machine)
    for a defined task (e.g., "open the portfolio, find what needs
    you, drill into a Room, read the brief").
  - The partner's feedback: what was clear, what was confusing, what
    broke, what they would use.
  - The feedback filed as evidence.
- Out:
  - Extended beta testing (one session, one partner).
  - Fixing issues the partner found (filed as observations).
  - The partner's access to the owner's real data (the session uses
    seeded or anonymized projects if the owner prefers).

## Acceptance criteria

- [ ] One partner completes a defined task on HoldSpeak.
- [ ] The partner's feedback is recorded verbatim.
- [ ] The feedback filed as evidence in the phase folder.
- [ ] Privacy/consent findings (if any) flagged as release-candidate
      blockers.

## Test plan

- Unit: n/a.
- Integration: n/a.
- Manual: the partner session; the feedback.

## Notes / open questions

- The partner is chosen by the owner. The session scope is agreed
  before the session starts. The partner does not need to be
  technical, but they should manage a team (the Tuesday question is
  about a manager's week).
- Whether Gate B feedback blocks the release candidate or is advisory
  is a deferred decision. Proposed: advisory, with privacy/consent
  findings blocking.
