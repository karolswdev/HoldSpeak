# HSM-22-01 — The `graph_json` serializer on iPad (Save, sync, and the golden pin)

- **Project:** holdspeak-mobile
- **Phase:** 22
- **Status:** done — see [`evidence-story-01.md`](./evidence-story-01.md). The graph
  travels: canvas → Save (canonical lowering, `BPNode.runsOn` closed) → desk record →
  DeskSync → the hub's `linearize()` accepts it runnable; the language boundary is
  golden-pinned (Swift-encoded fixtures fed byte-for-byte into the hub parser).
- **Depends on:** the Blueprint model + interpreter (Phase 14, shipped); the hub
  linearizer (HSM-22-02, shipped); `graph_json` sync survival (HSM-23-04, shipped).
- **Unblocks:** 22-03 (the web consumes/authors the same shape), 22-04 (the
  cross-surface proof needs an authored producer).
- **Owner:** unassigned

## Problem

The iPad authors a rich Blueprint that never leaves the canvas:

1. Nothing encodes a `Blueprint` into `WorkflowDefinition.graphJson` — the field is
   still commented "reserved" (`Contracts/Primitives.swift:346`); the canvas has no
   Save; `WorkbenchLibrary` (`WorkbenchUI.swift:11`) persists the engine model to
   UserDefaults only.
2. **`BPNode` carries no `runs_on`** (`Blueprint.swift:162`) — the hub parses a
   per-node field (`workflow_graph.py:74`) that no producer can emit. The audit
   missed this; the survey caught it.
3. The language boundary is unproven: the hub's conformance test runs a hand-written
   dict; Swift's Codable test round-trips Swift↔Swift with a plain coder (no
   snake_case, no wire-shape assertion).

## The design

1. **`runs_on` joins `BPNode`** (optional; absent = the hub's default), rendered on
   the node inspector with the existing `RunsOnPicker`.
2. **The lowering:** `Blueprint` → `graph_json` through the canonical
   `HoldSpeakContracts` coder (snake_case, the `{"extract":{"_0":…}}` tagged-union
   shape), landing in `WorkflowDefinition.graphJson` / `WorkflowRecord`.
3. **Save on the canvas:** an authored Blueprint persists as a real `WorkflowRecord`
   and rides `DeskSync` like every other primitive (no parallel store).
4. **The golden pin (the HS-72-01 pattern applied to graphs):** a fixture ENCODED BY
   SWIFT (a real Blueprint exercising entry/llm/extract/keepIf + `failure_policy` +
   `runs_on`) committed under `contracts/fixtures/`; a Swift test regenerates and
   compares; a pytest feeds the exact bytes into `workflow_graph.linearize()` and
   asserts the plan (order, policies, runs_on). A second fixture with a `branch`
   asserts the honest refusal reason. The two parsers can never drift silently again.

## Scope

- **In:** the `BPNode.runs_on` field + inspector picker; the lowering + Save +
  DeskSync wiring; both fixtures + the Swift regen test + the pytest conformance;
  sim proof (author → Save → the record visible on the hub via sync).
- **Out:** the hub executing control flow (22-02 refused it honestly; unchanged);
  web authoring (22-03); the iPad run-on-hub path (22-04).

## Test plan

- `swift test` (the new serializer/regen tests; Blueprint suites green).
- `uv run pytest -q tests/unit/test_workflow_graph.py` + the new fixture conformance
  test (Swift bytes → `linearize()`).
- Sim proof against a live scratch hub: Save on the canvas → `/api/sync/pull` shows
  the workflow with the real `graph_json`.
