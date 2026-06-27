# Phase 22 — The graph travels (the Workbench bridge)

**Status:** planned — independent of the iPad-client work; can run in parallel with 18/19.
Stories detailed on open.

**Last updated:** 2026-06-27 (**authored** from the parity audit, theme 5.)

## Why this phase exists

Audit theme 5: *the Workbench graph is authored richly on iPad but cannot travel.* The full
Blueprint interpreter (two wires, control flow, typed edges, event stream) runs on device, but:

- **It never serializes.** `GraphCanvasView` is disconnected from `graph_json`: no Save
  button, no serializer; `startRun()` runs against demo text and never persists. An authored
  graph runs once and is lost.
- **The hub runs linear-only.** `workflow_graph.py:linearize` parses one straight pipeline and
  **refuses** branch/loop/fan-out; the linearizer also drops per-node `failure_policy` and
  `runs_on` (`GraphNode` holds only id/kind/payload) though the Swift model carries them.
- **Web cannot author a graph.** `submitWorkflow` hardcodes `graph_json: {}` yet
  `primitives.ts` marks workflow `authorable: true`; `primitives.ts:153` even type-drifts
  (`graphJson?: string` vs the object wire).

The graph bridge is the keystone the cross-surface workflow story waits on.

## The load-bearing design call

**One `graph_json` wire shape, authored anywhere, run honestly.** Lower the iPad Blueprint to
the canonical snake_case `graph_json`, persist it as a `WorkflowRecord`, and sync it via
`DeskSync` — so a graph authored on the iPad survives, travels, and round-trips against
`workflow_graph.linearize`. The hub either *honors* control flow / `failure_policy` / `runs_on`
or **documents the omission honestly** (the audit filed these as low-severity desktop
footnotes; this phase promotes them to first-class contract findings per the EQUILIBRIUM rule
that desktop is audited, not assumed). Web ships a minimal linear-chain builder emitting the
same shape, or scopes its claim honestly with a "graphed on iPad" affordance.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HSM-22-01 | The `graph_json` serializer on iPad (+ Save + `DeskSync`) — **leads** | todo |
| HSM-22-02 | The hub honors the graph (control flow / `failure_policy` / `runs_on`, or honest omission) | todo |
| HSM-22-03 | Web authors a linear graph (or honest scope) + the `primitives.ts` type fix | todo |
| HSM-22-04 | The cross-surface proof + docs | todo |

## Where we are

Not started. **22-01 leads** (without serialization, nothing travels). 22-02 is the desktop
contract re-audit the program promised — the linearizer dropping `failure_policy`/`runs_on` is
a real cross-surface hole, not a footnote. Round-trip the serializer against
`workflow_graph.linearize` as the conformance test.
