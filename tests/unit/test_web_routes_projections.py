from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_projections_router


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "projection-routes.db")
    db.meetings.save_meeting(MeetingState(
        id="m1", started_at=datetime.now(), title="Daily return",
        capture_status="recoverable",
    ))
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    app.include_router(build_projections_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def test_projection_route_filters_counts_and_paginates(rig) -> None:
    _, client = rig
    response = client.get("/api/desk/projections?kind=attention&limit=1")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == 1
    assert body["page"]["total"] == 1
    assert body["counts"]["needs_attention"] == 1
    assert body["projections"][0]["subject_ref"] == "meeting:m1"
    assert client.get("/api/desk/projections?kind=everything").status_code == 400


def test_projection_dismissal_does_not_mutate_subject(rig) -> None:
    db, client = rig
    projection = client.get("/api/desk/projections").json()["projections"][0]
    before = db.meetings.get_meeting("m1")
    response = client.put(
        f"/api/desk/projections/{projection['id']}/presentation",
        json={"action": "dismiss"},
    )
    assert response.status_code == 200
    assert response.json()["subject_unchanged"] is True
    assert client.get("/api/desk/projections").json()["projections"] == []
    assert db.meetings.get_meeting("m1") == before
