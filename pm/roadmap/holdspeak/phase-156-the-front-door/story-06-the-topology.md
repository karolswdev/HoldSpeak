# HS-156-06 - The topology: this Mac, your nodes, and the map that runs the desk

- **Project:** holdspeak
- **Phase:** 156
- **Status:** done
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

## What shipped

**Library component** (`surface/graph/TopologySurface.tsx` + CSS):
DOM nodes over an SVG edge layer; bounded pan (pointer drag + Shift+Arrow);
home-node designation (accent border, star badge); bundled labeled flows
(2 labels inline, 3+ summarized as "A +N"); roving selection (Tab enters,
arrows navigate by nearest-neighbor direction, Home jumps to home node);
inspector + add-node render-prop slots; reduced-motion honored (CSS
`@media (prefers-reduced-motion: reduce)` kills animations); token-only
styling (all colors, spacing, elevations from design-tokens.json); 25
contract tests passing.

Barrel export added to `surface/index.ts`; guard fence extended
(`graph` in PRIVATE_IMPORT_RE, `surface-topology` in LIBRARY_CSS_RE).
Gallery section added to ComponentsCore (3 nodes, 2 bundled flows,
inspector + add-node slots).

**Topology map view** (`TopologyMapView.tsx` + CSS):
The advanced layer's opening view in the Models surface (the Disclosure
fold from story 05 opens onto the map; a Map/Table toggle switches to the
existing Library + Assignments table view). This Mac as the home node
(runtimes, downloaded models), one node per defined endpoint (the owner's
real desk shape: LAN server at 192.168.1.43:8080 with its model name).
The job groups as bundled labeled flows to their serving node. Node health
from existing facts (StateChip: ready/unreachable). Add-node opens the
existing connect grammar in-world via Disclosure (define-endpoint /
connect-hosted -- no modal, no new authority). Selecting a node shows its
models + jobs (inspector slot) and re-points a flow via the existing
assignments editor/set shapes (in place). 11 vitest tests passing.

**Backend** (`GET /api/front-door/topology`): thin aggregation of existing
facts (list_inference_targets + inspect_runtimes + assignment_summary);
no new authority, no new facts. API surface manifest regenerated.

**Glass legs** (`test_topology`, `test_topology_add_node`): real hub seeded
owner-shaped (global assignment + LAN endpoint profile + group assignments
to the LAN endpoint), 1440 + 393, zero horizontal overflow, 10 shots
captured in `assets/story-06-shots/`.

**Council-contract divergence:** Add-node uses Disclosure (in-flow push)
instead of Popover (overlay), because the Popover portal renders outside
the .desk-next scope and the backdrop blocks pointer events. The Disclosure
is more consistent with the codex rule ("Disclosure pushes layout rather
than opening a modal") and works correctly in both the vitest and glass
environments.

**Visual gate FAIL (pass 1) and fixes:**
The first shot sheet failed four items. Fixes applied:

1. **Flows invisible** -- the glass seeding assigned globally to a local
   profile, so all flows self-looped to this_machine (zero-length paths,
   invisible). Fixed: seed 5 group assignments (`thoughts_notes`,
   `writing_dictation`, `meetings`, `agents_tools`, `background`) to the
   LAN endpoint profile so the map draws a real bundled edge with
   "THOUGHTS & NOTES +4" label. Edge styling upgraded: `--accent-tint`
   stroke with 2px dashed line (3px solid when active), flow label chip
   uses `--accent-tint` border + 600-weight 10px text for legibility.

2. **Inspector overlaps Add-node** -- the add-node slot was absolutely
   positioned in the top-right, colliding with the inspector column.
   Fixed: restructured the TopologySurface container into a map-area
   flex row (viewport + inspector) above a toolbar row (add-node).
   The toolbar uses `border-top` separation and never overlaps.

3. **Default framing** -- nodes floated small at 1440; home node was
   half-clipped at 393. Fixed: the offset formula now anchors on the
   home node (center-left at ~30% from the viewport's left edge) instead
   of centering the content bounding box. The home node is fully visible
   at both widths on initial load.

4. **All 10 shots retaken** after fixes; both glass legs green.
