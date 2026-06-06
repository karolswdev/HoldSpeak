# HS-43-05 — Settings redesign

- **Project:** holdspeak
- **Phase:** 43
- **Status:** backlog
- **Depends on:** HS-43-01

## Problem
`/settings` is a single-scroll **form dump** — every field at once, no search, no
common/advanced split.

## Scope
- In: a sectioned settings surface (left-nav or grouped sections), **search**,
  **Common vs Advanced** progressive disclosure, inline help, the presence toggle
  (HS-43-04). Same `/api/settings` contract.
- Out: new settings fields.

## Acceptance criteria
- [ ] Settings is sectioned + searchable + progressive (no single form dump);
      save round-trip still works; screenshot; suite green.
