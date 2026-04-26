# HS-2-03 — Step 2: Windowing + multi-label scoring

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-02
- **Unblocks:** HS-2-04, HS-2-06
- **Owner:** unassigned

## Problem

Spec §9.3 — slide a deterministic-boundary window over the rolling
transcript and emit multi-label `IntentScore` outputs per window with
hysteresis-aware `IntentTransition` events. This is the core
classifier surface MIR-01 hangs everything else off.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.3.
- **Out:** Plugin chain dispatch (HS-2-04), persistence (HS-2-05).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up; existing `tests/unit/test_intent_signals.py` + `test_intent_timeline.py` are the foundation to extend._

## Notes / open questions

- Window size + hysteresis defaults to be defined. Spec §6.4 hints at "minimum confidence delta" — exact number TBD.
