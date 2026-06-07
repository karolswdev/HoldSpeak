# HS-47-01 — Concept & naming reconciliation (the model)

- **Project:** holdspeak
- **Phase:** 47
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HS-47-02, HS-47-03, HS-47-04, HS-47-05
- **Owner:** unassigned

## Problem
`/dictation` presents two adjacent, jargon-named tabs — **"Project KB"** (the
`kb:` map in `.holdspeak/project.yaml`, substituted deterministically by the
`kb-enricher` stage) and **"Project Context"** (the `.hs/` Markdown folder, used by
the optional `project-rewriter` LLM stage) — with no stated relationship and no
plain-language model. They are *different mechanisms* a syllable apart; even the
Phase-46 docs pass conflated them. Before any surface can explain the feature, the
project needs **one settled model**: what each part is, how they relate, and what
they're called.

## Scope
- **In:**
  - A short **concept decision** (under this phase folder or `docs/internal/`): the
    canonical mental model — e.g. "**Project knowledge** has two parts: **facts**
    (the `project.yaml` KB → exact values stamped into templates, no LLM) and
    **context** (the `.hs/` files → guidance the rewrite LLM reads)" — with the
    naming decision and rationale, and an explicit on-disk-rename decision (default:
    keep `.holdspeak/project.yaml` + `.hs/`, change presentation only).
  - **Apply the naming/label changes** in the UI (`/dictation` tab labels +
    section headers + ledes) so the two parts read as one coherent capability with
    a stated relationship — low-risk text/label changes only in this story.
  - A glossary/source-of-truth update (extend the corrected `DOCS_STYLE.md` entry)
    so UI and docs stay in lockstep.
- **Out:** the explainer/empty-state UI (HS-47-02), the guided flow (HS-47-03),
  pipeline behavior. This story decides + labels; later stories build the surfaces.

## Acceptance criteria
- [ ] A recorded decision states the canonical model, the names, and the
      on-disk-rename call (with rationale).
- [ ] The `/dictation` labels/headers/ledes reflect the settled model — the two
      tabs no longer read as unrelated jargon; their relationship is stated.
- [ ] UI labels and the `DOCS_STYLE.md` glossary agree; no surface implies the KB
      does what context does or vice-versa.
- [ ] Behavior unchanged (labels/copy only); page-content tests + pipeline tests
      green.

## Test plan
- Unit: `uv run pytest -q -k "dictation or doc_drift or link"`; `(cd web && npm run build)`.
- Manual: open `/dictation` → the two tabs read as one capability with a clear
  what/relationship; a newcomer can tell facts from context.

## Notes / open questions
- Lead candidate model: **"Project knowledge" = Facts (KB) + Context (`.hs/`)**;
  decide whether to rename the tabs to that or keep "Project KB"/"Project Context"
  with strong framing. Don't bikeshed — one decision, recorded, move on.
- Keep on-disk names unless a rename clearly earns its migration cost.
