# mcp_tools — adversarial review

Workflow id: `mcp_tools`  
Job: Run, inspect and retain a Desk tool operation  
Baseline: `main55572802181d6a8045f6d27e3c722aaf5694dbbd` (PR1430)  
Reviewer task: `review_mcp_tools`  
Evidence class: source, assertion and reference-capture inspection; no execution or owner observation

VERDICT: RATIFY-WITH-CONDITIONS

## Totality

The general job is an MCP client or bounded agent run calling a named tool:
authenticate, resolve its palette, admit it through the hub, expose
target/egress/outcome/receipt, retain the result, and return to its Workbench,
Thread or client. Reads, writes, prepared sends, config, refusal, expiry,
retry and cancel are different variants. `mcp_tools` bundles M1–M6 and the
whole catalogue, too broad for one face or acceptance loop.
`holdspeak/mcp/server.py:132-179` makes the sidecar a hub proxy;
`holdspeak/mcp/tools.py:630-683,960-990` supplies catalogue, schema and
dispatch. The Workbench result is the clearest active consumer, not a
universal MCP inspector.

The public mapping is materially wrong: `docs/USE_CASES.md:16` names “Review a
held tool request”, and
`docs/internal/betterment/native-experience/USE-CASE-INVENTORY.json:706-708`
assigns it here.
That is the Coder Gate job, with a hook-held request, owner decision, expiry,
restart invalidation and receipt; it is not a general `tools/call`. Gate's
actual lifecycle is `docs/GATE.md:42-102,121-143` and
`holdspeak/web/routes/system/gate_routes.py:81-146`.

FINDINGS:

1. **P1 — public job and implementation boundary are conflated.** Cost:
   approval controls may land in a generic MCP inspector, duplicating
   Conductor state. This fails Tenets 3 and 5. Correction: map the held row to
   `agents_conductor`/Coder Gate, retain `mcp_tools` for client operations, and
   cross-reference without merging screens.

2. **P1 — identity, recovery and return are not a settled contract.** Trace
   records only answered, object-bearing calls
   (`holdspeak/services/run_trace.py:377-425`) and folds by item/trace
   (`holdspeak/services/run_trace.py:514-563`); the HTTP route records launch/run calls at
   `holdspeak/web/routes/mcp_http.py:327-346`. Kernel receipts exist
   (`holdspeak/mcp/tools.py:711-719,831-839`), but failed/refused/read calls,
   egress, retry and cancelled-parent return are unspecified. Cost: “accepted”
   can look like “done”. This fails Tenets 3, 6 and 7. Correction: specify one
   projection over existing facts: caller/run key, tool-call id, target,
   egress, outcome, receipt/refusal and recovery link. Preserve `workflow_id`
   for the graph and `parent_operation_id` for its run; mint no parallel id.

3. **P2 — the audit evidence is incomplete before proposing work.** The
   inventory lists only `tests/unit/test_mcp_ask.py:62-83`, while active guards
   cover real-hub catalogue calls and mutation proof
   (`tests/integration/test_mcp_every_tool_runs_on_hub.py:1-18,198-225`), the
   one authority row for every dispatched tool (`tests/unit/test_thread_tool_gate.py:346-357`),
   Thread hold/deny/abort/pass-cap (`tests/unit/test_thread_tool_loop.py:339-451`),
   and Gate fail-closed restart/idempotency (`tests/integration/test_gate_threat_model.py:145-206`).
   Cost: duplicated guards or a new runtime; this fails Tenets 1 and 3.
   Correction: include this coverage, name its limits, and add only missing
   cross-surface assertions.

## Convergence

`automation_build` and `automation_schedule` should consume `run_trace`/
`workbench.results`; first consumers are
`web/src/desk/components/automation/ResultCard.tsx:8-18,83-103` and
`web/src/desk/components/UsedLines.tsx:103-155`. `threads` consumes the same call facts through
`ask_trace` and `record_value` (`holdspeak/services/thread_service.py:1906-1913`).
`agents_conductor` and `agent_result` retain Gate/session identity and owner
decision; held requests remain separate. `workflow.run`/cancel is a stored
graph with parent/child receipts (`docs/AGENTS_AND_THREADS.md:187-202`). Share
receipt language and projections only; do not merge Gate authority, Thread
policy, Workbench ownership, or add a second registry.

## User experience

The 393 captures
`/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/conductor-393.png`
and `/Users/karol/dev/tools/wt-modernize-all-20261022/.tmp/evidence-shots/desk-sweep/automation-393.png` show, respectively, an Agents list and a
readable Workbench result; neither shows a held request or MCP call identity.
Source supports a fast “call → result → continue” path for Workbench/Thread,
but not a general inspector or Gate decision path. Keep results in-world,
show target/egress where needed, and return refusal/retry to the originating row.

CONDITIONS: Correct the public mapping; bound this audit to MCP operation
inspection and name first consumers; specify identity/outcome/recovery/return
using existing trace and kernel receipts; add cross-surface assertions without
a new runtime or approval framework.

MISSED:

1. Gate hold, owner decision, hook resume, and hub restart invalidation.
2. Palette/authority refusal and return to the same item.
3. Duplicate/retry of one `command_id` or parent operation without a second effect.
4. Provider/egress failure where no external result may be claimed.

TUESDAY: A Workbench result can be useful quickly, but this audit does not yet let the owner reliably inspect one operation, recover it, and return to the exact job.

## Acceptance challenges

1. A Workbench agent reads notes, writes one note and prepares one send; the result shows linked Looked at/Wrote/Prepared rows, egress and receipt, then returns to Workbench.
2. Palette/authority refusal shows refusal, preserves the parent item, and Retry does not duplicate a write.
3. A Thread tool is held, denied, then retried; the turn retains decision, draft and source context.
4. A matched Bash Gate request is approved once; replay is idempotent, while restart invalidates the old hold and yields a named deny/new proposal.
5. `workflow.run` returns one workflow id, parent operation id and child receipts; cancel/reopen resolves that run, not a twin.

UNKNOWN: No tests were run. No live MCP/API/provider/native action, owner acceptance, performance, accessibility, or real egress was observed; the two reference captures are not MCP-operation or Gate acceptance proof.
