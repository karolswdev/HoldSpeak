# HS-133-06 — Sequences and Workflows run admitted

- **Project:** holdspeak
- **Phase:** 133
- **Status:** backlog
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

Sequences and Workflows can be authored via `desk.*` but not run from
MCP. The admitted run paths exist —
`SequenceWorkflowService.run_sequence` (:110) and `run_workflow` (:146)
both enter `InferenceRunner.invoke()` through `_invoke` (:38) with
kernel parent runs and durable receipts — but only the web routes reach
them.

## Scope

### In

Per assets/surface-spec.md §1E, verbatim:
`holdspeak/mcp/families/sequence.py` implementing `sequence.run`,
`sequence.cancel`, `workflow.run`, `workflow.cancel` with the spec's
schemas. Runs are async — `_run()` wrapped. The service constructor
takes `(db, broker)`; the broker comes from
`holdspeak.kernel.runtime._configure(db)`, the same pattern as
chains.py:56 / workflows.py:56. Cancels dispatch through
`broker.parent_run_controller.cancel_by_operation_id`, same as the web
routes (chains.py:72, workflows.py:70).

### Out

- Sequence/Workflow CRUD (already exists via `desk.*` with
  `kind="chains"`/`"workflows"` — the descriptions may say so). Any
  SequenceWorkflowService change. Any new resource (kernel receipts are
  already exposed via `pipeline://events/*`).

## Acceptance criteria

- [ ] All four tools in the catalogue with closed schemas; run results
  carry the receipt, steps, and artifact reference the service returns.
- [ ] Monkeypatched-service tests prove `_run()` wrapping for both runs
  and correct broker routing for both cancels.
- [ ] Unknown `chain_id`/`workflow_id`/`parent_operation_id` return
  `isError: true`.
- [ ] REQUIRED_TOOLS extended with the four names.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py --tb=short`
