"""HS-S42: a meeting decision is created once, then filed and corrected on its
canonical project axis; source tags, record provenance and the meeting stay.

The bounded producer chain the Meeting Decide well and the decision's filing
strip drive: POST /api/decision-records/from-desk, then the member PUT,
the relationship GET and the DELETE against ``decision_record:<id>``.
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import decision_records as record_routes
from holdspeak.web.routes.primitives.kbs import build_kbs_router
from holdspeak.web.routes.projects import build_projects_router


def _client(db: Database, monkeypatch) -> TestClient:
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    monkeypatch.setattr(record_routes, "get_database", lambda: db)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "owner-session")
        return await call_next(request)

    ctx = WebContext(
        get_state=lambda: {},
        primitive_service=PrimitiveService(db),
        project_service=ProjectService(db),
    )
    app.include_router(record_routes.build_decision_records_router(ctx))
    app.include_router(build_projects_router(ctx))
    app.include_router(build_kbs_router(ctx))
    return TestClient(app)


def _rows(client: TestClient, ref: str) -> list[dict]:
    response = client.get(f"/api/desk/relationships/{quote(ref, safe='')}")
    assert response.status_code == 200, response.text
    return response.json()["projects"]


def test_meeting_decision_files_and_corrects_on_the_canonical_axis_only(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "filing.db")
    db.projects.create_project(project_id="atlas", name="Atlas")
    db.projects.create_project(project_id="ledger", name="Ledger")
    db.kbs.upsert(kb_id="drawer", name="Reference")
    client = _client(db, monkeypatch)

    created = client.post("/api/decision-records/from-desk", json={
        "decision_text": "Adopt quorumdb",
        "title": "Adopt quorumdb",
        "status": "accepted",
        "project_id": "atlas",
        "project_name": "Atlas",
        "meeting_id": "m1",
        "meeting_title": "Ledger sync",
        "why": "Meeting: Ledger sync",
    })
    assert created.status_code == 201, created.text
    body = created.json()
    record_id, source_id = body["record"]["id"], body["decision"]["id"]
    assert record_id and source_id and record_id != source_id
    assert body["record"]["source_id"] == source_id
    record_ref, source_ref = f"decision_record:{record_id}", f"desk_decision:{source_id}"
    # One creation: one source decision, one canonical record.
    assert len(db.desk_decisions.list()) == 1

    # The source keeps a drawer; correction must never move it.
    assert client.put(f"/api/kbs/drawer/members/{quote(source_ref, safe='')}").status_code == 200

    filed = client.put(
        f"/api/projects/atlas/resources/{quote(record_ref, safe='')}", json={"relationship": "member"},
    )
    assert filed.status_code == 200, filed.text
    assert filed.json()["resource"]["relationship"] == "member"
    assert [(r["project_id"], r["relationship"]) for r in _rows(client, record_ref)] == [("atlas", "member")]

    # Correction: Atlas out, Ledger in, on the canonical ref only.
    removed = client.delete(f"/api/projects/atlas/resources/{quote(record_ref, safe='')}")
    assert removed.status_code == 200 and removed.json()["removed"] is True
    assert client.put(
        f"/api/projects/ledger/resources/{quote(record_ref, safe='')}", json={"relationship": "member"},
    ).status_code == 200
    assert [(r["project_id"], r["relationship"]) for r in _rows(client, record_ref)] == [("ledger", "member")]

    # A second DELETE is an acknowledged no-removal, not a removal.
    again = client.delete(f"/api/projects/atlas/resources/{quote(record_ref, safe='')}")
    assert again.status_code == 200 and again.json()["removed"] is False

    # History stays: source tags, record provenance, the meeting and the drawer.
    source = db.desk_decisions.get(source_id)
    tags = source["tags"] if isinstance(source, dict) else source.tags
    assert "project:atlas" in tags and "meeting:m1" in tags
    record = client.get(f"/api/decision-records/{record_id}").json()
    assert {("project", "atlas"), ("meeting", "m1")} <= {
        (s["source_type"], s["source_ref"]) for s in record["sources"]
    }
    source_axes = client.get(f"/api/desk/relationships/{quote(source_ref, safe='')}").json()
    assert [row["knowledge_id"] for row in source_axes["knowledge"]] == ["drawer"]
    assert len(db.desk_decisions.list()) == 1


def test_a_source_edge_on_the_canonical_ref_is_not_a_member_filing(tmp_path, monkeypatch) -> None:
    db = Database(tmp_path / "kinds.db")
    db.projects.create_project(project_id="atlas", name="Atlas")
    client = _client(db, monkeypatch)
    body = client.post("/api/decision-records/from-desk", json={"title": "Keep one ledger"}).json()
    record_ref = f"decision_record:{body['record']['id']}"

    assert client.put(
        f"/api/projects/atlas/resources/{quote(record_ref, safe='')}", json={"relationship": "source"},
    ).status_code == 200
    rows = _rows(client, record_ref)
    # The row names the project, but its kind is not member: the strip reads
    # the kind, never only the project id.
    assert [(r["project_id"], r["relationship"]) for r in rows] == [("atlas", "source")]
