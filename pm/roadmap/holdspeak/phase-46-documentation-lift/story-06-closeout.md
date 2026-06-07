# HS-46-06 — Closeout: before/after + guards + PR

- **Project:** holdspeak
- **Phase:** 46
- **Status:** backlog
- **Depends on:** HS-46-01, HS-46-02, HS-46-03, HS-46-04, HS-46-05
- **Owner:** unassigned

## Problem
Close Phase 46: prove the documentation lift end-to-end, capture the headline
before/after (a spec-sheet README + accreted guides → a hooking README + a
consistent, visual, accurate, navigable docs set), re-assert the invariants,
write the `final-summary.md`, and open the PR to `main`.

## Scope
- **In:**
  - **Before/after** evidence: the README (line count + first-screen snapshot,
    before vs after) and at least one guide (structure + a real screenshot), and
    the docs index (list → map).
  - **Invariant re-assertion:** every graphic preserved; cool facts cross-checked
    true (honesty); pre-release status intact; doc-drift + dangling-link/anchor +
    image-ref guards green; `(cd web && npm run build)` ✓ and **0**
    `holdspeak/static/_built/` tracked; **no source/behavior change** (docs-only
    phase) — the full suite stays green.
  - `final-summary.md` (goal/was-it-met, before/after, per-story recap,
    invariants, verification, handoff); flip the phase to CLOSED; update the
    roadmap README (current-phase + last-updated + the phase-index status).
  - Push the branch + open a PR to `main`; merge (merge commit) when CI is green.
- **Out:** new features / new docs beyond reconciling 01–05.

## Acceptance criteria
- [ ] Before/after captured for the README + a guide + the index.
- [ ] Invariants re-asserted: graphics kept; honesty (cool facts true,
      pre-release intact); doc-drift + link + image guards green; `npm run build`
      ✓; 0 `_built/`; full suite green (docs-only — no regressions).
- [ ] `final-summary.md` written; phase flipped CLOSED; roadmap README updated.
- [ ] PR to `main` opened; merged when CI green.

## Test plan
- Unit: `uv run pytest -q --ignore=tests/e2e/test_metal.py` (full suite stays
  green) + `-k "doc_drift or link"`.
- Manual: review the README + index before/after; confirm PR CI checks pass.

## Notes / open questions
- Keep the before/after honest — show the real prior README (the 205-line
  spec-sheet) next to the new hook so the lift is legible.
