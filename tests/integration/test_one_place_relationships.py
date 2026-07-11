"""HS-92-05: one identity, three independent relationship axes."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.grounding import hydrate_refs
from holdspeak.web.context import WebContext
from holdspeak.web.routes.primitives.directories import build_directories_router
from holdspeak.web.routes.primitives.kbs import build_kbs_router
from holdspeak.web.routes.projects import build_projects_router
from holdspeak.web.routes.sync import build_sync_router


def _client(db: Database, monkeypatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {})
    app.include_router(build_kbs_router(ctx))
    app.include_router(build_directories_router(ctx))
    app.include_router(build_projects_router(ctx))
    return TestClient(app)


def test_axes_are_independent_and_use_qualified_identity(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "desk.db")
    db.notes.upsert(note_id="same", title="A note", body_markdown="real text")
    db.kbs.upsert(kb_id="knowledge", name="Reference")
    db.directories.upsert(directory_id="zone", name="Focus")
    db.projects.create_project(project_id="project", name="Launch")
    client = _client(db, monkeypatch)

    assert client.put("/api/directories/zone/members/note%3Asame").status_code == 200
    assert client.put("/api/kbs/knowledge/members/note%3Asame").status_code == 200
    assert client.put(
        "/api/projects/project/resources/note%3Asame", json={"relationship": "source"}
    ).status_code == 200

    axes = client.get("/api/desk/relationships/note%3Asame").json()
    assert axes["zone"]["directory_id"] == "zone"
    assert [row["knowledge_id"] for row in axes["knowledge"]] == ["knowledge"]
    assert [row["project_id"] for row in axes["projects"]] == ["project"]

    assert client.delete("/api/kbs/knowledge/members/note%3Asame").status_code == 200
    after = client.get("/api/desk/relationships/note%3Asame").json()
    assert after["knowledge"] == []
    assert after["zone"]["directory_id"] == "zone"
    assert after["projects"][0]["project_id"] == "project"


def test_deleting_zone_returns_contents_and_children_to_root(tmp_path) -> None:
    db = Database(tmp_path / "desk.db")
    db.directories.upsert(directory_id="parent", name="Parent")
    db.directories.upsert(directory_id="child", name="Child", parent_id="parent")
    db.directory_memberships.upsert(
        primitive_id="note:kept", directory_id="parent"
    )

    assert db.directories.delete("parent") is True
    assert db.directory_memberships.get("note:kept") is None
    assert db.directories.get("child").parent_id is None


def test_container_grounding_resolves_real_content_and_refuses_stale(tmp_path) -> None:
    db = Database(tmp_path / "desk.db")
    db.notes.upsert(note_id="n1", title="Source", body_markdown="resolved body")
    db.kbs.upsert(kb_id="k1", name="Reference")
    db.knowledge_memberships.upsert(knowledge_id="k1", resource_ref="note:n1")

    blocks, unknown = hydrate_refs(
        db, [], [], "summary", qualified_refs=["knowledge:k1"]
    )
    assert unknown == []
    assert blocks[0].kind == "knowledge"
    assert "resolved body" in blocks[0].text

    db.notes.delete("n1")
    _, unknown = hydrate_refs(
        db, [], [], "summary", qualified_refs=["knowledge:k1"]
    )
    assert unknown == ["note:n1"]


def test_project_identity_and_relationship_round_trip_cross_device(tmp_path, monkeypatch) -> None:
    source = Database(tmp_path / "source.db")
    source.projects.create_project(project_id="p1", name="Launch")
    source.project_relationships.upsert(project_id="p1", resource_ref="note:n1")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: source)
    app = FastAPI()
    app.include_router(build_sync_router(WebContext(get_state=lambda: {})))
    pulled = TestClient(app).get("/api/sync/pull").json()

    destination = Database(tmp_path / "destination.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: destination)
    app2 = FastAPI()
    app2.include_router(build_sync_router(WebContext(get_state=lambda: {})))
    response = TestClient(app2).post("/api/sync/push", json={
        "projects": pulled["projects"],
        "project_relationships": pulled["project_relationships"],
    })

    assert response.status_code == 200
    assert destination.projects.get_project("p1").name == "Launch"
    assert destination.project_relationships.get("p1", "note:n1") is not None

    conflicting = dict(pulled["projects"][0])
    conflicting["value"] = {**conflicting["value"], "name": "Different at same clock"}
    conflict = TestClient(app2).post("/api/sync/push", json={"projects": [conflicting]})
    assert conflict.status_code == 409
    assert conflict.json()["conflict"] == {
        "kind": "project",
        "id": "p1",
        "last_modified": pulled["projects"][0]["meta"]["last_modified"],
    }
