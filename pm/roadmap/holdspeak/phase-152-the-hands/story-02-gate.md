# HS-152-02 - The gate (thread_tool_policy, the truth table, kernel children)

- **Project:** holdspeak
- **Phase:** 152
- **Status:** backlog
- **Depends on:** HS-152-01
- **Unblocks:** HS-152-03, HS-152-04
- **Owner:** unassigned

## Problem

Every call the model makes must be a child kernel operation of the turn
(Art. XI clause 6) with the owner's posture applied honestly: yolo =
receipt, safe = decision, and a per-thread policy row that wins when set
(counsel M3, M4). No new admission path.

## Scope

### In

- Additive `thread_tool_policy` (append-only, newest wins, soft-delete).
- `resolve_tool_decision(policy, control_mode, tool_class)` implementing the D2 truth table exactly; a table-driven test of all 8 rows.
- Admission of every call through `ToolCallCodec`/`ToolTurnController` with `parent_operation_id` = the turn's operation; held calls stay `awaiting_decision`; `decide(approve|deny)` resolves.
- Execution via `holdspeak.mcp.tools.dispatch(name, args, principal)` in-process under the lease byte cap; one-path census rows for the executor.
- Elicitation (M6): a result carrying `elicit: {schema, prompt}` holds the call; `POST /api/threads/{id}/decide {call_id, decision, answer?}`.

### Out

Anything DC-03+; external MCP servers.

## Acceptance criteria

- [ ] Truth-table test: all 8 rows produce the specified result.
- [ ] A held call has a kernel operation in `awaiting_decision` whose parent is the turn's operation; approve → executed + receipt; deny → `tool_denied` told to the model.
- [ ] Allow-always writes one policy row and the next identical call auto-admits; Allow-once writes none.
- [ ] `dw check` + the one-path census + the Phase-131 fence green with only the executor rows added.

## Test plan

- **Unit / integration:** tests/unit/test_thread_tool_gate.py, tests/unit/test_one_path_census.py, tests/unit/test_phase143_*census.py, tests/integration/test_threads_api.py
- **Manual / device:** `.43` legs in story 06.
