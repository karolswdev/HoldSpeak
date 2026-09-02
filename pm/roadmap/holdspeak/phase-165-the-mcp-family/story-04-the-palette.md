# HS-165-04 - The palette: agent-safe by construction

- **Project:** holdspeak
- **Phase:** 165
- **Status:** backlog
- **Depends on:** HS-165-03
- **Unblocks:** HS-165-05, HS-165-06
- **Owner:** unassigned

## Problem

MCP-007: a focused PROJECT_PALETTE and Project Thread mode make the
family safely reusable by agents without exposing all ~94 tools.
MCP-006 hardening and structured-error parity finish the driver.

## Scope

- **In:** the PROJECT_PALETTE (find the house palette mechanism —
  grep PALETTE in holdspeak/mcp/ and the thread modes from the 153
  arc; follow the existing species): the project family + the
  minimum companions the §15 scenario needs, nothing else. A
  Project Thread mode wiring the palette into the house thread
  practice. Hardening: a sweep proving every project-family error
  path returns the typed structured shape (no prose-only errors);
  partial-init behavior re-proven across ALL families (the MCP-006
  test from 01 widened). api-surface untouched (MCP is not HTTP);
  whatever MCP tool census the house keeps (grep for an
  mcp-tool-count pin — the 133 arc counted 52->82) updated honestly.
- **Out:** the walk (05), docs (06).

## Acceptance criteria

- [ ] The palette exposes the project family + named companions only; an agent session over the palette cannot reach unrelated tools (under test).
- [ ] Thread mode wired the house way; no second species.
- [ ] The error-shape sweep green; any tool-count pin updated with its name honest.

## Test plan

- **Unit:** tests/unit/test_project_mcp_palette.py.
