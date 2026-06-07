# HS-47-06 — Closeout — before/after + dogfood + PR

- **Project:** holdspeak
- **Phase:** 47
- **Status:** done
- **Depends on:** HS-47-01, HS-47-02, HS-47-03, HS-47-04, HS-47-05
- **Owner:** unassigned

## Problem
The phase needs a verified exit: proof that project knowledge is now legible,
inviting, and discoverable — captured as before/after, dogfooded end-to-end, and
merged.

## Scope
- **In:**
  - A **before/after** capture: the old bare two-tab surfaces vs. the new
    explainer + empty states + guided flow + discovery hint (real screenshots via
    the `scripts/screenshot_*.py` pattern).
  - A **dogfood**: fresh temp project → discover → guided flow → working
    project-aware dictation, zero hand-editing (provable without a mic).
  - `final-summary.md`; flip the phase to CLOSED; update the project README +
    phase status per the operating cadence; **open a PR to `main`** and merge when
    CI is green.
- **Out:** new feature work (that's HS-47-01→05).

## Acceptance criteria
- [x] Before/after captured (old bare tabs vs the new explainer + empty states +
      guided panel + nudge) under `docs/assets/screenshots/project-knowledge-*`;
      a repeatable `scripts/screenshot_project_knowledge.py` for the after-state;
      a green dogfood transcript (`scripts/dogfood_project_knowledge.py`).
- [x] Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py` →
      2372 passed, 17 skipped); `npm run build` ✓; 0 `_built/` tracked.
- [x] `final-summary.md` written; phase CLOSED; status docs + roadmap updated; PR
      to `main` opened (and merged when CI green).

## Test plan
- Full suite + the phase dogfood; manual walk of the before/after.

## Notes / open questions
- Mirror the Phase-43/44/45 closeout pattern (dogfood script + before/after evidence
  + final-summary + PR).
