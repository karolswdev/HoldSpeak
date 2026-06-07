# HS-47-05 — Docs alignment (both mechanisms, correctly)

- **Project:** holdspeak
- **Phase:** 47
- **Status:** done
- **Depends on:** HS-47-01
- **Unblocks:** HS-47-06
- **Owner:** unassigned

## Problem
The docs document `.hs/` ("project context") but **never document the real
(project.yaml) KB**, and historically conflated the two (fixed defensively in
Phase 46, but only as a heads-up callout). Once HS-47-01 settles the model and the
UI is reframed, the guides must match — accurately and consistently — or the
docs/product drift reopens the exact confusion this phase exists to close.

## Scope
- **In:**
  - Update the **Intelligent Typing guide** to document **both** mechanisms per the
    HS-47-01 model: the `project.yaml` KB (the `kb:` map → `{project.kb.*}`
    placeholders → the default `kb-enricher` stage) **and** the `.hs/` context (the
    optional `project-rewriter` stage) — each with what it is, when it fires, and a
    worked example, matching the new UI names/framing.
  - Reconcile **`DICTATION_COPILOT.md`** (already accurate on the KB) + the
    **README**/index hooks so every surface tells the same story.
  - Keep the `DOCS_STYLE.md` glossary entry authoritative; add a short "project
    knowledge" map if it helps.
- **Out:** the UI work (HS-47-01→04). Per the standing rule, every phase gets its
  own dedicated docs story — this is it.

## Acceptance criteria
- [x] The Intelligent Typing guide's new "§5. Set Up Project Knowledge" documents
      **both**: Facts (the `project.yaml` `kb:` map → `{project.kb.*}` →
      `kb-enricher`, no LLM, with a worked stack example) and Context (the `.hs/`
      files → optional `project-rewriter`), each with what it is, when it fires,
      and matching the UI tab names (Project Facts / Project Context). The intro
      callout reframes to the "facts + context" model.
- [x] README docs index + `DICTATION_COPILOT.md` + `USER_GUIDE.md` + the
      `dictation-runtime` web doc are consistent with the new framing; no doc
      implies the KB does what context does or vice-versa (also fixed the web doc
      that wrongly called KB enrichment an LLM step).
- [x] Doc-drift + dangling-link/image-ref guards green (8 passed); the new framing
      is grounded in `kb_enricher.py` / `project_kb.py` / `project_rewriter.py`.

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link"`.
- Manual: read the KB + context sections back-to-back; a newcomer can tell them
  apart and knows how to set up each.

## Notes / open questions
- This story exists because Phase 46 proved the conflation is easy to make — treat
  the `kb_enricher.py` / `project_kb.py` / `project_rewriter.py` code as canon.
