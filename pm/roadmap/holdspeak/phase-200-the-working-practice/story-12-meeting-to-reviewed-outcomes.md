# HS-200-12: Connect a real meeting to reviewed outcomes

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-04, HS-200-05, HS-200-06, HS-200-09
- **Unblocks:** HS-200-13, HS-200-14, HS-200-16, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-DEC-001–006; AC-07–09; C2, C6

## Problem

Meeting intelligence and the proposal bridge exist. Their full production chain must preserve source evidence, edits, and retry identity.

## Scope

Adopt the current completion trigger and proposal bridge. Repair only demonstrated gaps in the linked-meeting path.

Implementation seams: Meeting completion; ProposalBridgeService; decision services; follow-through; meeting review UI.

Out: Automatic external publication or invented organizational decision authority.

## Acceptance criteria

- [ ] One linked recording or import produces proposals through the actual completion and intelligence services.
- [ ] Each decision/action preserves meeting, relevant transcript evidence, and extraction provenance.
- [ ] Unknown owner, deadline, or acceptance remains unknown until supported or supplied by the user.
- [ ] Confirm, Edit, and Dismiss call the canonical service and return its durable result.
- [ ] Repeated completion, model retry, and lost acknowledgement do not create duplicate proposals or commitments.

## Test plan

Planned suite: phase200_meeting_outcomes. Drive the real completion seam with a fixture model; inject duplicates and failure. Live: one real meeting, reviewed against its transcript.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
