# HS-82-03 — The conveyor renders: phases as the belt, stories as the items

- **Project:** holdspeak
- **Phase:** 82
- **Status:** backlog
- **Depends on:** HS-82-02 (the bridge serves the feed).
- **Unblocks:** HS-82-05.

## Problem

The feed's `phases` array was amended into the frozen schema
precisely because "the Desk conveyor renders phases as the belt" —
the schema is waiting for the UI that motivated it. Without the
conveyor, mission control on the Desk is a JSON document nobody
looks at.

## The design

A conveyor component in the Desk island (`web/src/desk/`), fed by
the bridge's `state` route through the existing store patterns:
phases as belt segments (number, title, open/closed,
`stories_done/stories_total`), stories as items with status and
the evidence mark, the feed's `next_story` visually distinct,
project `warnings` visible without being noisy. Multiple projects
render as multiple belts. A `compatibility`/`unavailable` payload
from the bridge renders as an honest state, never an empty belt
pretending the rails are idle. Visual language follows the Desk's
existing voice — this is a new fixture on the same desk, not a new
app.

## Test plan

- Vitest: rendering from feed fixtures — the belt, the next-story
  highlight, the closed-phase treatment, the warnings, the
  compatibility and unavailable states.
- Screenshot(s) under this phase's `screenshots/` once the belt
  renders this repo's counterpart repo live (the delivery-workbench
  checkout on this desk).
