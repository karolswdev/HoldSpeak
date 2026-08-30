# DC-02 The Hands — seam census (2026-08-30)

- **Kernel tool turns:** `holdspeak/kernel/tool_call.py` ToolCallCodec `tool.call@1` (validate/authorize/admit/decide; family `tool_gate`; policy via `holdspeak/operation_policy.py`, default control_mode yolo); `holdspeak/services/tool_turn_controller.py` (durable authority; reserved→model_running→tool_requested→tool_admitted→tool_receipted→…; `_MAX_PROVIDER_STEPS=4`, `_MAX_TOOL_CALLS=6`); tables `turn_capability_leases`, `tool_turns`, `tool_turn_model_steps`, `tool_turn_tool_calls`, `tool_turn_tool_call_results`, `tool_turn_effect_children`, `tool_turn_commands`, `tool_turn_transitions` (schema.py:3124–3292); admission `admit_tool_call` → `reserve_tool_call` → `BrokerToolCallPort.admit` → `broker.submit(raw, MODEL_TURN_TOOL_PRINCIPAL)`.
- **Classes/dialects:** `holdspeak/services/tool_capability_service.py:20-22`; `ToolQualification` gates eligibility — the `.43` deployment must be qualified.
- **Model adapters:** `holdspeak/services/tool_model_adapter.py` (render/parse; deterministic test adapter); `agent_turn_service.py`'s prompt transport IGNORES tools=.
- **Registry:** `holdspeak/mcp/tools.py` TOOLS + 14 families; `dispatch(name, args, principal)` with module globals for db/observer → in-process call is trivial; People family gated (`access_mode`, `_mcp_readable`, `people_mcp_private_record_refused`).
- **Engine gap:** no `tools=`, no `delta.tool_calls` parsing in `_chat_completion_deltas` — built ahead of this charter (Delta kinds `tool_call_delta`, `tool_calls`).
- **Decisions today:** gate proposals routes + `web/src/desk/gate.ts`; `processWindowReducer.ts` awaiting_decision; no thread tool frames yet.
- **Web:** reusable renderers — DoorBoardLane, DecisionPullout card, BriefView PersonSection, FollowThroughView cards; RAW fold + receipt short-code in ThreadPullout; `threads.status_line` exists, no writer.
- **Tests to copy:** test_phase143_tool_turn_controller/model_steps/routing/capability_lease; integration tool_turn_boundaries; Phase 151 thread tests/rigs.
- **Risks:** one-path census rows for the executor; People results sensitive; the 4→10 cap must be lease-scoped; `thread_tool_policy` does not exist.
