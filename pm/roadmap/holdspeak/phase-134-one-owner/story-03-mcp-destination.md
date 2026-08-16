# HS-134-03 — MCP speaks destination

- **Project:** holdspeak
- **Phase:** 134
- **Status:** backlog
- **Depends on:** HS-134-02
- **Unblocks:** HS-134-09, HS-134-10
- **Owner:** unassigned

## Problem

The MCP surface still speaks the retiring vocabulary: five `profile.*`
tools (`holdspeak/mcp/tools.py:231-258, :528-539`) expose the dual API
to every agent client. The rename is high-risk by the audit's register:
`scripts/mcp_walk.py` (tool assertions ~:184-220; live leg calls
`profile.create` ~:365-407), REQUIRED_TOOLS
(`tests/unit/test_mcp_tools.py:11-33`), and the phase-133 catalogue
test all pin the old names.

## Scope

### In

- `profile.list/get/create/update/delete` → `destination.*`, same
  schemas and dispatch (the service layer is already target-shaped
  after HS-134-02).
- ONE COMMIT updates: the tools, REQUIRED_TOOLS, the phase-133 test
  references, and `scripts/mcp_walk.py` (assertions + live leg) — the
  walk harness must never be red across a commit boundary.
- The `holdspeak://profiles` resources rename to
  `holdspeak://destinations` (+ template), same one-commit rule for
  the resource tests and walk assertions.
- Tool descriptions keep the kind-gap/egress honesty language.

### Out

- Renaming `inference_target_id` params on ask/recipe/sequence/workflow
  tools (works today; vocabulary-only churn — Wave 2 may revisit).
  Internal service names.

## Acceptance criteria

- [ ] `grep -rn '"profile\.' holdspeak/ tests/ scripts/` returns zero
  hits; `destination.*` tools dispatch identically.
- [ ] `HOME=$(mktemp -d) uv run python scripts/mcp_walk.py` passes all
  assertions (82 tools, closed schemas, renamed resources).
- [ ] Full MCP battery green (test_mcp_tools + all test_mcp_phase133*).

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_tools.py tests/unit/test_mcp_phase133*.py --tb=short`
  and the walk harness run; both captured.
