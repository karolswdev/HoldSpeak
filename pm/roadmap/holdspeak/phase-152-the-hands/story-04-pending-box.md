# HS-152-04 - The pending box (decision + elicitation rows, decide route)

- **Project:** holdspeak
- **Phase:** 152
- **Status:** done
- **Depends on:** HS-152-02
- **Unblocks:** HS-152-05
- **Owner:** unassigned

## Problem

The owner sees every call: as a receipt row in yolo, as a decision box
in safe, as a form when a tool asks a question — in-flow, no modal
(Art. VII), keyboard reachable (settled-design D4).

## Scope

### In

- `threads.ts`: apply `thread_tool_pending` / `thread_tool_result` / `thread_status_line`; `decide()`; optimistic state + reconcile.
- `ThreadPullout` tool row: name · class glyph · args head · state; decision box (Allow once / Allow always / Deny); JSON-Schema form row (string/number/boolean/enum; Submit/Decline); receipt short-id + outcome; status line in the head.

### Out

Per-kind result renderers (story 05).

## Acceptance criteria

- [x] Real-Chromium probe: a held call renders the decision box; Allow once → row flips to receipted; Deny → `tool_denied` row.
- [x] Elicitation form renders from a schema fixture and submits the answer.
- [x] No horizontal overflow at 393; keyboard: Tab reaches all three verbs, Enter activates.

## Test plan

- **Unit / integration:** vitest ThreadPullout tool rows + threads store; tests/e2e/test_hs152_hands_glass.py
- **Manual / device:** shots reviewed by the orchestrator.

## What shipped (2026-08-30, opus worker + orchestrator review)

- **Store** (`web/src/desk/threads.ts`): `ToolRow` model keyed by
  call_id under its assistant message (pending / awaiting_decision /
  elicitation / running / receipted / failed / denied), status line per
  thread, `decideToolCall()` → `POST /decide`, optimistic decide +
  reconcile on the result frame, and **hydration from persisted parts**
  on load (the wire parts now carry `meta_json` + `tool_call_id`), so a
  reload shows the same rows the live frames built.
- **Pullout** (`ThreadPullout.tsx` + `thread-pullout.css`): tool row
  (name · class glyph R/B/E · args head, truncated · state), decision
  box with the three verbs in-flow under the row (Tab reaches all,
  Enter activates; no modal), JSON-Schema form row (string / number /
  boolean / enum; Submit / Decline), receipted = short-id + outcome,
  failed/denied = the error code in-flow, People badge on sensitive
  results, the status line in the head. A held call scrolls into view.
  Signal Workbench material (opaque, beveled, 2 px, mono).
- **Server, two real seams found by the build:** (1) `/decide` gained
  `always` — Allow-always writes a `thread_tool_policy(allow)` row
  before approving, and the next call auto-admits (truth-table row 1);
  the route only had bare approve/deny. (2) **Elicitation was a dead
  end**: the loop persisted a `{"elicit": …}` result as terminal and
  never collected the answer. Now an elicitation result re-emits
  `thread_tool_pending` with the schema, blocks on `decide(approve,
  answer)` / `decide(deny)`, then re-executes with `args.__answer` or
  ends `tool_denied`. Pinned in `tests/unit/test_thread_decide_always.py`.
- **Proof:** vitest 29 (store reducer + rows), unit 6 (+ scoped
  regression 70), glass `tests/e2e/test_hs152_hands_glass.py` 4 legs on
  the real hub (safe mode, valid `desk.create` → receipted; Deny;
  elicitation with all four field kinds, Submit and Decline; bogus
  `desk.get` → `tool_execution_failed`; no horizontal overflow at 393
  and 1440). Web baseline zero branch-new. 15 shots in
  `assets/story-04-shots/`, reviewed by the orchestrator.

Folded into story 05 (the status-line story): the head's
"Processing (pass 2)…" line lingers after `thread_turn_done` — clear it
on done; the boolean checkbox in the form is centred in its row at 393
(align with the label).
