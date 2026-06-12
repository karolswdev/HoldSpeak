# Evidence — HS-63-05: The backend density guard + docs

**Date:** 2026-06-12
**Verdict:** done. The shape is locked by 5 guard tests and documented for
the next contributor.

## What shipped

- `tests/unit/test_backend_density_guard.py` (5 tests): the runtime core
  ≤650 (shipped 555), the session core ≤850 (shipped 795), every module
  in `holdspeak/runtime/` and `holdspeak/meeting_session/` ≤600 (largest
  shipped: meeting_glue 552) — each failure message says **carve, don't
  bump** and names where the new mixin goes; proven both ways (the
  fires-on-a-regrown-file self-test); `routes/meetings.py` (1,525)
  recorded as the named watch item in the guard's docstring, deliberately
  NOT guarded (a different shape; its growth earns its own phase, not a
  silent budget).
- `docs/internal/ARCHITECTURE_BACKEND_RUNTIME.md`: the backend twin doc —
  the why (web_runtime regrew 294 lines after its Phase-52 slice), the
  full concern map for both packages, the five rules the pattern lives by
  (mixins-receive-via-self, **patch targets live where the lookup
  happens** with this phase's two hard-way stories, no unused imports in
  mixins, the relative-import-depth trap, carve-don't-bump), and the
  add-a-concern walkthrough.
- `CONTRIBUTING.md` points to it beside the frontend twin.

## Proof

- The guard slice: 5 passed, including the both-ways self-test.
- Full suite: **2773 passed, 17 skipped** (+5 = the guard).
- Docs are internal (`docs/internal/`), outside the voice-guard corpus by
  design; the CONTRIBUTING touch is prose-clean regardless.
