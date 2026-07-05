# Evidence — HSM-15-04 (one runner for the mesh) — DONE

**Closed 2026-07-05.** The story's own closing condition (set by the resume survey the
same morning): "closes when the runner dispatches per RUNS-ON". It does.

## What the closing slice built (with HSM-15-02)

- **`MeshDispatch`** (`WorkflowRunner.swift`): an injected
  `@Sendable (prompt) async throws -> String`; `.dispatchToMac` steps run through it
  under the SAME bounded retry loop as providers — an unreachable Mac reads exactly like
  an unreachable endpoint to the failure policy (retry → park / fall back on-device /
  skip). No handler wired (no paired desktop) → the step rides the policy, never a crash.
- **Per-step `targets`** on `run()` (index-aligned with `workflow.steps`; missing/nil →
  `.onDevice`): the node inspector's pin finally reaches run time. An empty array is
  byte-identical to the pre-mesh behaviour (locked by
  `testEmptyTargetsStaysByteIdenticalLegacy`).
- **`StepOutcome.ranOn`**: where the output ACTUALLY came from. A `.fellBack` step
  reports `.onDevice` — it never left; the badge updates (the 16-09 honesty grammar).
- The App wires the dispatch to the paired peer's `HTTPDesktopClient.runStep`
  (`POST /api/ask` — the hub runs the prompt on its configured intel and persists
  nothing; a step result is intermediate).

## Two latent finds fixed on the way

1. **Queue-HUD jobs never settled**: the run loop minted a fresh `UUID()` as `jobID` but
   `QueuedJob.init` self-generates its id — the settle lookup never matched, so every
   canvas-run job row stayed "working" forever (the earlier sim proof watched the node
   glow, a separate path). Fixed: the inserted job's real id is captured.
2. **The job's target label lied**: it read the app-wide `isLocal` for every step. Now it
   states the step's resolved pin, and settles to `ranOn` when the outcome lands.

## Proof

- **Host**: `swift test` → **476 passed / 9 skipped / 0 failures**, including the new
  dispatch matrix (`WorkflowRunnerTests`): dispatched step never touches the local
  provider + `ranOn` states the Mac; no-paired-peer parks resumable; unreachable Mac
  falls back on-device with `ranOn == .onDevice`; the retry bound covers dispatch;
  mixed targets thread one value across the mesh boundary; empty targets byte-identical.
  Client (`AskClientTests`): the exact `/api/ask` body (prompt + lens + EMPTY context),
  Bearer, the honest egress decode, non-2xx throws.
- **Live (Simulator + a REAL local hub)**: a scratch `MeetingWebServer` on loopback
  (intel faked in-process, the route real; `scripts/proof_hsm15_mesh_hub.py`); the app
  launched with `HS_CLASSIC_HOME=1 HS_DEMO_WB_MESH=1` and env pairing. The pinned
  Decisions step's fully-resolved prompt arrived as a receipt on the hub
  (`From the following, extract the decisions… Standup transcript…`) and the HUD job
  settled **Done · Karol's Mac** — `screenshots/hsm-15-02-mesh-run.png`. Re-verified on
  the final (debug-print-free) build: a fresh receipt landed.
- The on-device walk beat (real iPad + real hub) joins the phase's owner queue.

## The sim-harness trap worth remembering

The app's peer store persists in the APP CONTAINER's UserDefaults; `simctl spawn
defaults write` touches a DIFFERENT domain, and editing the container plist behind
cfprefsd gets clobbered. The reliable recipe for a clean-peer proof run:
`simctl uninstall` (wipes the container) → install → launch with
`SIMCTL_CHILD_HS_DESKTOP_{HOST,PORT,NAME}` (the store's env fallback applies only when
its defaults are empty). The stale container here carried a REAL old pairing to `.43` —
which is exactly what the first failed runs were honestly dialing.
