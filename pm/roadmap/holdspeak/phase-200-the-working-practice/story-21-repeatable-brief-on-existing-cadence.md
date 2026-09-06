# HS-200-21: Run a configured brief through an existing cadence

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-15, HS-200-17, HS-200-19, HS-200-20
- **Unblocks:** HS-200-22, HS-200-23, HS-200-31, HS-200-33, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-IVW-009–011; AA-AUT-001; AC-18, AC-35–36; C5, C9

## Problem

An installed recipe is useful when its trigger actually runs and its result returns to the Project.

## Scope

Bind one preparation or update recipe to the existing appropriate scheduler and result projection.

Implementation seams: Heartbeat, Cadence, Steward, Monday brief; recipe binding; Project result projection.

Out: General autonomous workers or an uninterrupted overnight guarantee before G4.

## Acceptance criteria

- [ ] The configuration names its actual scheduler, trigger, time zone, execution owner, and output.
- [ ] Run now and one actual scheduled occurrence produce linked results and receipts.
- [ ] Last run, next trigger, failure, and paused states reflect persisted owner records.
- [ ] Missing sources or models produce bounded recovery and partial-result semantics.
- [ ] Duplicate ticks cannot create unexplained duplicate local outputs under the existing scheduler's supported contract.

## Test plan

Planned suite: phase200_recurring_brief. Integration: actual scheduler with injected time, duplicate tick, failed source, disabled task. Live: one scheduled occurrence on the available hub.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
