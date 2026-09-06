# HS-200-24: Review the Assignment boundary and first adapter

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-01, HS-200-06, HS-200-17
- **Unblocks:** HS-200-25, HS-200-26, HS-200-31, HS-200-32, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-RUN-001–004, AA-RUN-009–010; AC-14–15, AC-21; C7–8

## Problem

HoldSpeak has launch and steering mechanisms but needs an explicit contract tying delegated work to an outcome and acceptance.

## Scope

Reconcile Phase 155 and existing delivery contracts. Specify definition ownership, run linkage, adapter capabilities, and failure windows before implementation.

Implementation seams: Architect-assistant CONTRACTS; Phase 155; delivery factory, steering, agent capability ledger; kernel parent runs.

Out: Unbounded crews, multiple adapters, or product implementation before the invariant review.

## Acceptance criteria

- [ ] One domain model separates immutable definitions, kernel execution, and business acceptance.
- [ ] The first registered adapter declares actual target identity, cancellation, tool control, and usage capabilities.
- [ ] Unsupported guarantees have a refusal or clearly limited supervised scope.
- [ ] Review resolves the failure windows in C8 with transaction and fencing boundaries.
- [ ] No second worker queue, generic terminal, or child-thread runtime is introduced.

## Test plan

Design review: trace each transition and crash window to an existing seam or named new contract. Prototype only uncertain adapter capabilities and retain actual results.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
