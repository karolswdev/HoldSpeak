# HS-200-39: Rehearse the release without implementation guidance

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-37, HS-200-38
- **Unblocks:** HS-200-40
- **Owner:** unassigned
- **Gate:** G5
- **Trace:** AA-UX; AA-NFR-001–002, AA-NFR-007; AC-26–27; C11–12

## Problem

A familiar developer can work around problems that a user will encounter immediately.

## Scope

Run a cold task rehearsal of the packaged candidate through normal product controls and the public guide.

Implementation seams: Packaged candidate; public guides; existing UAT tools; critical journey suite.

Out: Replacing physical or semantic proof with screenshots alone.

## Acceptance criteria

- [ ] The rehearsal covers first value, preparation, meeting review, revisit, assignment review, and recovery.
- [ ] Record initial understanding, task time, unexpected concepts, dead ends, and assistance required.
- [ ] Verify desktop/compact layouts, keyboard, voice affordances, focus, and interrupted work.
- [ ] Required platform, backend, Web, integration, and critical E2E checks pass on the selected candidate.
- [ ] Fix material failures and repeat only the affected paths. Retain earlier failed attempts.

## Test plan

Cold reviewer with no implementation briefing where available. If unavailable, record the limitation and do not claim independent adoption proof. Physical capture remains a real-device leg.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G5](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
