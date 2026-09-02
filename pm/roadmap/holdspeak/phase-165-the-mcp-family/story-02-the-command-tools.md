# HS-165-02 - The command tools: the same verbs, the same laws

- **Project:** holdspeak
- **Phase:** 165
- **Status:** done
- **Depends on:** HS-165-01
- **Unblocks:** HS-165-03
- **Owner:** unassigned

## Problem

MCP-001: identical service commands, revision checks, idempotency,
events, and error codes as Web. MCP-002: effect tools require or
generate a returned command_id; retries are safe. MCP-005: typed
capability refusals, never simulated success.

## Scope

- **In:** project.create / update / archive / restore, project.link
  / unlink, project.open_review / get_delta, decide_proposal /
  accept_review, project.list_updates / draft_update / update_draft
  / publish_update — every one a THIN driver over the exact service
  command the Web route calls (read the route, call its service
  seam; the revision law and one-transaction publish ride the
  services untouched). command_id: accept an optional caller id,
  generate otherwise, RETURN it, and prove replay safety (same id +
  same payload = replayed result; mismatched payload = typed
  conflict — the project_commands machinery from 162/163 is the
  substrate). MCP-005: mutations the contract does not admit refuse
  with the typed capability error.
- **Out:** steward/setup/provider/watch tools (03), palette (04).

## Acceptance criteria

- [ ] Parity under test: for each command, the MCP result and the Web route result agree on shape, error codes, and side effects (revision rows, events).
- [ ] MCP-002 proven: replay returns the stored result and mints nothing; conflict refuses typed.
- [ ] No tool touches SQL or re-implements a verb (counsel's hunt pre-paid by construction; grep-able).

## Test plan

- **Unit:** tests/unit/test_project_mcp_commands.py.

## Trace record (orchestrator round, 2026-09-02)

- The build report composed the delta service with a _NullCollector
  ("the sidecar cannot run source adapters"). WRONG per HS-164's
  proven finding: collect_all is DB-only (native adapters read the
  DB; the WatchAdapter reads stored snapshots, never a provider).
  Replaced with the REAL ProjectEvidenceCollector (the web_server
  recovery block's own composition) — project.open_review is now
  true MCP-001 parity, honest coverage included.
- Copied-glue register (the parity risk counsel weighs): ONE item —
  project.decide_proposal replicates the route's
  proposal-belongs-to-review ownership check
  (project_reviews.py:157-174); the validation lives in the route,
  not the service. Pre-existing seam split; registered, not paid
  here.
- PublishedUpdateError (a DB-layer exception) is re-raised as
  ConflictError(code="published_update"), mirroring the route's 409.
