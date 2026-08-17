# HS-134-01 — Recipe execution takes the precedence door

- **Project:** holdspeak
- **Phase:** 134
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-134-04, HS-134-07
- **Owner:** unassigned

## Problem

Recipe run and chat are the ONLY execution paths bypassing the
Phase-130 precedence authority. `recipe_service.py` chat (:93 region)
and run (:130-131) chain `inference_target_id or recipe.profile_id or
"this_machine"` through `_target()` → `resolve_inference_target`
(:168-171), while the listing path (:170) correctly calls
`resolve_placement`. A Workbench override is visible in the listing's
provenance and invisible to actual execution — an Article II lie.
Orchestrator-verified on glass at charter.

## Scope

### In

- Migrate run and chat to `resolve_placement(db, invocation=...,
  workbench=<caller context where available>, agent=recipe.profile_id)`
  (`holdspeak/inference_targets.py:538-575`), keeping the readiness
  refusal and `capture_deployment_revision` behavior of `_target()`.
- The workbench tier plumbs through from callers that carry workbench
  context (WorkbenchRunner/SequenceWorkflow paths that invoke recipes).
- A regression test proving a workbench-tier override changes actual
  execution target, not just the listing.

### Out

- Response provenance fields (HS-134-04). API/vocabulary changes
  (HS-134-02/03). Any resolver behavior change — `resolve_placement`
  is settled Phase-130 law.

## Acceptance criteria

- [x] `grep resolve_inference_target holdspeak/services/recipe_service.py`
  shows no execution-path use; run + chat resolve via
  `resolve_placement`.
- [x] The new test: recipe with agent-tier target A, workbench override
  B → execution admits B; without override → A; invocation arg wins
  over both.
- [x] Existing guards green: `HOME=$(mktemp -d) uv run pytest -q
  tests/unit/test_recipe_runner_migration.py tests/unit/test_one_path_spine.py
  tests/unit/test_placement_resolver.py --tb=short`.

## Test plan

- The focused command above plus the new test file/case; evidence
  captures the run tail.
