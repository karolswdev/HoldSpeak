# HS-200-20: Make Interview revisits fast and reliable

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-08, HS-200-10, HS-200-18, HS-200-19
- **Unblocks:** HS-200-21, HS-200-23, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-IVW-001–018; AC-30–38; C5–6, C11

## Problem

A repeatable interview should remember relevant context, respect corrections, and change the intended setup without repeated questioning.

## Scope

Complete revisit, revise, pause, and recovery flows. Evaluate the actual selected model on the held-out scenario set.

Implementation seams: Interview/Thread services and store; recipe projections; shared form and disclosure components.

Out: Claiming semantic quality from scripted model responses.

## Acceptance criteria

- [ ] Revisit selects the existing configuration and displays its actual state.
- [ ] Corrections invalidate dependent plans and stop repeated dismissed suggestions.
- [ ] Pause disables future starts and distinguishes active-run stop.
- [ ] An acknowledged prompt survives reconnect and a failed send retains recoverable input.
- [ ] Live evaluation reports repeated questions, unsupported claims, suggestion usefulness, and correction effort against declared thresholds.

## Test plan

Planned suite: phase200_interview_revisit plus held-out live evaluation. Browser: lost events, reload, section switch, direct edits, pause, and resume at both widths.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
