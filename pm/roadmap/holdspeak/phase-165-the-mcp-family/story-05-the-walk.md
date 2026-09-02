# HS-165-05 - The walk: one client drives the whole loop

- **Project:** holdspeak
- **Phase:** 165
- **Status:** backlog
- **Depends on:** HS-165-04
- **Unblocks:** HS-165-07
- **Owner:** unassigned

## Problem

The P6 exit: a local MCP client drives the same scenario. §15's
acceptance list is the script. THE OWNER'S VERDICT closes this
story — Gate B readiness is his call.

## Scope

- **In:** tests/integration/test_hs165_mcp_walk.py: a REAL local
  stdio MCP client (the house client harness; if none exists, the
  minimal honest one — subprocess stdio JSON-RPC against the real
  sidecar, no in-process shortcuts) drives: setup interview →
  finalize into a Project with a tested Watch → evaluation with a
  changed snapshot → steward configure (opt-in) + run_steward →
  poll to completed with ≥1 real deduplicated effect + receipts →
  draft/publish an update → re-run at the same watermark mints
  nothing → get_room shows the same revisions Web sees (§15 items
  1-10 mapped explicitly in asserts). Every step through the
  palette (04). A transcript artifact (the walk record: each tool
  call + structured result, written to assets/story-05-transcript.
  json) + the owner-verdict gallery built from it (the stable
  artifact URL). ×2 deterministic.
- **Out:** remote transport; Jira.

## Acceptance criteria

- [ ] §15's ten points asserted through the client, ×2 deterministic; zero prose-parsing (MCP-004 on the walk).
- [ ] The transcript artifact carries every call + result; the dedup and revision-parity numbers measured, not asserted.
- [ ] THE OWNER'S VERDICT recorded verbatim (Gate B readiness).

## Test plan

- **Integration:** the walk ×2; **Manual:** the owner's verdict.
