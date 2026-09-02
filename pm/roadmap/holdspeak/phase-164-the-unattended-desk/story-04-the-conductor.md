# HS-164-04 - The conductor: two boundaries, honest events, Cadence attention

- **Project:** holdspeak
- **Phase:** 164
- **Status:** backlog
- **Depends on:** HS-164-03
- **Unblocks:** HS-164-05, HS-164-06
- **Owner:** unassigned

## Problem

§9.1: the main conductor SHOULD call run_due() as an isolated block;
§14 P5: evaluate_due() and run_due() as INDEPENDENT failure
boundaries. §10: the steward event kinds are mostly missing (only
steward.run_completed exists, project_steward_service.py:1119), and
Cadence MAY project review_due / source_degraded /
steward_intervention_required but MUST NOT become the schedule of
record.

## Scope

- **In:** two new blocks in the conductor tick following the house
  idiom (workbench_conductor.py:498 — own try/except, named log
  prefix, a broken Project/source never stops other duties):
  evaluate_due then run_due. §10 events at the seams via
  ServiceEventLedger.append_in_transaction: steward.configured (on
  policy PUT), run_started, step_completed, intervention_required
  (circuit open, bounds exhausted, repeated identical failure);
  payloads small and ref-oriented. Cadence projections for
  review_due, source_degraded, steward_intervention_required through
  the CadenceService seam — attention only, never execution. Wire
  surface: whatever unattended config needs on HTTP (policy PUT
  extension), api-surface additive.
- **Out:** UI (05), glass (06).

## Acceptance criteria

- [ ] A poisoned evaluate_due never stops run_due or the other conductor duties (fault-injection at the block seam); both blocks tick under test.
- [ ] Every §10 steward event kind emits at its seam with a ref-oriented payload, in-transaction; intervention_required fires on circuit-open and bounds-exhausted.
- [ ] Cadence shows the three projections without owning schedule state; api-surface additive, prior pins untouched.

## Test plan

- **Unit + integration:** tests/unit/test_steward_conductor.py; event/projection assertions in the existing suites.
