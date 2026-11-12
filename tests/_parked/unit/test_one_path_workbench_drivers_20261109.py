# PARKED 2026-11-09: Unused drivers for the retired Workbench runner.
def _drive_workbench_manual(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_workbench_runner_migration import OWNER as WORKBENCH_OWNER
    from tests.unit.test_workbench_runner_migration import _run as _workbench_run
    from tests.unit.test_workbench_runner_migration import _setup_runner

    db, broker, workbench, _items, _state = _setup_runner(tmp_path, monkeypatch)
    result = _workbench_run(db, broker, workbench.id, memory_enabled=False)
    return SurfaceRun(
        db, WORKBENCH_OWNER, result["parent_operation_id"], workbench.profile_id,
        parent_kind="workbench",
    )


def _drive_workbench_memory(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_workbench_runner_migration import OWNER as WORKBENCH_OWNER
    from tests.unit.test_workbench_runner_migration import _run as _workbench_run
    from tests.unit.test_workbench_runner_migration import _setup_runner

    db, broker, workbench, _items, _state = _setup_runner(tmp_path, monkeypatch)
    result = _workbench_run(db, broker, workbench.id, memory_enabled=True)
    # Memory writeback is the SECOND admitted child of the same parent: one
    # item dispatch, then the writeback dispatch. Both must be inspected.
    return SurfaceRun(
        db, WORKBENCH_OWNER, result["parent_operation_id"], workbench.profile_id,
        expected_children=2, parent_kind="workbench",
    )


def _drive_workbench_scheduled(tmp_path, monkeypatch) -> SurfaceRun:
    from tests.unit.test_schedule_delegations import OWNER as SCHEDULE_OWNER
    from tests.unit.test_schedule_delegations import SCHEDULER
    from tests.unit.test_schedule_delegations import _rig as _schedule_rig
    from holdspeak.services.workbench_runner import WorkbenchRunner

    db, service, wid = _schedule_rig(tmp_path)
    db.workbench_items.upsert(item_id="i-spine", workbench_id=wid, title="scheduled")
    service.update_workbench(SCHEDULE_OWNER, wid, schedule_enabled=True)

    class FakeIntel:
        def run_prompt(self, **_):
            return "scheduled output"

    monkeypatch.setattr("holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: FakeIntel())
    broker = _configure(db)
    result = asyncio.run(WorkbenchRunner(db, broker).run_scheduled(SCHEDULER, wid, due_minute=999))
    # The scheduled run leaves memory writeback ON, so the same parent emits
    # the item child and the writeback child.
    return SurfaceRun(
        db, SCHEDULER, result["parent_operation_id"], db.workbenches.get(wid).profile_id,
        expected_children=2, parent_kind="workbench",
    )


