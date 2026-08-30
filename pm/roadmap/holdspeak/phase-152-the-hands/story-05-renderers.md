# HS-152-05 - The renderers and the status line

- **Project:** holdspeak
- **Phase:** 152
- **Status:** backlog
- **Depends on:** HS-152-04
- **Unblocks:** HS-152-06
- **Owner:** unassigned

## Problem

A tool result that renders as raw JSON is a coder's chat; a manager's
desk renders the meeting chip, the person card, the board lanes
(settled-design D5, counsel S3).

## Scope

### In

- Per-kind renderers reusing existing desk components (meeting, person = display name + readiness only, board, note, decision); unknown → key/value; RAW fold always.
- `thread.set_status` MCP tool (one new tool; docs count arithmetic) → `threads.status_line` → `thread_status_line` frame → the head.
- Error rows per taxonomy code.

### Out

Anything DC-03+.

## Acceptance criteria

- [ ] Fixture results of each known kind render their component (vitest); unknown renders the table; RAW present on all.
- [ ] `thread.set_status` from a fake engine updates the head live on glass.
- [ ] Tool count documented = registry count (arithmetic in evidence).

## Test plan

- **Unit / integration:** vitest renderers; tests/unit/test_mcp_tools.py; doc guard tests
- **Manual / device:** shots reviewed by the orchestrator.
