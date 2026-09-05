# HS-180-10 — The close

- **Project:** holdspeak
- **Phase:** 180
- **Status:** backlog
- **Depends on:** HS-180-09
- **Unblocks:** --
- **Owner:** unassigned

## Problem

Phase 180 is the last phase of the arc. Its close is the arc's close.
The doctor's honest bill of health, the final summary, the last PR
merged on the owner's word.

## Scope

- In:
  - `holdspeak doctor` -- the doctor's honest bill of health
    (Article VI.1).
  - The full Python suite green.
  - The Swift test suite green.
  - The web baseline green.
  - The UX canon ratchet green.
  - Counsel reads the final tree and passes.
  - The final summary written
    (phase-180-the-proof/final-summary.md) -- the arc's epitaph:
    what shipped, what was proved, what was not, what comes next.
  - The last PR opened; the owner's word to merge.
  - The git tag applied.
  - The arc is complete.
- Out:
  - Post-arc work (filed as a new roadmap or backlog items).

## Acceptance criteria

- [ ] `holdspeak doctor` reports zero blocking issues.
- [ ] The full Python suite passes with zero failures.
- [ ] The Swift suite passes with zero failures.
- [ ] The web baseline passes with zero branch-new.
- [ ] The UX canon ratchet is green.
- [ ] Counsel reads the final tree and passes.
- [ ] The final summary is written -- the arc's epitaph.
- [ ] The last PR is opened and passes CI.
- [ ] The owner's word to merge (Article IX.4).
- [ ] The git tag is applied.

## Test plan

- Unit: the full Python suite; the Swift suite.
- Integration: CI.
- Manual: counsel read; `holdspeak doctor`; the owner's word.

## Notes / open questions

- This is the last story of the last phase of the arc. The final
  summary is the most important deliverable: it is the record that
  the arc completed, what it proved, and what comes next.
