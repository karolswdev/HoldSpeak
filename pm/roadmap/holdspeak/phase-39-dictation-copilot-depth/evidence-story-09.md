# Evidence — HS-39-09 — Dictation copilot showcase (all features + public doc)

- **Shipped:** 2026-06-05
- **Commit:** this commit on branch `phase-39/hs-39-01-multi-pass-rewriting`
- **Owner:** unassigned

## Files touched

- `scripts/dictation_enrichment_demo.py` — all-features run (intent-router +
  kb-enricher + multi-pass project-rewriter), seeded intent correction,
  model-assisted target over an empty window signal; new "Features that fired"
  panel + `router_classify_failed` rescue note.
- `tests/e2e/test_dictation_enrichment_e2e.py` — asserts each feature fired.
- `tests/fixtures/dictation_demo_project/.holdspeak/blocks.yaml` (**new**),
  `.../.holdspeak/project.yaml` (**new**) — block taxonomy + KB.
- `docs/DICTATION_COPILOT.md` (**new**) — the showcase + two Mermaid diagrams.
- `docs/README.md`, `docs/INTELLIGENT_TYPING_GUIDE.md`, root `README.md` —
  links to the showcase.
- `pm/roadmap/.../evidence/dictation_enrichment_demo.txt` — refreshed capture.

## Verification artifacts

- Real `.43` e2e (all features asserted):
  `HOLDSPEAK_DICTATION_E2E_BASE_URL=http://192.168.1.43:8080/v1 HOLDSPEAK_DICTATION_E2E_MODEL=Qwen3.5-9B-UD-Q6_K_XL.gguf uv run pytest -q tests/e2e/test_dictation_enrichment_e2e.py`
  → `1 passed in 18.77s`.
- Live demo panel (from the run): `① multi-pass 2 passes (5202ms + 5615ms)` ·
  `② correction memory → agent_task_buildout@0.85 corrected ✓ (classifier
  missed; rescued by your correction)` · `③ model-assisted: window none →
  unknown@0.00 (<0.80) → claude_code@0.70 src=llm ✓ fired` · `④ kb-enricher →
  injected project facts`. See `evidence/dictation_enrichment_demo.txt`.
- Doc guards: `uv run pytest -q -k "doc_drift or dangling or no_live_doc or link"`
  → `4 passed, 1 skipped`.
- Hermetic suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → `2167 passed, 16 skipped`.
- Ruff (`scripts/…` + e2e) → `All checks passed!`.
- Mermaid: 2 blocks; syntax reviewed (escaped `<`→`&lt;`, `&`→`&amp;`, quoted
  labels, `-.->|…|` edge labels). A headless `mermaid.parse` (v11.15.0 in
  `web/node_modules`) could not run — it requires a DOM/DOMPurify absent here —
  so a CLI render wasn't performed; GitHub renders Mermaid client-side.

## Acceptance criteria — re-checked

- [x] All four features fire in one run, panel reports each — capture +
      `_features_panel`.
- [x] e2e asserts each + passes live on `.43` (18.77s).
- [x] `docs/DICTATION_COPILOT.md` with before/after + feature table + 2 Mermaid
      diagrams + config + demo command; linked 3 ways; guards green.
- [x] Hermetic suite unaffected; ruff clean.

## Deviations from plan

- Added mid-phase (user request); phase grew 8→9. Split from HS-39-08 (rather
  than amending its shipped evidence) to honor the "evidence ships with the
  story's done-flip" PMO rule.

## Follow-ups

- HS-39-06 (the dedicated docs story) should cross-link this showcase and add
  the comprehensive knob-by-knob reference in `INTELLIGENT_TYPING_GUIDE.md`.
