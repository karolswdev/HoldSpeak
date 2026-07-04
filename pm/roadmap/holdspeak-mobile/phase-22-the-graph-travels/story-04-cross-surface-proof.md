# HSM-22-04 — The cross-surface proof + docs

- **Project:** holdspeak-mobile
- **Phase:** 22
- **Status:** todo
- **Depends on:** 22-01 (the producer), 22-02 (the runner, shipped), 22-03 (the web
  leg).
- **Unblocks:** phase closeout.
- **Owner:** unassigned

## Problem

The travel is proven only in fragments: the hub runs a hand-written dict; sync
round-trips a placeholder graph that would not linearize; the iPad cannot ask the hub
to run a workflow at all (`runOnHub` switches only agent/chain,
`DeskDioramaStage.swift:4934`; no `runWorkflow` on the desktop client); and no single
trace shows one authored graph crossing surfaces.

## The design

1. **`runWorkflow` joins the iPad hub path** (`IDesktopClient` + `runOnHub` +
   `PendingHubRun.kind`), surfacing the hub's `steps` + `warning` like agent/chain
   runs — the printed card carries the run's real `artifact_id` (the 18-07 lesson).
2. **The sync fixture upgrades** to a linearizable graph (the 23-04 placeholder shape
   documented as a non-example), and an integration test runs a SYNCED graph: push a
   real graph_json → run via `/api/workflows/{id}/run` → assert the threaded steps.
3. **The live proof:** author on the iPad canvas → Save → sync to a scratch hub →
   run from the iPad (and once from web) → the same steps/warning on both readers.
4. **Docs + the rider:** ARCHITECTURE's pipeline section gains the graph bridge;
   a short rider joins the staged couch session.

## Scope

- **In:** the client route + UI surface, the fixture upgrade + synced-run test, the
  live proof, docs + rider.
- **Out:** hub-side control-flow execution; retry/queue enforcement (documented
  omissions stand).

## Test plan

- `swift test` (client + decode tests) + sim proof against a live scratch hub.
- `uv run pytest -q tests/unit/test_web_routes_sync_primitives.py
  tests/integration/test_primitive_framework_sync.py tests/unit/test_web_routes_primitives.py`.
- Doc drift guard green; the rider staged.
