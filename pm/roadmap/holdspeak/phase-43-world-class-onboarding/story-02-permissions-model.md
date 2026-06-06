# HS-43-02 — Permissions polish + Model picker step

- **Project:** holdspeak
- **Phase:** 43
- **Status:** done (2026-06-06)
- **Depends on:** HS-43-01
- **Unblocks:** HS-43-03

## Problem
The Model step is a placeholder. A newcomer should pick their intelligence level
(Basic / Local / Endpoint) inside the wizard with a live Test, distinct from the
other steps.

## Scope
- In: a selectable model-choice step (big radio-tiles, selected state, the
  `POST /api/setup/runtime-test` Test result, copyable installs); permissions
  step refinements (per-OS guidance, a "grant" deep link where possible).
- Out: new backends.

## Acceptance criteria
- [x] The Model step lets a user choose Basic/Local/Endpoint with a clear selected
      state + a one-click Test result; reuses the HS-42-06 endpoint; persists to config.
- [x] Distinct visual treatment (selection grid); reduced-motion safe; suite green.
