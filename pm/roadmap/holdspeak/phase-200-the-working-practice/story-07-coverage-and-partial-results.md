# HS-200-07: Make incomplete attention coverage explicit

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-01, HS-200-03
- **Unblocks:** HS-200-11, HS-200-14, HS-200-15, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-ATT-001–004; AC-11–12; C4

## Problem

Failed Room reads can disappear from an aggregate that appears fresh. Users need to distinguish an all-clear from incomplete observation.

## Scope

Extend the existing aggregate and cache with per-source coverage, observation time, and repair state. Carry that state through its consumers.

Implementation seams: NeedsYouCache and build_aggregate; HeartbeatService; Door and shade consumers.

Out: New portfolio aggregation or a second attention store.

## Acceptance criteria

- [ ] A failed, forbidden, stale, or unavailable Project remains in the coverage projection.
- [ ] Aggregate computation time does not imply source freshness.
- [ ] An empty partial result cannot render a complete all-clear in arrival, shade, or brief.
- [ ] Known unresolved items remain traceable when a source fails and later recovers.
- [ ] Cache invalidation and concurrent refresh preserve coverage with bounded work.

## Test plan

Planned suite: phase200_attention_coverage. Inject one failed Room among healthy Rooms, all failures, forbidden data, stale cache, and concurrent refresh. Inspect both viewport states.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
