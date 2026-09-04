# HS-168-06 - The docs: "Connect your tools"

- **Project:** holdspeak
- **Phase:** 168
- **Status:** backlog
- **Depends on:** HS-168-03, HS-168-04
- **Unblocks:** HS-168-07
- **Owner:** unassigned

## Problem

The guide describes connecting GitHub and Jira as a step inside the
Project Rooms interview; the README's prerequisites name gh and acli
with no face to point at. The dedicated docs story (the standing
law) records the new front door.

## Scope

- **In:** docs/USER_GUIDE.md gains "Connect your tools" (Settings →
  Connections; the states; the one command per tool; labels
  verbatim from the face); the Project Rooms guide's setup section
  re-shot on the recomposed Sources step; README prerequisites point
  at the face; docs/MCP_SIDECAR.md REGENERATED (the generator, never
  hand-edited counts) with the two new tools; the doc drift guard,
  the product-copy guard and the roadmap-vocabulary guard green;
  ARCHITECTURE's provider section names the connections service with
  verified anchors.
- **Out:** positioning changes.

## Acceptance criteria

- [ ] Every label in the guide matches the built face verbatim; shots current.
- [ ] MCP_SIDECAR regenerated with the drift guard green; README prerequisites updated.
- [ ] All doc guards green with the stash-compare law (zero branch-new violations).

## Test plan

- **Guards:** `uv run pytest -q tests/ -k "doc or guard or drift"`; the MCP_SIDECAR generator's check mode.
