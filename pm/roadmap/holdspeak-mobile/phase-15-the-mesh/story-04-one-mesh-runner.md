# HSM-15-04 — One runner for the mesh (local or dispatched, policy-enforcing)

- **Project:** holdspeak-mobile
- **Phase:** 15
- **Status:** in-progress — **the pure on-device/endpoint runner is BUILT + host-proven (2026-06-22).**
  `apple/Sources/RuntimeCore/Workbench/WorkflowRunner.swift` walks the linear `Workflow` model,
  threads input, substitutes `{input}`, runs model-backed steps through an injected `ILLMProvider`
  (on-device by default), does `keepIf` as a pure filter, and enforces a new `FailurePolicy`
  (retryThenQueue / fallbackOnDevice / skip) with an injectable backoff + resume-from-cache. The
  `RunTarget.dispatchToMac` seam is **stubbed** (additive mesh dispatch, not built). `WorkflowRunnerTests`
  (9) green; full suite **250 tests / 6 skipped / 0 failures** (orchestrator-verified). Remaining: the
  App canvas → `Workflow` lowering + wiring `Run` to drive the real `RunQueueStore`/pulses + the Mac
  dispatch (HSM-15-02).
- **Depends on:** the existing RuntimeCore `Workflow` model (linear; the App graph→`Workflow` lowering
  is later); `InferenceConfigStore.makeProvider`; `HTTPDesktopClient` (for the dispatched-to-Mac seam);
  the `RunQueueStore`.
- **Owner:** unassigned

## Grounding (2026-06-22)

The on-device execution seam exists (`InferenceConfigStore.makeProvider` → `LlamaProvider` /
endpoint). The **dispatch-to-Mac** branch depends on the new desktop "run a capability and return the
result" RPC called out in HSM-15-02's grounding (no such generic endpoint exists today — capabilities
are reachable only via their domain routes). So: build the pure runner + the on-device/endpoint path
now (fully host-testable); the Your-Mac dispatch lands when that RPC exists. Failure-policy park/resume
reuses the already-built `RunQueueStore`.

## Vision

The Workbench draws a program; the runner makes it real. Built **once, for the mesh**: it walks the
graph and, per node's RUNS-ON, either runs the step **locally** (on-device `LlamaProvider` /
endpoint) or **dispatches** it to the Mac — there is no separate local-only runner to throw away.
It enforces the **per-workflow** failure policy (retry → queue → fallback) and feeds the real
QueueHUD. This is the honest version of the canvas's Run pulses.

## The design

- **Pure orchestration in RuntimeCore** (`Sources/RuntimeCore/Workbench/WorkflowRunner.swift`),
  host-testable with a fake `ILLMProvider` and a fake `DesktopClient`.
- **Topological walk.** Nodes execute in dependency order; each resolves its input from upstream
  outputs (cached — resume never recomputes a completed node). Input resolution: a source's text /
  the previous node's output; `{input}` substitution for the custom `LLM call`.
- **Per-node execution by target:**
  - On-device / Endpoint → `provider.complete(prompt:)` via `makeProvider` (a fresh provider per
    call; the on-device one MUST be fresh — see the existing `generate()` note).
  - **Your Mac (mesh)** → dispatch the node to the desktop over `HTTPDesktopClient` (its model /
    its connectors).
  - Pure transforms (`keepIf`/`summarize`/`rewrite` templates) need no model where they are pure.
- **Failure policy (per-workflow default, node override).** On an unreachable target: `retryThenQueue`
  → backoff, then **park the run in the `RunQueue`** as `blocked` (a monitor resumes from the parked
  node when reachable); `fallbackOnDevice` → swap to the on-device model (the egress badge updates —
  it didn't leave after all); `skip` → carry the input through.
- **Drives the queue + the canvas.** Each node is a `QueuedJob`; the canvas pulses are driven by real
  job state (a node glows while its job runs, pulses on `blocked`).

## Acceptance criteria

- [ ] **Host-tested runner** — input threading, `{input}` substitution, the `keepIf` filter, step
      ordering, and resume-from-cached all unit-tested with a fake provider.
- [ ] **Targeted execution** — on-device / endpoint run via `makeProvider`; a Your-Mac node dispatches
      over `HTTPDesktopClient` (fake-client unit-tested; LAN-proven once HSM-15-02 lands).
- [ ] **Policy enforcement** — retry → queue → resume and fallback-on-device are unit-tested
      (unreachable target drives the documented path, not a crash).
- [ ] **Real queue + pulses** — running a workflow populates the real `RunQueueStore`; canvas pulses
      track job state. Simulator-shot + (post HSM-15-02) a LAN run.

## Build plan

1. `WorkflowRunner` (pure) — topo walk + input resolution + `{input}`; fake-provider tests.
2. Per-node target dispatch (local vs `HTTPDesktopClient`); fake-client tests.
3. Failure policy → `RunQueue` park/resume + fallback; tests.
4. Wire `Run` (canvas) to the runner; drive pulses + the HUD from job state.
5. Simulator shot of a real run; LAN run once mesh targets (15-02) exist.

## Test plan

- Host (the spine): `WorkflowRunnerTests` with fakes — assert the exact prompt sent for an `llmCall`,
  `{input}` substitution, `keepIf` filtering, threading, resume-from-cache, and each failure-policy
  branch (retry-count, queue-park, fallback-swap). Run `swift test` and read the output.
- Device/LAN: a real workflow runs end-to-end through the configured provider(s); a mesh-targeted node
  runs on the Mac.

## Notes

- This is the engine owed since the canvas shipped. Building it mesh-aware now (not local-only) is the
  cheaper path — dispatch is one branch in the per-node step, not a parallel runner.
- Honesty rule: until this lands, the canvas Run is a **visualization**; the docs say so. Do not claim
  custom-prompt execution until it runs on a model.
