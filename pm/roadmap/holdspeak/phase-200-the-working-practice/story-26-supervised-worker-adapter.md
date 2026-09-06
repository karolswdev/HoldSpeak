# HS-200-26: Launch one bounded supervised worker

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-24, HS-200-25
- **Unblocks:** HS-200-27, HS-200-28, HS-200-29, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-RUN-003–004, AA-RUN-007, AA-RUN-010; AC-15, AC-17; C7

## Problem

An assignment is not executable until a real adapter can bind its target and report the capabilities it enforces.

## Scope

Connect the selected existing delivery adapter to Assignment execution and registration.

Implementation seams: Delivery factory launch; coder steering; agent capabilities; selected adapter; kernel runtime.

Out: Multiple worker providers, arbitrary executable strings, or a claim of sandboxing without enforcement.

## Acceptance criteria

- [ ] A launch binds the actual repository revision, worktree/session identity, and immutable assignment revision.
- [ ] Registration timeout, missing executable, and unsupported capabilities produce named outcomes.
- [ ] Limits are enforced where declared; unavailable usage or interception remains unknown.
- [ ] Worker and tool activity retain kernel or adapter provenance without borrowing owner authority.
- [ ] One real supervised assignment starts and can be inspected through the supported session controls.

## Test plan

Planned suite: phase200_assignment_adapter. Fake adapter failure injection plus one real worker trial with synthetic or selected permitted repository content.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
