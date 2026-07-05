# Evidence — HSM-16-07 (docs catch-up: the desk across surfaces)

**Done 2026-07-05.** The entry points now say what the phase built — the Phase-64 lesson
applied up front, not as a closeout footnote.

## What changed

- **`docs/ARCHITECTURE.md`** — new section "The desk across surfaces": one primitive
  convention rendered three times (links `THE_PRIMITIVE_FRAMEWORK.md` as the contract),
  the four-class sync taxonomy (content / organization / capability / layout) with the
  canonical-hub and layout-never-syncs rules, the model MANIFEST's availability-only
  no-binary rule (naming the three independent assertions), and the Ask atom's
  cross-surface story (grounded runs, keep/bin, one provenance shape, per-run egress).
  Plus one new mermaid diagram (hub ↔ iPad ↔ web: what flows, what stays local).
- **`docs/WEB_DESK.md`** — caught up to the recipe rename (sprites list, create chips
  now five incl. + Recipe / + Workflow, the rail and editor speak "recipes", the editor's
  advanced fields listed) and gained **"Rope things together and Ask AI"**: the lasso,
  the bundle bar, the lens grid, the mic, the runs-on pick, the honest printed badge,
  Keep/Bin semantics, and the cross-surface lineage promise.
- **`README.md`** — the Desk section speaks "recipes" and names the lasso → Ask AI →
  keep/bin arc in one sentence (the entry-point tour stays a tour).

## Verification

- Doc drift guard: `uv run pytest tests/unit/test_doc_drift_guard.py` → **18 passed**
  (dash rule, roadmap-vocabulary rule, AI-vocabulary rule, canonical names, link + image
  resolution all green over the edited files).
- Mermaid render guard: `uv run pytest tests/e2e/test_mermaid_renders.py` → **2 passed**
  (the new diagram renders).

## Deviations

- Written before the 16-06 walk (the story's dependency note says the proof informs the
  docs): everything documented is code-true and test-locked today — the walk verifies
  feel on glass, not the shapes described here. If the walk falsifies a sentence, the fix
  rides the walk's bug list.
