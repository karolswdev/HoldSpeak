# HS-179-05 — The brief on the companion

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-02
- **Unblocks:** HS-179-07
- **Owner:** unassigned

## Problem

The Monday brief's portfolio section (178) should be readable on the
companion. A senior architect checking his phone at 08:00 should see
the brief without opening the MacBook.

## Scope

- In:
  - The companion's brief view: the Monday brief's portfolio section
    rendered in SwiftUI.
  - The data comes from the brief's stored representation (the API
    route that 171 and 178 build).
  - The brief view shows per-project summary, delta since last brief,
    and scorecard indicator.
- Out:
  - Brief generation from the companion (the desktop generates the
    brief).
  - The full brief (only the portfolio section ships on the companion
    initially; the design story may widen this).

## Acceptance criteria

- [ ] The companion shows the Monday brief's portfolio section
      (Article I -- the Desk, including its reach, is the operating
      surface).
- [ ] Per-project summary, delta, and scorecard indicator render.
- [ ] The data comes from the brief API route.
- [ ] Verified by a screenshot on the real device.

## Test plan

- Unit: SwiftUI preview with seeded brief data.
- Integration: the companion fetches the brief from the hub on the LAN.
- Manual: the owner's phone with his real brief.

## Notes / open questions

- If the design story decides the companion shows the full brief (not
  just the portfolio section), this story's scope widens.
