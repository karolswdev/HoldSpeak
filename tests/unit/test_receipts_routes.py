"""HTTP transport coverage for the Desk decision-receipt ledger."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database
from holdspeak.services.decision_receipt_service import DecisionReceiptService
from holdspeak.web.routes import receipts as receipt_routes


def test_receipt_routes_list_search_and_expand_detail(tmp_path, monkeypatch) -> None:
    database = Database(tmp_path / "receipts.db")
    monkeypatch.setattr(receipt_routes, "get_database", lambda: database)
    service = DecisionReceiptService(database)
    receipt = service.create(
        None,
        decision_text="Ship the searchable receipt ledger.",
        rationale="The Desk should answer why.",
        source_type="desk",
        source_id="HS-128-04",
    )
    service.link_work(None, receipt["id"], "story", "HS-128-04")

    app = FastAPI()
    app.include_router(receipt_routes.build_receipts_router(None))
    client = TestClient(app)

    listing = client.get("/api/receipts")
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == receipt["id"]

    searched = client.get("/api/receipts/search", params={"q": "searchable ledger"})
    assert searched.status_code == 200
    assert [item["id"] for item in searched.json()] == [receipt["id"]]

    source = client.get("/api/receipts/source/desk/HS-128-04")
    assert source.status_code == 200
    assert [item["id"] for item in source.json()] == [receipt["id"]]

    governing = client.get("/api/receipts/work/story/HS-128-04")
    assert governing.status_code == 200
    assert [item["id"] for item in governing.json()] == [receipt["id"]]

    detail = client.get(f"/api/receipts/{receipt['id']}")
    assert detail.status_code == 200
    assert detail.json()["work"][0]["work_type"] == "story"
    assert detail.json()["work"][0]["work_ref"] == "HS-128-04"

    assert client.get("/api/receipts/missing").status_code == 404
