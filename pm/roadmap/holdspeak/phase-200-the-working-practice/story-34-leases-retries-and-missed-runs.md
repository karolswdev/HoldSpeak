# HS-200-34: Enforce leases, bounded retry, and missed-run policy

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-29, HS-200-33
- **Unblocks:** HS-200-35, HS-200-36, HS-200-40
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** AA-AUT-002–007; AC-18–20; C8–9

## Problem

Unattended work must recover without duplicate dispatch, unlimited retries, or misleading coverage.

## Scope

Implement durable claim leases, generation fencing, finite retry classification, and explicit missed/overlap policies at existing owner seams.

Implementation seams: Existing scheduler owners; kernel claims/fences; assignment run links; Heartbeat notifications.

Out: Blind replay after an uncertain external effect or uninterrupted-coverage claims on a sleeping hub.

## Acceptance criteria

- [ ] Concurrent processes cannot own the same logical occurrence.
- [ ] An expired lease requires reconciliation before replacement dispatch.
- [ ] Retryable, terminal, and indeterminate failures have distinct bounded handling.
- [ ] The default preparation recipe coalesces missed occurrences into one current result and preserves the gap record.
- [ ] Pause, stop, quiet hours, overlap, DST, and budget exhaustion match the declared binding policy.

## Test plan

Planned suite: phase200_schedule_recovery. Inject duplicate processes, expired lease, reboot, forward/backward clock change, DST gaps/folds, timeouts, and stop races.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
