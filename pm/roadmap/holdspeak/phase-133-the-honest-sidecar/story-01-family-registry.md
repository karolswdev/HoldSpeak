# HS-133-01 — One registry, many families

- **Project:** holdspeak
- **Phase:** 133
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-133-02..07, HS-133-09
- **Owner:** unassigned

## Problem

Phase 133 adds 30 tools. `holdspeak/mcp/tools.py` is already 610 lines
holding all 52 existing tools and one dispatch chain; landing eight new
families there means six parallel workers editing one file in a shared
tree — the exact contention the wave plan must avoid. The spec's
structural ruling (assets/surface-spec.md Part 5) mandates per-family
modules aggregated by a registry seam.

## Scope

### In

- `holdspeak/mcp/families/` package. Each family module (ask.py,
  settings.py, coder.py, cadence.py, sequence.py, memory.py,
  plugin_job.py) exports a `TOOLS` list (spec-schema dicts) and a
  `dispatch(name, arguments, principal)` callable. This story creates
  the package, the module skeletons (empty TOOLS, NotImplemented-free
  dispatch that simply matches nothing), and the aggregation seam.
- `tools.py` aggregates: the catalogue returned for `tools/list` is its
  own TOOLS plus every family's TOOLS; `dispatch()` routes names claimed
  by a family to that family's dispatcher before its own chain. The
  existing 52 tools and their dispatch stay in `tools.py` untouched.
- The catalogue law seam: `tests/unit/test_mcp_tools.py` REQUIRED_TOOLS
  (:11-17) keeps passing; the aggregation is covered by a unit test
  proving a family-registered tool appears in `tools/list` and routes to
  the family dispatcher (use a synthetic family in the test).

### Out

- Any real family tools (stories 02-07). Any change to existing tool
  behavior or schemas.

## Acceptance criteria

- [ ] `tools/list` through `handle_message` returns the existing 52
  tools unchanged with the families package in place.
- [ ] A test-registered synthetic family tool appears in the catalogue
  with a closed schema and dispatches to its family callable.
- [ ] No existing MCP test changes behavior:
  `tests/unit/test_mcp_tools.py`, `test_brief_mcp.py`,
  `test_follow_through_mcp.py`, `test_124_verify_round3.py` all green.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_tools.py tests/unit/test_brief_mcp.py tests/unit/test_follow_through_mcp.py tests/unit/test_124_verify_round3.py tests/unit/test_mcp_phase133.py --tb=short`
- New registry tests live at the top of `tests/unit/test_mcp_phase133.py`.
