# HS-200-14: Make permitted People preparation useful

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-07, HS-200-12, HS-200-13
- **Unblocks:** HS-200-16, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-INT-005; AC-10, AC-37; C3, C11

## Problem

People preparation can connect meetings and commitments, but identity ambiguity and protected information need their existing boundaries preserved.

## Scope

Reuse the People resolver and permitted projections for one relevant preparation flow.

Implementation seams: PeopleService; People security boundary; Watch resolver; existing PeopleCore and Project links.

Out: Personal scoring, inferred motives, or inferred organizational authority.

## Acceptance criteria

- [ ] Ambiguous aliases require resolution instead of attributing another person's work.
- [ ] Preparation shows source-backed commitments and observable work facts.
- [ ] Protected fields remain in their permitted storage, retrieval, prompt, and export paths.
- [ ] The user can reach People from the relevant Project at both widths and return to the task.
- [ ] Missing or locked People context produces a specific partial result.

## Test plan

Planned suite: phase200_people_preparation. Include same-name identities, locked store, revoked source, derived summary, and compact navigation. Manual: one relevant preparation task.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
