"""HS-157-03 -- Project routes characterization: pin every route's current
response shape and error behavior through the real FastAPI app, exactly as
it stands today.

Pattern: the 153/154 route-test pattern (isolated DB, real app, TestClient).
Change NO runtime code.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
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


class TestCreateProjectRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        resp = client.post("/api/projects", json={"name": "Alpha"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "project" in body
        proj = body["project"]
        # HS-157-03 legacy keys
        expected_keys = {"id", "name", "description", "keywords", "team_members",
                         "context", "detection_threshold", "is_archived",
                         "meeting_count", "created_at", "updated_at"}
        # HS-158-02 additive envelope keys
        assert expected_keys <= set(proj.keys())
        assert "result_kind" in proj
        assert "project_revision" in proj
        assert "changed_refs" in proj
        assert proj["name"] == "Alpha"

    def test_empty_name_400(self, rig) -> None:
        _db, client = rig
        resp = client.post("/api/projects", json={"name": ""})
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert "error" in body

    def test_missing_name_400(self, rig) -> None:
        _db, client = rig
        resp = client.post("/api/projects", json={})
        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False

    def test_bad_threshold_400(self, rig) -> None:
        _db, client = rig
        resp = client.post("/api/projects", json={"name": "X",
                                                    "detection_threshold": "bad"})
        assert resp.status_code == 400


# ── GET /api/projects ────────────────────────────────────────────────────


class TestListProjectsRoute:
    def test_empty_list(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        body = resp.json()
        assert body["projects"] == []

    def test_returns_projects(self, rig) -> None:
        _db, client = rig
        _create_project(client, name="P1")
        _create_project(client, name="P2")
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        assert len(resp.json()["projects"]) == 2

    def test_exclude_archived_by_default(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        client.delete(f"/api/projects/{proj['id']}")
        resp = client.get("/api/projects")
        assert resp.json()["projects"] == []

    def test_include_archived(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        client.delete(f"/api/projects/{proj['id']}")
        resp = client.get("/api/projects?include_archived=true")
        assert len(resp.json()["projects"]) == 1


# ── GET /api/projects/{id} ──────────────────────────────────────────────


class TestGetProjectRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}")
        assert resp.status_code == 200
        body = resp.json()
        expected_keys = {"id", "name", "description", "keywords", "team_members",
                         "context", "detection_threshold", "is_archived",
                         "meeting_count", "created_at", "updated_at"}
        # get is a READ -- no additive envelope keys required
        assert expected_keys <= set(body.keys())

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope")
        assert resp.status_code == 404
        body = resp.json()
        assert "error" in body
        # Pin: the error says "Project not found" (not_found helper)
        assert body["error"] == "Project not found"


# ── PATCH /api/projects/{id} ────────────────────────────────────────────


class TestUpdateProjectRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.patch(f"/api/projects/{proj['id']}",
                            json={"name": "Renamed"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["project"]["name"] == "Renamed"
        # HS-158-02 additive: envelope keys present
        assert "result_kind" in body["project"]
        assert "project_revision" in body["project"]

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.patch("/api/projects/proj-nope", json={"name": "X"})
        assert resp.status_code == 404
        body = resp.json()
        assert body.get("success") is False
        assert "error" in body

    def test_empty_name_400(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.patch(f"/api/projects/{proj['id']}", json={"name": ""})
        assert resp.status_code == 400
        assert resp.json()["success"] is False


# ── DELETE /api/projects/{id} ────────────────────────────────────────────
# CHARACTERIZATION: DELETE is an ARCHIVE, not a hard delete. The project
# remains in the DB with is_archived=True.


class TestDeleteArchiveProjectRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.delete(f"/api/projects/{proj['id']}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

    def test_project_is_archived_not_deleted(self, rig) -> None:
        """Pin: DELETE archives, not destroys."""
        _db, client = rig
        proj = _create_project(client)
        client.delete(f"/api/projects/{proj['id']}")
        # Project is still retrievable by GET
        resp = client.get(f"/api/projects/{proj['id']}")
        assert resp.status_code == 200
        assert resp.json()["is_archived"] is True

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.delete("/api/projects/proj-nope")
        assert resp.status_code == 404
        body = resp.json()
        assert body.get("success") is False


# ── GET /api/projects/{id}/meetings ──────────────────────────────────────


class TestProjectMeetingsRoute:
    def test_empty_list(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/meetings")
        assert resp.status_code == 200
        assert resp.json()["meetings"] == []

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/meetings")
        assert resp.status_code == 404


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


class TestProjectResourcesRoute:
    def test_empty_list(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/resources")
        assert resp.status_code == 200
        assert resp.json()["resources"] == []

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/resources")
        assert resp.status_code == 404
        body = resp.json()
        # Pin: resources route says "Unknown Project: <id>" (different casing)
        assert "Unknown Project" in body["error"]


# ── PUT /api/projects/{id}/resources/{ref} ───────────────────────────────


class TestAddResourceRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.put(f"/api/projects/{proj['id']}/resources/note:n1",
                          json=None)
        assert resp.status_code == 200
        body = resp.json()
        assert "resource" in body
        resource = body["resource"]
        # HS-157-03 legacy keys
        expected_keys = {"id", "project_id", "resource_ref", "relationship",
                         "source", "confidence", "created_at", "last_modified",
                         "deleted"}
        # HS-158-02 additive envelope keys
        assert expected_keys <= set(resource.keys())
        assert "result_kind" in resource

    def test_bad_ref_400(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.put(f"/api/projects/{proj['id']}/resources/bad-ref",
                          json=None)
        assert resp.status_code == 400

    def test_project_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.put("/api/projects/proj-nope/resources/note:n1",
                          json=None)
        assert resp.status_code == 404


# ── DELETE /api/projects/{id}/resources/{ref} ────────────────────────────


class TestRemoveResourceRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        client.put(f"/api/projects/{proj['id']}/resources/note:n1", json=None)
        resp = client.delete(f"/api/projects/{proj['id']}/resources/note:n1")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "removed" in body

    def test_project_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.delete("/api/projects/proj-nope/resources/note:n1")
        assert resp.status_code == 404


# ── GET /api/desk/relationships/{ref} ───────────────────────────────────


class TestResourceRelationshipsRoute:
    def test_success_shape(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/desk/relationships/note:n1")
        assert resp.status_code == 200
        body = resp.json()
        assert set(body.keys()) == {"resource_ref", "zone", "knowledge",
                                     "projects", "explanations"}

    def test_bad_ref_400(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/desk/relationships/bad-ref")
        assert resp.status_code == 400


# ── POST /api/projects/{id}/meetings/{mid} ──────────────────────────────


class TestAssociateMeetingRoute:
    def test_success(self, rig) -> None:
        db, client = rig
        proj = _create_project(client)
        _save_meeting(db, "m1")
        resp = client.post(f"/api/projects/{proj['id']}/meetings/m1")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_project_not_found_404(self, rig) -> None:
        db, client = rig
        _save_meeting(db, "m1")
        resp = client.post("/api/projects/proj-nope/meetings/m1")
        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False

    def test_meeting_not_found_404(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.post(f"/api/projects/{proj['id']}/meetings/m-gone")
        assert resp.status_code == 404
        assert resp.json()["success"] is False


# ── DELETE /api/projects/{id}/meetings/{mid} ─────────────────────────────


class TestDisassociateMeetingRoute:
    def test_success(self, rig) -> None:
        db, client = rig
        proj = _create_project(client)
        _save_meeting(db, "m1")
        client.post(f"/api/projects/{proj['id']}/meetings/m1")
        resp = client.delete(f"/api/projects/{proj['id']}/meetings/m1")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_project_not_found_404(self, rig) -> None:
        db, client = rig
        _save_meeting(db, "m1")
        resp = client.delete("/api/projects/proj-nope/meetings/m1")
        assert resp.status_code == 404

    def test_meeting_not_found_404(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.delete(f"/api/projects/{proj['id']}/meetings/m-gone")
        assert resp.status_code == 404


# ── GET /api/meetings/{mid}/projects ────────────────────────────────────


class TestMeetingProjectsRoute:
    def test_empty_list(self, rig) -> None:
        db, client = rig
        _save_meeting(db, "m1")
        resp = client.get("/api/meetings/m1/projects")
        assert resp.status_code == 200
        assert resp.json()["projects"] == []

    def test_returns_associated(self, rig) -> None:
        db, client = rig
        proj = _create_project(client)
        _save_meeting(db, "m1")
        client.post(f"/api/projects/{proj['id']}/meetings/m1")
        resp = client.get("/api/meetings/m1/projects")
        assert resp.status_code == 200
        assert len(resp.json()["projects"]) == 1

    def test_meeting_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/meetings/m-gone/projects")
        assert resp.status_code == 404


# ── GET /api/projects/{id}/since-last-meeting ────────────────────────────


class TestSinceLastMeetingRoute:
    def test_empty_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/since-last-meeting")
        assert resp.status_code == 200
        body = resp.json()
        assert body["project_id"] == proj["id"]

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/since-last-meeting")
        assert resp.status_code == 404


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


class TestProjectArtifactsRoute:
    def test_empty_shape(self, rig) -> None:
        _db, client = rig
        proj = _create_project(client)
        resp = client.get(f"/api/projects/{proj['id']}/artifacts")
        assert resp.status_code == 200
        body = resp.json()
        assert body["artifacts"] == []

    def test_not_found_404(self, rig) -> None:
        _db, client = rig
        resp = client.get("/api/projects/proj-nope/artifacts")
        assert resp.status_code == 404
