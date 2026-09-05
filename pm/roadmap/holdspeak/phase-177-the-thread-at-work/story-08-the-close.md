# HS-177-08 — The close

- **Project:** holdspeak
- **Phase:** 177
- **Status:** backlog
- **Depends on:** HS-177-07 (or HS-177-01 if CUT)
- **Unblocks:** Phase 178
- **Owner:** unassigned

## Problem

Phase 177 must close cleanly: all exit criteria checked (or explicitly
deferred if the measured decision was CUT), the full suite green,
counsel pass, the final summary written, the PR opened, and the merge
on the owner's word.

## Scope

- In:
  - The full suite run (`HOME=$(mktemp -d) uv run pytest -q
    --ignore=tests/e2e/test_metal.py -n auto`); zero branch-new
    failures.
  - The web baseline check (`uv run python
    scripts/check_web_baseline.py --run`); zero branch-new.
  - The UX canon ratchet green (ceiling per rule + per face).
  - Counsel reads the final tree.
  - The final summary written
    (phase-177-the-thread-at-work/final-summary.md); if the measured
    decision was CUT, the final summary records the metric, the kill
    criterion, and the owner's verdict as the phase's outcome.
  - The PR opened; the owner's word to merge.
- Out:
  - Implementation work (that is stories 02-07).
  - Post-merge follow-ups (filed as new stories if material).

## Acceptance criteria

- [ ] The full suite passes with zero branch-new failures.
- [ ] The web baseline check passes with zero branch-new.
- [ ] The UX canon ratchet is green.
- [ ] Counsel reads the final tree and passes.
- [ ] The final summary is written; if CUT, it records the metric and
      the owner's verdict.
- [ ] The PR is opened and passes CI.
- [ ] The owner's word to merge (Article IX.4).

## Test plan

- Unit: the full suite.
- Integration: CI.
- Manual: counsel read; owner's word.

## Notes / open questions

- If the measured decision is CUT, this story follows immediately
  after HS-177-01. The close records the measured decision as the
  phase's primary outcome and marks stories 02-07 as cancelled in the
  final summary.
