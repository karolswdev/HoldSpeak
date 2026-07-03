# Phase 79 — Backend Decomposition II

**Status:** in-progress (opened 2026-07-03, owner-picked: "Let's do the backend decomp").

**Last updated:** 2026-07-03 (scaffolded; survey corrected the handover's target list —
`routes/meetings.py` was already split by Phase 72; today's three are `db/activity.py`
1,596 / `routes/system.py` 1,299 / `routes/primitives.py` 1,294. `db/core.py` 1,266 is
deliberately out: schema DDL + migrations, snapshot-pinned, named watch item.)

## Why this phase exists

The desk-era handover's candidate 2. Three backend monoliths absorb every feature that
touches their concern (activity since Phase 53; system routes since Phase 26; primitives
since the framework merge). The Phase-63 discipline applies verbatim: carve along concern
seams, bodies move verbatim, tests unmodified (patch-target paths excepted and listed),
guard-locked so nothing regrows.

## Stories

| ID | Title | Status |
|----|-------|--------|
| HS-79-01 | `db/activity.py` → the activity package (concern mixins) | **done** ([evidence](./evidence-story-01.md): 1,596 → six mixins, largest 406; zero body drift; tests unmodified, 2407 + 685 green) |
| HS-79-02 | `routes/system.py` → the system package (five routers) | todo |
| HS-79-03 | `routes/primitives.py` → the primitives package (per family + shared run helpers) | todo |
| HS-79-04 | The density guard locks the new shapes | todo |
| HS-79-05 | The docs story (internal backend map) | todo |
| HS-79-06 | Closeout (full suite + web build + swift test + manifest stability + final-summary) | todo |

## Where we are

**01 done** (the activity package). The carve order continues 02 → 03 (largest first; all three independent), then
the guard, docs, closeout. One PR on `phase-79-backend-decomposition-ii`, merged on
conclusion-checked green.

## Carried context

- The API-surface manifest records `module` per route: 02/03 regenerate it in the same
  commit; the accepted diff class is module fields only.
- Patch targets move with code (the Phase-63 production lesson) — grep tests for every
  moved module-level name before a done-flip.
- Public constructors stay put: package `__init__` composes and re-exports
  (`build_system_router`, `build_primitives_router`, `ActivityRepository`).
