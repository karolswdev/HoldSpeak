# HS-200-48: A practice recipe is nameable as scheduled work without borrowing the agent-persona table

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-17
- **Unblocks:** HS-200-49, HS-200-50, HS-200-53
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); C5's execution-owner table; C9; HS-200-17's `practice_recipe.*` namespacing

## Problem

**The schedule delegation cannot be minted for a practice recipe at all, because
the word `recipe` on the delegation means the other thing.**

The delegation's terms resolve `wb.recipe_id` against `db.recipes`
(`holdspeak/services/schedule_delegation.py:17`) — the **agent-persona** table:
`system_prompt`, `user_template`, `tools_json`, `kb_id`
(`holdspeak/db/schema.py:1396-1414`). When the lookup misses, `_terms` raises
`delegation_stale_work` — *"Workbench has no recipe"* — at `:19`. So a Workbench
that names one of HS-200-17's three practice recipes cannot be scheduled: the
owner's `enable_from_owner_in_transaction` (`:50-58`) never gets past the terms
freeze.

This is exactly the collision HS-200-17 anticipated when it namespaced its own
surface `practice_recipe.*` rather than `recipe.*`
(`holdspeak/mcp/families/practice_recipe.py:4`, and the module docstring at
`holdspeak/services/recipe_catalog.py:3` — *"This is not
`holdspeak.services.recipe_service`"*). The namespace was separated on the
discovery surface. It was never separated on the **authority** surface, which is
where a schedule actually needs it.

The delegation row already carries the right shape for versioned bound work —
`recipe_id`, `recipe_revision`, `workbench_revision`, `schedule_revision`,
`cadence`, `deployment_revision_id`, `terms_sha256`
(`holdspeak/db/schema.py:1815-1825`; built at
`holdspeak/services/schedule_delegation.py:30-34`). Only the resolution target
is wrong.

## Scope

Let a schedule delegation name a practice-recipe descriptor as its bound work,
with its own revision, without pretending it is an agent persona and without
retiring the persona binding that already ships.

Implementation seams: `holdspeak/services/schedule_delegation.py` (`_terms`, the
terms vocabulary, `validate`); `holdspeak/services/recipe_catalog.py` (the
descriptor's version is the `recipe_revision` a delegation freezes);
`holdspeak/db/schema.py` (`workbenches` and/or
`kernel_schedule_delegations`, additive only); the Workbench schedule verbs and
the `practice_recipe.*` family.

Out: the domain dispatch itself (HS-200-50), the Project binding (HS-200-49),
and the output mapping (HS-200-51). This story makes the delegation MINTABLE and
VALIDATABLE for a practice recipe; it does not yet make a run do anything new.

Out: renaming the `recipes` table or the `recipe.*` MCP family. The persona
meaning is shipped and the owner's rows carry it.

## Acceptance criteria

- [ ] A Workbench bound to a practice-recipe descriptor mints a LIVE delegation
      by the owner, with no row in the agent-persona `recipes` table.
- [ ] A Workbench bound to an agent persona keeps minting exactly as it does
      today — the existing behaviour is fenced, not replaced.
- [ ] The frozen terms record which kind of work is bound, and the descriptor's
      own version is the frozen `recipe_revision`.
- [ ] Editing the descriptor (a new catalog version) makes the delegation stale
      by the existing mechanism, not by a new one — a stale binding refuses with
      a named code rather than running an older plan.
- [ ] Only the owner can mint; the `owner_principal_required` refusal
      (`holdspeak/services/schedule_delegation.py:52`) still holds on both
      kinds.
- [ ] The terms hash changes when the bound kind or descriptor version changes
      (`:37-39`), so a swap is a re-approval.
- [ ] A Workbench that names neither still refuses, and the refusal names which
      namespace it looked in — the current sentence *"Workbench has no recipe"*
      is ambiguous between the two meanings and is corrected.
- [ ] Every new fence proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_practice_recipe_binding`. Mint through the real
`ScheduleDelegationService` with a real owner `Principal` against a real
temporary database; resolve descriptors through the real
`holdspeak.services.recipe_catalog`, never a fixture copy of a descriptor
(`reference_lying_test_doubles`). Prove the persona path unchanged by driving
the same service with a real `recipes` row.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidate (HS-200-46).** One sentence must stay true: a schedule
delegation resolves a practice-recipe binding against the catalog and never
against the persona table. The predicate is cheap — mint both kinds through the
real service and assert the persona table stays empty for one of them. Each is **`known_false` today** and can enter the registry before the fix: the predicate fails now, and HS-200-46's rule makes it fail again the moment the code starts satisfying it, which forces the flip to `holds` in the same commit as the repair.

**Open, for the implementer to settle and record:** whether the bound kind
lives on `workbenches` (a second column beside `recipe_id`) or on
`kernel_schedule_delegations` (a discriminator on the terms). Either satisfies
the criteria; the choice belongs in the evidence with its reason, not in this
charter.
