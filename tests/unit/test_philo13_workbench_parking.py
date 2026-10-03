"""PHILO-13-02 — Workbench items park and restore as durable rows."""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pytest

from holdspeak.db import Database
from holdspeak.db.models import VALID_WORKBENCH_ITEM_STATUSES
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.workbenches import build_workbenches_router


OWNER = Principal(PrincipalKind.OWNER, "philo-13-owner")


def _seed(db: Database, *, item_count: int = 1):
    workbench = db.workbenches.upsert(workbench_id="wb-philo-13", name="Park proof")
    # A retained run row makes the proof exercise the same links that a real
    # Workbench result carries, without fabricating a parked item row.
    db.workbench_runs.create(run_id="run-philo-13", workbench_id=workbench.id)
    items = []
    for index in range(1, item_count + 1):
        item_id = f"wbi-{index}"
        artifact_id = f"artifact-{index}"
        db.plugins.record_artifact(
            artifact_id=artifact_id,
            meeting_id="",
            artifact_type="workbench_output",
            title=f"Agent result {index}",
            body_markdown=f"Result {index}",
            sources=[{"source_type": "input", "source_ref": f"workbench_item:{item_id}"}],
        )
        items.append(
            db.workbench_items.upsert(
                item_id=item_id,
                workbench_id=workbench.id,
                title=f"Item {index}",
                body=f"Body {index}",
                status="pending",
                result=f"Result {index}",
                result_artifact_id=artifact_id,
            )
        )
    return workbench, items


def _client(db: Database, service: WorkbenchService) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(
        build_workbenches_router(
            WebContext(get_state=lambda: {}, workbench_service=service)
        )
    )
    return TestClient(app)


