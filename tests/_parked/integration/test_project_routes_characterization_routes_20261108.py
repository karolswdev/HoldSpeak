"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_project_routes_characterization.py``: TestProjectBriefingsRoute, TestProjectSummaryRoute, TestProjectActionItemsRoute. Not collected.
"""
from __future__ import annotations
"""HS-157-03 -- Project routes characterization: pin every route's current
response shape and error behavior through the real FastAPI app, exactly as
it stands today.

Pattern: the 153/154 route-test pattern (isolated DB, real app, TestClient).
Change NO runtime code.
"""

from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_projects_router

# ── Fixture ──────────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "project-routes-char.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    svc = ProjectService(db)
    app = FastAPI()

    # PHILO-9-02 admitted archive, link, unlink and the resource writes under
    # Article XI: they need the transport's authenticated principal. The hub's
    # edge (web_server._web_auth_gate) sets request.state.principal before any
    # route runs; this bare router has no edge, so the rig sets the owner the
    # way the hub does. Without it every admitted write is refused by name.
    @app.middleware("http")
    async def _owner_edge(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "project-routes-char")
        return await call_next(request)

    app.include_router(build_projects_router(WebContext(
        get_state=lambda: {},
        project_service=svc,
    )))
    yield db, TestClient(app)
    reset_database()


def _create_project(client: TestClient, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": "Test Project", **overrides}
    resp = client.post("/api/projects", json=payload)
    assert resp.status_code == 200
    return resp.json()["project"]


def _save_meeting(db: Database, meeting_id: str, title: str = "Stand-up") -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id, started_at=datetime(2025, 1, 15, 10, 0),
        title=title, capture_status="finalized",
    ))


# ── POST /api/projects ──────────────────────────────────────────────────


# ── GET /api/projects ────────────────────────────────────────────────────


# ── GET /api/projects/{id} ──────────────────────────────────────────────


# ── PATCH /api/projects/{id} ────────────────────────────────────────────


# ── DELETE /api/projects/{id} ────────────────────────────────────────────
# CHARACTERIZATION: DELETE is an ARCHIVE, not a hard delete. The project
# remains in the DB with is_archived=True.


# ── GET /api/projects/{id}/meetings ──────────────────────────────────────


# ── GET /api/projects/{id}/briefings ─────────────────────────────────────


class TestProjectBriefingsRoute:
    def test_empty_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/briefings")
        assert resp.status_code == 200
        body = resp.json()
        assert body["project_id"] == proj["id"]
        assert body["briefings"] == []

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/briefings")
        assert resp.status_code == 404
        body = resp.json()
        # Pin: error message uses the project_id, not "Project not found"
        # (the briefings route has its own NotFound handler)
        assert "Unknown project" in body["error"]


# ── GET /api/projects/{id}/resources ─────────────────────────────────────


# ── PUT /api/projects/{id}/resources/{ref} ───────────────────────────────


# ── DELETE /api/projects/{id}/resources/{ref} ────────────────────────────


# ── GET /api/desk/relationships/{ref} ───────────────────────────────────


# ── POST /api/projects/{id}/meetings/{mid} ──────────────────────────────


# ── DELETE /api/projects/{id}/meetings/{mid} ─────────────────────────────


# ── GET /api/meetings/{mid}/projects ────────────────────────────────────


# ── GET /api/projects/{id}/since-last-meeting ────────────────────────────


# ── GET /api/projects/{id}/summary ──────────────────────────────────────


class TestProjectSummaryRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/summary")
        assert resp.status_code == 200
        body = resp.json()
        expected_keys = {"meeting_count", "first_meeting", "last_meeting",
                         "action_items_by_status", "artifact_count"}
        assert set(body.keys()) == expected_keys

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/summary")
        assert resp.status_code == 404


# ── GET /api/projects/{id}/action-items ──────────────────────────────────


class TestProjectActionItemsRoute:
    def test_empty_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/action-items")
        assert resp.status_code == 200
        body = resp.json()
        assert body["action_items"] == []

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/action-items")
        assert resp.status_code == 404


# ── GET /api/projects/{id}/artifacts ─────────────────────────────────────


