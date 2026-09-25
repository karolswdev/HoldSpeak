# PHILO-6-04 - One cause, one row

- **Project:** holdspeak-philo
- **Phase:** 6
- **Status:** done
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

- [x] One missing decision id over HTTP records ONE observer failure row (one cause, one row), the same count as the `op` path. Proof: `tests/unit/test_philo6_04_one_cause_one_row.py::test_missing_id_has_one_real_observer_failure_row`; evidence-story-04.md, parity capture.
- [x] Legacy decision reads are preserved: a lifecycle-only decision id still answers through `GET /api/decisions/{id}` with its lineage; fenced. Proof: `test_lifecycle_only_id_uses_one_observed_lineage_read` and `test_desk_owner_wins_when_real_producers_share_an_id`; evidence-story-04.md, 33-pass capture.
- [x] Failures are not suppressed globally: a real failure of either service still records its row; fenced (a mutation that silences the observer turns the fence red). Proof: `test_each_real_service_failure_keeps_its_observer_receipt`; `docs/internal/philo/phase-6/rows/observer-mutation.txt` (zero-row red).
- [x] Fence red pre-fix: the real route with the real observer (`SQLiteObserver`) and a missing id records two rows on a `git archive origin/main` copy; one after. Proof: `docs/internal/philo/phase-6/rows/pre-fix-missing-id.txt` (`assert 2 == 1`); `rows/baseline.json`.
- [x] The op/browser parity pair `missing-decision` (`case.philo504.decision_missing.refusal` and `.op`, `docs/internal/philo/graph/atlas-phase3.json:6452,6504`) has a sidecar-verifier verdict of FAIL 2:1 → PASS 1:1 at 1440 and 393 (`rows/verify_parity.py` over `walk_one_row.py` observer rows). The rig’s atlas refusal verdict is `pass` on both sides; it does not assert row parity. Proof: `docs/internal/philo/phase-6/rows/verify_parity.py`; evidence-story-04.md. The HTTP case gained viewport 393 at `atlas-phase3.json:6500` so the same actual case runs at both widths.

## Effort (council-style estimate, not a promise)

0.5 day

## Test plan

- **Unit:** pytest through the real route, the real registry and the real observer (red pre-fix: 2 rows).
- **Integration:** `case.philo504.decision_missing.refusal` and its `.op` sibling on the rig; the observer row counts retained.
- **Manual / device:** exit 3's morning shots show one broke row per cause.

## Notes

- 2026-09-24 — chartered from XXVIII r2 + Astra's check (finding 2 row 5: canvas-free; preserve legacy reads; parity never by global suppression).
- 2026-09-24 night — built and verified in lane B. Astra-invoked claude -p check RATIFY-WITH-CONDITIONS, both bookkeeping conditions paid (`checks/story-04-built-astra-invoked-claude.md`). Full phase rehearsal and lane-PR counsel remain separate.
