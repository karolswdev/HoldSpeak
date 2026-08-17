# HS-134-04 — Every answer names its decider

- **Project:** holdspeak
- **Phase:** 134
- **Status:** done
- **Depends on:** HS-134-01
- **Unblocks:** HS-134-10
- **Owner:** unassigned

## Problem

`PlacementResolution.placement_dict()` exists
(`holdspeak/inference_targets.py:525-530`) but only listings use it.
Execution responses across Ask (`ask_service.py:127`), Recipe (after
HS-134-01), Workbench (`workbench_runner.py:30-31`),
Sequence/Workflow (`sequence_workflow_service.py:31-33`), and Cadence
(`cadence_service.py:221`) do not say who decided the placement — the
ledger exists, the answer hides it.

## Scope

### In

- Every placement-resolving execution response carries
  `{"placement": {"effective_target_id": ..., "source": ...}}` from
  `placement_dict()` — Ask, Recipe run/chat, Workbench runs,
  Sequence/Workflow runs, Cadence drafted actions.
- The same block reaches the corresponding MCP tool results (they pass
  service dicts through — verify, don't duplicate).
- Tests per surface asserting the block and the correct `source` under
  an override.

### Out

- Web UI rendering of provenance (Comfy Chair / later slice — the API
  carries it, the UI catches up separately). New resolver tiers.

## Acceptance criteria

- [ ] Each named execution response carries the placement block; a
  workbench-tier override yields `source: "workbench"` in Recipe runs
  (ties to HS-134-01's test fixture).
- [ ] MCP `ask.run` / `sequence.run` / `workflow.run` results include
  the block (walk harness may assert it in HS-134-10).
- [ ] Focused tests green per touched service.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_placement_resolver.py tests/unit/test_recipe_runner_migration.py tests/unit/test_one_path_spine.py --tb=short`
  plus per-service focused files named in the worker report.
