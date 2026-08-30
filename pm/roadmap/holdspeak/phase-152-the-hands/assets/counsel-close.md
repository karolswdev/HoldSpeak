# Close counsel -- Phase 152 The Hands (DC-02)

**Verdict: RATIFY-WITH-CONCERNS**

Zero must-fixes. Two should-fixes. Seven recorded notes.

---

## MUST-FIX

None.

Every vector named by the brief was investigated to the code line, the
test, and the live payload. The People fence, the truth table, the
kernel children, the abort path, the elicitation wire, the 32 KB cap, the
one-path census, and the UI surfaces are all sound. Details below.

---

## SHOULD-FIX

> **Orchestrator, in-round (2026-08-30):** both applied. S1 — `/decide`
> answers 409 `tool_call_not_pending` unless `handle.state ==
> "awaiting_decision"` (`holdspeak/web/routes/threads.py`). S2 — the
> sentinel `_sensitive_texts` is stripped on every return path of
> `_m1_redactor` (`holdspeak/services/thread_service.py`). Focused tests
> green (`test_thread_decide_always.py`, `test_thread_people_fence.py`).

### S1. `/decide` does not guard against stale handles

`holdspeak/web/routes/threads.py:280` looks up the handle in
`executor._handles` but does not check whether
`handle.state == "awaiting_decision"`. A second POST to `/decide` for
a call that already completed mutates the handle's state back to
`"admitted"` (via `thread_tools.py:529`) and returns
`{"state": "admitted"}` -- misleading. No re-execution, no data
corruption, no observable side effect beyond the wrong response body.

- **Repro:** call `/decide` twice for the same `call_id` within the
  turn's lifetime (between the first decide and `_tool_executor.unregister`
  at `thread_service.py:986`).
- **Consequence:** incorrect API response; dead handle mutated.
- **Fix:** add `if handle.state != "awaiting_decision": return 409` before
  `executor.decide()` at `threads.py:291`.

### S2. `_sensitive_texts` not stripped from the payload on local egress

`_m1_redactor` (`thread_service.py:1181-1182`) returns early for local
boundaries (`same_device`, `local`, `private_network`) before reaching
the `result.pop("_sensitive_texts", None)` at line 1227. The key
survives in the dict passed to the prompt adapter. The adapter
(`prompt_adapter.py:115-122`) destructures only `messages`,
`temperature`, `max_tokens`, `tools`, `tool_choice`, so the engine
never sees the key. The key also persists in the frozen admission
evidence.

- **Consequence:** no functional impact; implementation detail leaks into
  internal structures. The data it carries is already present in the
  messages on local turns.
- **Fix:** move `payload.pop("_sensitive_texts", None)` before the
  `return payload` at `thread_service.py:1182` (or strip unconditionally
  at the top of the function).

---

## RECORDED NOTES

### R1. Multi-tool-per-pass sibling gap

When the model calls 2+ tools in a single pass, each result is a
sibling `tool` message with `parent_id = assistant_msg_id`
(`thread_service.py:834`). The leaf-path walker (`db/threads.py:476`)
picks only the newest sibling. Earlier siblings are absent from later
turns' `_assemble_payload` messages. Not a People fence issue (the
data is simply not in the payload, so there is nothing to leak), but a
functional context loss for rare parallel-tool-call scenarios.

### R2. Paraphrase laundering is real and stays DC-03

Story-03 observed the model paraphrasing a People readiness result
into its answer text. The M1 redactor handles verbatim strings, not
semantic content. The DC-03 `egress-guard` guardrail is the belt over
braces for this gap.

### R3. Cleanup block is not in a `finally`

`thread_service.py:918-987` runs after `except Exception` at line 912,
not in a `finally`. `BaseException` subclasses (`SystemExit`,
`KeyboardInterrupt`) would skip cleanup, but process termination
destroys class-level dicts anyway. Acceptable for a single-owner desk.

### R4. Leaked override rows on failed admission

`_apply_profile_override` at `thread_service.py:338-343` writes a
next-run override row before `admit`. If admission raises, the row
persists keyed by a unique invocation UUID. No future admission
consumes it. Minor data accumulation; no functional consequence.

### R5. Historical tool messages replayed without `tool_call_id`

