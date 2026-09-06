# HS-176-08 — The close

- **Project:** holdspeak
- **Phase:** 176
- **Status:** done
- **Depends on:** HS-176-07
- **Unblocks:** Phase 177
- **Owner:** unassigned

## Problem

Phase 176 must close cleanly: all exit criteria checked, the full suite
green, counsel pass, the final summary written, the PR opened, and the
merge on the owner's word.

## Scope

- In:
  - The full suite run (`HOME=$(mktemp -d) uv run pytest -q
    --ignore=tests/e2e/test_metal.py -n auto`); zero branch-new
    failures.
  - The web baseline check (`uv run python
    scripts/check_web_baseline.py --run`); zero branch-new.
  - The UX canon ratchet green (ceiling per rule + per face).
  - Counsel reads the final tree.
  - The final summary written (phase-176-the-speak-loop/final-summary.md).
  - The PR opened; the owner's word to merge.
  - The hygiene lane items this phase's tree touches are paid.
- Out:
  - Implementation work (that is stories 02-05).
  - Post-merge follow-ups (filed as new stories if material).

## Acceptance criteria

- [ ] The full suite passes with zero branch-new failures.
- [ ] The web baseline check passes with zero branch-new.
- [ ] The UX canon ratchet is green.
- [ ] Counsel reads the final tree and passes.
- [ ] The final summary is written.
- [ ] The PR is opened and passes CI.
- [ ] The owner's word to merge (Article IX.4).

## Test plan

- Unit: the full suite.
- Integration: CI.
- Manual: counsel read; owner's word.

## Notes / open questions

- None.
