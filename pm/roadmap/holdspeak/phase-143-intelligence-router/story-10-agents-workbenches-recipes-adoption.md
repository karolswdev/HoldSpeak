# HSEGHS001HS104-143-10 - Agents, Workbenches, Recipes, and Workflows Adoption

- **Project:** holdspeak
- **Phase:** 143
- **Status:** backlog
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
