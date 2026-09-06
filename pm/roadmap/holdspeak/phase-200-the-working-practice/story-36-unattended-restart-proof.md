# HS-200-36: Prove unattended operation through real occurrences and restart

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-31, HS-200-32, HS-200-34, HS-200-35
- **Unblocks:** HS-200-37, HS-200-38, HS-200-40
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** AA-AUT-001–008; AC-18–21; C9–12

## Problem

Simulated ticks cannot establish that the selected deployment survives real scheduling, restarts, and credential changes.

## Scope

Run three consecutive real scheduled occurrences per enabled recipe and the declared recovery drill.

Implementation seams: Selected deployment; Reach/runner; scheduler and assignment records; operator runbook.

Out: Counting three immediate run-now calls as three real scheduled occurrences.

## Acceptance criteria

- [ ] Each occurrence has its planned time, identity, run link, result, and receipt.
- [ ] Restart or controlled outage demonstrates the declared missed-run and reconciliation behavior.
- [ ] Credential rotation, revocation, and source/model failure produce the expected bounded outcome.
- [ ] No unexplained duplicate effect, false all-clear, or false stopped/completed state remains.
- [ ] The operator can pause, inspect, repair, and resume through documented controls.

## Test plan

Real scheduling proof plus the C8/C9 failure matrix. Keep wall-clock occurrence evidence separate from injected-clock tests.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
