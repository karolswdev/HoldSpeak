# HS-47-05 — Docs alignment (both mechanisms, correctly)

- **Project:** holdspeak
- **Phase:** 47
- **Status:** backlog
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
- [ ] The guide documents **both** the KB (`project.yaml`) and the context (`.hs/`)
      correctly, with the right stage for each and a worked example, matching the UI.
- [ ] README/index + `DICTATION_COPILOT.md` are consistent with the new framing; no
      doc implies the KB does what context does or vice-versa.
- [ ] Doc-drift + dangling-link/image-ref guards green; the new framing is checked
      against live code (the standing doc-truth rule).

## Test plan
- Unit: `uv run pytest -q -k "doc_drift or link"`.
- Manual: read the KB + context sections back-to-back; a newcomer can tell them
  apart and knows how to set up each.

## Notes / open questions
- This story exists because Phase 46 proved the conflation is easy to make — treat
  the `kb_enricher.py` / `project_kb.py` / `project_rewriter.py` code as canon.
