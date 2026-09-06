# HS-200-35: Enable bounded unattended preparation and analysis

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-23, HS-200-30, HS-200-32, HS-200-33, HS-200-34
- **Unblocks:** HS-200-36, HS-200-40
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** AA-AUT-008; AC-21; C5, C9–10

## Problem

Automatic execution should begin with tasks whose scope, output, and limits are already understood.

## Scope

Enable two bounded recipe classes using the reviewed contracts: preparation and selected change analysis or verification.

Implementation seams: Existing preparation/Steward services; AssignmentService; scheduler owners; Project result projection.

Out: Automatic reviewer nudges, issue writes, publication, or unrestricted agent crews as new Phase 200 defaults.

## Acceptance criteria

- [ ] Each enabled recipe has a useful manual/supervised result and a versioned trigger binding.
- [ ] Initial effects are limited to permitted reads and local result creation.
- [ ] Failures, budget exhaustion, unavailable sources, and uncertain outcomes have visible repair states.
- [ ] Results return to the originating Project with support, coverage, and execution evidence.
- [ ] A new external effect class cannot be enabled by a model suggestion or inherited from unrelated owner identity.

## Test plan

Planned suite: phase200_unattended_recipes. Execute both recipes on the selected host with controlled failure and scope tests.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
