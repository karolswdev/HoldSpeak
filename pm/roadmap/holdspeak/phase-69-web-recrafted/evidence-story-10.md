# Evidence — HS-69-10: Node canvas — foundation

**Date:** 2026-06-30
**Verdict:** done. The `/workbench` node canvas renders the canonical linear
`Workflow` as a draggable, typed node graph on a pannable/zoomable dot grid —
the iPad Workbench's foundation, on the web, pure-vanilla.

## What shipped

- **`web/src/pages/workbench.astro`** — the page shell (AppLayout, `current=
  "workbench"`): the header + preset pills + a Fit button + the canvas viewport
  (`.wb-canvas` with the dot-grid background, `.wb-world` transformed layer, and
  the `<svg>` cable layer). The node/cable/world styles are `is:global` (the
  nodes + cables are JS-rendered).
- **`web/src/scripts/workbench/model.js`** — the `Workflow`-shaped model
  (`{id, name, source, steps, output}`, byte-compatible with the iPad's Codable
  form), three presets, the port-type → web-status-palette map (text→accent /
  findings→ok / signal→info), and `graphFromWorkflow` (the source→steps→output
  chain + edges) with a localStorage layout under the iPad's `hs.workflows.v1`.
- **`web/src/scripts/workbench/canvas.js`** — the pure-vanilla engine: pan
  (pointer-drag the canvas), zoom (wheel, about the cursor, clamped 0.4–2.0),
  node drag (pointer deltas ÷ z, live cable re-layout, layout persisted), the SVG
  bezier cable layer (the iPad's `max(46,|dx|·0.45)` horizontal-tangent cubic),
  and the node-card render (signal-card + glyph chip + typed port dots).
- **Routing:** `/workbench` registered in `holdspeak/web/routes/pages.py`, the
  `TopNav` (under Live, beside Desk) + the `Route` union in both TopNav and
  AppLayout, and `PAGE_ROUTES` in the route pre-flight (so it is swept).

## Proof

- **`screenshots/workbench-default.png`** — the "Meeting digest" workflow:
  Full transcript → Summarize → Extract actions → Output, as signal-card nodes
  with glyph chips, joined by **type-colored cables** (orange text, then a green
  `findings` cable from Extract → Output), typed port dots, source/output
  tinting, on the dot grid. (`4 nodes / 3 cables`.)
- **`screenshots/workbench-dragged.png`** — the "Summarize" node dragged down;
  the bezier cables **follow it live** (smooth horizontal-tangent curves).
- **`screenshots/workbench-triage.png`** — the "Action triage" preset (a switch
  re-renders the graph): Tacked moments → Extract actions → Keep if → LLM call,
  showing all three cable types incl. the **blue `signal`** cable out of Keep-if.
  (`5 nodes`.)
- **Tests:** the route pre-flight now sweeps `/workbench` for zero page errors;
  pre-flight + frontend density guard = **7 passed**. Build green (17 pages).
