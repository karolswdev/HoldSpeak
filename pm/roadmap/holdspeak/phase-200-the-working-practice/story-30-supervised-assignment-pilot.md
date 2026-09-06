# HS-200-30: Prove five supervised assignments on useful tasks

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-23, HS-200-27, HS-200-28, HS-200-29
- **Unblocks:** HS-200-35, HS-200-37, HS-200-38, HS-200-40
- **Owner:** unassigned
- **Gate:** G3
- **Trace:** AA-NFR-007; AC-14–17; C12

## Problem

A technically controlled worker must still deliver work that the owner can evaluate with reasonable effort.

## Scope

Run five bounded assignments across actual permitted architecture tasks and report accepted, corrected, failed, and inconclusive results.

Implementation seams: ACCEPTANCE.md supervised sample; assignment and delivery evidence.

Out: Autonomous external actions or selecting only successful tasks for the report.

## Acceptance criteria

- [ ] Every assignment has a frozen outcome, target, sources, limits, and acceptance criteria before launch.
- [ ] Five real opportunities reach inspectable outcomes; unavailable opportunities extend the sample.
- [ ] Record supervision, correction, verification, and repair effort alongside result quality.
- [ ] The owner can explain why each accepted result satisfies its evidence and checks.
- [ ] No unexplained duplicate effect, critical source fabrication, or false completion remains unresolved.

## Test plan

Real worker pilot using one supported adapter. Repeat affected recovery and acceptance checks after any repair.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G3](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
