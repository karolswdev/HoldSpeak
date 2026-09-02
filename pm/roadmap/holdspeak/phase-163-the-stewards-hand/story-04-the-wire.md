# HS-163-04 - The wire: runs on HTTP

- **Project:** holdspeak
- **Phase:** 163
- **Status:** done
- **Depends on:** HS-163-03
- **Unblocks:** HS-163-05, HS-163-06
- **Owner:** unassigned

## Problem

§9.2: POST /api/projects/{id}/steward/runs MUST persist and return a
run ID immediately; the run state is pollable; Stop is a verb.

## Scope

- **In:** holdspeak/web/routes/steward.py under the house law:
  POST /api/projects/{id}/steward/runs (run_once; envelope;
  command_id replay), GET /api/projects/{id}/steward/runs (list),
  GET /api/steward/runs/{run_id} (pollable state: phase, steps,
  receipts), POST /api/steward/runs/{run_id}/stop (STW-003 on the
  wire), GET/PUT the per-Project steward policy (bounds + eligible
  effects — named columns, typed validation). api-surface regen
  additive. Integration tests through the real app: the immediate-
  id contract, polling a completing run, stop mid-run, policy
  round-trip, STW-002 refusal on the wire.
- **Out:** UI (05), scheduling.

## Acceptance criteria

- [ ] Every route success + failure typed; the run id returns before phase work (proven by a slow-phase fixture).
- [ ] The full loop through HTTP: policy → run → poll to completed → the run summary names its effects + receipts; stop mid-run lands interrupted.
- [ ] api-surface additive; prior pins untouched; consumers honest.

## Test plan

- **Integration:** tests/integration/test_steward_routes.py.
