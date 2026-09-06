# HS-200-19: Apply and recover multi-service recipe setup

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-17, HS-200-18
- **Unblocks:** HS-200-20, HS-200-21, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-IVW-010–011; AC-31–32, AC-35–36; C6

## Problem

A configuration can partially succeed before a crash. A repeated request must reconcile real effects and preserve successful steps.

## Scope

Implement C6 command persistence, per-step service links, read-back, and recovery for the three recipe adapters.

Implementation seams: InterviewService; ProjectSetupService; owning schedule/update services; existing command envelopes.

Out: A global database transaction across services or unsupported compensating effects.

## Acceptance criteria

- [ ] Intent and stable command identity are durable before the first effect.
- [ ] Each step calls its owning service and records the returned identity and receipt.
- [ ] Lost acknowledgement and replay reconcile the existing result without duplicate Projects, schedules, or outputs.
- [ ] Concurrent direct edits and expired setup sessions produce precise revalidation or recovery.
- [ ] Partial setup remains inspectable; abandonment does not silently roll back successful steps.

## Test plan

Planned suite: phase200_setup_recovery. Inject crashes before/after each effect, changed replay payload, concurrent edits, expired sessions, and failed read-back. Drive real services with controlled external adapters.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
