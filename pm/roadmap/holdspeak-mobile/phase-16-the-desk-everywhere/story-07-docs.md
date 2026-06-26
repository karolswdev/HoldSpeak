# HSM-16-07 — Docs catch-up (mesh + DeskObject across surfaces)

- **Project:** holdspeak-mobile
- **Phase:** 16
- **Status:** todo
- **Depends on:** HSM-16-01..06 (documents what shipped).
- **Owner:** unassigned

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

- [ ] `docs/ARCHITECTURE.md` reflects organization sync across the three surfaces.
- [ ] The DeskObject convention is linked from at least one entry-point doc.
- [ ] The taxonomy + canonical-hub rule are documented where they belong; doc/voice guards pass.

## Test plan

- The doc guards / mermaid render guard pass (`tests/e2e/test_mermaid_renders.py` if a diagram
  changes); links resolve; the voice guard is green.
