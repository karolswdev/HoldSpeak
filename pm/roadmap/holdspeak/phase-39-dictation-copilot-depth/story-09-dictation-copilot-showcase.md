# HS-39-09 — Dictation copilot showcase (all features + public doc)

- **Project:** holdspeak
- **Phase:** 39
- **Status:** done
- **Depends on:** HS-39-01, HS-39-02, HS-39-03, HS-39-08
- **Unblocks:** HS-39-06 (the docs story can build on / cross-link this)
- **Owner:** unassigned

## Problem

HS-39-08 proved the multi-pass rewrite against a real endpoint, but the other
two depth features (correction memory, model-assisted target) were only shown
firing in *unit* tests, and there was **no user-facing doc** showing the copilot
off. Added mid-phase on direct user request: grow the demo so **all four depth
features fire in one real run**, and write a public **showcase doc with a
diagram** of exactly what happens.

## Scope

- In:
  - Grow `scripts/dictation_enrichment_demo.py` to
    `stages=["intent-router", "kb-enricher", "project-rewriter"]` with:
    ① `rewrite_passes=2`, ② a seeded intent correction +
    `corrections_enabled`, ③ `target_detect_llm_enabled` over an empty window
    signal, ④ a project block + KB so the kb-enricher injects. Add a "Features
    that fired" panel that reports each feature's concrete effect (incl. the
    honest case where the raw classify fails and the correction rescues routing).
  - Fixture: `.holdspeak/blocks.yaml` (a block taxonomy) + `.holdspeak/project.yaml`
    (a KB).
  - Strengthen `tests/e2e/test_dictation_enrichment_e2e.py` to assert **each**
    feature fired (`passes_run`, `correction_nudge`, `kb_applied_block`,
    `model_assisted_fired` + `source == "llm"`).
  - New **`docs/DICTATION_COPILOT.md`** — a public showcase: the real
    before/after, a feature-by-feature table, **two Mermaid diagrams** (the
    pipeline flow + the target-detection decision), the config to turn it on,
    and how to run the demo. Linked from `docs/README.md`,
    `docs/INTELLIGENT_TYPING_GUIDE.md`, and the root README.
- Out:
  - New product behavior — this is a demo/test/doc story; no `holdspeak/**`
    runtime change.
  - The comprehensive knob-by-knob reference (that's HS-39-06; this is a
    showcase that HS-39-06 will cross-link).

## Acceptance criteria

- [x] The demo fires all four features in one run; the panel reports each. —
      `scripts/dictation_enrichment_demo.py`, capture in
      `evidence/dictation_enrichment_demo.txt`.
- [x] The e2e asserts each feature fired and **passes live on `.43`** —
      `1 passed in 18.77s` (`passes_run==2`, `correction_nudge==agent_task_buildout`,
      `kb_applied_block==agent_task_buildout`, `model_assisted_fired`,
      `target_final_source=="llm"`).
- [x] `docs/DICTATION_COPILOT.md` exists with the real before/after, a feature
      table, **two valid Mermaid diagrams**, the enabling config, and the demo
      command; linked from the docs index + Intelligent Typing guide + root README.
- [x] Doc-drift guard + live-doc link-check green; hermetic suite unaffected
      (`2167 passed, 16 skipped`); touched files ruff-clean.

## Test plan

- Real e2e: `HOLDSPEAK_DICTATION_E2E_BASE_URL=… HOLDSPEAK_DICTATION_E2E_MODEL=… uv run pytest -q tests/e2e/test_dictation_enrichment_e2e.py` → `1 passed`.
- Doc guards: `uv run pytest -q -k "doc_drift or dangling or no_live_doc or link"` → green.
- Hermetic: `uv run pytest -q --ignore=tests/e2e/test_metal.py` → e2e skips.
- Mermaid: syntax reviewed (escaped `<`/`&`, quoted labels, `-.->|…|` edges);
  GitHub renders Mermaid client-side. Headless `mermaid.parse` needs a
  DOM/DOMPurify not present in `web/node_modules`, so a CLI render wasn't run —
  not a grammar issue.

## Notes / open questions

- The classify-fails-but-correction-rescues case is a *feature*, not a flaw of
  the demo: the openai-compatible runtime isn't constrained-decoded, so the raw
  LLM classify is unreliable — and HS-39-02's correction memory makes routing
  robust regardless. The panel says so plainly.
- Added mid-phase per user request; phase grew 8→9. HS-39-07 closeout remains
  the finale.
