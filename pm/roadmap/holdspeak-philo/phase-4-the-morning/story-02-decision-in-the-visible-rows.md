# PHILO-4-02 - The new decision is in the visible rows

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** backlog
- **Depends on:** PHILO-4-01
- **Unblocks:** the morning in one move
- **Owner:** unassigned (two-brains: one owner brain, the other counsels on built)
- **Closure finding:** Phase 3 final-summary "What he still cannot do" #3

## Problem

The Arrival's BRIEF section shows three rows and folds the rest behind `1 more` (1440) / `2 more` (393); in every successful closure generation the new decision was behind the fold at both widths, and at 393 its title sat under the footer after the fold opened (`20260924T014339Z`) (`20260924T013738Z`, `014018Z`). The API brief had it. The face hid it.

## Scope

- **In:** the result below, its fence(s) red pre-fix, the rig case at 1440 and 393.
- **Out:** everything the phase status lists as out.

## Acceptance criteria

- [ ] After Generate, the row for the newly recorded decision is inside the visible rows at 1440 and 393 (newest decision first, or the cap raised — read the ratifying Phase 175 canvas first; changing a ratified cap needs the owner's word, changing the ORDER does not).
- [ ] Fence red pre-fix: a rendered BRIEF section with four older rows and one new decision shows the decision.
- [ ] Rig: closure chain step 5 as written PASSES on the face at both widths.

## Effort (council-style estimate, not a promise)

1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
