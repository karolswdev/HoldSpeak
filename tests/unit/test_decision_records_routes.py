"""HTTP transport coverage for the Desk decision-record ledger."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database
from holdspeak.services.decision_record_service import DecisionRecordService
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
