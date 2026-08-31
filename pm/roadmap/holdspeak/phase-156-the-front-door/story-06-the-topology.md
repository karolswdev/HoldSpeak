# HS-156-06 - The topology: this Mac, your nodes, and the map that runs the desk

- **Project:** holdspeak
- **Phase:** 156
- **Status:** backlog
- **Depends on:** HS-156-03, HS-156-04
- **Unblocks:** HS-156-07
- **Owner:** unassigned

## Problem

The owner's real setup is a small mesh — this Mac (MLX, local models)
plus the `.43` home-lab server — and the advanced layer should show it
as one: a map with "this Mac" at home, nodes around it, and jobs
visibly flowing to where they run. Owner, verbatim: "I feel like I
need a visual topography editor almost… 'this PC/(Mac)' is displayed,
and then we can 'add nodes'. All workbench 2.0+ on steroids, elegance
to the max" (settled design D6).

## Scope

- **In:** `TopologySurface` lands FIRST as a library component under `surface/graph/` (the council contract: DOM nodes / SVG edges, bounded pan, keyboard pan-select-repoint, inspector + add-node slots, presentation only) with its own contract tests and gallery shot sheet; THEN the topology map as the advanced layer's opening view
  (the table view stays one toggle away): **this Mac** as the home
  node showing its runtimes (MLX, local llama.cpp) and downloaded
  models; one node per connected endpoint (the `.43` server with its
  model name), hosted connection, and paired device; the seven job
  groups drawn as flows from the desk to their serving node. **Add
  node** opens the EXISTING connect grammar in-world (define-endpoint /
  connect-hosted / paired device — no new authority, no modal);
  selecting a node shows its models + the jobs it serves and re-points
  a flow through the existing assignments editor in place. Node health
  (reachable / unreachable / downloading) rides the existing status
  facts. Desk tokens, the workbench node-graph visual lineage, pan
  inside the map container (the page never scrolls sideways), 1440
  beautiful and 393 honest, keyboard reachable.
- **Out:** network-wide scanning (recorded), mesh execution changes,
  editing node internals beyond what the existing surfaces offer.

## Acceptance criteria

- [ ] vitest: the map renders home + endpoint nodes from the real wire shapes; flows match the assignments summary; add-node drives the existing connect calls (spies); selecting + re-pointing a flow posts the existing editor/set shapes; unreachable node shows its state and its ONE action.
- [ ] Glass 1440 + 393 on a real hub seeded owner-shaped (an explicit LAN endpoint + local models): the map shows this Mac + the LAN node with true model names, flows match GET /api/inference/assignments, add-node round-trips a second endpoint; zero horizontal page overflow (the map pans). Shots both widths.
- [ ] The no-parallel-authority fence: the map's writes are exactly the existing service calls (a test enumerates them).

## Test plan

- **Unit:** vitest `topologyMap.test.tsx`; a wire-shape test if a thin `GET /api/front-door/topology` aggregator is added (aggregation only — no new facts).
- **Integration:** glass legs `topology`, `topology-add-node` in the 156 glass file.
- **Manual / device:** story 07 (the owner's real mesh is the walk).

## Notes / open questions

- OWNER: "the vis is not only viz, it's also a configuration
  interface… cohesive with the style, the component library." Both are
  acceptance-level: every map gesture performs the real operation, and
  the map is composed from the EXISTING component library/tokens — a
  vitest asserts no new one-off styled primitives where a library
  component exists.

- Elegance is the requirement, not decoration: the map must read at a glance — home node anchored, flows legible, no cable spaghetti at seven groups (bundle flows to the same node).
