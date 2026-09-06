# HS-200-11: Produce a useful Project preparation brief

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-04, HS-200-06, HS-200-07, HS-200-09, HS-200-10
- **Unblocks:** HS-200-13, HS-200-16, HS-200-17, HS-200-22, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-CTX-001–006; AC-04–06; C2–4

## Problem

A generated brief becomes useful when the right scope, current decisions, source coverage, and next questions are visible.

## Scope

Compose one manual preparation path over Project, Memory, existing briefs, and kept artifacts.

Implementation seams: ProjectService; MemoryService; MondayBriefService; ProjectUpdateService; existing Thread/document surfaces.

Out: Additional connectors or mandatory calendar integration.

## Acceptance criteria

- [ ] The user can name a meeting purpose without configuring a calendar.
- [ ] Preparation binds a source manifest with current/superseded decisions and named omissions.
- [ ] The result contains bounded priorities, questions, and obligations rather than an unfiltered source dump.
- [ ] Sources open in context and the kept brief remains attached to the originating Project.
- [ ] Unavailable AI retains the user's purpose and exposes the existing setup or manual completion path.

## Test plan

Planned suite: phase200_preparation. Use mixed freshness, conflicting decisions, large source sets, missing model, and restart. Live: prepare one actual upcoming conversation.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
