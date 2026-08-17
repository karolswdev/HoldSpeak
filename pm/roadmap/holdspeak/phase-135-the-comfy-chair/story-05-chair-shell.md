# HS-135-05 — The Chair shell

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** HS-135-03
- **Unblocks:** HS-135-06..11
- **Owner:** unassigned

## Problem

The Chair does not exist. L2 (ratified with conditions) defines its
anatomy: capture hero slot, four fixed lanes composed from existing
surfaces via a contract, everything-windows.

## Scope

### In

Per assets/design-laws.md L2 + the counsel conditions verbatim:

- The Chair surface component (desk-era kit only, Signal Workbench
  material, L1 depth grammar): capture hero region (placeholder slot —
  HS-135-11 fills it) + four lane slots in the fixed order.
- The lane composition contract: a lane receives `maxItems` (JS
  default per curated-dozen ruling; NO CSS property), renders Surface
  primitives, exposes header-click and per-item `onOpenInWindow`, an
  optional footer verb slot; no per-lane spinners — the single
  300ms all-lanes-blank fallback renders ONE SurfaceState (counsel
  condition 2).
- Single-instance-per-surface: opening a surface already open FOCUSES
  its window, never duplicates (the counsel's demanded addition —
  implement at the window-opening seam the Chair uses, as the shared
  rule).
- Ember-only on the Chair (no accent-cool on composed lanes — settled
  Q3); accent-gradient nowhere on the shell (hero-only, story 11).
- Tests: lane contract (maxItems bound, open-in-window fires,
  fallback state at 300ms), single-instance focus behavior.

### Out

- Real lane data (stories 07-10); home routing (06); the hero's verbs
  (11); any floor change.

## Acceptance criteria

- [ ] The Chair renders with four ordered lane slots + hero slot,
  composed via the contract, on kit primitives only (no bespoke CSS
  beyond a chair stylesheet using tokens).
- [ ] maxItems enforced; open-twice focuses (tests).
- [ ] All-blank >300ms shows exactly one SurfaceState.

## Test plan

- `cd web && npx vitest run` — new chair suite + touched window seam
  suite.
