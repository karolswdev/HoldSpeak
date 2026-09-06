# HS-200-33: Bind triggers to versioned recipes and assignments

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-17, HS-200-21, HS-200-25, HS-200-31, HS-200-32
- **Unblocks:** HS-200-34, HS-200-35, HS-200-40
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** AA-AUT-001–003, AA-AUT-007; AC-18–19; C9

## Problem

Recurring work needs a stable logical occurrence linked to the exact configuration and assignment revision.

## Scope

Extend the existing scheduler owners with versioned bindings, occurrence identity, and unified status projection.

Implementation seams: Heartbeat/Cadence/Steward scheduling seams; assignment run links; recipe configuration projection.

Out: A new generic scheduler or arbitrary workflow graph semantics.

## Acceptance criteria

- [ ] Each trigger names its owner, binding revision, recipe/assignment revision, scope, authority, and limits.
- [ ] Scheduled times and source watermarks produce stable occurrence identities.
- [ ] Last run, next trigger, missed coverage, paused state, and actual executor derive from durable records.
- [ ] Configuration edits do not retarget an admitted occurrence.
- [ ] Two scheduler ticks cannot create two run links for the same logical occurrence.

## Test plan

Planned suite: phase200_trigger_bindings. Test duplicate ticks, edited bindings, DST repeated times, source watermark replay, and pause.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
