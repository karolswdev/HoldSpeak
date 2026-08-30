# HS-155-01 - chat.subthread: a child thread, receipted, never a side door

- **Project:** holdspeak
- **Phase:** 155
- **Status:** backlog
- **Depends on:** HS-154-05
- **Unblocks:** HS-155-02, HS-155-05
- **Owner:** unassigned

## Problem

Delegation must be a desk object, not a hidden fork: `chat.subthread`
creates a child thread bound to a mode, admitted and receipted through
the same gate as every other effect (settled design D1; RFC §6.9 —
warpdrv auto-approves, we do not).

## Scope

- **In:** the `chat.subthread` MCP tool (effect_proposal, thread
  family): args {title, mode, prompt, wait_s?}; S7 validation (mode
  exists, kind='mode', prompt non-empty, depth cap 1 — a child of a
  child is refused with a typed error); creates the child via
  `threads.parent_thread_id`; optional pre-allow of the mode's list in
  `thread_tool_policy` (append-only rows, receipted). The call rides
  the SAME ThreadToolExecutor/truth-table path — safe mode holds it in
  the pending box like any effect. Tool count arithmetic updated
  (`len(TOOLS)` is truth).
- **Out:** running the child (02), notifications (03).

## Acceptance criteria

- [ ] Real coordinator + fake engine: the model calls chat.subthread → a child threads row exists with parent_thread_id set and the recipe bound; the receipt row renders; in safe mode the call waits in the pending box.
- [ ] Depth cap: a child calling chat.subthread gets the typed refusal, no row.
- [ ] Validation: unknown mode / empty prompt → typed error, no row; the census + tool-count fences updated and green.

## Test plan

- **Unit:** `tests/unit/test_chat_subthread.py` (the 152/153 real-coordinator pattern) + the tool census/count fences.
- **Integration:** glass leg `subthread` (the 155 glass file) shows the receipt row.
- **Manual / device:** story 05.

## Notes / open questions

- The child inherits the owner principal; the profile follows the child's mode/thread assignment, not the parent's override.
