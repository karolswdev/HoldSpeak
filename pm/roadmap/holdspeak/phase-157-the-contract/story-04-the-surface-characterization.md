# HS-157-04 - The surface characterization: Web + MCP registration pinned

- **Project:** holdspeak
- **Phase:** 157
- **Status:** backlog
- **Depends on:** -
- **Unblocks:** HS-157-05
- **Owner:** unassigned

## Problem

AD-PRJ-003 graduates `ProjectMemoryCore` into the Project Room — it
is not replaced by an unrelated page. WEB-IA-010 keeps
`open-project-memory` / `surface-project-memory` compatible, and
WEB-ARC-006 demands existing Project Memory tests survive or migrate.
On the MCP side, the Watch tools being graduated live in the
`reactions` family, and no `project.*` family exists — that
registration truth is the baseline P6 builds on (MCP-006: an
unrelated family failure must not suppress Project tools). Pin all
of it before the graduation touches it.

## Scope

- **In:** (a) Web: characterization of the Desk application
  registration seam — `open-project-memory` action, windowId
  `surface-project-memory`, scoped singleton opening/focus behavior
  (`web/src/desk/applications.ts:274`) — plus an inventory pass over
  `web/src/pages/cores/__tests__/projectMemoryCore.test.tsx`
  confirming (and where thin, adding) cover for opening, timeline
  composition, citations, Ask, and empty/error states (the
  WEB-ARC-006 baseline list). (b) MCP: a registration-truth test —
  the family module list, the Watch/Reaction tool names and their
  result envelopes as they are today (in `reactions.py`), and the
  absence of a `project.*` family recorded as the starting fact;
  plus a partial-initialization characterization if one family
  import fails today (current behavior recorded as-is).
- **Out:** any UI change (no beauty pass needed — P0 ships no
  pixels); renaming/moving MCP tools; building `project.*`.

## Acceptance criteria

- [ ] Desk registration for Project Memory is pinned: action id, window id, label/glyph, scoped-open + refocus behavior, under vitest.
- [ ] The WEB-ARC-006 baseline list is inventoried against existing tests; gaps are covered; web baseline stays zero branch-new.
- [ ] MCP registration truth is pinned: family list snapshot, Watch tool names + result shape characterization, no-project-family fact.
- [ ] Zero behavior change; `npm --prefix web run check` green; scoped vitest suites green.

## Test plan

- **Web unit:** vitest — desk applications registration + ProjectMemoryCore gaps; `uv run python scripts/check_web_baseline.py --run`.
- **Unit:** `tests/unit/test_mcp_registration_characterization.py` (or extend the existing MCP registration suite if one exists — check first).

## Notes / open questions

- The MCP snapshot test must not be brittle to unrelated families being added — pin the Project-relevant facts (reactions tools, no project family), not the whole universe.
