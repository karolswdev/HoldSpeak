# HS-200-15: Present actionable attention with controlled notifications

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-07, HS-200-09, HS-200-13
- **Unblocks:** HS-200-16, HS-200-21, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-ATT; AC-11–12; C4

## Problem

Counts alone do not tell the owner what to do. Notifications can also miss a new item when the total stays unchanged.

## Scope

Rank and deduplicate the existing attention projection, expose its lawful actions, and refine notification transitions.

Implementation seams: Needs-you aggregate; Door; SystemShade; notification bridge; Heartbeat settings.

Out: A second task manager or opaque model-only priority ranking.

## Acceptance criteria

- [ ] The first view shows at most five items with reason, source, and action, plus accessible remaining items.
- [ ] Ranking uses observable urgency and age with deterministic tie-breaking.
- [ ] Duplicate projections of one obligation produce one attention item with traceable sources.
- [ ] Changed-item, same-count, quiet-hour, mute, restart, and recovery transitions have explicit notification behavior.
- [ ] A failed source cannot silently clear known work or produce a false all-clear.

## Test plan

Planned suite: phase200_attention_relevance. Fake clock and multiple zones for notification tests. Browser: perform each primary action and verify receipt and updated aggregate.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
