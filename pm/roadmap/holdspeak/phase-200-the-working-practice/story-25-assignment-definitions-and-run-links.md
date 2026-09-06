# HS-200-25: Persist immutable assignments and canonical run links

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-24
- **Unblocks:** HS-200-26, HS-200-27, HS-200-28, HS-200-29, HS-200-33, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-RUN-001–003; AA-INT-001; AC-14–15, AC-19, AC-25; C7–8

## Problem

Delegated work needs a durable outcome definition before the worker starts.

## Scope

Implement the missing AssignmentService records, qualified refs, revision commands, and kernel parent linkage.

Implementation seams: Proposed AssignmentService; existing refs registry; database migration framework; kernel parent-run registration.

Out: A second execution journal or credentials supplied through assignment JSON.

## Acceptance criteria

- [ ] Prepare and revise create immutable definitions with Project, manifest, target, constraints, worker, limits, and checks.
- [ ] Run links are durable before dispatch and unique for the logical start.
- [ ] Web and supported MCP commands use the same validation and trusted principal derivation.
- [ ] Stale revision and changed-payload replay produce atomic conflicts.
- [ ] Migration and restore preserve existing data and assignment lineage.

## Test plan

Planned suite: phase200_assignment_contract. Test revision conflicts, replay identity, target validation, reference resolution, no-dispatch-before-commit, and restore.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
