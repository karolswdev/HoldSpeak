# HS-179-03 — The portfolio on the companion

- **Project:** holdspeak
- **Phase:** 179
- **Status:** backlog
- **Depends on:** HS-179-01, HS-179-02
- **Unblocks:** HS-179-07
- **Owner:** unassigned

## Problem

The companion must show the portfolio surface from Phase 178 as a
Swift recreation. The web spec is the source of truth; the companion
renders the same data (from `GET /api/desk/portfolio`) in the iPad/
iPhone idiom.

## Scope

- In:
  - The companion's portfolio view: Room rows with needs-you count,
    release-readiness indicator (green/amber/red), urgency sort,
    oldest-unresolved age token.
  - The data comes from `GET /api/desk/portfolio` (178).
  - The view uses SwiftUI and the design system tokens from the web
    spec (mapped to Swift; same colors, same type steps, same species
    grammar).
  - Both iPad and iPhone layouts (if universal).
  - Pull-to-refresh.
- Out:
  - The depth pane (HS-179-04 handles the drill-down).
  - Write operations.
  - Features not in the web spec.

## Acceptance criteria

- [ ] The companion's portfolio view shows every active Room with
      needs-you count, release-readiness indicator, and urgency sort
      (Article VIII.3 -- every glass is first-class).
- [ ] The data comes from `GET /api/desk/portfolio`.
- [ ] The view matches the design artboards.
- [ ] Pull-to-refresh updates the portfolio.
- [ ] Verified by a screenshot on the real device beside the web
      desk's portfolio.

## Test plan

- Unit: SwiftUI preview with seeded portfolio data; verify row order
  and indicator mapping.
- Integration: the companion fetches from the hub on the LAN and
  renders the portfolio.
- Manual: the owner's iPad/phone with his real projects.

## Notes / open questions

- The design system token mapping (web CSS variables to Swift Color/
  Font) is a one-time investment that all subsequent companion views
  reuse. If 178's design system ships a token export, the mapping is
  mechanical.
