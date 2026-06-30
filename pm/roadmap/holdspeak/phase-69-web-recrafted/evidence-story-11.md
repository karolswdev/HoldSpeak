# Evidence — HS-69-11: Node canvas — wiring + inspector

**Date:** 2026-06-30
**Verdict:** done. The `/workbench` canvas gains free port wiring (with type
validation), an inspector drawer, and a palette — completing the iPad Workbench
on the web.

## What shipped

- **Port wiring** (`web/src/scripts/workbench/canvas.js`): `wirePort` — a
  `pointerdown` on an output port starts a live dashed cable that follows the
  cursor; hovering an input port highlights it **green** (compatible) or
  **danger** (incompatible) via `portsCompatible(outType, inType)` (the matching
  data-type rule, `model.js`); a valid `pointerup` commits a new typed cable
  (`custom: true`), persisted to the iPad's `hs.workflows.v1` key.
- **The inspector** (`web/src/pages/workbench.astro` drawer + `updatePrompt`):
  tapping a node opens a premium right-drawer (the HS-69-05 sheet idiom — grab
  handle, glyph chip) showing the in/out **type chips** (web-palette colored) and
  an editable **Prompt** field; edits call `api.updatePrompt`, updating the node's
  subtitle live and persisting (source/output nodes are read-only).
- **The palette** (`addNode`): "ADD" chips for every step kind drop a free node
  near the view; it is immediately wirable and selected into the inspector.
- **A real bug fixed:** the canvas pan handler called `setPointerCapture` on
  every `pointerdown`, stealing clicks from the palette + inspector (they are
  inside the viewport). It now skips pointerdowns on `.wb-palette / .wb-inspector
  / .wb-node` so their own captures win.

## Proof

`scripts/screenshot_phase69_workbench_wiring.py` (real server):
- **`screenshots/workbench-inspector.png`** — the inspector drawer on the
  "Summarize" node: the pencil glyph chip, in·text / out·text type chips, the
  Prompt field ("in three crisp bullets"), and the edit reflected live on the
  node's subtitle.
- **`screenshots/workbench-wiring-live.png`** — a live dashed cable dragged from
  the source output toward the Extract-actions input, the **target port glowing
  green** (the compatibility highlight).
- **`screenshots/workbench-wired.png`** — the committed new cable
  (`cables: 3 → 4`).
- **`screenshots/workbench-added-node.png`** — a palette-added "Rewrite" node
  (`nodes: 4 → 5`).
- **Tests:** route pre-flight (zero page errors on `/workbench`) + frontend
  density guard = **7 passed**. Build green.
