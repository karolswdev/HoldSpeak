# Phase 152 settled design — The Hands (DC-02)

Ruled by the orchestrator 2026-08-30 from the DC-02 seam census
([audit-census.md](./audit-census.md)) and the holistic counsel
design-beat ([counsel-design-beat.md](./counsel-design-beat.md):
RATIFY-WITH-CONCERNS; M1–M6 accepted). Parent RFC
`docs/internal/PLAN_PHASE_DESK_CHAT.md` §6.4, §6.7. Builders implement.

## The one sentence

Inside a Thread turn the model may call the desk's own tools — the
in-process MCP families — and every call is a child kernel operation of
that turn with its own receipt: in yolo it runs and the row is a receipt
box; in safe the row is Allow-once / Allow-always / Deny; a `people.*`
result is marked sensitive at birth and withheld from any later cloud
turn; ten passes, then the model must answer.

## D1 — the loop (story 01)

- `ThreadService._run_streaming_turn` becomes a pass loop (≤ 10; the
  chat lease's own cap, the Recipe agent turn keeps its 4): stream →
  if `tool_calls` delta → persist a `tool_call` part per call
  (meta: id, name, args, class, state) → resolve each (D2) → execute
  (D2) → persist a `tool`-role message with the result parts → next
  pass with the tool messages appended. No `tool_calls` → done.
- Frames: `thread_tool_pending {thread_id, message_id, call_id, name,
  args_head, class, decision_required: bool, elicitation?: schema}`,
  `thread_tool_result {…, receipt_id, outcome, kind, summary, sensitive}`,
  `thread_status_line {thread_id, text}`.
- Abort (M5): the cancel event is checked before every pass, before
  every tool execution, and tool handlers run under a 30 s deadline; on
  cancel the in-flight result is discarded, the turn ends
  `indeterminate`, `thread_turn_done{aborted}` within 250 ms of the
  next check.
- Engine: `tools=` + `tool_call_delta`/`tool_calls` deltas (built
  ahead of this charter); the tool palette sent = the thread's allowed
  tools (D2) rendered as OpenAI function schemas from the MCP tool
  `inputSchema`.
- Error taxonomy (S1) on `error_json.code`: `tool_execution_failed`,
  `tool_timeout`, `tool_denied`, `pass_cap_reached`, `tool_unknown`.

## D2 — the gate (story 02) — the truth table (M3, M4)

Additive: `thread_tool_policy(id, thread_id, tool_name, decision CHECK
('allow','ask','deny'), set_at, deleted_at)` — append-only rows, newest
wins, never updated.

| `thread_tool_policy` | `control_mode` | class | result |
| --- | --- | --- | --- |
| allow | any | any | admit → execute; receipt row |
| deny | any | any | refused; model told `tool_denied` |
| ask | any | any | hold → decision box |
| unset | yolo | any | admit → execute; receipt row |
| unset | neutral | evidence_read / candidate_builder | admit |
| unset | neutral | effect_proposal | hold → decision box |
| unset | safe | evidence_read | admit |
| unset | safe | candidate_builder / effect_proposal | hold → decision box |

Every call — admitted or held — is a kernel child of the turn's
`operation_id` through the existing `ToolCallCodec` (`tool.call@1`) and
the `ToolTurnController`/foundation (M4; NO new admission path; the
one-path census gains rows for the thread executor, nothing else).
Execution = `holdspeak.mcp.tools.dispatch(name, args, principal)`
in-process, principal = the model-turn tool principal, result bytes
capped by the lease. Decision box gestures: Allow-once → `decide(approve)`
this call; Allow-always → policy row `allow` + approve; Deny → policy row
`deny` for this call only? NO — Deny = refuse this call (no row);
"Never" is not offered in DC-02 (recorded). Elicitation (M6): a tool may
return `{"elicit": {schema, prompt}}`; the executor holds the call as
`awaiting_decision`, the `thread_tool_pending` frame carries
`elicitation`, `POST /api/threads/{id}/decide {call_id, decision:
approve|deny, answer?}` resolves it and the answer is passed back to the
tool as `args.__answer`.

Allowed palette (until DC-03 modes): every `evidence_read` +
`candidate_builder` tool; `effect_proposal` tools included (the truth
table gates them); tool classes come from each family's declaration
(census: `tool_capability_service`), People tools are class
`evidence_read`/`effect_proposal` as declared and additionally
`sensitive`.

## D3 — the People fence (story 03) — M1, M2

- Any `people.*` result → its `tool`-role message parts are inserted
  with `sensitive=1` (source of truth, M2).
- The pass loop carries a `_sensitive_texts` accumulator: initial
  assembly + every sensitive result's text; `_m1_redactor` runs on EVERY
  pass's reconstructed payload via the coordinator's `payload_redactor`
  (M1). Pinned through the real coordinator: seed a `people.*` tool
  result, switch `profile_override` to cloud, the captured payload is
  clean; local verbatim.
- The model may call `people.*` effects only through the truth table
  (an effect_proposal, held in safe/neutral). The MCP People family's
  own refusals (`people_mcp_private_record_refused`) stand unchanged.

## D4 — the pending box + elicitation (story 04)

Rows in `ThreadPullout`: a `tool_call` part renders as a tool row
(name · class glyph · args head · state); pending + `decision_required`
→ the decision box (Allow once / Allow always / Deny, keyboard
reachable, no modal); pending + `elicitation` → a JSON-Schema form row
(string/number/boolean/enum fields; Submit / Decline); receipted → the
receipt short-id + outcome. `thread_status_line` → the head. Client:
`decide()` + optimistic state, reconcile on the result frame.

## D5 — the renderers + status line (story 05)

Per-kind result renderers reusing existing desk components: meeting →
meeting chip, person → the People card projection (display name +
readiness, never ledger text), board → DoorBoardLane, note → Material,
decision → decision card; unknown kinds → key/value table; RAW fold
always. `set_current_status` becomes a `thread.*` MCP family tool
(one new tool; docs count arithmetic) writing `threads.status_line`.

## D6 — the walk (story 06)

Counsel's four legs: real `.43` with a `people.*` read + a `door.*`
effect (receipts; control = no tools); People boundary under profile
switch with the captured payload; safe-mode decision box (Allow-once
writes no row, Allow-always writes one and the next call auto-admits);
glass 1440 + 393 (tool rows, decision box, elicitation form,
`tool_execution_failed`, status line). Door-walk leg extended; docs;
close counsel. The `.43` deployment must be tool-QUALIFIED
(`ToolQualification` for Qwen3.6, dialect `qwen`/`openai`) — the walk
seeds that qualification honestly (an eval against the real model).

## Recorded (not fixing): R1 adaptive cap later; R2 paraphrase
laundering = DC-03 guardrail; "Deny always" not offered.

## Addendum (HS-152-03, 2026-08-30) — the palette, the override, the runner

Ruled by the orchestrator from what the real path showed:

- **Palette ≠ census.** D2's "allowed palette = every class" stands as
  the GATE's table (`TOOL_NAMES`: any call the model makes is classified
  and resolved). What a turn OFFERS is `CHAT_PALETTE` (26 desk-facing
  hands: desk/zone/memory, door/monday, meeting/follow-through/decision
  records, six People reads+adds). The full 141-schema census is 79 KB
  and the admission law reserves one token per byte — it overflowed a
  32k context at admission. DC-03 modes widen or narrow the palette per
  recipe; the census is not a palette.
- **The palette rides inside the admitted payload.** `execute_stream`
  replays frozen admission evidence; anything injected after admit never
  reaches pass 1.
- **`tool_calls` is a first-class delta** in `InferenceRunner._attempt_stream`
  (forwarded like text/reasoning; sets `first_delta_seen`).
- **`thread.profile_override` is honored at admission** as an
  invocation-scoped next-run override (`apply_next_run_override`) —
  per invocation, so every pass of a tool turn re-applies it. The
  assignment ledger stays the routing truth; the thread row is the pick.
- **The hub's ThreadService has hands**: `_thread_factory.py` wires
  `mcp.tools.dispatch` + `Config.control_mode`.
