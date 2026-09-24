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

- [ ] Provenance settled (Astra's check): the three-row Arrival cap (`BRIEF_CAP = 3`) was introduced as code in Phase 170 (`328d06fd`) and is cited as existing code in Phase 200's settled design (`settled-design-daily-workflow.md:204`); no canvas ratified it. It is KEPT (the smaller change); the repair is selection and order, and the resulting order is shown on story 01's canvas for the owner's ratification.
- [ ] Ordering rule (to settle before any worker brief): today the Arrival concatenates sections with decisions LAST (`ChairHome.tsx:801`), decision items get random ids and equal priority, and reload orders by priority then id (`monday_brief_service.py:761,1168`) — there is NO recency source. The rule: the decision section leads, and decision items carry the decision record's `created_at` (a real timestamp from the record, never inferred from item ids) and sort newest first; other sections keep their order.
- [ ] After Generate, the row for the newly recorded decision is inside the visible rows at 1440 and 393, readable (visible, inside the viewport, not under the footer).
- [ ] Fence red pre-fix: a rendered BRIEF section with SEVERAL older decisions (distinct `created_at`) plus older non-decision rows and one new decision shows the new decision first.
- [ ] Rig: closure chain step 5 as written PASSES on the face at both widths.

## Effort (council-style estimate, not a promise)

1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
