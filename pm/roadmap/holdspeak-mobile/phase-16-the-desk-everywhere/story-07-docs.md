# HSM-16-07 — Docs catch-up (mesh + DeskObject across surfaces)

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** done (2026-07-05 — entry points caught up to the shipped phase; see
  `evidence-story-07.md`. Written before the 16-06 walk by design: the docs describe what
  is code-true and test-locked today; the walk verifies feel, not shape)
- **Depends on:** HSM-16-01..06 (documents what shipped).
- **Owner:** agent (Fable)

## Problem

Per the standing lesson, feature work must touch the **entry-point** docs, not just the phase files
(see [[project_phase64_docs_catch_up]]). After this phase, the Desk is a cross-surface, syncing mesh
citizen — the architecture docs and the DeskObject convention must say so.

## Scope

- **In:**
  - Extend `docs/ARCHITECTURE.md` (or its mesh diagram) to show the organization layer flowing
    desktop ↔ iPad ↔ web, distinct from content sync.
  - Reference the **DeskObject convention** ([[story-20-the-desk-object-model]]) from the web +
    desktop-facing docs, so the one-convention framing is discoverable from the entry points.
  - Note the content / organization / layout taxonomy and the "desktop is canonical, layout is local"
    rule where a reader would look for it.
- **Out:** new diagrams beyond the mesh/organization additions; marketing copy.

## Acceptance criteria

- [x] `docs/ARCHITECTURE.md` reflects organization sync across the three surfaces (new
      "The desk across surfaces" section + a mermaid diagram of what flows vs what stays;
      the model manifest's no-binary rule stated).
- [x] The DeskObject convention is linked from at least one entry-point doc
      (ARCHITECTURE.md links `THE_PRIMITIVE_FRAMEWORK.md` as the one contract).
- [x] The taxonomy (content / organization / capability / layout) + the canonical-hub +
      layout-is-local rules documented in the same section; `WEB_DESK.md` gained the
      "Rope things together and Ask AI" walkthrough and caught up to the recipe rename
      (chips, rail, editor); README's Desk section names the lasso arc. Doc drift guard
      18/18, mermaid render guard 2/2, voice rules honoured (no dashes, no roadmap
      vocabulary, canonical names).

## Test plan

- The doc guards / mermaid render guard pass (`tests/e2e/test_mermaid_renders.py` if a diagram
  changes); links resolve; the voice guard is green.
