# HS-165-05 - The walk: one client drives the whole loop

- **Project:** holdspeak
- **Phase:** 165
- **Status:** in-progress
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

## Trace record (orchestrator round, 2026-09-02)

- The client was BUILT (none existed): a real subprocess speaking
  newline-delimited JSON-RPC against the real sidecar, isolated
  HOME. ONE fixture seam, verified by my own read of
  _mcp_walk_server.py: the snapshot fetcher reads a file instead of
  invoking the gh CLI — the subprocess boundary, protocol, dispatch,
  and service composition are all real.
- SEAM DEBT LEDGERED: project.py's _watch_service() factory builds
  WatchService(db) with NO snapshot_fetcher — the real sidecar
  cannot evaluate/test watches without live gh auth
  (connector_unavailable). Pre-existing shape (the web app injects
  its fetcher via _gh_watch_service_kwargs; the sidecar composes
  bare). Carried to the close ledger; the docs story must state it.
- The palette-consumer split recorded: the walk's legs run over the
  subprocess; dispatch_for_palette is proven in-process (it has no
  server wiring yet — its production consumer beyond the walk is
  future agent sessions).
- §15 item 1 (legacy reconcile) honestly pointered to the reconcile
  suites rather than re-proven in the walk (fresh-DB context).
