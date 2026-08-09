# HS-131-04 — Sequence and Workflow admit every model step

- **Project:** holdspeak
- **Phase:** 131
- **Status:** backlog
- **Depends on:** HS-131-02, HS-131-03
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

Sequence and Workflow currently open one coarse lifecycle without a principal,
then execute several model calls inside it. `RunLifecycle` falls back to a native
invocation because the definitions are not `persona:` refs, and the outer run
can absorb every model step. This is the nesting loophole Article XI forbids.

## Scope

### In

- Give Sequence and Workflow routes an authenticated run context and one native
  parent operation for the whole definition execution.
- Route every model step in
  `holdspeak/web/routes/primitives/chains.py:101-260` and every model node in
  `holdspeak/web/routes/primitives/workflows.py:105-380` through the invocation
  runner as a causally linked child of that parent.
- Resolve placement once per child according to the Phase-130 precedence rule,
  freeze its deployment revision, and record the definition/node/step revision
  that actually executed.
- Keep ordering, graph branching, output binding, and domain result persistence
  in Sequence/Workflow code. The runner owns only the model invocation.
- Cancellation of the parent stops future children, cancels the active child,
  and prevents late child output from advancing the graph.
- Repair
  `tests/integration/test_primitive_framework_sync.py::test_ipad_synced_graph_workflow_runs_on_the_hub`,
  the seventh sync/admission failure assigned by HS-130-10, without Swift
  implementation work.

### Out

- Changing Sequence or Workflow semantics, editors, graph format, or
  `capability_ref`.
- Treating non-model computation nodes as consequential model invocations.
- One receipt for the whole graph in place of child receipts. The parent summary
  may project children; it cannot replace them.

## Acceptance criteria

- [ ] A three-step Sequence produces one parent run plus exactly three admitted
  invocation children and three terminal child receipts.
- [ ] A Workflow produces one invocation child for each model node actually
  dispatched, including retries/fallbacks, and none for skipped branches or pure
  computation nodes.
- [ ] Every child cites the parent causation ID, exact definition/node revision,
  and immutable deployment revision used.
- [ ] No Sequence or Workflow model call can execute without an authenticated
  principal and runner admission.
- [ ] Parent cancellation prevents new children, reaches the active child, and
  blocks late output from mutating subsequent step or graph state.
- [ ] A failed/refused child determines the existing domain outcome without
  losing that child's terminal receipt.
- [ ] The synced graph Workflow integration test passes against the canonical
  Python sync registry and exact deployment revision, with no Swift source edit.

## Test plan

- Unit: `uv run pytest -q tests/unit/test_workflow_graph.py` plus focused chain,
  parent-child cardinality, branch, fallback, and cancellation tests.
- Integration: `uv run pytest -q tests/integration/test_primitive_framework_sync.py::test_ipad_synced_graph_workflow_runs_on_the_hub` and a real two-step Sequence against the LAN endpoint.
- Manual / device: run one Sequence and one branched Workflow, inspect the parent
  and children, then cancel a run mid-step.

## Notes / open questions

The historical test name mentions iPad because it was written as a cross-client
proof. Phase 131 treats its pushed graph as input to the Python contract; it does
not modify or migrate Swift.
