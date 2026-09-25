"""PHILO-6-04: one durable decision cause produces one observer row."""

from __future__ import annotations

import datetime as dt

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
import holdspeak.web.routes.decisions as decisions_route
from holdspeak import operations
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.errors import NotFound
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_decisions_router


MISSING_ID = "philo504-deliberately-absent"
OWNER = Principal(PrincipalKind.OWNER, "philo6-04-test-owner")


def _events(db: Database) -> list[dict[str, object]]:
    with db._connection() as conn:
        rows = conn.execute(
            """
            SELECT service, method, error, error_code, args_summary
            FROM pipeline_events
            ORDER BY rowid
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _app(db: Database, observer: SQLiteObserver, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr(hsdb, "get_observer", lambda *args, **kwargs: observer)
    monkeypatch.setattr(decisions_route, "get_observer", lambda: observer)
    # A read does not use the broker. Keeping this route seam empty avoids
    # opening another runtime while the route still owns the real lifecycle
    # service and the real SQLite observer.
    monkeypatch.setattr(decisions_route, "_kernel_service", lambda: None)

    primitive = PrimitiveService(db, observer=observer)
    ctx = WebContext(
        get_state=lambda: {},
        primitive_service=primitive,
        operations=operations.bind_available({"primitive_service": primitive}),
    )
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_decisions_router(ctx))
    return TestClient(app, raise_server_exceptions=False)


def _lifecycle_decision(db: Database, decision_id: str = "legacy-only-504") -> dict[str, object]:
    db.meetings.save_meeting(
        MeetingState(
            id="meeting-philo6-04",
            title="PHILO-6-04 source",
            started_at=dt.datetime(2026, 9, 24, 9),
            ended_at=dt.datetime(2026, 9, 24, 9, 30),
        )
    )
    # This is the production artifact producer. Its decisions projection
    # creates a lifecycle-only record with durable lineage.
    db.plugins.record_artifact(
        artifact_id=f"artifact-{decision_id}",
        meeting_id="meeting-philo6-04",
        artifact_type="decisions",
        title="PHILO-6-04 source",
        structured_json={"decisions": [{"decision": "Keep the lifecycle lineage"}]},
        plugin_id="decision_capture",
    )
    row = db.decisions.list(lifecycle="recorded")[0]
    assert row.id != decision_id
    return {"id": row.id, "text": row.text}


def _desk_decision(db: Database, decision_id: str = "desk-produced-504") -> dict[str, object]:
    # This is the production desk repository writer used by the operation
    # service.  It gives the route a real desk-owned record to dispatch.
    row = db.desk_decisions.upsert(
        decision_id=decision_id,
        title="Desk-owned decision",
        status="accepted",
        decision_markdown="The desk owns this read.",
    )
    return row.to_dict()


def test_missing_id_has_one_real_observer_failure_row(tmp_path, monkeypatch):
    db = Database(tmp_path / "missing.db")
    observer = SQLiteObserver(db._connection)
    client = _app(db, observer, monkeypatch)

    response = client.get(f"/api/decisions/{MISSING_ID}")

    assert response.status_code == 404
    assert response.json() == {"error": "decision_not_found"}
    rows = _events(db)
    assert len(rows) == 1
    assert (rows[0]["service"], rows[0]["method"]) == ("PrimitiveService", "get_decision")
    assert rows[0]["error_code"] == "not_found"
    assert MISSING_ID in str(rows[0]["error"])


def test_desk_id_uses_one_registry_read(tmp_path, monkeypatch):
    db = Database(tmp_path / "desk.db")
    observer = SQLiteObserver(db._connection)
    desk = _desk_decision(db)
    client = _app(db, observer, monkeypatch)

    response = client.get(f"/api/decisions/{desk['id']}")

    assert response.status_code == 200, response.text
    assert response.json()["decision"]["id"] == desk["id"]
    rows = _events(db)
    assert [(row["service"], row["method"]) for row in rows] == [
        ("PrimitiveService", "get_decision")
    ]
    assert rows[0]["error"] is None


def test_lifecycle_only_id_uses_one_observed_lineage_read(tmp_path, monkeypatch):
    db = Database(tmp_path / "legacy.db")
    observer = SQLiteObserver(db._connection)
    legacy = _lifecycle_decision(db)
    client = _app(db, observer, monkeypatch)

    response = client.get(f"/api/decisions/{legacy['id']}")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"]["id"] == legacy["id"]
    assert body["decision"]["text"] == legacy["text"]
    assert body["lineage"]["superseded_by"] is None
    rows = _events(db)
    assert [(row["service"], row["method"]) for row in rows] == [
        ("DecisionLifecycleService", "get_decision")
    ]
    assert rows[0]["error"] is None


def test_desk_owner_wins_when_real_producers_share_an_id(tmp_path, monkeypatch):
    db = Database(tmp_path / "collision.db")
    observer = SQLiteObserver(db._connection)
    legacy = _lifecycle_decision(db)
    desk = _desk_decision(db, decision_id=str(legacy["id"]))
    client = _app(db, observer, monkeypatch)

    response = client.get(f"/api/decisions/{desk['id']}")

    assert response.status_code == 200, response.text
    assert response.json()["decision"]["title"] == "Desk-owned decision"
    assert "lineage" not in response.json()
    rows = _events(db)
    assert [(row["service"], row["method"]) for row in rows] == [
        ("PrimitiveService", "get_decision")
    ]


def test_each_real_service_failure_keeps_its_observer_receipt(tmp_path):
    db = Database(tmp_path / "service-failures.db")
    observer = SQLiteObserver(db._connection)
    primitive = PrimitiveService(db, observer=observer)
    lifecycle = DecisionLifecycleService(db, kernel=None, observer=observer)

    with pytest.raises(NotFound):
        primitive.get_decision(OWNER, "missing-desk-service")
    with pytest.raises(NotFound):
        lifecycle.get_decision(OWNER, "missing-lifecycle-service")

    rows = _events(db)
    assert [(row["service"], row["method"], row["error_code"]) for row in rows] == [
        ("PrimitiveService", "get_decision", "not_found"),
        ("DecisionLifecycleService", "get_decision", "not_found"),
    ]
