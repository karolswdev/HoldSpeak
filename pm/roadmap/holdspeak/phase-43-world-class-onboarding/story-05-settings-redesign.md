# HS-43-05 — Settings redesign

- **Project:** holdspeak
- **Phase:** 43
- **Status:** done (2026-06-06)
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
- [x] Settings is sectioned + searchable + progressive (Common/Advanced) — no
      single form dump; save round-trip proven live (save → disk); the config-
      backed presence toggle lives in Settings; screenshots; suite green.
