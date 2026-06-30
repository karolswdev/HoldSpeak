# HS-69-10 — Node canvas — foundation

- **Status:** done
- **Priority:** HIGH (heavy)
- **Depends on:** HS-68-03 technical design; owner confirm (full canvas)
- **Catalog pattern(s):** §2 Workbench
- **Evidence:** [evidence-story-10.md](./evidence-story-10.md)

## Goal

A pannable/zoomable dot-grid canvas with typed, draggable Signal node cards —
the first half of the iPad Workbench on the web. Owner decision: the **full node
canvas** (not a lighter pipeline view).

## Scope

- Pure-vanilla per the Phase-68 design: SVG bezier cables + HTML signal-card
  nodes in ONE transformed world layer (no graph lib).
- The model is the canonical linear `Workflow` shape (`source → steps → output`),
  byte-compatible with the iPad's Codable form.
- Pan + zoom (about the cursor) + node drag (with live cable re-layout). The dot
  grid is a viewport CSS background synced to pan/zoom.
- Wiring + inspector are HS-69-11.

## Proof required

Pannable/zoomable dot-grid canvas + draggable Signal node cards; screenshots of
nodes placed/dragged.

## Done

Shipped and screenshot-proven. A new `/workbench` route (registered in pages.py,
TopNav, AppLayout, and the route pre-flight) renders the `Workflow` as a node
chain of signal-card nodes with glyph chips, joined by type-colored bezier cables
(orange text / green findings / blue signal — the web-wins port palette), on a
pannable/zoomable dot grid. Dragging a node re-lays its cables live; preset
switching re-renders the graph. The cable math is the iPad's exact
horizontal-tangent cubic. Route pre-flight (zero page errors on `/workbench`) +
density guard = 7 passed.
