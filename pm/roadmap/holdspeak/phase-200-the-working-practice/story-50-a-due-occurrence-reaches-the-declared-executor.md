# HS-200-50: A due occurrence reaches the service the recipe declares, not the inference waist

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-48, HS-200-49
- **Unblocks:** HS-200-51, HS-200-53
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); C5's execution-owner column; C9's "which executor performs the work"

## Problem

**The clock can fire, and there is nothing at the other end that knows how to
run a recipe.**

A scheduled run reaches `WorkbenchRunner.run_scheduled`
(`holdspeak/services/workbench_runner.py:342`), which revalidates the delegation
and hands off to the ordinary admitted loop. That loop drives
`workbench_items`: a free-text `title` and `body`, per-item `grounding_json` and
`context_json`, and a `result` string (`holdspeak/db/schema.py:1722-1741`) — one
inference call per item. The frozen route says so out loud: the delegation
freezes its plan at `capability_id="workbench.item"`
(`holdspeak/services/schedule_delegation.py:24`).

**Nothing dispatches to a domain service.** HS-200-17's three descriptors name
their execution owners by qualified ref —
`PreparationBriefService.prepare`
(`holdspeak/services/recipe_catalog.py:405`), the decision/follow-through
services, and `ProjectUpdateService` for the weekly update
(`holdspeak/services/recipe_catalog.py:34-43`). C5's table names the same three
("Existing preparation and artifact services", "Existing decision,
follow-through, and preparation services", "Existing Project update and Steward
services"). A due minute today cannot call any of them.

This is the gap HS-200-17 declared rather than hid: every descriptor's
`scheduled` `TriggerBinding` carries `available=False` with a `supplied_by`
sentence naming the adapter a future story must add
(`holdspeak/services/recipe_catalog.py:424-430`, `:528`, `:602`), and
`compile_recipe` returns the typed `trigger_owner_not_wired` gap for it
(`:942-950`). This story is that adapter.

## Scope

Make a due occurrence execute a compiled practice-recipe plan through the
descriptor's declared steps, under the delegation's authority, with the run
receipted exactly as an inference run is.

Implementation seams: `holdspeak/services/workbench_runner.py` (`run_scheduled`
and the admitted loop's dispatch fork);
`holdspeak/services/schedule_delegation.py` (the frozen route's
`capability_id` for a domain step); `holdspeak/services/recipe_catalog.py` (the
compiled plan's steps are the dispatch table);
`holdspeak/kernel/schedule_delegated.py` (the tick and refusal receipts);
`holdspeak/workbench_conductor.py` if the tick must distinguish the two kinds.

Out: the result's projection into the Project (HS-200-51). Out: leases, retry
classification and missed-run policy — those are HS-200-34's and stay there.
Out: enabling any recipe unattended on the owner's desk; his policies stay his.

## Acceptance criteria

- [ ] A due occurrence for a practice-recipe binding compiles the descriptor and
      calls the declared execution owner through its real qualified ref.
- [ ] A due occurrence for an agent-persona Workbench still runs items through
      the inference waist, unchanged and fenced.
- [ ] The run carries the SCHEDULER principal and the LIVE delegation the
      existing path requires
      (`holdspeak/services/workbench_runner.py:345-349`); a revoked or expired
      delegation refuses with a recorded reason before any effect.
- [ ] Duplicate ticks for one due minute stay one run — the existing
      `duplicate_tick` rejection
      (`holdspeak/kernel/schedule_delegated.py:84-86`) covers the new kind too,
      proven, not assumed.
- [ ] A compile that returns any `unavailable` gap refuses the occurrence with
      that gap on the receipt, rather than running a partial plan and reporting
      success.
- [ ] The occurrence's authority basis, delegator and route are recorded the way
      the shipped path records them — no new provenance vocabulary.
- [ ] The descriptors' `scheduled` `TriggerBinding` and
      `SCHEDULED_TRIGGER_OWNER` are corrected to the owner that actually fires
      the recipe, and the `supplied_by` sentences that name a future story stop
      being true-by-being-unfinished.
- [ ] Every new fence proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_recipe_dispatch`. Drive the real `WorkbenchRunner`
with a real SCHEDULER `Principal` and a real minted delegation against a real
temporary database; resolve steps through the real
`holdspeak.services.recipe_catalog` and assert the real service was entered
(its own durable record), never a spy that could pass while the real ref is
wrong (`reference_lying_test_doubles`). Duplicate-tick leg drives two real
ticks on one minute.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidates (HS-200-46).** Two sentences must stay true: that every
descriptor's scheduled `TriggerBinding` names an owner that can be shown to
fire (HS-200-17's own ruling R17-8, currently satisfied only by declaring the
binding unavailable), and that a scheduled occurrence enters the declared
execution owner rather than `capability_id="workbench.item"`. Both predicates
read the real catalog module. Each is **`known_false` today** and can enter the registry before the fix: the predicate fails now, and HS-200-46's rule makes it fail again the moment the code starts satisfying it, which forces the flip to `holds` in the same commit as the repair.

**And one sentence already in the code is false today and belongs in the registry as `known_false` before this story starts:** the preparation descriptor's `supplied_by` reads *"HS-200-21 must add a watch_effects action_kind for a prepared brief and drain it beside project.steward.run_once"* (`holdspeak/services/recipe_catalog.py:426-429`, and the same owner at `:528` and `:602`). It names a change-driven chain as the supplier of a periodic firing. This story makes it true or replaces it; either way the registry should be holding it to account in the meantime.

**A contradiction this story must settle, not inherit.**
`SCHEDULED_TRIGGER_OWNER` (`holdspeak/services/recipe_catalog.py:128-133`)
names the connector-watch chain — *"connector_watches interval →
HeartbeatService.run_sweep → WatchService.evaluate_due → watch_effects →
ProjectStewardService.run_due"* — as the thing that would supply a recurring
firing, and the preparation descriptor's `supplied_by` assigns the work to
HS-200-21. That chain is **change-driven, not periodic**: an effect is minted
only by a completed evaluation with transitions AND a matching rule
(`if not rules: return []`, `holdspeak/services/watch_service.py:1291-1292`).
A Monday-morning brief is periodic. The cluster's ruling is that the periodic
owner is the Workbench cron clock; this story writes that into the descriptors
so the code and the charter stop disagreeing.
