"""PARKED 20261108 (Lane S2): cases of ``tests/unit/test_workbench_parking.py`` that drove the item queue.

The item queue is parked (holdspeak/services/_parked/workbench_runner_queue_20261108.py);
an automation's run is a Program of one prompt step. Not collected; they import the
helpers of the live file. Restore with ``git revert`` of the parking commit.
"""
# ruff: noqa
from tests.unit.test_workbench_parking import *  # noqa: F401,F403


def test_runner_never_claims_a_parked_pending_item(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.services.workbench_runner import WorkbenchRunner
    from tests.unit.test_workbench_runner_migration import _setup_runner

    db, broker, workbench, items, state = _setup_runner(tmp_path, monkeypatch)
    WorkbenchService(db).park_item(OWNER, workbench.id, items[0].id)

    result = asyncio.run(
        WorkbenchRunner(db, broker).run(OWNER, workbench.id, memory_enabled=False)
    )

    assert result["skipped"] is True
    assert state["calls"] == []
    retained = db.workbench_items.get(items[0].id, include_parked=True)
    assert retained is not None and retained.parked is True and retained.status == "pending"


def test_real_runner_artifact_and_receipt_links_survive_park_reload_restore(
    tmp_path: Path, monkeypatch
) -> None:
    from tests.unit.test_workbench_runner_migration import _setup_runner, _run

    # The existing rig replaces only the inference provider's text output.
    # The real runner writes the item, artifact, source links and receipts.
    db, broker, workbench, items, _ = _setup_runner(tmp_path, monkeypatch)
    result = _run(db, broker, workbench.id, memory_enabled=False)
    item = db.workbench_items.get(items[0].id)
    assert item is not None and item.result_artifact_id

    def links(database):
        with database._connection() as conn:
            artifact = dict(conn.execute(
                "SELECT * FROM artifacts WHERE source_item_id = ?", (item.id,)
            ).fetchone())
            run = dict(conn.execute(
                "SELECT * FROM workbench_runs WHERE id = ?", (result["run_id"],)
            ).fetchone())
        assert artifact["id"] == item.result_artifact_id
        assert artifact["source_run_id"] == result["run_id"]
        assert run["parent_operation_id"] == result["parent_operation_id"]
        assert run["parent_receipt_id"] == result["receipt_id"]
        return artifact, run

    before = links(db)
    WorkbenchService(db).delete_item(OWNER, workbench.id, item.id)
    assert links(db) == before
    db.close()
    reopened = Database(tmp_path / "workbench.db")
    assert links(reopened) == before
    restored = WorkbenchService(reopened).restore_item(OWNER, workbench.id, item.id)
    assert restored["id"] == item.id and restored["result"] == item.result
    assert restored["result_artifact_id"] == item.result_artifact_id
    assert links(reopened) == before


def test_runner_skips_item_parked_after_pending_snapshot(tmp_path: Path, monkeypatch) -> None:
    from holdspeak.services.workbench_runner import WorkbenchRunner
    from tests.unit.test_workbench_runner_migration import _setup_runner

    db, broker, workbench, items, state = _setup_runner(tmp_path, monkeypatch)
    runner = WorkbenchRunner(db, broker)
    real_expire = runner.broker.parent_run_controller.expire_if_due
    parked = False

    def park_at_claim_boundary(context, principal):
        nonlocal parked
        if not parked:
            parked = True
            WorkbenchService(db).park_item(OWNER, workbench.id, items[0].id)
        return real_expire(context, principal)

    monkeypatch.setattr(
        runner.broker.parent_run_controller,
        "expire_if_due",
        park_at_claim_boundary,
    )
    result = asyncio.run(
        runner.run(OWNER, workbench.id, memory_enabled=False)
    )

    assert result["receipt_id"]
    assert broker.store.receipt(result["parent_operation_id"])["outcome"] == "succeeded"
    assert state["calls"] == []
    retained = db.workbench_items.get(items[0].id, include_parked=True)
    assert retained is not None and retained.parked is True and retained.status == "pending"
