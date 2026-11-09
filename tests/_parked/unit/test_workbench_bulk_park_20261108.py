"""PARKED 20261108 (queue view park): cases of ``tests/unit/test_workbench_parking.py`` that drove the bulk park and restore.

POST /api/workbenches/{id}/items/park and /items/restore and
``WorkbenchService.park_items``/``restore_items`` had one caller, the queue view
(WorkbenchWindow), parked with them (holdspeak/web/routes/_parked/
workbench_queue_view_routes_20261108.py). The one-item park (DELETE) and
restore stay live and stay tested. Not collected; they import the helpers of
the live file. Restore with ``git revert`` of the parking commit.
"""
# ruff: noqa
from tests.unit.test_workbench_parking import *  # noqa: F401,F403
import pytest
from holdspeak.db.models import VALID_WORKBENCH_ITEM_STATUSES
from holdspeak.services.errors import ConflictError


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
