"""HS-132-08 — the Monday Brief item triage shelf.

Acknowledge/Defer used to live only in React state, so triage vanished on
reload. The shelf is durable, keyed by brief item, and read back with the
brief itself so the desk's attention badge reflects it.
"""
from __future__ import annotations

import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.db.core import Database
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.web.routes import monday_brief as brief_routes


def _service(tmp_path) -> MondayBriefService:
    return MondayBriefService(Database(tmp_path / "shelf.db"))


def _brief_with_one_item(service: MondayBriefService):
    service._db.desk_decisions.upsert(
        decision_id="desk-decision-1", title="Choose the release train", status="proposed"
    )
    return service.generate(None, now=datetime.datetime(2026, 8, 3, 9, 30))


def test_shelf_is_empty_before_any_triage(tmp_path):
    service = _service(tmp_path)
    brief = _brief_with_one_item(service)

    assert brief.shelf == {}
    assert service.shelf(None) == {}


def test_acknowledge_survives_a_fresh_read(tmp_path):
    service = _service(tmp_path)
    brief = _brief_with_one_item(service)
    item_id = brief.sections["decisions"][0].id

    service.shelve(None, item_id, "acknowledged")

    assert service.shelf(None) == {item_id: "acknowledged"}
    # A fresh service over the same database is the reload the desk performs.
    reopened = MondayBriefService(Database(tmp_path / "shelf.db"))
    assert reopened.get_latest(None).shelf == {item_id: "acknowledged"}


def test_defer_replaces_an_earlier_state(tmp_path):
    service = _service(tmp_path)
    brief = _brief_with_one_item(service)
    item_id = brief.sections["decisions"][0].id

    service.shelve(None, item_id, "acknowledged")
    service.shelve(None, item_id, "deferred")

    assert service.shelf(None) == {item_id: "deferred"}


def test_clearing_returns_the_item_to_untouched(tmp_path):
    service = _service(tmp_path)
    brief = _brief_with_one_item(service)
    item_id = brief.sections["decisions"][0].id
    service.shelve(None, item_id, "deferred")

    service.shelve(None, item_id, None)

    assert service.shelf(None) == {}


def test_unknown_item_and_state_are_refused_by_name(tmp_path):
    service = _service(tmp_path)
    brief = _brief_with_one_item(service)
    item_id = brief.sections["decisions"][0].id

    with pytest.raises(LookupError, match="Unknown brief item"):
        service.shelve(None, "brief-item-missing", "acknowledged")
    with pytest.raises(ValueError, match="Unknown shelf state"):
        service.shelve(None, item_id, "filed")


def _client(tmp_path, monkeypatch) -> tuple[TestClient, MondayBriefService]:
    database = Database(tmp_path / "shelf.db")
    monkeypatch.setattr(brief_routes, "get_database", lambda: database)
    monkeypatch.setattr(brief_routes, "get_observer", lambda: None)
    app = FastAPI()
    app.include_router(brief_routes.build_monday_brief_router(None))
    return TestClient(app), MondayBriefService(database)


def test_shelf_routes_round_trip(tmp_path, monkeypatch):
    client, service = _client(tmp_path, monkeypatch)
    brief = _brief_with_one_item(service)
    item_id = brief.sections["decisions"][0].id

    written = client.post(f"/api/brief/items/{item_id}/shelf", json={"state": "deferred"})
    assert written.status_code == 200
    assert written.json() == {"item_id": item_id, "state": "deferred"}

    assert client.get("/api/brief/shelf").json() == {item_id: "deferred"}
    assert client.get("/api/brief/latest").json()["shelf"] == {item_id: "deferred"}

    cleared = client.post(f"/api/brief/items/{item_id}/shelf", json={"state": None})
    assert cleared.status_code == 200
    assert client.get("/api/brief/shelf").json() == {}


def test_shelf_route_refusals_name_the_cause(tmp_path, monkeypatch):
    client, service = _client(tmp_path, monkeypatch)
    brief = _brief_with_one_item(service)
    item_id = brief.sections["decisions"][0].id

    missing = client.post("/api/brief/items/brief-item-missing/shelf", json={"state": "deferred"})
    assert missing.status_code == 404
    assert "Unknown brief item" in missing.json()["detail"]

    bad = client.post(f"/api/brief/items/{item_id}/shelf", json={"state": "filed"})
    assert bad.status_code == 422
    assert "Unknown shelf state" in bad.json()["detail"]
