# HS-200-10: Promote reusable working context into canonical records

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-06, HS-200-09
- **Unblocks:** HS-200-11, HS-200-13, HS-200-17, HS-200-20, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-IVW-002–003; AA-CTX; AC-31, AC-37; C3

## Problem

Interview facts belong to one Thread. Useful goals and constraints need explicit, inspectable reuse across related work.

## Scope

Promote selected facts into existing Note, Thought, or Project-owned context and attach canonical refs in later tasks.

Implementation seams: InterviewService; Note/Thought/Project services; qualified refs; context attachment.

Out: A global personal profile, organization crawler, or a new Goals database.

## Acceptance criteria

- [ ] Promotion identifies source quotation, target scope, and target revision.
- [ ] Two Threads can reference the same context without separate editable copies.
- [ ] A correction updates the canonical record once and marks dependent prepared work stale.
- [ ] Removing or revoking a source blocks new unauthorized disclosure and names the resulting gap.
- [ ] Protected People content cannot enter ordinary context through promotion or derived suggestions.

## Test plan

Planned suite: phase200_working_context. Exercise concurrent edits, promotion replay, source deletion, cross-Thread reuse, protected material, and reopen.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
