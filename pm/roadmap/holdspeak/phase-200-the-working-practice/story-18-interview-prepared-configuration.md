# HS-200-18: Turn Interview intent into a reviewable setup plan

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-08, HS-200-09, HS-200-17
- **Unblocks:** HS-200-19, HS-200-20, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-IVW-004–010; AC-30, AC-33–35; C5

## Problem

Interview currently produces manual suggestions. A supported recurring request needs a concrete plan whose scope the user can inspect.

## Scope

Add typed prepared recipe plans to the existing Interview controller and conversation surfaces.

Implementation seams: InterviewService and contracts; thread tools; InterviewPanel; existing configuration handoffs.

Out: An unrestricted tool palette, chat-based secret collection, or a replacement setup wizard.

## Acceptance criteria

- [ ] The plan shows source scope, route and boundary, trigger, time zone, output, limits, and current prerequisites.
- [ ] Material ambiguities require a concise question. Existing supplied facts are reused.
- [ ] Exploration and unsupported ideas cannot be represented as installed configuration.
- [ ] An exact sufficient request proceeds under existing authority without an invented extra confirmation.
- [ ] Model statements of success are derived from recorded operations and read-back.

## Test plan

Planned suite: phase200_interview_plan. Test exploratory wording, exact configure intent, changed target revision, missing time zone, unavailable tool, and model failure. Live: one natural setup conversation.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
