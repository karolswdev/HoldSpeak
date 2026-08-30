# HS-152-01 - The tool loop (passes, tool_call parts, frames, abort)

- **Project:** holdspeak
- **Phase:** 152
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-152-02, HS-152-03
- **Owner:** unassigned

## Problem

A Thread turn ends at the model's first answer; it cannot ask the desk
for anything. DC-02's keystone is the pass loop (settled-design D1):
tool_calls deltas become `tool_call` parts, resolved calls become
`tool`-role messages, and the model runs again — ten passes at most —
with abort honoured between every step (counsel M5).

## Scope

### In

- `_run_streaming_turn` pass loop (≤ 10 for chat; the Recipe agent turn keeps 4); `tool_call` parts (meta: id, name, args, class, state); `tool`-role result messages; the tool palette rendered from MCP `inputSchema` into OpenAI function schemas and passed as `tools=`.
- Frames `thread_tool_pending`, `thread_tool_result`, `thread_status_line` (+ web mirror, drift test).
- Abort: cancel checked before every pass and every execution; 30 s per-tool deadline; discarded in-flight result; `indeterminate`; done{aborted} ≤ 250 ms after the next check.
- Error taxonomy on `error_json.code` (S1): tool_execution_failed / tool_timeout / tool_denied / pass_cap_reached / tool_unknown.
- Execution + policy behind the executor interface story 02 provides.

### Out

Anything DC-03+; external MCP servers.

## Acceptance criteria

- [ ] With a fake engine yielding tool_calls then text: 2 passes, 1 tool_call part, 1 tool message, final answer; frames in order.
- [ ] Pass cap: the 11th tool request ends the turn `pass_cap_reached` with a named error row.
- [ ] Abort during a (stubbed slow) tool execution ends `indeterminate` within 250 ms of the check; no result persisted.
- [ ] Frame drift test green; no-tools turns byte-identical to DC-01.

## Test plan

- **Unit / integration:** tests/unit/test_thread_tool_loop.py, tests/unit/test_realtime_frame_registry.py, tests/unit/test_thread_service.py
- **Manual / device:** `.43` legs in story 06.
