# HS-200-29: Prove assignment recovery, cancellation, and scope change

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-25, HS-200-26, HS-200-27, HS-200-28
- **Unblocks:** HS-200-30, HS-200-34, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-RUN-008; AA-NFR-003–005; AC-19–21, AC-28; C8

## Problem

Crashes and late results can produce duplicate work or acceptance against the wrong scope.

## Scope

Implement and test the C8 recovery matrix through real coordinator and adapter seams.

Implementation seams: AssignmentService; kernel parent runs and fences; adapter registration; source/credential checks.

Out: Universal exactly-once physical execution or provider-side interruption guarantees.

## Acceptance criteria

- [ ] Crash recovery reconciles the same admitted run and target before any replacement.
- [ ] Cancellation fences new dispatch and late accepted output, with honest unsupported termination.
- [ ] Scope change creates a new definition and explicit disposition of old execution.
- [ ] Credential/source revocation prevents new unauthorized work and disclosure.
- [ ] Terminal races have one winner; uncertain external effects remain indeterminate.

## Test plan

Planned suite: phase200_assignment_recovery. Inject every C8 window, browser loss, worker death, stale lease, duplicate callback, stop/result race, and revoked source.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
