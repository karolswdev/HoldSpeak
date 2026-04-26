# HS-2-06 — Step 5: Meeting runtime wiring

- **Project:** holdspeak
- **Phase:** 2
- **Status:** backlog
- **Depends on:** HS-2-03, HS-2-04, HS-2-05
- **Unblocks:** HS-2-07
- **Owner:** unassigned

## Problem

Spec §9.6 — connect the windowing + multi-label scoring + plugin host
+ persistence stack to the live meeting runtime so a real meeting
session drives the new pipeline.

## Scope

- **In:** Per `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` §9.6.
- **Out:** Synthesis pass (HS-2-07), API/CLI surfaces (HS-2-08), feature-flag plumbing (HS-2-09).

## Acceptance criteria

- [ ] _TBD when story is picked up._

## Test plan

- _TBD when story is picked up; the existing meeting-runtime e2e tests are the regression baseline._

## Notes / open questions

- Gating: should the new path be behind a feature flag from day one (deferred to HS-2-09), or wired live with the old path retained as fallback? Mirror DIR-01's pattern (off-by-default with controller-side gate) seems right.
