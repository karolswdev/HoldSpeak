# HS-33-06 — Phase closeout + final-summary

- **Status:** done (2026-06-03). Evidence: [evidence-story-06.md](./evidence-story-06.md).

## Goal

Close Phase 33 cleanly: confirm the OSS-readiness bar is met end-to-end, the docs
are true and navigable, and write the phase `final-summary.md`.

## Scope

- **Link-check sweep** — no broken relative links across `README.md`, `docs/**`,
  and `CONTRIBUTING.md` after the HS-33-03 reorg + HS-33-04 README pass (extend
  the HS-32-06 drift guard or add a focused link-existence test).
- **Doc-truth re-verify** — the HS-32-06 drift guard still green; the new
  `MODELS.md` / README state only true things; the "not released" positioning is
  consistent everywhere.
- **OSS checklist** — LICENSE present, pyproject metadata complete, README badges
  resolve, docs index navigable, assets wired, CHANGELOG/CONTRIBUTING present.
- **`final-summary.md`** — the phase's exit record (what shipped, decisions,
  state), and update the project README phase row → `done`.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- Manual: a clean-clone walkthrough of the README quickstart + docs index.

## Done when

- [x] No broken links; drift guard + doc-truth green.
- [x] OSS checklist satisfied (LICENSE / metadata / README / docs / assets /
      CHANGELOG / CONTRIBUTING).
- [x] `final-summary.md` written; project README phase row = `done`; full suite green.
