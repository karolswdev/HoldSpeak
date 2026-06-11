# HS-54-04 — The density guard

- **Project:** holdspeak
- **Phase:** 54
- **Status:** done
- **Depends on:** HS-54-03
- **Unblocks:** HS-54-06
- **Owner:** unassigned

## Problem
The density invariant has been a soft rule since Phase 48 ("factor as you go") and it
lost every round: Phases 40, 45, 47, 48, and 53 each grew the dictation page. Without a
mechanical lock, the paydown this phase ships erodes one feature at a time, exactly the
way it accumulated.

## Scope
- **In:**
  - A unit test (the doc-drift-guard pattern: `tests/unit/test_doc_drift_guard.py` is
    the precedent) that locks the post-carve budgets: no file under
    `web/src/components/dictation/` or `web/src/scripts/dictation/` over the shipped
    per-file budget (~600 lines), and `web/src/pages/dictation.astro` under its
    post-carve budget (~300 lines). Budgets are constants with a comment telling a
    future agent what to do when the guard fires (carve, don't bump).
  - Before/after metrics recorded in evidence: 6,101 lines across 2 files → N lines
    across M files, largest file size.
- **Out:** guarding the other pages (they have not been carved; guarding them now
  would either fail or need budgets so loose they are meaningless — noted as
  follow-up for the phase that carves them).

## Acceptance criteria
- [x] The guard test exists, is in the default suite (no marker gymnastics), and
      passes on the carved tree. (`tests/unit/test_frontend_density_guard.py`,
      5 tests incl. a non-vacuity sanity check; budgets: page ≤300, entry ≤50,
      components/modules ≤600.)
- [x] Proven both ways: temporarily exceeding a budget makes it fail with an
      actionable message; reverting makes it pass (shown in evidence, not committed).
- [x] Before/after metrics recorded in the evidence file. (6,101 lines / largest
      3,134 → largest 576; full table in `evidence-story-04.md` §3.)

## Test plan
- `uv run pytest -q tests/unit -k "density"` plus the full suite
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Notes / open questions
- Line counts are a blunt instrument; that is fine. The guard's job is to force the
  conversation ("this file needs a carve") at commit time, not to measure quality.
