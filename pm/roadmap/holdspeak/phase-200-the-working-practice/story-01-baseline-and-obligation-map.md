# HS-200-01: Establish the integration baseline and obligation map

- **Project:** holdspeak
- **Phase:** 200
- **Status:** ready
- **Depends on:** none
- **Unblocks:** HS-200-02, HS-200-03, HS-200-06, HS-200-07, HS-200-08, HS-200-09, HS-200-22, HS-200-24, HS-200-40
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** AA-ENV; AA-INT-003; DP-00

## Problem

Several roadmaps and checkouts describe different states. Implementation needs one attested baseline and one active destination for each surviving obligation.

## Scope

Inspect current main, active runtimes, Phase 175, and the architect-assistant package. Record reuse, integration, repair, new work, or deferral per capability. Reconcile inherited roadmap issues without inventing evidence.

Implementation seams: Repository and runtime inspection; BASELINE.md; existing health and setup routes.

Out: Runtime replacement, implementation, and bulk historical completion claims.

## Acceptance criteria

- [ ] Record backend, frontend, database, model, and source observations separately from Git state.
- [ ] Map every Phase 200 requirement to an existing implementation or an explicit missing capability.
- [ ] Assign relevant earlier proof obligations one destination and delivery owner. Preserve historical records.
- [ ] Record the current CI failures by identity, reproduction method, and intended repair story.
- [ ] Select one real pilot Project and sources when available. Keep unavailable employer context explicit.

## Test plan

Documentation: check all changed links and the Phase 200 dependency table. Read-only: reproduce identity observations twice with the actual selected runtime. Do not mutate the owner database.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G0](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
