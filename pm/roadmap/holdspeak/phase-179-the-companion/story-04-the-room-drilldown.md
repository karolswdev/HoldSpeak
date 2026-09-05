# HS-179-04 — The Room drill-down

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-03
- **Unblocks:** HS-179-07
- **Owner:** unassigned

## Problem

Tapping a Room in the companion's portfolio must open the Room's
needs-you detail: the rows, the health tokens, the first WHY. The
data comes from `GET /api/projects/{id}/room` (projects.py:46).

## Scope

- In:
  - The companion's Room drill-down: needs-you rows with severity,
    age, source, and the first WHY; health tokens (review latency,
    CI health, from 173); the release-readiness scorecard indicator.
  - Navigation: tapping a Room row in the portfolio pushes the
    drill-down view.
  - Both iPad and iPhone layouts (if universal).
  - Pull-to-refresh.
- Out:
  - The full Room (sources, changes, review, decisions, commitments,
    updates, steward sections -- the companion shows needs-you and
    health only).
  - Write operations (confirm, edit, drop).
  - Verbs that open the desktop Room (the companion is read-only).

## Acceptance criteria

- [ ] Tapping a Room row in the portfolio opens the Room drill-down
      (Article VIII.3).
- [ ] The drill-down shows needs-you rows with severity, age, source,
      and the first WHY.
- [ ] Health tokens from 173 appear in the drill-down.
- [ ] The data comes from `GET /api/projects/{id}/room`.
- [ ] Verified by a screenshot on the real device.

## Test plan

- Unit: SwiftUI preview with seeded Room data; verify row rendering.
- Integration: the companion fetches a Room from the hub on the LAN.
- Manual: the owner's iPad/phone with a real Room.

## Notes / open questions

- The companion shows the Room's read-only summary, not the full Room.
  The full Room (with its 12 sections) is the desktop's job. The
  companion answers "what needs me?" -- not "what is the Room's full
  state?"
