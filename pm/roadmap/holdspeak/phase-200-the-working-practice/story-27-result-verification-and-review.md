# HS-200-27: Verify results against the frozen acceptance contract

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-06, HS-200-25, HS-200-26
- **Unblocks:** HS-200-28, HS-200-29, HS-200-30, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-RUN-005–006; AC-16; C2, C7

## Problem

Worker completion alone cannot establish that the requested result exists or satisfies its acceptance criteria.

## Scope

Persist structured results, evaluate mandatory checks, and record independent business review.

Implementation seams: AssignmentService; existing artifacts; delivery attempt/dossier; check adapters; review projection.

Out: Model-only acceptance or automatic merge/publication.

## Acceptance criteria

- [ ] Results identify produced artifacts/diffs, target revision, actual checks, unresolved issues, and receipts.
- [ ] Mandatory deterministic checks are evaluated against the frozen assignment criteria.
- [ ] A worker's claim that tests passed requires actual verifiable check evidence.
- [ ] Accept, Request changes, and Reject record reviewer provenance and preserve earlier results.
- [ ] Related commitments or publications change only through their own explicit domain commands.

## Test plan

Planned suite: phase200_assignment_acceptance. Include fabricated test claims, wrong repository revision, missing artifact, failed mandatory check, and altered result after review.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
