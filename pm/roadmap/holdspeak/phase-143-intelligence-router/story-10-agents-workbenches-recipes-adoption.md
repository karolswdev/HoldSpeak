# HSEGHS001HS104-143-10 - Agents, Workbenches, Recipes, and Workflows Adoption

- **Project:** holdspeak
- **Phase:** 143
- **Status:** in-progress
- **Depends on:** 143-06, 143-07
- **Unblocks:** 143-14
- **Owner:** unassigned

## Problem

Workbench→Recipe→global SQL resolution, agent overrides, sequences/workflows,
and reference-resolution code currently reconstruct placement independently.

## Scope

- **In:** Migrate non-tool Agent, Workbench, Recipe, sequence/workflow, and
  reference-resolution callers; retire mutable `inference.run` late routing and
  fake workflow fallback labels; bring the remaining censused Apple provider,
  companion, and mesh physical leaves behind the server route-plan and
  `InferenceRunner` waist. Tool-bearing steps are owned by Story 09.
- **Out:** Feature-owned route editors and unrelated workflow branching changes.

## Acceptance criteria

- [ ] Every caller uses the canonical resolver/controller and InferenceRunner waist.
- [ ] Workbench/Recipe/Agent precedence preserves its old effective primary until owner edit.
- [ ] Subject changes affect next run only and never mutate group/global policy.
- [ ] `inference.run` cannot physically dispatch through mutable late resolution.
- [ ] Generated census finds no remaining placement-resolution fork.
- [ ] The Apple physical-leaf census has no remaining unadmitted provider leaf;
  Swift workflow retry/fallback law is first retired or controller-aligned by
  Story 06.

## Test plan

- **Unit:** precedence, deletion, dangling subject, concurrent override.
- **Integration:** recipe/workflow restart and receipt reconstruction.
- **Manual / device:** application-level subject summary/override walk; shared
  editable UI and cross-surface reuse belong to Story 13.

## Notes / open questions

The shared UI must replace, not sit beside, private target selectors.

## Progress

- 2026-08-25 — Round 1 (Slices 1+2 of
  `assets/story-10-placement-adoption-plan.md`): one-way Recipe/Workbench
  pointer migration into exact canonical subject assignments
  (`recipe.run`/`recipe.chat`/`workbench.item`/`voice.reference_resolve`,
  marker-first, atomic, idempotent); Recipe run/chat migrated onto routed
  admission, frozen plans, controller execution, and Runner receipts with
  `_target`/`_invoke`/display re-resolution retired; post-marker legacy-field
  writes translate to canonical mutations or refuse explicitly; narrow
  `AgentTurnService` façade added as the only product seam over
  `ToolTurnFoundationService`. Orchestrator-verified: Slice 1 set 67 passed,
  Slice 2 set 50 passed, one-path guards 166 passed. Two design findings
  triaged and ruled in the plan's Round-1 triage section: `PluginDispatch.chat`
  reclassified ALREADY-DONE (admitted leaf, identity-fenced to its runner
  reservation) and the first ToolTurn adopter amended to `RecipeService.chat`
  on a tool-qualified route; dead workbench tier on the standalone recipe
  entry ledgered (no production transport passes it). Story 15 (repo-wide
  router docs) chartered by owner ruling; Story 14 now depends on it.
- 2026-08-25 — Round 2 (amended adopter + Slice 3): qualified
  `RecipeService.chat` is now the first production ToolTurn adopter —
  transport → façade → foundation → controller → `InferenceRunner` with
  production-object proofs (parent, lease, model step, attempt, receipt);
  `RecipeRecord.tools` proven inert. WorkbenchRunner's local `_target`/
  `_invoke` forks retired for frozen parent-route child admission (items +
  memory); `retry_mint` reads exact historical route evidence; voice
  resolution rides a frozen `voice.reference_resolve` route/controller
  execution; schedule enablement freezes delegated route terms (owner
  reapproval mints a later frozen route); legacy selector writes
  write-through to canonical assignments post-marker. Census fixtures
  reduced only for removed source authority. Orchestrator-verified: Slice 3
  set 72 passed, adopter set 39 passed, one-path guards + census suites 188
  passed.
