# HS-155-02 - The conductor runs the child; the parent waits 30 s then backgrounds

- **Project:** holdspeak
- **Phase:** 155
- **Status:** backlog
- **Depends on:** HS-155-01
- **Unblocks:** HS-155-03, HS-155-05
- **Owner:** unassigned

## Problem

A child that only exists as a row does nothing. The desk already owns a
run-loop for fresh-session agent runs — the workbench conductor — and
the child runs there, not in a new executor (settled design D2).

## Scope

- **In:** wire child-thread runs into
  `holdspeak/workbench_conductor.py`'s run-loop: the subthread tool
  enqueues a child run (the child's first turn = its prompt through the
  REAL start_turn path — palette, guardrails, fence all apply); the
  parent's executor waits up to `wait_s` (default 30, capped — S7) for
  the child's turn to finish, then returns {child_thread_id, state:
  "done"|"backgrounded", answer?}. Backgrounded children keep running;
  their completion lands via 03. The conductor's bus frames are reused
  for run state.
- **Out:** notification consumption (03), the crew row (04).

## Acceptance criteria

- [ ] Real coordinator, two fake engines (parent + child): a fast child returns state=done with the answer in the tool result; a slow child returns backgrounded within ~wait_s and finishes afterwards (its turn rows exist).
- [ ] The child's turn goes through admission (captured payload; its mode's palette applied; a guardrail-enabled child mode runs its guardrail).
- [ ] Stopping the child run through the conductor leaves the child thread consistent (no orphaned pending frames).

## Test plan

- **Unit:** `tests/unit/test_subthread_conductor.py`.
- **Integration:** glass leg `crew-run` (a stubbed slow child shows backgrounded).
- **Manual / device:** story 05 (.43).

## Notes / open questions

- One conductor, one run-loop — no parallel authority (the #511 platform-reset spirit applies to the backend too).