def test_park_hides_item_but_reopens_the_same_row_and_links(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench.db")
    workbench, items = _seed(db)
    service = WorkbenchService(db)

    receipt = service.park_item(OWNER, workbench.id, items[0].id)
    assert receipt["id"] == items[0].id
    assert receipt["parked"] is True
    assert db.workbench_items.get(items[0].id) is None
    parked = db.workbench_items.get(items[0].id, include_parked=True)
    assert parked is not None
    assert parked.parked is True
    assert parked.result == "Result 1"
    assert parked.result_artifact_id == "artifact-1"
    assert db.plugins.get_artifact("artifact-1") is not None
    assert [run.id for run in db.workbench_runs.list_for_workbench(workbench.id)] == [
        "run-philo-13"
    ]

    db.close()
    reopened = Database(tmp_path / "workbench.db")
    assert reopened.workbench_items.get(items[0].id) is None
    parked_after_reload = reopened.workbench_items.get(items[0].id, include_parked=True)
    assert parked_after_reload is not None
    assert parked_after_reload.parked is True
    assert reopened.plugins.get_artifact("artifact-1") is not None
    assert [run.id for run in reopened.workbench_runs.list_for_workbench(workbench.id)] == [
        "run-philo-13"
    ]
    restored = WorkbenchService(reopened).restore_item(OWNER, workbench.id, items[0].id)
    assert restored["id"] == items[0].id
    assert restored["parked"] is False
    assert reopened.workbench_items.get(items[0].id).result == "Result 1"


def test_normal_delete_verb_retains_real_result_and_run_links(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench-delete-retention.db")
    workbench, items = _seed(db)
    service = WorkbenchService(db)
    artifact_before = db.plugins.get_artifact("artifact-1")
    runs_before = db.workbench_runs.list_for_workbench(workbench.id)
    assert artifact_before is not None and runs_before

    receipt = service.delete_item(OWNER, workbench.id, items[0].id)
    assert receipt["parked"] is True
    assert db.workbench_items.get(items[0].id) is None
    with db._connection() as conn:
        row = conn.execute(
            "SELECT id, result, result_artifact_id, parked FROM workbench_items WHERE id = ?",
            (items[0].id,),
        ).fetchone()
    assert row is not None
    assert row["result"] == "Result 1"
    assert row["result_artifact_id"] == "artifact-1"
    assert row["parked"] == 1
    assert db.plugins.get_artifact("artifact-1").id == artifact_before.id
    assert [run.id for run in db.workbench_runs.list_for_workbench(workbench.id)] == [
        run.id for run in runs_before
    ]

    restored = service.restore_item(OWNER, workbench.id, items[0].id)
    assert restored["parked"] is False


def test_bulk_park_claimed_item_refuses_without_partial_change(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench.db")
    workbench, items = _seed(db, item_count=3)
    assert "claimed" in VALID_WORKBENCH_ITEM_STATUSES
    claimed_status = next(
        status for status in VALID_WORKBENCH_ITEM_STATUSES if status == "claimed"
    )
    db.workbench_items.upsert(
        item_id=items[1].id,
        workbench_id=workbench.id,
        title=items[1].title,
        body=items[1].body,
        status=claimed_status,
        result=items[1].result,
        result_artifact_id=items[1].result_artifact_id,
    )

    with pytest.raises(ConflictError, match="claimed"):
        WorkbenchService(db).park_items(OWNER, workbench.id, [item.id for item in items])

    assert [
        db.workbench_items.get(item.id, include_parked=True).parked
        for item in items
    ] == [False, False, False]


def test_upsert_keeps_a_parked_item_parked(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench.db")
    workbench, items = _seed(db)
    service = WorkbenchService(db)
    service.park_item(OWNER, workbench.id, items[0].id)

    db.workbench_items.upsert(
        item_id=items[0].id,
        workbench_id=workbench.id,
        title="Updated retained item",
        body="Updated body",
        status="done",
        result="Updated result",
        result_artifact_id="artifact-1",
    )

    parked = db.workbench_items.get(items[0].id, include_parked=True)
    assert parked is not None and parked.parked is True
    assert parked.title == "Updated retained item"


def test_workbench_payload_selects_parked_items_only_when_requested(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench.db")
    workbench, items = _seed(db, item_count=2)
    service = WorkbenchService(db)
    service.park_item(OWNER, workbench.id, items[0].id)

    normal = service.get_workbench(OWNER, workbench.id)
    parked = service.get_workbench(OWNER, workbench.id, parked=True)
    assert [item["id"] for item in normal["items"]] == [items[1].id]
    assert [item["id"] for item in parked["items"]] == [items[0].id]


def test_production_routes_park_bulk_reload_and_restore(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench-route.db")
    service = WorkbenchService(db)
    client = _client(db, service)

    created = client.post("/api/workbenches", json={"name": "Route proof"})
    assert created.status_code == 201, created.text
    workbench_id = created.json()["workbench"]["id"]
    item_ids = [
        client.post(
            f"/api/workbenches/{workbench_id}/items",
            json={"title": f"Route item {index}", "body": "retained"},
        ).json()["item"]["id"]
        for index in (1, 2)
    ]

    parked_one = client.delete(
        f"/api/workbenches/{workbench_id}/items/{item_ids[0]}"
    )
    assert parked_one.status_code == 200, parked_one.text
    assert parked_one.json()["parked"] == item_ids[0]
    assert "deleted" not in parked_one.text.lower()
    with db._connection() as conn:
        assert conn.execute(
            "SELECT id FROM workbench_items WHERE id = ?", (item_ids[0],)
        ).fetchone() is not None
    assert [
        item["id"]
        for item in client.get(f"/api/workbenches/{workbench_id}").json()["workbench"]["items"]
    ] == [item_ids[1]]

    parked_view = client.get(f"/api/workbenches/{workbench_id}?parked=true")
    assert parked_view.status_code == 200
    assert [item["id"] for item in parked_view.json()["workbench"]["items"]] == [item_ids[0]]

    restored_one = client.post(
        f"/api/workbenches/{workbench_id}/items/{item_ids[0]}/restore"
    )
    assert restored_one.status_code == 200, restored_one.text
    assert restored_one.json()["item"]["parked"] is False

    bulk = client.post(
        f"/api/workbenches/{workbench_id}/items/park",
        json={"item_ids": item_ids},
    )
    assert bulk.status_code == 200, bulk.text
    assert bulk.json()["parked"] == item_ids
    assert len(client.get(f"/api/workbenches/{workbench_id}").json()["workbench"]["items"]) == 0

    db.close()
    reopened = Database(tmp_path / "workbench-route.db")
    reopened_client = _client(reopened, WorkbenchService(reopened))
    assert [
        item["id"]
        for item in reopened_client.get(
            f"/api/workbenches/{workbench_id}?parked=true"
        ).json()["workbench"]["items"]
    ] == item_ids

    restored_bulk = reopened_client.post(
        f"/api/workbenches/{workbench_id}/items/restore",
        json={"item_ids": item_ids},
    )
    assert restored_bulk.status_code == 200, restored_bulk.text
    assert restored_bulk.json()["restored"] == item_ids


def test_legacy_repository_delete_parks_and_repeats_are_idempotent(tmp_path: Path) -> None:
    db = Database(tmp_path / "workbench-delete-compat.db")
    workbench, items = _seed(db)
    assert db.workbench_items.delete(items[0].id) is True
    with db._connection() as conn:
        retained_row = conn.execute(
            "SELECT id FROM workbench_items WHERE id = ?", (items[0].id,)
        ).fetchone()
    assert retained_row is not None
    assert db.workbench_items.delete(items[0].id) is True
    retained = db.workbench_items.get(items[0].id, include_parked=True)
    assert retained is not None and retained.parked is True
    assert db.workbench_items.get(items[0].id) is None
    assert WorkbenchService(db).restore_item(OWNER, workbench.id, items[0].id)["parked"] is False


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
