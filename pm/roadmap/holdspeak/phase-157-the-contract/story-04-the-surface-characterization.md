# HS-157-04 - The surface characterization: Web + MCP registration pinned

- **Project:** holdspeak
- **Phase:** 157
- **Status:** done
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

## What shipped

- `web/src/desk/__tests__/applicationManifest.test.ts` +2 tests: the
  Project Memory registration pinned (action `open-project-memory`,
  windowId `surface-project-memory`, label, glyph `▤`, href, surface
  eyebrow "Long memory", minW 640) and its presence in the
  surface-application projection (AD-PRJ-003 / WEB-IA-010).
- `web/src/pages/cores/__tests__/projectMemoryCore.test.tsx` +3 tests
  closing the WEB-ARC-006 gaps: Ask interaction (submit → grounded
  answer with receipt), load-error state, no-scope empty state.
  The rest of the WEB-ARC-006 baseline list was already covered
  (opening, timeline composition + rendering, citations, lifecycle,
  empty timeline/search); scoped-singleton refocus lives at the
  `surface-windows.test.tsx` seam and was left there, not duplicated.
- `tests/unit/test_mcp_registration_characterization.py` — 7 tests
  pinning: reactions family registered; NO `project` family (the P6
  starting fact, import refused); every family exports TOOLS+dispatch;
  the 11 Watch/Reaction tool names exactly; every reactions tool
  schema valid; `watch.create` schema shape (connector enum
  gh/github/jira); reactions tools present in the aggregated
  catalogue. Robust to unrelated new families.
- Verification: vitest 18/18 (2 files), pytest 7/7, both re-run by the
  orchestrator; captured in evidence.

## Notes / open questions

- **MCP-006 baseline truth (P6 must fix):** `holdspeak/mcp/families/__init__.py:18-34` does bare top-level imports of all 15 families — ONE family import failure suppresses ALL families, the exact opposite of MCP-006. No cheap test seam exists today (recorded by code reading); P6's hardening story owns it.
- Result-envelope invocation of reactions tools is NOT pinned: `reactions.dispatch()` needs a live DB; names + schemas are the honest pin at this seam.
- The registration pins are deliberately fact-scoped, not universe snapshots — adding an unrelated family breaks nothing.
