# HS-164-02 - evaluate_due: watches evaluate themselves, safely

- **Project:** holdspeak
- **Phase:** 164
- **Status:** backlog
- **Depends on:** HS-164-01
- **Unblocks:** HS-164-03
- **Owner:** unassigned

## Problem

WatchService.evaluate_once is MANUAL by design ("P5 owns
scheduling", watch_service.py:451). §14 P5: evaluate_due() as an
independent conductor failure boundary. A broken watch or provider
must never stop the others, and repeated failure must open a circuit
instead of hammering.

## Scope

- **In:** WatchService.evaluate_due(principal): select due watches
  (cadence from 01), evaluate each through the EXISTING evaluate_once
  path (reuse the whole manual seam — snapshot, diff, transitions,
  observations, idempotence by UNIQUE(watch_id, watch_revision,
  source_revision)), per-watch isolation (one failure isolates,
  outcome recorded, the loop continues), the circuit: N consecutive
  failures opens it for that source/watch (backoff window; half-open
  probe; honest outcome states), success resets. TRACE the legacy
  ReactionService.refresh_due_watches boundary from 01 and record
  which scheduler owns which watch family — never two. Bookkeeping
  writes (last_evaluated, next_due) in the same transaction as the
  evaluation row.
- **Out:** steward triggering (03), conductor wiring (04).

## Acceptance criteria

- [ ] Due selection honors cadence under test; a not-due watch never evaluates; bookkeeping advances transactionally.
- [ ] One broken watch isolates: others still evaluate, the failure is a recorded outcome, nothing raises out of evaluate_due.
- [ ] The circuit opens after the configured streak, refuses evaluation with an honest outcome while open, half-opens after the window, and closes on success — all under test.

## Test plan

- **Unit:** tests/unit/test_watch_evaluate_due.py.
