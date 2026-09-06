# HS-171-10 — The close

- **Project:** holdspeak
- **Phase:** 171
- **Status:** backlog
- **Depends on:** HS-171-09
- **Unblocks:** Phase 172
- **Owner:** unassigned

## Problem

Phase 171 must close cleanly: all exit criteria checked, the full suite
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
  - The final summary written (phase-171-the-heartbeat/final-summary.md).
  - The PR opened; the owner's word to merge.
  - The hygiene lane items this phase's tree touches are paid (the
    parallel conductor loops, any other items from THE-TUESDAY-ARC.md
    section 4 that apply).
- Out:
  - Implementation work (that is stories 02-07).
  - Post-merge follow-ups (filed as new stories if material).

## Acceptance criteria

- [x] The full suite passes with zero branch-new failures. (9501 green; 6 inherited with zero diff vs main; 4 xdist-only green alone; the 4 branch-new paid before the PR.)
- [x] The web baseline check passes with zero branch-new.
- [x] The UX canon ratchet is green.
- [x] Counsel reads the final tree and passes. (RATIFY-W-C; C1/C2 paid the same hour.)
- [x] The final summary is written. (DRAFT tag lifts on his word.)
- [ ] The PR is opened and passes CI. (OPEN: https://github.com/karolswdev/HoldSpeak/pull/554 — CI pending.)
- [ ] The owner's word to merge (Article IX.4).

## Test plan

- Unit: the full suite.
- Integration: CI.
- Manual: counsel read; owner's word.

## Notes / open questions

- None.
