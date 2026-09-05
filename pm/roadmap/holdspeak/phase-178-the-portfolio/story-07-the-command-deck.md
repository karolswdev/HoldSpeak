# HS-178-07 — The command deck

- **Project:** holdspeak
- **Phase:** 178
- **Status:** backlog
- **Depends on:** HS-178-01, HS-178-03
- **Unblocks:** HS-178-08
- **Owner:** unassigned

## Problem

The command deck (`verbRegistry.ts`) registers `desk.new-project` but
no verb to open the portfolio surface and no per-Room verbs. A senior
architect should reach any Room or the portfolio from the command deck
without navigating through the Door.

## Scope

- In:
  - A PORTFOLIO verb in the command deck that opens the Projects
    surface.
  - Per-Room verbs: each active Room appears in the command deck by
    name; selecting one opens that Room.
  - The verbs are indexed in the command deck's search.
- Out:
  - Project creation from the command deck (the Door owns that).
  - Archived projects in the command deck.

## Acceptance criteria

- [ ] The command deck registers a PORTFOLIO verb that opens the
      Projects surface (Article I — the Desk is the operating surface).
- [ ] Each active Room appears as a verb in the command deck; selecting
      one opens the Room.
- [ ] The verbs are searchable (the Room's name is the search key).
- [ ] Verified by a unit test registering verbs for two seeded
      projects.

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k command_deck_portfolio`
  - Verb registration for two projects.
  - Search by project name.
- Integration: the command deck opens the portfolio and a Room.
- Manual: the owner's desk; the command deck with his real projects.

## Notes / open questions

- The verb names should match the canonical feature names
  (POSITIONING.md): "Projects" for the portfolio surface, and the
  project's own name for per-Room verbs.
