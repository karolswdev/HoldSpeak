# HS-200-09: Design the daily Project workflow on existing surfaces

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-01
- **Unblocks:** HS-200-10, HS-200-11, HS-200-12, HS-200-15, HS-200-18, HS-200-22, HS-200-28, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-UX-001–005; AC-26; C11

## Problem

The product has many capabilities. The daily path needs a coherent interaction design before additional controls are implemented.

## Scope

Design first architecture result, returning priorities, preparation, meeting review, recall, and recovery using the existing Desk library.

Implementation seams: Desk arrival; Project Room; Thread; document and People surfaces; shared UI library.

Out: A new home metaphor, top-level application, or environment art collection.

## Acceptance criteria

- [ ] Show the full path at 1440 and 393 pixels, including empty, loading, partial, failed, and resumed states.
- [ ] Each daily posture has a clear primary action, evidence access, and continuity back to the originating Project.
- [ ] Reuse the existing library and identify required shared components before implementing feature-specific controls.
- [ ] Voice, keyboard operation, accessible names, focus return, and disclosure behavior are specified.
- [ ] Record the owner design verdict under the existing repository convention, with unresolved concerns visible.

## Test plan

Design: interaction walkthrough and library inventory. Manual: perform the three recipe paths with the proposed controls at both widths. Implementation checks follow in the owning stories.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
