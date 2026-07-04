# Phase 22 — The graph travels (the Workbench bridge)

**Status:** in-progress (opened 2026-07-04) — audit theme 5, the keystone the
cross-surface workflow story waits on. Independent of the walk-gated phases.

**Last updated:** 2026-07-04 (**4/4 — FULLY BUILT, GATE STAGED, all in the day it
opened. THE EQUILIBRIUM BUILD IS COMPLETE.** 22-04 closed the loop ON REAL METAL: the
iPad-authored `Canvas · Decisions` graph (saved from the shipping canvas in 22-01,
synced in the same pass) ran ON THE HUB against the real .43 Qwythos endpoint — the
printed card wears Cloud · your desktop with the standup's actual decision extracted,
and the hub's pull carries the run-born artifact whose lineage names the workflow.
`runWorkflow` joined the iPad hub path (workflow drops with a graph aboard now offer
the runs-on sheet; refusal warnings ride the card), the crown integration test locks
Swift-fixture → sync → run, the 23-04 placeholder sync fixture upgraded to the real
wire, ARCHITECTURE gained the graph-bridge node, and
[`HSM-22-WALK-RIDER.md`](./HSM-22-WALK-RIDER.md) is staged (G1+G2, ~3 min) — **the
couch session now closes FIVE phases: 18, 19, 21, 22, 23.** Earlier: **3/4 — 22-03
followed: the web is the second producer.**
The desk authors a real linear graph in-world (`+ Workflow` → the step builder;
palette/params/reorder, debounced PUTs), emitting the ONE canonical wire — live-proven
in real Chromium against a scratch hub (authored → persisted → the hub's `linearize()`
accepts). `primitives.ts` types the object wire; the hub's honest run `warning`
finally reaches the reader; and graphs the web cannot faithfully re-emit (control
flow, iPad provenance) are read-only, never silently stripped. vitest 18, pytest 34,
web build + real-Chromium preflight green. Only 22-04 remains (the cross-surface RUN
+ `runWorkflow` on the iPad hub path + docs/rider). Earlier: **2/4 — 22-01 landed the
day the phase opened: THE GRAPH TRAVELS.** The shipping canvas saves a real linear Blueprint (per-node
`failure_policy` + the NEW `runs_on`) through the canonical coder into a desk
`WorkflowRecord`; a live DeskSync pass ported it to a scratch hub whose own
`linearize()` accepted it runnable — authored → saved → synced → parseable, proven
end to end on the connected sim. The language boundary is golden-pinned the HS-72-01
way: Swift-ENCODED fixtures (linear + branching) fed byte-for-byte into the hub
parser by a new pytest. Full `swift test` 442/8-skip/0-fail; the pytest battery 71
passed. Next: 22-03 (web) or 22-04 (the cross-surface run). Earlier: **OPENED,
survey-corrected — the hub half was pre-paid, the authoring half was not.** The 2026-06-27 draft predates Equilibrium Wave 1 and
Phase 23: **22-02 shipped in Wave 1** (`workflow_graph.py` linearizes the Swift
tagged-union shape, carries AND applies per-node `failure_policy`, carries `runs_on`,
refuses control flow honestly with a `warning`, and documents what it does not
enforce — 50 tests re-run green on open), and 23-04 locked `graph_json` surviving sync
byte-faithful. But the survey KILLED a false memory: the Wave-2 "web authors a linear
graph" claim is **not backed by code** (no `exec_edges` anywhere in `web/src`; the
workbench page is localStorage-only; `primitives.ts:153` still types `graphJson` as a
string) — 22-03 stays genuinely todo. And the audit itself missed a producer hole:
**`BPNode` carries no `runs_on` at all**, so the iPad cannot emit the policy the hub
already reads; 22-01 absorbs that fix. Stories re-grounded below.)

## Why this phase exists

Audit theme 5: *the Workbench graph is authored richly on iPad but cannot travel.* The
full Blueprint interpreter (two wires, control flow, typed edges, event stream) runs on
device, but the graph never leaves the canvas:

- **It never serializes.** Nothing encodes a `Blueprint` into
  `WorkflowDefinition.graphJson` (still commented "reserved",
  `Contracts/Primitives.swift:346`); the canvas has no Save; `startRun()` is
  demo-gated; `WorkbenchLibrary` persists the engine model to UserDefaults only.
- **The iPad cannot even express `runs_on`.** `BPNode` (`Blueprint.swift:162`) carries
  `failurePolicy` but no per-node runs-on — the hub parses a field no producer emits.
- **Web cannot author a graph.** No surface emits `nodes`/`exec_edges`;
  `useDesk.createPrimitive` has no workflow case; `primitives.ts` type-drifts
  (`graphJson?: string` vs the object wire).
- **The language boundary is unproven.** The hub's conformance test runs a
  hand-written Python dict in the Swift shape; no test feeds real Swift-ENCODER bytes
  into `linearize()`. (The 23-04 sync fixture survives the wire but would not
  linearize — a placeholder shape, worth upgrading.)

## The load-bearing design call

**One `graph_json` wire shape, authored anywhere, run honestly.** Lower the iPad
Blueprint to the canonical snake_case `graph_json` through the shared coder, persist it
as a `WorkflowRecord`, and sync it via `DeskSync` — and pin the language boundary the
HS-72-01 way: a golden fixture ENCODED BY SWIFT, committed, and fed byte-for-byte into
`workflow_graph.linearize()` by pytest, so the two parsers can never drift again. The
hub already honors the faithful subset and warns on the rest (22-02, shipped). Web
ships a minimal linear builder emitting the same shape, or scopes its claim honestly.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-22-01 | The `graph_json` serializer on iPad (+ `runs_on` on `BPNode`, Save, `DeskSync`, the Swift-encoded golden fixture → `linearize()` conformance) — **leads** | done — [`evidence-story-01.md`](./evidence-story-01.md) |
| HSM-22-02 | The hub honors the graph (control flow / `failure_policy` / `runs_on`, or honest omission) | done (pre-paid, Wave 1) — [`evidence-story-02.md`](./evidence-story-02.md) |
| HSM-22-03 | Web authors a linear graph (or honest scope) + the `primitives.ts` type fix + the run UI renders the hub's `warning` | done — [`evidence-story-03.md`](./evidence-story-03.md) |
| HSM-22-04 | The cross-surface proof (authored → synced → run) + `runWorkflow` on the iPad hub path + docs | done — [`evidence-story-04.md`](./evidence-story-04.md); [`HSM-22-WALK-RIDER.md`](./HSM-22-WALK-RIDER.md) staged (G1+G2, ~3 min) |

## Where we are

Opened 2026-07-04, survey-corrected: **1/4 on open** — 22-02 shipped in Equilibrium
Wave 1 (evidence recorded from the shipped code + a fresh 50-test green run). **22-01
landed the same day (2/4)** — the keystone: the Save on the shipping canvas, the
canonical lowering (with `BPNode.runsOn` closing the producer hole), the desk-record
sync wiring, and the Swift-encoded golden fixtures a new pytest feeds into
`linearize()` — proven live (authored → saved → synced → the hub parses it
runnable). **22-03 followed the same day (3/4)** — the web desk is the second
producer of the one wire. **22-04 closed the phase (4/4)** — the cross-surface run
proven on real metal, the crown test locked, the rider staged. **Every build story
in the six-phase Equilibrium program is now done; the owner's one couch session
(18-06 + 19-07 + the 21/22/23 riders) closes all five open phases on glass.**
