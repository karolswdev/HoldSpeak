# HS-163-01 - The run ledger: durable before asynchronous

- **Project:** holdspeak
- **Phase:** 163
- **Status:** done
- **Depends on:** -
- **Unblocks:** HS-163-02
- **Owner:** unassigned

## Problem

STW-001: a run MUST be durable before asynchronous work begins and
MUST expose a pollable state. §9.2: every phase checkpoints durable
run/step state. The v68 tables (watch_rules/evaluations/effects) and
the pstpol_/pstrun_/pststep_ ID prefixes exist in the frozen
contract; the steward's OWN persistence does not yet.

## Scope

- **In:** schema v71 (additive, named columns): steward policy
  (per-Project: eligible effect kinds, YOLO flags, bounds — retry
  counts, per-run action caps, cooldowns per STW-008), steward runs
  (id pstrun_, project_id, state (queued|running|stopping|
  completed|failed|interrupted), phase (observe|compare|propose|
  act|verify|record), requested_by, stop_requested_at, watermark,
  timestamps, summary_json), steward steps (id pststep_, run_id,
  phase, seq, state, effect kind + idempotency_key + expected/
  observed state JSON — THE STW-005 RECONCILIATION SUBSTRATE —
  receipts, error_json), command records for replay. Check the
  existing v68 watch_effects table first — reuse/extend rather than
  duplicate if it already carries the effect shape. Repo layer with
  conn-accepting variants; active-run uniqueness enforced at the DB
  level (STW-002 — partial unique index or the house equivalent);
  reconcile proven on a COPY of the real DB.
- **Out:** the engine (02), effects (03), routes (04), UI (05).

## Acceptance criteria

- [ ] v71 additive; real-DB reconcile green; positional-INSERT fence green; snapshot regenerated (the 162 scar).
- [ ] STW-002 as DB law under test: a second active run for the same project refuses at the persistence layer.
- [ ] The step record carries idempotency_key + expected/observed columns and a test proves a step can be reconciled by key lookup.

## Test plan

- **Unit:** tests/unit/test_steward_schema.py (+ repo truth tables).
