# HS-152-04 - The pending box (decision + elicitation rows, decide route)

- **Project:** holdspeak
- **Phase:** 152
- **Status:** backlog
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

- [ ] Real-Chromium probe: a held call renders the decision box; Allow once → row flips to receipted; Deny → `tool_denied` row.
- [ ] Elicitation form renders from a schema fixture and submits the answer.
- [ ] No horizontal overflow at 393; keyboard: Tab reaches all three verbs, Enter activates.

## Test plan

- **Unit / integration:** vitest ThreadPullout tool rows + threads store; tests/e2e/test_hs152_hands_glass.py
- **Manual / device:** shots reviewed by the orchestrator.
