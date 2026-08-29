"""Calendar settings transport proofs (HS-144-02, HS-146-02 sources wire)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.config import Config, calendar_subscription_revision
from holdspeak.db.core import get_database, reset_database
from holdspeak.mcp.families.settings import dispatch
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

OWNER = Principal(PrincipalKind.OWNER, "test-owner")


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", path)
    return path


@pytest.fixture
def production_db(tmp_path: Path):
    reset_database()
    db = get_database(tmp_path / "holdspeak.db")
    try:
        yield db
    finally:
        reset_database()


@pytest.fixture
def client(production_db) -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
            on_settings_applied=MagicMock(),
        )
    )
    return TestClient(server.app)


def _put(client: TestClient, patch: dict) -> dict:
    response = client.put("/api/settings", json=patch)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    return body["settings"]


def test_empty_file_and_https_calendar_subscription_round_trip_through_http_and_mcp_service(
    client: TestClient, settings_path: Path
) -> None:
    empty = _put(client, {"calendar": {"subscription": "   "}})
    assert empty["calendar"]["subscription"] == ""
    assert empty["_calendar_subscription"]["kind"] == "disabled"

    file_settings = _put(client, {"calendar": {"subscription": "  /tmp/team.ics  "}})
    assert file_settings["calendar"]["subscription"] == "/tmp/team.ics"
    assert file_settings["_calendar_subscription"] == {
        "kind": "file",
        "host": "",
        "refresh_seconds": 900,
        "egress": False,
    }

    mcp_result = dispatch(
        "settings.update",
        {"patch": {"calendar": {"subscription": "https://Calendar.Example.test/team.ics"}}},
        Principal(PrincipalKind.OWNER, "test-owner"),
    )
    assert mcp_result["success"] is True
    assert mcp_result["settings"]["calendar"]["subscription"] == (
        "https://Calendar.Example.test/team.ics"
    )
    assert mcp_result["settings"]["_calendar_subscription"] == {
        "kind": "https",
        "host": "calendar.example.test",
        "refresh_seconds": 900,
        "egress": True,
    }
    persisted_source = "https://Calendar.Example.test/team.ics"
    assert Config.load(path=settings_path).calendar.subscription == persisted_source
    assert calendar_subscription_revision(f"  {persisted_source}  ") == (
        calendar_subscription_revision(persisted_source)
    )


def test_calendar_subscription_rejects_http_userinfo_and_malformed_https(
    client: TestClient, settings_path: Path
) -> None:
    for subscription in (
        "http://calendar.example.test/feed.ics",
        "https://owner:password@calendar.example.test/feed.ics",
        "https://",
        "ftp://calendar.example.test/feed.ics",
        "https://calendar.example.test/#fragment",
    ):
        response = client.put("/api/settings", json={"calendar": {"subscription": subscription}})
        assert response.status_code == 400, response.text
        assert response.json()["success"] is False

    assert Config.load(path=settings_path).calendar.subscription == ""


def test_settings_projection_derives_url_host_cadence_and_file_no_egress(
    client: TestClient, settings_path: Path
) -> None:
    _put(client, {"calendar": {"subscription": "https://calendar.example.test/a.ics?x=1"}})
    url_fact = client.get("/api/settings").json()["_calendar_subscription"]
    assert url_fact == {
        "kind": "https",
        "host": "calendar.example.test",
        "refresh_seconds": 900,
        "egress": True,
    }

    _put(client, {"calendar": {"subscription": "calendar.ics"}})
    file_fact = client.get("/api/settings").json()["_calendar_subscription"]
    assert file_fact == {
        "kind": "file",
        "host": "",
        "refresh_seconds": 900,
        "egress": False,
    }


# ── HS-146-02: sources wire ──────────────────────────────────────────────


def test_sources_wire_accepts_two_sources_and_persists_both(
    client: TestClient, settings_path: Path
) -> None:
    settings = _put(client, {"calendar": {"sources": [
        {"label": "Work", "url": "https://work.example.test/cal.ics", "enabled": True},
        {"label": "Personal", "url": "/home/user/personal.ics", "enabled": False},
    ]}})
    sources = settings["calendar"]["sources"]
    assert len(sources) == 2
    assert sources[0]["label"] == "Work"
    assert sources[0]["url"] == "https://work.example.test/cal.ics"
    assert sources[0]["enabled"] is True
    assert sources[0]["id"]
    assert sources[1]["label"] == "Personal"
    assert sources[1]["url"] == "/home/user/personal.ics"
    assert sources[1]["enabled"] is False
    assert sources[1]["id"]
    assert sources[0]["id"] != sources[1]["id"]

    loaded = Config.load(path=settings_path)
    assert len(loaded.calendar.sources) == 2
    assert loaded.calendar.sources[0].url == "https://work.example.test/cal.ics"
    assert loaded.calendar.sources[1].url == "/home/user/personal.ics"


def test_sources_wire_preserves_existing_ids_on_update(
    client: TestClient, settings_path: Path
) -> None:
    first = _put(client, {"calendar": {"sources": [
        {"label": "A", "url": "https://a.example.test/cal.ics"},
    ]}})
    original_id = first["calendar"]["sources"][0]["id"]
    assert original_id

    second = _put(client, {"calendar": {"sources": [
        {"id": original_id, "label": "A updated", "url": "https://a.example.test/cal.ics"},
    ]}})
    assert second["calendar"]["sources"][0]["id"] == original_id
    assert second["calendar"]["sources"][0]["label"] == "A updated"


def test_sources_wire_mints_id_for_entry_without_one(
    client: TestClient, settings_path: Path
) -> None:
    settings = _put(client, {"calendar": {"sources": [
        {"url": "https://cal.example.test/feed.ics"},
    ]}})
    assert settings["calendar"]["sources"][0]["id"]


def test_sources_wire_refuses_invalid_url_by_name(
    client: TestClient, settings_path: Path
) -> None:
    response = client.put("/api/settings", json={"calendar": {"sources": [
        {"label": "Good", "url": "https://good.example.test/cal.ics"},
        {"label": "Bad feed", "url": "http://bad.example.test/cal.ics"},
    ]}})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "Bad feed" in body["error"]


def test_sources_wire_refuses_invalid_url_by_index_when_no_label(
    client: TestClient, settings_path: Path
) -> None:
    response = client.put("/api/settings", json={"calendar": {"sources": [
        {"url": "ftp://bad.example.test/cal.ics"},
    ]}})
    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "sources[0]" in body["error"]


def test_sources_wire_refuses_non_list_sources(
    client: TestClient, settings_path: Path
) -> None:
    response = client.put("/api/settings", json={"calendar": {"sources": "bad"}})
    assert response.status_code == 400
    assert "must be a list" in response.json()["error"]


def test_sources_wire_refuses_non_object_entry(
    client: TestClient, settings_path: Path
) -> None:
    response = client.put("/api/settings", json={"calendar": {"sources": ["bad"]}})
    assert response.status_code == 400
    assert "must be an object" in response.json()["error"]


def test_calendar_sources_fact_reports_per_source_truth(
    client: TestClient, settings_path: Path
) -> None:
    settings = _put(client, {"calendar": {"sources": [
        {"label": "Work", "url": "https://work.example.test/cal.ics", "enabled": True},
        {"label": "Local", "url": "/tmp/local.ics", "enabled": False},
    ]}})
    facts = settings["_calendar_sources"]
    assert len(facts) == 2
    assert facts[0]["label"] == "Work"
    assert facts[0]["kind"] == "https"
    assert facts[0]["host"] == "work.example.test"
    assert facts[0]["egress"] is True
    assert facts[0]["enabled"] is True
    assert facts[0]["id"] == settings["calendar"]["sources"][0]["id"]
    assert facts[1]["label"] == "Local"
    assert facts[1]["kind"] == "file"
    assert facts[1]["egress"] is False
    assert facts[1]["enabled"] is False


def test_calendar_sources_fact_empty_when_no_sources(
    client: TestClient, settings_path: Path
) -> None:
    settings = _put(client, {"calendar": {"sources": []}})
    assert settings["_calendar_sources"] == []


def test_old_subscription_key_and_sources_fact_coexist(
    client: TestClient, settings_path: Path
) -> None:
    settings = _put(client, {"calendar": {"sources": [
        {"label": "Main", "url": "https://main.example.test/cal.ics"},
    ]}})
    assert "_calendar_subscription" in settings
    assert settings["_calendar_subscription"]["kind"] == "https"
    assert "_calendar_sources" in settings
    assert len(settings["_calendar_sources"]) == 1


def test_sources_wire_via_mcp(
    client: TestClient, settings_path: Path
) -> None:
    result = dispatch(
        "settings.update",
        {"patch": {"calendar": {"sources": [
            {"label": "MCP source", "url": "https://mcp.example.test/cal.ics"},
        ]}}},
        OWNER,
    )
    assert result["success"] is True
    sources = result["settings"]["calendar"]["sources"]
    assert len(sources) == 1
    assert sources[0]["label"] == "MCP source"
    assert sources[0]["id"]
    assert result["settings"]["_calendar_sources"][0]["kind"] == "https"
