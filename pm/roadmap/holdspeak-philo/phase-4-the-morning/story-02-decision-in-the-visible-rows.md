# PHILO-4-02 - The new decision is in the visible rows

- **Project:** holdspeak-philo
- **Phase:** 4
- **Status:** done
- **Depends on:** PHILO-4-01
- **Unblocks:** the morning in one move
- **Owner:** Astra (two Luna lanes); Muad'Dib counsels on built
- **Closure finding:** Phase 3 final-summary "What he still cannot do" #3

## Problem

The Arrival's BRIEF section shows three rows and folds the rest behind `1 more` (1440) / `2 more` (393); in every successful closure generation the new decision was behind the fold at both widths, and at 393 its title sat under the footer after the fold opened (`20260924T014339Z`) (`20260924T013738Z`, `014018Z`). The API brief had it. The face hid it.

## Scope

- **In:** the result below, its fence(s) red pre-fix, the rig case at 1440 and 393.
- **Out:** everything the phase status lists as out.

## Acceptance criteria

- [x] Provenance settled (Astra's check): the three-row Arrival cap (`BRIEF_CAP = 3`) was introduced as code in Phase 170 (`328d06fd`) and is cited as existing code in Phase 200's settled design (`settled-design-daily-workflow.md:204`); no canvas ratified it. It is KEPT (the smaller change); the repair is selection and order, and the resulting order is shown on story 01's canvas for the owner's ratification.
  **Proof:** Charter [findings 1–2](checks/charter-astra.md), [owner ratification](current-phase-status.md#status-of-this-charter), and [canvas round six, ask 2](assets/story-01-canvas/README.md). `BRIEF_CAP = 3` is retained; rendered fence `decisionRows.philo402.test.tsx:128` checks the cap and fold.
- [x] Ordering rule (to settle before any worker brief): today the Arrival concatenates sections with decisions LAST (`ChairHome.tsx:801`), decision items get random ids and equal priority, and reload orders by priority then id (`monday_brief_service.py:761,1168`) — there is NO recency source. The rule: the decision section leads, and decision items carry the decision record's `created_at` (a real timestamp from the record, never inferred from item ids) and sort newest first; other sections keep their order.
  **Proof:** `tests/unit/test_philo4_02_decision_rows.py:40,72,111` uses the real desk writer and meeting-artifact producer. [Archived-main red](../../../../docs/internal/philo/phase-4/rows/red-producer-final.log): `3 failed in 1.29s`; [final scoped green](../../../../docs/internal/philo/phase-4/rows/green-python-final.log): `92 passed in 3.90s`. Timestamp strings come from the source records; other section reload order is unchanged.
- [x] After Generate, the row for the newly recorded decision is inside the visible rows at 1440 and 393, readable (visible, inside the viewport, not under the footer).
  **Proof:** [1440 shot](assets/story-02-shots/20260924T072614Z-case.closure.chain.s5_next_day_brief_has_it-astra-1440/after.png), [393 shot](assets/story-02-shots/20260924T072514Z-case.closure.chain.s5_next_day_brief_has_it-astra-393/after.png), and [checked geometry/DB proof](../../../../docs/internal/philo/phase-4/rows/closure-proof.json). Position 1, all nine hit points owned. `tests/e2e/test_philo4_02_generated_clearance.py:121` separately proves a longer result clears the bar after the click; [red](../../../../docs/internal/philo/phase-4/rows/red-clearance-main.log) and [green](../../../../docs/internal/philo/phase-4/rows/green-clearance.log).
- [x] Fence red pre-fix: a rendered BRIEF section with SEVERAL older decisions (distinct `created_at`) plus older non-decision rows and one new decision shows the new decision first.
  **Proof:** `web/src/desk/chair/__tests__/decisionRows.philo402.test.tsx:128,134` checks first paint and Generate replacement with three older decisions, three non-decision rows and one new decision. [Archived-main red](../../../../docs/internal/philo/phase-4/rows/red-rendered.log): `Tests  2 failed (2)`; [ChairHome green](../../../../docs/internal/philo/phase-4/rows/green-rendered-final.log): `Tests  81 passed (81)`.
- [x] Rig: closure chain step 5 as written PASSES on the face at both widths.
  **Proof:** As-written PASS: `20260924T072614Z` at 1440 and `20260924T072514Z` at 393, case `case.closure.chain.s5_next_day_brief_has_it`. No Ack/Defer/fold. New id/date, exact decision timestamp, old durable rows/shelf unchanged, real LAN summary and cumulative restart retained: [observations and verification](../../../../docs/internal/philo/phase-4/rows/lane-report.md#proof), [DW captures](evidence-story-02.md). Separate breakage variants `20260924T072814Z`/`20260924T072722Z` pay story 03’s assigned rig obligation.

## Effort (council-style estimate, not a promise)

1 day

## Test plan

- **Unit:** fences that fail pre-fix for every repaired seam.
- **Integration:** the rig case(s) named above through `scripts/graph_walk.py`, observations retained (rig `--out` under this phase's assets).
- **Manual / device:** the owner's sitting on the morning.

## Notes

- 2026-09-24 — Built on `566495b0`. The [lane report](../../../../docs/internal/philo/phase-4/rows/lane-report.md) carries the real-producer red/green fences, the actual closure runs, the THIS WEEK ruling and the ledger. The 393 whole-row predicate exposed covered bottom padding; the measured bar is 138 px. The [seam check](checks/rows-seam-muaddib.md) ratifies native nearest scrolling after Generate with measured clearance. The unchanged as-written case and the separately named breakage variant both pass at 1440 and 393; the [built check](checks/rows-built-muaddib.md) is RATIFY-WITH-CONDITIONS, with all conditions paid in this commit and C2 corrected by the checker.
- 2026-09-23 — chartered from the Phase 3 closure run `20260924T013355Z` / `013440Z` (BLOCKED), `013738Z` / `014018Z` (FAIL behind "1 more"), `012420Z` (500).
