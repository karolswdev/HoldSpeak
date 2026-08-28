"""Calendar subscription settings transport proofs for HS-144-02."""
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
