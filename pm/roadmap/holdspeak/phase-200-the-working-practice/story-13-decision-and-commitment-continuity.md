# HS-200-13: Carry decisions and commitments into the next day

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-10, HS-200-11, HS-200-12
- **Unblocks:** HS-200-14, HS-200-15, HS-200-16, HS-200-17, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-DEC; AA-TRF-001–002; AC-08–09, AC-13; C2–3

## Problem

An accepted outcome matters when later work can retrieve its current meaning and unresolved obligation.

## Scope

Connect current decision, supersession, commitment status, Project recall, and the next preparation result.

Implementation seams: DecisionRecordService; decision lifecycle; follow-through; Memory; Project relationships.

Out: Enterprise approval workflows and new issue-tracker writes.

## Acceptance criteria

- [ ] Recall returns the current decision, rationale, and original source.
- [ ] Superseded and disputed decisions remain discoverable without being presented as current.
- [ ] A commitment has an actual owner/date or explicit unknown values and a lawful next action.
- [ ] Assignment or artifact association alone cannot mark the commitment complete.
- [ ] The complete chain survives service restart and a later preparation session.

## Test plan

Planned suite: phase200_decision_continuity. Exercise supersession, owner/date correction, conflicting records, completion commands, and restart. Manual: next-day recall from the Desk.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
