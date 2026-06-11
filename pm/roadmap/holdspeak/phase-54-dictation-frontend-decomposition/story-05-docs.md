# HS-54-05 — Docs: the frontend architecture pattern

- **Project:** holdspeak
- **Phase:** 54
- **Status:** backlog
- **Depends on:** HS-54-03
- **Unblocks:** HS-54-06
- **Owner:** unassigned

## Problem
Phase 54 defines the first frontend decomposition pattern in the codebase (every page
was a monolith before it). An undocumented pattern does not survive contact with the
next phase: the next agent grows `history.astro` the old way, or carves it a second,
incompatible way.

## Scope
- **In:**
  - An internal architecture doc (`docs/internal/ARCHITECTURE_WEB_FRONTEND.md` or the
    natural home in `docs/internal/`) recording: how a page decomposes (section
    partials under `web/src/components/<page>/`, behavior modules under
    `web/src/scripts/<page>/`), the module-seam decision from HS-54-01 (what the
    `?raw` + `new Function()` loader was, what replaced it or why it stays), the
    `<style is:global>` rule for JS-injected DOM with the screenshot-verify
    discipline, the density-guard budgets and what to do when the guard fires, and
    how to add a new section to the dictation cockpit step by step.
  - Name `history.astro` and `index.astro` as the follow-up candidates once the
    pattern is proven (so the next density phase has a paved road).
  - Link from `CONTRIBUTING.md`'s development section.
- **Out:** user-facing docs (nothing user-visible changed); rewriting existing
  internal plans.

## Acceptance criteria
- [ ] The doc exists, matches what actually shipped (verified against the tree, not
      the plan), and is linked from `CONTRIBUTING.md`.
- [ ] A "add a new cockpit section" walkthrough is concrete enough to follow without
      reading this phase's history.
- [ ] The Phase-51 roadmap-vocab guard is untouched and green (internal docs are out
      of its scope; user-facing docs were not modified).

## Test plan
- `uv run pytest -q tests/unit -k "doc"` (the doc guards) plus the full suite
  (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Notes / open questions
- This is an internal doc; roadmap vocabulary is fine here. Keep it about the
  architecture as it exists, not the journey.
