# HSM-14-16 — The Workbench, Blueprints edition (a visual programming environment)

- **Project:** holdspeak-mobile
- **Phase:** 14
- **Status:** in-progress — opened 2026-06-22. The owner's third and decisive direction for the
  Workbench, after the vertical pipeline and the node-graph both fell short ("still a freaking easy
  basic and frankly embarrassing thing").
- **Depends on:** the node-canvas groundwork (HSM-14-15), `ILLMProvider`, the mesh runtime bus.
- **Owner:** unassigned

## Vision (owner, verbatim direction)

> "It's meant to be a visual builder, like draw.io but with our primitives… the meta language should
> be relatively robust — not Fortran, but if/and, looping controls. Blueprints-style is fine.
> Gamify the visualization of an execution flow; how an execution context provides real-time updates
> to whoever, on where they are on the execution path. Interface gamified."

The reference is **draw.io's ease + Unreal Blueprints' power**: a real visual programming
environment a senior engineer respects, with genuine **control flow** — not a linear pipeline.

## The design

### Blueprints model — two wire kinds
- **Exec pins/edges** (white) — the control flow, the *order*. A node has an exec-in + named exec-outs.
- **Typed data pins/edges** (colored) — the *values*; type-checked on connect.
- `Blueprint` = nodes + execEdges + dataEdges + `entry`. **All Codable** (the canvas + the mesh
  serialize/stream it).

### The meta-language (control flow + primitives)
- **Control flow:** `branch(condition)` (true/false exec-outs), `forEach` (run a body per item +
  `completed`), `whileLoop(condition, maxIterations)` (bounded), `sequence`, `merge`. Conditions:
  `contains` / `isNonEmpty` / `countAtLeast` (kept simple but real).
- **Primitives:** sources, the intelligence ops + the custom `llm(prompt)` (`{input}` substitution),
  pure transforms (`keepIf`, `splitIntoItems`), outputs. Composes with the control flow into a program.

### The execution context (the part the owner emphasized) — real-time "where am I"
- The runner becomes a **flow interpreter** with a live cursor that walks the exec graph (branches,
  loops). It threads an **`ExecutionContext`**: active node(s), per-node status, the path taken, loop
  counters.
- It emits a stream of small **Codable `ExecutionEvent`s** (`runStarted`, `nodeEntered`, `nodeStatus`,
  `branchTaken`, `loopIteration`, `nodeProduced`, `runFinished/Failed`). Because they're serializable,
  the **same stream feeds the local canvas AND rides the mesh bus** — so *whoever* is watching (you on
  the iPad while the Mac executes, the Queue HUD, a teammate) sees the cursor move in real time. A live
  debugger trace, turned into a spectacle.

### Gamified execution visualization
- A glowing token travels the exec wires; the active node ignites/scales; the taken path stays lit as a
  trail, untaken branches dim; **Branch** forks visibly with a ✓/✗ badge; **For-each** orbits with a
  live `3/10` counter; completion lands with a flourish + haptic. You **watch your program think** —
  tasteful, not childish.

### Composability
- Typed exec + data pins with type-checked wiring; and **save any graph as a node** (a function/macro)
  droppable into other graphs — composition at scale.

## Build plan (verifiable pieces, each proven on the OWNER'S DEVICE — no seeded screenshots)
1. **Engine** — the Blueprints model + flow interpreter + `ExecutionContext` event stream, with
   branch/loop/condition working, **host-tested** (orchestrator re-verifies `swift test`). *(in progress)*
2. **The Blueprints canvas** — exec + data pins, the control-flow palette, draw.io-grade UX
   (drag-place, type-checked connect, align/snap, inspector). Device-proven.
3. **The gamified live execution** — the token/trail/branch-fork/loop-orbit overlay driven by the real
   `ExecutionEvent` stream. Device-proven on a real run.
4. **Mesh streaming** — the event stream rides the bus so a second device watches a live execution.

## Acceptance criteria
- [x] **Engine: DONE + orchestrator-verified (2026-06-22).** `Blueprint.swift` (Codable graph: exec
      edges + typed data edges, control-flow node kinds, `BPCondition`) + `BlueprintInterpreter.swift`
      (walks exec from entry; branch/forEach/while/sequence/merge; pull-based memoized data resolution +
      `{input}`; injected `ILLMProvider`; per-node `FailurePolicy`; bounded loops + `maxSteps` cycle
      guard) + `ExecutionContext`/`ExecutionEvent` (Codable: runStarted/nodeEntered/nodeStatus/
      branchTaken/loopIteration/nodeProduced/runFinished/Failed) exposed as a callback sink AND an
      `AsyncStream`. **`BlueprintInterpreterTests` 13/0 (re-run by orchestrator, each case named);
      full suite 271/7/0.** Honest seams for the canvas: single-sink (multi-subscriber fan-out for
      local+mesh is the next seam), `merge` is pass-through (no true diamond join yet), `nodeProduced`
      preview truncated to 80 chars.
- [ ] Canvas: Blueprints editor (exec + data pins, control-flow nodes, type-checked wiring), device shot.
- [ ] Live execution: the gamified trace plays from real events on a real run, on the device.
- [ ] Composability: save-graph-as-node works.
- [ ] Mesh: a second observer sees the live execution path.

## Test plan
- Host: `BlueprintInterpreterTests` (branch both ways, for-each×N, while-bounded, data pull, `{input}`,
  the ordered event sequence, failure policy). Device: the owner drives a real graph and watches it run.

## Notes
- Supersedes the linear `Workflow`/`WorkflowRunner` for the builder (those stay for the simple path); the
  canvas lowers to the `Blueprint` graph. The hard lesson driving this story: **the UI must be walked on
  the real device, not shipped as a seeded Simulator screenshot.**
