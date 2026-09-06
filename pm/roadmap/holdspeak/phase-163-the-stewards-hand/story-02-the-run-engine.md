# HS-163-02 - The run engine: six phases, checkpointed, stoppable, recoverable

- **Project:** holdspeak
- **Phase:** 163
- **Status:** done
- **Depends on:** HS-163-01
- **Unblocks:** HS-163-03
- **Owner:** unassigned

## Problem

§9.2: OBSERVE → COMPARE → PROPOSE → ACT → VERIFY → RECORD, every
phase checkpointing durable state. STW-003: Stop is a durable
request checked between steps and before every new effect — never
dependent on a model response. STW-009: startup recovery marks
abandoned running steps/runs interrupted and reconciles safe
resumability.

## Scope

- **In:** `ProjectStewardService` (holdspeak/services/) owning run
  coordination: `run_once(project_id)` persists the run (state
  queued) and RETURNS THE RUN ID IMMEDIATELY (the §9.2 contract);
  the worker executes the six phases with a checkpoint write per
  transition; phase bodies in 02 are the NO-EFFECT spine (OBSERVE
  delegates to the 160 evidence collector; COMPARE/PROPOSE delegate
  to the Delta's deterministic machinery; ACT is a bounded no-op
  hook 03 fills; VERIFY/RECORD write the run summary + ledger
  event). STW-002 at the service level (the DB law surfaces as a
  typed refusal). `stop(run_id)` sets the durable request; the loop
  checks it between phases AND before every effect slot. STW-009:
  `recover_on_startup()` marks stale running runs/steps interrupted
  (wired where the house does startup work — find the pattern).
  Failure isolation per the conductor's patterns (§9.1: reuse
  heartbeat/failure-isolation shapes — study holdspeak's conductor).
- **Out:** real effects (03), routes (04), scheduling (P5).

## Acceptance criteria

- [ ] run_once returns a durable pollable run before any phase work; each phase transition is a visible checkpoint row.
- [ ] Stop honored between phases and before effect slots (a test injects a slow phase and stops mid-run ⇒ state stopping→interrupted with an honest summary; no model dependence).
- [ ] STW-002 typed refusal on a second concurrent run; STW-009 recovery test (a run abandoned mid-phase is marked interrupted on startup and is safely re-runnable).

## Test plan

- **Unit:** tests/unit/test_steward_engine.py (lifecycle truth table, stop, uniqueness, recovery).
