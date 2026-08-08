# HS-126-09 — The walk

- **Project:** holdspeak
- **Phase:** 126
- **Status:** backlog
- **Depends on:** HS-126-08
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

The brief is real only if a person can create the operational facts, open the
desk, and receive an honest, actionable account. This walk proves collection,
composition, delivery, empty-state honesty, and the MCP resource end to end.

### The walk script

`scripts/desk_walk/walk_monday_brief_126.py` uses the existing desk walk
harness to:

1. Seed material pipeline events, follow-through items, broken connectors,
   and pending owner decisions inside a Monday brief window.
2. Generate the brief and open the Monday Brief pullout.
3. Verify Changed, Broke, Waiting, and Your Decisions are populated from the
   correct cited sources.
4. Acknowledge, defer, and open a source item; verify persisted state.
5. Read `holdspeak://briefs/latest` and verify it matches the desk brief.
6. Generate a no-evidence brief and verify its honest empty sections.

## Acceptance criteria

1. The walk completes without assertion failures.
2. All four populated sections contain the expected evidence and no raw noise.
3. Item source actions resolve to the supporting records.
4. The MCP latest-brief resource matches the persisted desk result.
5. An empty brief says "Nothing material changed." and invents no activity.

## Test plan

- `uv run python scripts/desk_walk/walk_monday_brief_126.py` passes.
- Screenshots are captured and visually verified at desk and narrow widths.
- Focused unit and integration tests for Phase 126 pass before the walk.
