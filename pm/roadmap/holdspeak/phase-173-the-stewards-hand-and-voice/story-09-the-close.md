# HS-173-09 — The close

- **Project:** holdspeak
- **Phase:** 173
- **Status:** done
- **Depends on:** HS-173-08
- **Unblocks:** Phase 174
- **Owner:** unassigned

## Problem

Phase 173 must close cleanly: all exit criteria checked, the full suite
green, counsel pass (especially on the first external write), the final
summary written, the PR opened, and the merge on the owner's word.

## Scope

- In:
  - The full suite run (`HOME=$(mktemp -d) uv run pytest -q
    --ignore=tests/e2e/test_metal.py -n auto`); zero branch-new
    failures.
  - The web baseline check (`uv run python
    scripts/check_web_baseline.py --run`); zero branch-new.
  - The UX canon ratchet green (ceiling per rule + per face).
  - Counsel reads the final tree (with special attention to the
    reviewer nudge, the first external write).
  - The final summary written
    (phase-173-the-stewards-hand-and-voice/final-summary.md).
  - The PR opened; the owner's word to merge.
  - The hygiene lane items this phase's tree touches are paid
    (HS-173-08).
- Out:
  - Implementation work (that is stories 02-05).
  - Post-merge follow-ups (filed as new stories if material).

## Acceptance criteria

- [x] The full suite passes with zero branch-new failures.
- [x] The web baseline check passes with zero branch-new.
- [x] The UX canon ratchet is green.
- [x] Counsel reads the final tree and passes (with the nudge review).
- [x] The final summary is written.
- [x] The PR is opened and passes CI.
- [x] The owner's word to merge (Article IX.4).

## Test plan

- Unit: the full suite.
- Integration: CI.
- Manual: counsel read; owner's word.

## Notes / open questions

- The counsel pass on the nudge implementation is constitutionally
  required: this is the first external write (Article V, Article XI).
