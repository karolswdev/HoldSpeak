# HSM-25-04 — The pocket, proven on device

- **Status:** backlog
- **Depends on:** HSM-25-02, HSM-25-03.

## Problem

Fixtures prove the shapes; only a device proves the pocket. The conveyor must render a real hub's mission-control feed over the owner token, on a phone.

## The design

The on-device leg, evidence-captured: pair to a hub running the backend's `/api/missioncontrol/*` routes, render the belt, watch a session pin and an event tick, and show the owner-only auth state when the token is wrong. Screenshots under `screenshots/`.

## Test plan

Manual/device: the real hub demonstration above. **Depends on the backend's PR #247 being merged and a hub serving the routes** — until then this story is blocked and 01–03 stand on fixtures (the honest split the backend's Phase 82 carried).
