# HS-133-04 — Coder and Memory read out

- **Project:** holdspeak
- **Phase:** 133
- **Status:** done
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

Coder sessions and the memory store are invisible to MCP clients.
`CoderService` reads (`list_sessions` :30, `get_session` :54,
`list_steering_audit` :88) and `MemoryService.search` (:18) are
transport-neutral, but only the web reaches them.

## Scope

### In

Per assets/surface-spec.md §1C and §1F, verbatim:
`holdspeak/mcp/families/coder.py` implementing `coder.list`,
`coder.get`, `coder.audit` (constructor with `reply_sender=None` — the
sidecar cannot deliver replies; descriptions name steering as
out-of-scope), and `holdspeak/mcp/families/memory.py` implementing
`memory.search` with the spec's full filter schema.

### Out

- Coder write verbs (`reply`, `select_session`) — backlogged per counsel
  Q4; they raise `ValidationError` without a live `reply_sender`
  (coder_service.py:83-84). Any resource for either family (declined in
  the spec).

## Acceptance criteria

- [ ] All four tools in the catalogue with closed schemas, dispatching
  to the anchored methods with filters passed through.
- [ ] `coder.get` with an unknown session and `memory.search` with a
  missing `query` return `isError: true`.
- [ ] REQUIRED_TOOLS extended with the four names.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py --tb=short`
