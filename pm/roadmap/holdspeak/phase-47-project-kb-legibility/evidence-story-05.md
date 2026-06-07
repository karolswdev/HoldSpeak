# Evidence — HS-47-05: Docs alignment (both mechanisms, correctly)

**Date:** 2026-06-07. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-47-project-kb-legibility`.

## What shipped

The docs now document both halves of project knowledge correctly and match the new
UI framing. The real (`project.yaml`) facts mechanism, previously undocumented in
the guide, has a full section with a worked example.

### Intelligent Typing guide (`docs/INTELLIGENT_TYPING_GUIDE.md`)

- The intro callout was reframed from "two different things" into the settled
  model: **project knowledge = Facts + Context**, naming the **Project Facts** and
  **Project Context** tabs, and stating the relationship ("facts are exact values
  stamped in; context is guidance a rewrite reads").
- "## 5. Create Project Context" became **"## 5. Set Up Project Knowledge"** with
  two subsections:
  - **Facts (the Project Facts tab):** the `project.yaml` `kb:` map, the
    `{project.kb.<key>}` placeholder, the default `kb-enricher` stage (no LLM), a
    worked `stack` example (`Rails 7 + Postgres 16` stamped into a template), the
    key regex, and a pointer to the `project_facts_context` starter block.
  - **Context (the Project Context tab):** the existing `.hs/` content, now with a
    pointer to the guided "Set up project knowledge" panel (the starter set and the
    coding-agent prompt from HS-47-03).
- The §5 anchor changed to `#5-set-up-project-knowledge`; the only link to it (the
  intro callout, in-file) was updated. No cross-doc links targeted the old anchor
  (only `#11`/`#12` are linked externally, untouched).
- The "Optional: add `project-rewriter` stage" callout now says "stamps in your
  project facts" instead of "injects project KB context".

### Reconciled surfaces

- `docs/README.md` (the index): the Intelligent Typing line now says
  "project-facts enrichment", and a new entry "Project knowledge: facts + context"
  points to the new §5 anchor.
- `docs/DICTATION_COPILOT.md`: "project KB" → "project facts (the `kb:` map)" in
  the fixture list and the mermaid `kb-enricher` node.
- `docs/USER_GUIDE.md`: added a "Project facts" capabilities row (verbatim,
  no LLM) beside the existing "Project context" row.
- `web/src/pages/docs/dictation-runtime.astro`: fixed a double error left from
  HS-47-01 — it called KB enrichment an LLM step. Now: the runtime is for "block
  classification and the optional project-context rewrite", and "Project Facts
  enrichment is deterministic and needs no model." (Bundle rebuilt.)

## Tests run

- `uv run pytest -q -k "doc_drift or link or doc_guard"` → **8 passed, 1 skipped**
  (the dangling-link guard validates the new `#5-set-up-project-knowledge` anchor;
  image-ref + plugin-count guards green).
- Full-suite gate: `uv run pytest -q --ignore=tests/e2e/test_metal.py`
  → **2372 passed, 17 skipped** (exit 0).
- `(cd web && npm run build)` clean; **0** `_built/` tracked.
- Grounded against code: `kb_enricher.py` (`requires_llm = False`, `{project.kb.*}`
  substitution), `project_kb.py` (the `kb:` map + key regex), `project_rewriter.py`
  (the optional LLM stage reading `.hs/`).

## Acceptance criteria

- [x] The guide documents both Facts (`project.yaml`) and Context (`.hs/`)
      correctly, with the right stage + a worked example, matching the UI.
- [x] Index + `DICTATION_COPILOT.md` + `USER_GUIDE.md` + the web doc are
      consistent; no doc conflates the two.
- [x] Doc-drift + dangling-link/image-ref guards green; grounded in live code.