On later turns, `_assemble_payload` (`thread_service.py:1302`) builds
`{"role": "tool", "content": ...}` from persisted tool-role messages
without `tool_call_id`. A strict cloud provider may reject this
(already recorded in story-03; R6 of this counsel's predecessor).

### R6. `test_the_mesh_receiver_names_no_model_execution_at_all` order-sensitive under `-n 4`

Fails in parallel, passes serially (`evidence-story-05.md` run 1 vs
run 3). Already recorded in story-05 narrative; branch-inherited, not
new to this phase.

### R7. The 250 ms abort contract is best-effort

The cancel event is checked before every pass and before/after every
tool execution, but a tool handler that blocks for its full 30 s
deadline delays the abort response by up to 30 s. The 250 ms contract
holds "within the stated window" (the next check), not wall-clock from
the cancel signal. The story-01 acceptance criteria and settled-design
D1 both describe it this way ("within 250 ms of the next check").
Honest, but worth noting.

---

## Evidence reviewed

| Question | Verdict | Key evidence |
|---|---|---|
| M1/M2 fence: People bytes reach cloud? | **CLEAN.** `_sensitive_texts` accumulated across passes (`thread_service.py:476,880`); `_m1_redactor` runs on every `execute_stream` call (`inference_adoption_service.py:1694`); prompt adapter ignores the key; hub-leg.py LEG B LIVE: `"PASS cloud payload carries [people content withheld]"`, `"PASS no sentinel key leaks"`. Truncation at UTF-8 boundary does not break the fence (both `sensitive_texts` and message content use the same truncated `result_text`). | `evidence-story-03.md`, `story-03-hub-payloads-live/leg-b-thread.json`, `test_thread_people_fence.py` (15 passed) |
| M3/M4 gate: truth table correct, kernel children? | **CLEAN.** All 8 rows tested. Allow-always scoped to (thread\_id, tool\_name), newest-wins, append-only (`db/threads.py:714,730`). Deny holds. Sequential processing prevents bypass. `broker.submit` with `tool.call@1` creates the child. | `test_thread_tool_gate.py` (29 passed), `test_one_path_census.py` (34 passed) |
| M5 abort: discard in-flight, no leak? | **CLEAN.** Cancel checked before every pass (`line 553`), before every execution (`line 751`), after execution (`line 761`). `decision_events` popped on break. Executor unregistered at line 986. No realistic leak path. | `test_thread_tool_loop.py` (abort test), M5 fork audit |
| M6 elicitation: `__answer`, decline, double-answer? | **CLEAN.** Re-dispatch carries `args.__answer` (`thread_tools.py:565`). Decline ends `tool_denied` with persisted part. Double-answer: stale mutation on dead handle, no re-execution (S1 above). | `test_thread_decide_always.py` (6 passed), `test_hs152_hands_glass.py::test_elicitation_form_submit_and_decline` |
| Palette sizing for 32k profile? | **CLEAN.** `CHAT_PALETTE` = 26 tools, 12.6 KB. Full census (141 tools, 79 KB) stays as `TOOL_NAMES` gate table only. | `thread_tools.py:209-227`, story-03 addendum |
| Pass cap (10)? | **CLEAN.** `range(max_passes + 1)` gives 10 streaming passes (0-9); cap fires at pass\_num=10 with `pass_cap_reached` persisted and turn done. | `test_thread_tool_loop.py::test_pass_cap_*` |
| Profile override race? | **CLEAN.** Invocation-scoped UUID, consumed at admission. Each pass gets its own invocation\_id. No cross-turn interference. | `thread_service.py:575,577-580` |
| 32 KB cap: UTF-8 boundary, sensitive match? | **CLEAN.** `_truncate_utf8` walks back from cap to valid boundary (`thread_tools.py:377-383`). Meta persisted. Both `sensitive_texts` and message content use the same truncated string; exact-string match succeeds. | `thread_tools.py:376-383`, `thread_service.py:825-831,879-880` |
| One admission path? | **CLEAN.** `test_one_path_census.py`: 34 passed. New sites use existing pathways: (1) re-admission through `inference_adoption_service.admit`, (2) tool admission through `broker.submit` with `tool.call@1`. | `test_one_path_census.py` (34 passed serially) |
| UI: modal, prose, overlap, keyboard, 393 overflow? | **CLEAN.** All shots reviewed: decision box in-flow under the tool row, no modal. Labels state what (HELD, DONE, DENIED, FAILED, `tool_execution_failed`). Errors in-flow. Tab reaches all three verbs. 393 does not overflow. Elicitation form renders correctly at both widths (checkbox, dropdown, text input, Submit/Decline). RAW fold on every result row. Status line in the head with persisted text. | `assets/story-04-shots/` (15 PNGs), `assets/story-05-shots/` (6 PNGs), `test_hs152_hands_glass.py` (5 legs), `test_hs152_renderers_glass.py` (2 legs) |

---

## What the phase got right

This is a clean phase. The four latent defects story-03 surfaced --
handless hub service, palette after admission, runner dropping
tool\_calls, census overflowing admission -- are the kind of real-path
bugs that only appear when you drive the code honestly through the
production coordinator instead of trusting fake-adoption loop tests.
Finding and fixing them in-round, then banking the LIVE `.43` metal
proof before the walk story, is exactly how Art. IX is supposed to
work. The truth table is a genuine truth table (eight rows, one
function, table-driven test, no heuristic). The People fence
(`_sensitive_texts` accumulator + `_m1_redactor` on every pass + the
prompt adapter as a final firewall) is defense in depth that survived
every vector this counsel could construct. The UI is constitutionally
correct -- no modals, no prose, errors in-flow, keyboard-reachable,
393-clean -- and the Signal Workbench material model holds. The tool
count arithmetic (141 to 142, families 30 to 31) is honest and the
doc-drift guard confirms it. The one-path census gained rows for the
executor and nothing else. Zero must-fixes from close counsel on a
six-story phase is a good result.
