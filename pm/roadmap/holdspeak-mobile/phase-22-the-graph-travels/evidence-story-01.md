# Evidence — HSM-22-01 — The `graph_json` serializer on iPad (Save, sync, the golden pin)

**Status:** done (2026-07-04), on `holdspeak-mobile/hsm-22-01-graph-serializer`.

## 1. The pieces

- **`BPRunsOn` joins `BPNode`** (`Blueprint.swift`): the per-node run target
  (`auto`/`onDevice`/`endpoint` — the exact `_RUN_TARGETS` vocabulary the hub parses,
  raw-value-shared with the App's `ModelPref`). The producer hole the audit missed is
  closed: the iPad can now emit the field the hub was already reading.
- **The lowering (`BlueprintWire.swift`, RuntimeCore):** `Blueprint.graphJSONData()`
  (canonical `HoldSpeakContracts` encoder + `.sortedKeys` for byte-stable fixtures) and
  `graphJSONValue()` (decoded into `JSONValue` with a PLAIN decoder on purpose — the
  snake_case-converting decoder would mangle the already-snake_case wire keys), plus
  `workflowDefinition(id:prompt:)` landing the graph in the synced contract. The
  Contracts "graphJson is reserved" comment is retired.
- **Save on the shipping canvas (`WorkbenchUI.swift`):** `PatchModel.lowerToBlueprint()`
  walks the same primary source→…→output chain the runner walks and produces a LINEAR
  Blueprint — exactly the subset the hub runs — with each model-op node carrying the
  inspector's `failure_policy` + `runs_on`. A Save button (with a settle beat) lowers
  the canvas and upserts a `WorkflowRecord` through `DeskWorkflowLibrary` into the
  DESK's own record store (`hs.diorama.workflows` + the `hs.diorama.synctimes` LWW
  stamp, the stage's exact coders), so the next `DeskSyncDriver` pass ports it like
  every other primitive. `HS_DEMO_WB_SAVE=1` (sim-only) drives the same save path.
- **The golden pin (the HS-72-01 pattern applied to graphs):**
  `contracts/fixtures/blueprint-linear-sample.json` + `blueprint-branching-sample.json`
  are ENCODED BY SWIFT (`BlueprintWireTests`, regen via
  `HS_REGEN_BLUEPRINT_FIXTURES=1`); a new pytest
  (`tests/unit/test_blueprint_graph_conformance.py`) feeds those exact bytes into
  `workflow_graph.linearize()` — the real encoder against the real parser. The linear
  fixture linearizes with order + `failure_policy` + `runs_on` intact (and the
  absent-key = inherit rule held); the branching fixture is refused with the honest
  control-flow reason.

## 2. The live proof (connected simulator, real scratch hub)

- [`hsm-22-01-canvas-saved.png`](./screenshots/hsm-22-01-canvas-saved.png) — the
  shipping Workbench canvas wearing the green **Saved** beat beside Run.
- The saved record inspected in the app container: `graphJson` carries the canonical
  wire (tagged-union kinds, snake_case `exec_edges`, `runs_on: "auto"` +
  `failure_policy: "retryThenQueue"` on the model op).
- **The travel:** the desk (paired to a scratch `MeetingWebServer` on
  `127.0.0.1:8123`) synced on load; `GET /api/sync/pull` returned the workflow with
  the full `graph_json` aboard:
  `entry → source → n1(extract, auto, retryThenQueue) → out`.
- **The loop closed:** the hub's own `linearize()` accepted the SYNCED graph —
  `linearizable: True`, the four-node plan with provenance intact. Authored on the
  canvas, saved, synced, parsed runnable by the hub. The graph travels.

## Suites

- `swift test` (full package) — **442 tests, 8 skipped, 0 failures** (+5
  `BlueprintWireTests`).
- `uv run pytest -q tests/unit/test_blueprint_graph_conformance.py
  tests/unit/test_workflow_graph.py tests/unit/test_web_routes_primitives.py
  tests/unit/test_doc_drift_guard.py` — **71 passed** (+3 conformance).
- Meeting-capture sim build — **BUILD SUCCEEDED** (gen + patch + xcodebuild).

## Honest boundaries

- The v1 canvas authors LINEAR graphs (its model is a patch, not a Blueprint); the
  full control-flow Blueprint ships in the (currently unreachable) v2 canvas — when
  v2 lands, it saves through the same `workflowDefinition()` path, and the branching
  fixture already pins how the hub will refuse it.
- The canvas's `questions` node lowers to its intent (an open-questions llm node);
  Blueprint has no lens vocabulary.
- The save id is session-stable (re-saves in one session update one record); a new
  session mints a new workflow — v0 semantics, visible in the proof (two records
  after two app sessions).
- Running the synced graph END-TO-END from another surface is 22-04's proof, not
  claimed here (linearize-accepts is this story's close).
