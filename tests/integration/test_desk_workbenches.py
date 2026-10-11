"""The Workbench window's Park, on the hub side (the test diet, 2026-10-11).

Successors of the hub halves of tests/e2e/test_philo13_02_park_glass.py: the
real Workbench routes on an isolated database, with the browser test's own
seed (four items, two done, one artifact linked to an item) and the runner's
own claim statement. The face halves (receipts, the PARKED token, Restore)
are vitest: web/src/desk/components/__tests__/workbenchPark.test.tsx.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.workbench_service import WorkbenchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.workbenches import build_workbenches_router

OWNER = Principal(PrincipalKind.OWNER, "desk-workbenches")
TITLES = ["Draft rollback runbook", "Old sampling spike", "Rerun shard benchmark", "Close the audit ticket"]


def _client(db: Database) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_workbenches_router(
        WebContext(get_state=lambda: {}, workbench_service=WorkbenchService(db))))
    return TestClient(app)


def _seed(db: Database, client: TestClient) -> tuple[str, dict[str, str]]:
    """The glass seed, through the same routes (POST, POST items, PUT done)."""
    made = client.post("/api/workbenches", json={"name": "Ledger cutover bench"})
    assert made.status_code == 201, made.text
    wb = made.json()["workbench"]["id"]
    ids: dict[str, str] = {}
    for title in TITLES:
        added = client.post(f"/api/workbenches/{wb}/items", json={"title": title})
        assert added.status_code == 201, added.text
        ids[title] = added.json()["item"]["id"]
    for title in TITLES[2:]:
        done = client.put(f"/api/workbenches/{wb}/items/{ids[title]}", json={"status": "done"})
        assert done.status_code == 200, done.text
    db.plugins.record_artifact(
        artifact_id="p13-wb-artifact", meeting_id="", artifact_type="workbench_output",
        title="Spike result", body_markdown="Sampling at 1 in 10.",
        sources=[{"source_type": "input", "source_ref": f"workbench_item:{ids['Old sampling spike']}"}])
    return wb, ids


def _item_row(db: Database, item_id: str) -> dict[str, Any]:
    """The glass's own DB read: the row is kept; parked, status, links."""
    with db._connection() as conn:
        row = conn.execute("SELECT parked, status FROM workbench_items WHERE id = ?", (item_id,)).fetchone()
        links = conn.execute(
            "SELECT COUNT(*) FROM artifact_sources WHERE source_ref = ?", (f"workbench_item:{item_id}",)
        ).fetchone()[0]
    return {"present": row is not None, "parked": None if row is None else int(row[0]),
            "status": None if row is None else row[1], "links": links}


def _listed(client: TestClient, wb: str, *, parked: bool = False) -> list[str]:
    path = f"/api/workbenches/{wb}" + ("?parked=true" if parked else "")
    return [item["id"] for item in client.get(path).json()["workbench"]["items"]]


def test_park_one_and_clear_done_keep_the_rows_parked_across_a_reload(tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo13_02_park_glass.py::test_workbench_item_park_single_bulk_restore_and_reload
    (the hub half: the row is kept and parked in the DB, and a reload reads it parked)."""
    path = tmp_path / "workbench.db"
    db = Database(path)
    client = _client(db)
    wb, ids = _seed(db, client)
    spike = ids["Old sampling spike"]
    before = _item_row(db, spike)
    assert before == {"present": True, "parked": 0, "status": "pending", "links": 1}, before

    # Park (the face's one press is DELETE): kept, parked, its link kept.
    parked = client.delete(f"/api/workbenches/{wb}/items/{spike}")
    assert parked.status_code == 200, parked.text
    assert parked.json()["parked"] == spike
    assert _item_row(db, spike) == {**before, "parked": 1}
    assert spike not in _listed(client, wb)
    assert _listed(client, wb, parked=True) == [spike]

    # A reload is a new read of the same database: still parked.
    db.close()
    db = Database(path)
    client = _client(db)
    assert _item_row(db, spike) == {**before, "parked": 1}
    assert _listed(client, wb, parked=True) == [spike]

    # Restore brings it back with its link.
    restored = client.post(f"/api/workbenches/{wb}/items/restore", json={"item_ids": [spike]})
    assert restored.status_code == 200, restored.text
    assert restored.json()["restored"] == [spike]
    assert _item_row(db, spike) == before
    assert spike in _listed(client, wb)

    # Clear done parks both done items at once; a reload reads both parked.
    done = [ids[t] for t in TITLES[2:]]
    bulk = client.post(f"/api/workbenches/{wb}/items/park", json={"item_ids": done})
    assert bulk.status_code == 200, bulk.text
    assert bulk.json()["parked"] == done
    db.close()
    db = Database(path)
    client = _client(db)
    assert [_item_row(db, i)["parked"] for i in done] == [1, 1]
    assert sorted(_listed(client, wb, parked=True)) == sorted(done)

    # Restore each, one at a time (the face restores from the Parked filter).
    for item_id in done:
        one = client.post(f"/api/workbenches/{wb}/items/{item_id}/restore")
        assert one.status_code == 200, one.text
        assert one.json()["item"]["parked"] is False
    assert [_item_row(db, i) for i in done] == [
        {"present": True, "parked": 0, "status": "done", "links": 0}
    ] * 2
    assert _listed(client, wb, parked=True) == []


def test_a_claimed_item_is_refused_in_place(tmp_path: Path) -> None:
    """replaces: tests/e2e/test_philo13_02_park_glass.py::test_a_claimed_item_is_refused_in_place
    A run claims the item between the face's read and his press: Park is
    refused (409, the status the face reads to say NOT PARKED · CLAIMED BY A
    RUN, WorkbenchWindow.tsx), and the row stays claimed and not parked."""
    db = Database(tmp_path / "workbench.db")
    client = _client(db)
    wb, ids = _seed(db, client)
    item = ids["Draft rollback runbook"]
    assert item in _listed(client, wb)  # the face's read: pending, not parked

    # The runner's own claim statement (holdspeak/services/workbench_runner.py:257),
    # as the glass ran it, after the read and before the press.
    with db._connection() as conn:
        claimed = conn.execute(
            "UPDATE workbench_items SET status='claimed', claimed_at=? WHERE id=? AND status='pending' AND parked=0",
            (datetime.now().isoformat(), item),
        )
        assert claimed.rowcount == 1

    refused = client.delete(f"/api/workbenches/{wb}/items/{item}")
    assert refused.status_code == 409, refused.text
    row = _item_row(db, item)
    assert row["parked"] == 0 and row["status"] == "claimed", row
    assert item in _listed(client, wb)
    assert _listed(client, wb, parked=True) == []
