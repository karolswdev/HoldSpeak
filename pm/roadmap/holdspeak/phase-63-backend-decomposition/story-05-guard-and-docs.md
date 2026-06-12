# HS-63-05 — The backend density guard + docs

- **Project:** holdspeak
- **Phase:** 63
- **Status:** done
- **Depends on:** HS-63-01, HS-63-02, HS-63-03, HS-63-04
- **Unblocks:** HS-63-06
- **Owner:** unassigned

## Problem
Phase 54 proved a carve regrows without a guard (web_runtime came back
294 lines HEAVIER after its Phase-52 slice). The shape must be locked,
and the pattern documented for the next contributor.

## Scope
- **In:** `tests/unit/test_backend_density_guard.py` — scoped budgets
  (the two cores + every `holdspeak/runtime/*.py` and
  `holdspeak/meeting/*.py` module ≤ the shipped-max budget) with
  carve-don't-bump failure messages, proven both ways;
  routes/meetings.py (1,525) recorded as the named watch item in the
  guard's comments. `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md` (the sibling doc) records the pattern
  (the mixin pattern, the concern map, the patch-target rule, a
  add-a-concern walkthrough); CONTRIBUTING pointer; voice guard green.
- **Out:** carving routes/meetings.py (watch item only).

## Acceptance criteria
- [x] The guard fails on a regrown module with a carve-don't-bump
      message, passes on the shipped shape (both proven).
- [x] The docs record the pattern; doc guard green.
- [x] Full suite green.

      See `evidence-story-05.md`.

## Test plan
- The guard slice both ways; the doc guard; the full suite.
