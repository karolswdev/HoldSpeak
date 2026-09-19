# HS-200-49: A scheduled recipe binds the Project it prepares and the sources it may read

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-48
- **Unblocks:** HS-200-50, HS-200-53
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); C5's plan record ("target refs and expected revisions, source scope"); C9

## Problem

**Two of the seven fields C5 requires a configuration plan to record have no
home on the thing that actually fires.**

C5 requires every plan to record "its ID and revision, recipe version, target
refs and expected revisions, **source scope**, route policy, output, trigger,
and limits" ([CONTRACTS.md](CONTRACTS.md#c5-prepared-recipe-configuration)). The
schedule delegation freezes five of those — `recipe_id`, `recipe_revision`,
`workbench_revision`, `schedule_revision`, `cadence`, plus the route through
`deployment_revision_id` and `route_plan_sha256`
(`holdspeak/services/schedule_delegation.py:30-34`).

**The target ref and the source scope are missing, and `workbenches` has nowhere
to put them.** The table is `id`, `name`, `recipe_id`, `profile_id`,
`resolver_profile_id`, `schedule`, `schedule_enabled`, `schedule_revision`,
`item_order_json`, timestamps, `deleted` (`holdspeak/db/schema.py:1708-1720`) —
**no `project_id`**. Every one of HS-200-17's three descriptors takes a Project
as a required input and compiles its source scope against that Project's real
observed coverage (`holdspeak/services/recipe_catalog.py`, `compile_recipe` at `:875`). A schedule that cannot name a Project cannot supply that input, so
a scheduled compile can only fail on a missing input or be handed one from
somewhere the receipt does not record.

`connector_watches`, the other recurring owner, already has the column
(`project_id`, `holdspeak/db/schema.py:2476`) and `list_due_watches` joins on it
to exclude archived Projects (`holdspeak/db/automations.py:454-462`). The
Workbench clock has no equivalent.

## Scope

Bind a scheduled Workbench to one Project and to an explicit source scope, freeze
both into the delegation's terms, and honour the Project's lifecycle the way the
watch path already does.

Implementation seams: `holdspeak/db/schema.py` (`workbenches`, additive only —
`feedback_migrations_stay_minimal`); `holdspeak/services/workbench_service.py`;
`holdspeak/services/schedule_delegation.py` `_terms`;
`holdspeak/services/recipe_catalog.py` (the compile inputs a scheduled firing
supplies); the Workbench routes and MCP family.

Out: a Project-scoped Workbench list face, or moving existing Workbenches into
Projects. An unbound Workbench stays unbound and keeps working.

Out: the dispatch (HS-200-50) and the result's return (HS-200-51).

## Acceptance criteria

- [ ] A scheduled Workbench can name exactly one Project, and the binding is
      part of the frozen delegation terms — changing it changes `terms_sha256`
      and requires the owner's re-approval.
- [ ] The source scope the descriptor will compile against is recorded on the
      binding, not derived fresh at fire time.
- [ ] A compile driven from the binding produces the same plan as the equivalent
      manual compile for the same Project and scope, gaps included — proven by
      comparing the two real outputs, not by asserting a transcribed shape.
- [ ] An archived Project's scheduled Workbench does not fire, matching the
      exclusion `list_due_watches` already applies
      (`holdspeak/db/automations.py:454-462`).
- [ ] A source that leaves the permitted scope produces the descriptor's typed
      gap and a refusal receipt — never a silently narrower run reported as
      complete (C4's coverage rules stand).
- [ ] An existing unbound Workbench keeps its current behaviour, fenced.
- [ ] Every new fence proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_schedule_project_scope`. Drive the real
`WorkbenchService` schedule verbs and the real `ScheduleDelegationService`
against a real temporary database; compile through the real
`holdspeak.services.recipe_catalog` and compare the scheduled plan to the
manual plan produced by the same real function. Archive a real Project through
the real service for the lifecycle leg.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidate (HS-200-46).** One sentence must stay true: a scheduled
Workbench's frozen terms carry the Project ref and the source scope. The
predicate reads the real `SCHEMA_SQL` and the real terms dict. Each is **`known_false` today** and can enter the registry before the fix: the predicate fails now, and HS-200-46's rule makes it fail again the moment the code starts satisfying it, which forces the flip to `holds` in the same commit as the repair.

**Depends on HS-200-47 in practice, not on paper.** The zone belongs in the same
frozen-terms conversation, and doing both in one hand is cheaper. They are
separate stories because the zone is a defect in a shipped path (R5) and must be
able to land alone.
