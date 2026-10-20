"""HTTP transport coverage for the Desk decision-record ledger."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind, UNAUTHENTICATED
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import decision_records as record_routes


def test_record_routes_list_search_and_expand_detail(tmp_path, monkeypatch) -> None:
    database = Database(tmp_path / "records.db")
    monkeypatch.setattr(record_routes, "get_database", lambda: database)
    service = DecisionRecordService(database)
    record = service.create(
        None,
        decision_text="Ship the searchable record ledger.",
        rationale="The Desk should answer why.",
        source_type="desk",
        source_id="HS-128-04",
    )
    service.link_work(None, record["id"], "story", "HS-128-04")

    app = FastAPI()
    app.include_router(record_routes.build_decision_records_router(None))
    client = TestClient(app)

    listing = client.get("/api/decision-records")
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == record["id"]

    searched = client.get("/api/decision-records/search", params={"q": "searchable ledger"})
    assert searched.status_code == 200
    assert [item["id"] for item in searched.json()] == [record["id"]]

    source = client.get("/api/decision-records/source/desk/HS-128-04")
    assert source.status_code == 200
    assert [item["id"] for item in source.json()] == [record["id"]]

    governing = client.get("/api/decision-records/work/story/HS-128-04")
    assert governing.status_code == 200
    assert [item["id"] for item in governing.json()] == [record["id"]]

    detail = client.get(f"/api/decision-records/{record['id']}")
    assert detail.status_code == 200
    assert detail.json()["work"][0]["work_type"] == "story"
    assert detail.json()["work"][0]["work_ref"] == "HS-128-04"

    assert client.get("/api/decision-records/missing").status_code == 404


def test_from_desk_uses_admitted_create_and_returns_one_canonical_record(tmp_path, monkeypatch) -> None:
    database = Database(tmp_path / "from-desk.db")
    monkeypatch.setattr(record_routes, "get_database", lambda: database)
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = Principal(PrincipalKind.OWNER, "test-owner")
        return await call_next(request)

    context = WebContext(get_state=lambda: {}, primitive_service=PrimitiveService(database))
    app.include_router(record_routes.build_decision_records_router(context))
    client = TestClient(app)

    response = client.post("/api/decision-records/from-desk", json={
        "title": "Use one canonical record",
        "status": "accepted",
        "project_id": "project-1",
        "project_name": "P9 canonical project",
        "meeting_id": "meeting-1",
        "why": "Keep every surface on one identity.",
        "source_id": "forged-source-id",
    })
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["decision"]["id"] != "forged-source-id"
    assert body["record"]["source_id"] == body["decision"]["id"]
    assert body["record"]["status"] == "accepted"
    assert "About: P9 canonical project" in body["record"]["rationale"]
    assert "Why: Keep every surface" in body["record"]["rationale"]
    assert body.get("operation_id") and body.get("receipt")
    assert {(source["source_type"], source["source_ref"]) for source in body["record"]["sources"]} == {
        ("project", "project-1"), ("meeting", "meeting-1"),
    }
    assert database.desk_decisions.get(body["decision"]["id"]) is not None
    assert len(database.desk_decisions.list()) == 1


def test_from_desk_unauthenticated_refusal_writes_no_source_or_record(tmp_path, monkeypatch) -> None:
    database = Database(tmp_path / "from-desk-refused.db")
    monkeypatch.setattr(record_routes, "get_database", lambda: database)
    app = FastAPI()

    @app.middleware("http")
    async def unauthenticated(request, call_next):
        request.state.principal = UNAUTHENTICATED
        return await call_next(request)

    context = WebContext(get_state=lambda: {}, primitive_service=PrimitiveService(database))
    app.include_router(record_routes.build_decision_records_router(context))
    client = TestClient(app)

    response = client.post("/api/decision-records/from-desk", json={
        "title": "Must not be written",
        "source_id": "forged-source-id",
    })
    assert response.status_code == 400, response.text
    assert "authenticated principal" in response.json()["error"]
    assert database.desk_decisions.list() == []
    assert DecisionRecordService(database).list_records(None) == []
