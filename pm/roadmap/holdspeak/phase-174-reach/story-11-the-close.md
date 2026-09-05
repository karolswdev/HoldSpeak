# HS-174-11 — The close

- **Project:** holdspeak
- **Phase:** 174
- **Status:** in-progress
- **Depends on:** HS-174-10
- **Unblocks:** Phase 175
- **Owner:** unassigned

## Problem

Phase 174 must close cleanly: all exit criteria checked, the full suite
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
  - The final summary written
    (phase-174-reach/final-summary.md).
  - The PR opened; the owner's word to merge.
  - The hygiene lane items this phase's tree touches are paid (the
    MCP_SIDECAR.md generator for remote; any other items from
    THE-TUESDAY-ARC.md section 4 that apply).
- Out:
  - Implementation work (that is stories 02-09).
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

- If story 09 (LAN companion notifications) is deferred, the final
  summary records the deferral honestly and the close proceeds without
  it.
