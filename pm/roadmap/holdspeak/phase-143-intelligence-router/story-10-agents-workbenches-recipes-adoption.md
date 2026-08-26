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
- [ ] ~~The Apple physical-leaf census has no remaining unadmitted provider
  leaf; Swift workflow retry/fallback law is first retired or
  controller-aligned by Story 06.~~ **OUT OF THIS STORY'S BAR — owner
  ruling 2026-08-25 (final form): the Slice-5 Swift progress is FROZEN
  IN TIME on hold branch `hold/hs143-10-slice5-swift-bridge` at
  compile-green; the story refocuses on the web/Python portion. The
  seven Swift leaves stay censused as HELD. Full ruling history in the
  plan's ruling blocks.**

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
- 2026-08-25 — Opus gate audit over Slices 1–3 + amended adopter: CLEAN on
  all five dimensions (migration honesty, frozen-plan integrity, ToolTurn
  adoption reality, receipt/refusal truth, test honesty), zero findings;
  the audit traced recipe.chat → façade → foundation → controller →
  InferenceRunner in source and verified every census-fixture reduction
  against deleted code.
- 2026-08-25 — Round 3 (Slice 4): Sequence/Workflow model steps admit
  through frozen `sequence.step`/`workflow.node` routes with stable
  operation identities for restart replay; new executable `inference.run@1`
  admission is refused before mutable resolution (historical records stay
  readable); duplicate `RunLifecycle` submissions removed; legacy policy
  vocabulary decodes honestly (`fallbackOnDevice`→`carry` — it was always a
  carry-through; `retryThenQueue`→`hold`, retry authority retired); no
  `fell_back` receipt for carry. Orchestrator-verified: Slice 4 set 130
  passed, all one-path guard legs 168 passed.
- 2026-08-25 — Owner ruling arc on Swift (three beats, final form): Slice 5
  progress FROZEN IN TIME at compile-green on
  `hold/hs143-10-slice5-swift-bridge` (build clean, 28/28 smoke, 6/6
  bridge integration, orchestrator-verified); criterion 6 out of this
  story's bar; story refocused on the web/Python portion. Full history in
  the plan's ruling blocks.
- 2026-08-25 — Round 5 (Slice 6, Python-only): zero-Python-fork census
  convergence with fail-closed regeneration; three census artifacts
  regenerated (routing-authority mutable families 10→7 with an
  exact-empty adopter-fork scanner; capability census 102 Python AST
  sites, 7 Swift leaves explicitly HELD, never falsely zeroed; surface
  fallback 0 executable Swift policy sites held); new 16-case table-driven
  placement adoption matrix over real production entries (Recipe run,
  plain+qualified chat, Workbench item+memory, agent façade, voice,
  sequence, workflow, legacy inference.run refusal) proving
  freeze/mutate/later-admission and receipt linkage per family.
  Orchestrator-verified: census+matrix set 96 passed; spine/provenance/
  cardinality/context guards 114 passed.
- 2026-08-25 — Second opus gate audit (Slices 4+6 + story-level acceptance):
  CLEAN on all six dimensions, zero findings — second consecutive
  zero-finding audit.
- 2026-08-25 — Sweep №1: 6574 passed / 39 failed / 53 skipped (7:23,
  xdist). Triage: 34 inherited (baseline), 1 census xdist flake
  (serial-green ×2, ledgered), 4 REAL branch-new in recipe web surfaces —
  files no round's focused set covered. Fix round: two product defects
  fixed (post-marker recipe CREATE with a dangling profile_id wrongly
  refused via an invalid assignment write — now creation succeeds and
  run/chat return an honest 409 inference_target_unavailable pre-admission;
  routed provider failures laundered into generic 409s — now 502 with the
  transient error preserved, no exception text in durable route evidence)
  + blank-recipe rigs migrated from retired ambient placement to canonical
  global-default seeding. Orchestrator-verified: fixed surfaces 63 passed
  (incl. previously-inherited workflow-route failures now healed); guards +
  census + matrix 210 passed.
