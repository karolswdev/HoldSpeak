# HS-144-04 — The upcoming rail + doorframe repairs

- **Project:** holdspeak
- **Phase:** 144
- **Status:** in-progress
- **Depends on:** HS-144-02, HS-144-03
- **Unblocks:** HS-144-05
- **Owner:** unassigned

## Problem

Upcoming time is invisible from the front. Scheduled recordings hide
as badged rows inside the meetings lane with no Chair-level create
(audit B: creating one takes the Cadence surface, 2 clicks); calendar
events (HS-144-02) have no glass at all. And the walk found two
doorframe defects: the Go menu is invisible at 393px, and the
`/meetings` deep-link races SurfaceWindows registration.

## Scope

### In

- **The upcoming rail** on the Door: renders `GET /api/door`
  `upcoming` — one ordered timeline of calendar events and
  scheduled-recording fires, each honestly labeled for what it is
  (an event is not a recording; a schedule is not an invitation —
  Article VI). "Next in 45 min" style relative time. Calendar-less
  installs (or an owner cut of HS-144-02) render the rail
  scheduled-recordings-only with no orphaned chrome.
- **Chair-level schedule create**: the in-world schedule-creation
  control (Phase 136's, reached today via Cadence) becomes reachable
  from the rail — reuse the existing control and verbs
  (`POST /api/scheduled-recordings`), no re-implementation. Mic on
  the title field rides along (it already exists).
- **Doorframe repairs** (audit B surprises):
  - the Go menu gets a lawful 393px presence;
  - the `/meetings` deep-link race is fixed with a real readiness
    fact, not a sleep (the Phase 143 hydration-race fix is the
    precedent: a server-fact attribute the code awaits).
- **The meetings lane's surviving duties re-homed**: live/recent
  meetings remain reachable from the Door (the rail handles
  *upcoming*; recent stays wherever HS-144-03's reforge put it) —
  nothing becomes unreachable.
- Both widths, all states, beauty pass after functional.

### Out

- Auto-starting a capture from a calendar event (follow-on; unruled).
- Any new backend beyond consuming HS-144-01/02 aggregates.
- OWA/CalDAV anything.

## Acceptance criteria

- [ ] The rail renders the merged timeline with honest per-kind
  labels and relative times; empty and calendar-less states are
  designed, not blank (tests + shots).
- [ ] A schedule can be created from the Door in-world, no modal,
  through the existing verb; the countdown/cancel behavior from
  Phase 136 still holds (e2e).
- [ ] The Go menu is present and usable at 393px (e2e + shot).
- [ ] The `/meetings` deep-link opens deterministically — the race is
  fixed by an awaited readiness fact, proven by repeated runs (e2e
  ×15 serial, the 143 precedent bar).
- [ ] Live shots at 1440 + 393 (+200%): populated, empty, error.

## Test plan

- `(cd web && npx vitest run)` — rail, create path, labels.
- Real-hub Playwright: rail states, schedule create round-trip,
  393px Go menu, deep-link determinism (isolated HOME).
