# HS-70-05 — Meetings mode, made whole

- **Status:** todo
- **Priority:** MED
- **Depends on:** HS-70-01
- **Evidence:** _(added at close)_

## Goal

The **Meetings** destination cleanly contains the entire meeting mode: start a
live capture, import a recording or transcript, browse the archive with facets,
and act on aftercare. `/history` stops being an oddly-named archive tab and
becomes the front door to the mode.

## Scope

- Rename the surface to **Meetings** (route may stay `/history` with a
  canonical redirect, or move to `/meetings` with `/history` redirecting —
  pick one, keep both reachable; update the three registrations + pre-flight).
- **Surface the entry actions at the top, not buried:** "Start a meeting" /
  "Import a recording or transcript" are primary affordances on arrival, not
  hidden behind a scroll (the Phase-55/57 import flow already exists; promote
  it). Capture entry is clear even with an empty archive.
- The archive (Phase-55 faceted search), the artifact cards (Phase-36), and
  aftercare (Phase-49) all live under this one mode; keep them, frame them as
  one mode's surface.
- The Meetings empty state (HS-70-07) tells a new user the one move: capture
  or import your first meeting.
- Canonical names: meeting intelligence, meeting plugins, meeting aftercare,
  meeting import, the archive.

## Proof required

Screenshots of Meetings with the entry actions prominent on arrival (empty +
seeded); a real capture/import path still working (reuse the Phase-55/57
dogfood); the `/history`↔`/meetings` redirect proven (no 404). Faceted search +
aftercare still function.

## Done

_(filled at close)_
