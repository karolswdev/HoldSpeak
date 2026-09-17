# HS-200-43: Let a watch become schedulable, and let a manual evaluation count

- **Project:** holdspeak
- **Phase:** 200
- **Status:** ready
- **Depends on:** HS-200-42
- **Unblocks:** HS-200-13, HS-200-15, HS-200-16, HS-200-23
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** the 2026-09-13 operational-surface audit §3.2-3.3 (`docs/internal/OPERATIONAL-SURFACE-AUDIT.md`)

## Problem

**A watch can only become schedulable inside the function that only runs on
already-schedulable watches.**

`list_due_watches` requires `next_evaluation_at IS NOT NULL`
(`holdspeak/db/automations.py:451`). Every write of that column in the package is
`holdspeak/services/watch_service.py:922` and `:1009` — **both inside
`evaluate_due`** (which begins at `:850`). No creation path passes it: the Door
(`project_door_service.py:322`) and the Interview (`project_setup_service.py:750`)
set only `baseline_state="pending"`, and `baseline_watch` (`watch_service.py:573`)
sets only `baseline_state`.

**So a watch that has never been evaluated by the scheduler can never be selected
by the scheduler.** The owner's desk: **32 watches, 30 enabled, 2 armed.**

**And a manual evaluation cannot substitute**, because
`_match_and_record_effects` (`watch_service.py:958`) has exactly one caller —
inside `evaluate_due`. The MCP tool `project.watch.evaluate` therefore runs, and
records no effects, and can never reach the steward. `watch_effects` on his desk:
**0**.

Downstream, everything unattended in the Project Rooms arc depends on this:
steward `run_due` (`workbench_conductor.py:632`) waits on watches that never
arm, and all nine of his steward policies have `unattended_enabled=0`.

## Scope

Arm a watch at the moment it is created or enabled, backfill the watches already
on disk, and make a manual evaluation record its effects like a scheduled one.

Implementation seams: `holdspeak/services/watch_service.py` (creation, enable,
baseline, `evaluate_due`, `_match_and_record_effects`);
`holdspeak/db/automations.py`; the Door and Interview creation paths;
`holdspeak/db/reconcile.py` for the backfill.

Out: changing the cadence model, the circuit breaker, or the effect vocabulary.
Out: turning unattended execution ON for the owner — the policies stay his.

## Acceptance criteria

- [ ] A watch created through the Door and a watch created through the Interview
      are both selectable by `list_due_watches` without a prior manual run.
- [ ] Enabling a previously disabled watch arms it; disabling does not leave a
      row that the scheduler will pick up anyway.
- [ ] Watches already on disk are backfilled, and the backfill is proven wired by
      driving the real reconcile entry point — not the helper (HS-200-10's B3
      lesson: the helper shipped built, tested and uncalled).
- [ ] A manual `project.watch.evaluate` records effects exactly as a scheduled
      evaluation does, and the steward can act on them.
- [ ] Arming respects the paused and retired states; a tombstoned watch is not
      resurrected by the backfill.
- [ ] The double-scheduler question is settled: both `workbench_conductor` and
      `heartbeat_service` call `evaluate_due`, and **only the heartbeat checks
      quiet hours** (`heartbeat_service.py:318`). Either the conductor honours
      quiet hours or the promise is corrected. Name the ruling in the evidence.
- [ ] Every new fence proven to FAIL against the pre-fix tree.

## Test plan

Planned suite: `phase200_watch_arming`. Create through the real Door and real
Interview services, then assert selection through the real
`list_due_watches`. Backfill proven through `reconcile_schema`.

## Notes / open questions

The audit's §3.2 and §3.3. Note the related inherited defect found in Phase 166:
`older_than`/`newer_than` returned False unconditionally, so at least one shipped
watch had never matched. Confirm it stays fixed once watches actually run.
