# PHILO-6-04 - One cause, one row

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** in-progress
- **Depends on:** -
- **Unblocks:** exit 3 (one broke row per cause); the `missing-decision` op/browser parity pair
- **Owner:** Astra (Luna); Muad'Dib checks
- **Closure finding:** BACKLOG "PHILO-5-04 follow-ups", ledger row 2; Astra's check of the drafts, finding 2 row 5
- **Canvas:** none

## Problem

One missing decision read over HTTP records two observer failures. `GET /api/decisions/{id}` tries the desk decision through the registry (`holdspeak/web/routes/decisions.py:58`), catches `NotFound` and falls through (`:59`) to the lifecycle service (`:60`), which fails again. The retained rows show it: HTTP observer rows 67 (`PrimitiveService.get_decision`) and 68 (`DecisionLifecycleService.get_decision`) for the id `philo504-deliberately-absent` (`../phase-5-the-one-service-layer/assets/story-04-shots/carried/verification/missing-browser-missing-id-rows.txt`); the `op` path records one row, row 6 (`…/missing-op-missing-id-rows.txt`). The brief collector (`monday_brief_service.py:577-593`) then says two things broke. The op/browser parity pair `missing-decision` is FAIL 2:1.

## Scope

- **In:** the legacy-id dispatch settled so one missing id makes one observer row; legacy (lifecycle) decision reads kept; the fence; the parity pair.
- **Out:** any global suppression of observer failures; a change of the lifecycle service; everything the phase status lists as out.

## Acceptance criteria

- [ ] One missing decision id over HTTP records ONE observer failure row (one cause, one row), the same count as the `op` path.
- [ ] Legacy decision reads are preserved: a lifecycle-only decision id still answers through `GET /api/decisions/{id}` with its lineage; fenced.
- [ ] Failures are not suppressed globally: a real failure of either service still records its row; fenced (a mutation that silences the observer turns the fence red).
- [ ] Fence red pre-fix: the real route with the real observer (`SQLiteObserver`) and a missing id records two rows on a `git archive origin/main` copy; one after.
- [ ] The op/browser parity pair `missing-decision` (`case.philo504.decision_missing.refusal` and `.op`, `docs/internal/philo/graph/atlas-phase3.json:6452,6504`) goes from FAIL 2:1 to PASS on the rig.

## Effort (council-style estimate, not a promise)

0.5 day

## Test plan

- **Unit:** pytest through the real route, the real registry and the real observer (red pre-fix: 2 rows).
- **Integration:** `case.philo504.decision_missing.refusal` and its `.op` sibling on the rig; the observer row counts retained.
- **Manual / device:** exit 3's morning shots show one broke row per cause.

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 5: canvas-free; preserve legacy reads; parity never by global suppression).
