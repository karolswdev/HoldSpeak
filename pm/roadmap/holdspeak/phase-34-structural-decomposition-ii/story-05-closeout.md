# HS-34-05 — Phase closeout + final-summary

- **Status:** not-started.

## Goal

Close Phase 34 cleanly: prove the decomposition was behavior-preserving end-to-end
(route table unchanged, full suite green, all four trees ruff-clean) and write the
phase `final-summary.md`.

## Scope

- **Route-table invariant re-verify** — the app's full `(path, method)` set is
  identical to the pre-phase baseline (the shared gate from HS-34-01/02). Keep the
  check committed (a small test, or a recorded before/after diff in the evidence).
- **Line-count accounting** — record the before/after of the four targets and the
  resulting package layouts (like Phase 31's `5481 → container + 5 repos`).
- **Ruff + suite** — `uv run ruff check holdspeak/web/routes/dictation/
  holdspeak/web/routes/activity/ holdspeak/agent_context/ holdspeak/intel/` clean;
  full suite green.
- **`final-summary.md`** — what shipped, the conventions reused (Phase-26 `ctx`
  pattern, Phase-31 re-export), decisions, and state at close; update the project
  README phase row → `done` and refresh the HANDOVER pickup pointer.

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- Route-table diff: zero changes.

## Done when

- [ ] Route table unchanged vs. the pre-phase baseline; all four packages
      ruff-clean; full suite green.
- [ ] `final-summary.md` written; project README phase row = `done`; HANDOVER
      pickup pointer refreshed.
