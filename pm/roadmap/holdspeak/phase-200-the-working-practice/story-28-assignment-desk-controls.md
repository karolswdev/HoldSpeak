# HS-200-28: Make assignment progress and intervention usable

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-09, HS-200-25, HS-200-26, HS-200-27
- **Unblocks:** HS-200-29, HS-200-30, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-RUN-007–008; AA-UX-004; AC-17, AC-26; C11

## Problem

The owner needs to steer an assignment and review its result without reconstructing process state from logs.

## Scope

Add assignment projections and controls to the existing Project, Thread, Agents, and document surfaces.

Implementation seams: Existing Agents/Thread/Project surfaces; delivery dossiers; assignment projection; shared UI library.

Out: A new process screen or terminal implementation.

## Acceptance criteria

- [ ] The surface shows outcome, actual state, next intervention, elapsed time, placement, and known usage.
- [ ] Blocker answers reach the identified supported worker; failed delivery remains visible.
- [ ] Result, evidence, and acceptance controls are accessible from the originating Project or Thread.
- [ ] Reconnect recovers the authoritative run and preserves unsent recoverable input according to the draft contract.
- [ ] Voice, keyboard, focus, and primary actions work at both required widths.

## Test plan

Planned browser suite: test_phase200_assignment_glass.py. Use a controlled running adapter, blocked worker, failed reply, reconnect, and review. Inspect live worker interaction.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
