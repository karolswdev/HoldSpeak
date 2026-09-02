# HS-164-02 - evaluate_due: watches evaluate themselves, safely

- **Project:** holdspeak
- **Phase:** 164
- **Status:** done
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

## Trace record

### Boundary rule: legacy vs graduated scheduler

**Legacy scheduler:** `ReactionService.refresh_due_watches`
(reaction_service.py:308). Iterates ALL enabled watches via
`self._repo.list_watches()`, reads cadence from
`watch["query"].get("refresh_interval_minutes")` (JSON field), uses
`watch["updated_at"]` as the due-ness clock. Calls
`self.refresh_watch()` for each due watch. Owns pre-graduation
connector_watches rows (state='' or no schema_version).

**Graduated scheduler:** `WatchService.evaluate_due`
(watch_service.py). Queries `list_due_watches(now_iso)` which selects
only rows where `enabled=1 AND state IN ('active','tested') AND
next_evaluation_at IS NOT NULL AND next_evaluation_at <= ?`. Reads
cadence from the `evaluation_cadence_minutes` column. Calls
`_evaluate_core()` for each due watch.

**Boundary:** graduated watches have `state IN ('active','tested')`
set during the WatchSpec@1 graduation flow. Legacy watches have
`state=''` (the column default). The two schedulers are partitioned
by the state column: `refresh_due_watches` touches all rows but only
legacy rows have the JSON cadence field; `evaluate_due` only queries
graduated rows via the state filter. No row is ever owned by both
schedulers.

### Extraction: _evaluate_core

evaluate_once's body was extracted to `_evaluate_core(self, principal,
watch_id, *, trigger_kind, now_iso, txn_hook)`. evaluate_once
delegates to it with trigger_kind="manual" and no txn_hook, then does
the same post-txn `update_watch_spec(baseline_state, last_evaluated_at)`
as before -- byte-identical public behavior. evaluate_due delegates
with trigger_kind="scheduled" and a txn_hook that writes bookkeeping +
circuit reset inside the evaluation transaction.

### Circuit lifecycle

- **Threshold:** `CIRCUIT_FAILURE_THRESHOLD = 3` (module constant,
  watch_service.py; mirrors endpoint_health.py HS-103-04).
- **Cooldown:** `CIRCUIT_COOLDOWN_SECONDS = 900` (15 minutes; module
  constant). The brief noted steward_policies.cooldown_seconds exists
  but the circuit is per-watch, not per-project; a policy lookup would
  couple the watch scheduler to the steward layer. A module constant
  with a clear name is honest; revisit when per-watch tuning is needed.
- **Open:** after N consecutive failures, circuit_state='open',
  circuit_opened_at=now, circuit_failure_streak=N.
- **Cooldown gate:** if opened_at + CIRCUIT_COOLDOWN_SECONDS > now,
  the watch is skipped with outcome `skipped_circuit_open`.
- **Half-open probe:** if cooldown elapsed, ONE evaluation is allowed.
  Reported as outcome `probe_half_open`. Success: closes circuit
  (state='closed', streak=0, opened_at=None). Failure: re-opens with
  fresh opened_at and streak+1.
- **Manual override:** evaluate_once never checks the circuit. The
  owner's hand overrides. Only the scheduler (evaluate_due) respects
  the circuit. Stated in code comments and tested in
  TestManualOverride.

### Outcome taxonomy

- `evaluated` — successful scheduled evaluation (or idempotent no_op).
- `probe_half_open` — successful half-open probe after cooldown.
- `skipped_circuit_open` — circuit open, cooldown not elapsed.
- `failed` — exception during evaluation; error string recorded.
