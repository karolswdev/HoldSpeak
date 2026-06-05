"""HS-39-02: integration tests for the dictation correction-memory routes.

`GET/POST /api/dictation/corrections` record + read session corrections
through the `CorrectionStore` the server owns and shares with the live
runtime. Consumption (the routing nudge) is unit-tested on `IntentRouter` /
`apply_target_correction`; these cover the HTTP capture surface.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import holdspeak.config as config_module
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def settings_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    target = tmp_path / "config.json"
    monkeypatch.setattr(config_module, "CONFIG_FILE", target)
    return target


@pytest.fixture
def test_client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=MagicMock(),
            on_stop=MagicMock(),
            get_state=MagicMock(return_value={}),
        )
    )
    return TestClient(server.app)


def test_corrections_empty_by_default(test_client: TestClient, settings_path: Path) -> None:
    resp = test_client.get("/api/dictation/corrections")
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is False  # opt-in; default config has it off
    assert body["size"] == 0
    assert body["items"] == []
    assert "intent" in body["kinds"] and "target" in body["kinds"]


def test_record_and_list_correction(test_client: TestClient, settings_path: Path) -> None:
    resp = test_client.post(
        "/api/dictation/corrections",
        json={"kind": "intent", "text": "fix the cli thing", "value": "code_exercise"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"recorded": True, "size": 1}

    listed = test_client.get("/api/dictation/corrections").json()
    assert listed["size"] == 1
    assert listed["items"][0]["kind"] == "intent"
    assert listed["items"][0]["value"] == "code_exercise"
    assert listed["items"][0]["key"] == "fix the cli thing"


def test_record_rejects_bad_kind(test_client: TestClient, settings_path: Path) -> None:
    resp = test_client.post(
        "/api/dictation/corrections",
        json={"kind": "nonsense", "text": "x", "value": "y"},
    )
    assert resp.status_code == 400


def test_record_rejects_empty_text(test_client: TestClient, settings_path: Path) -> None:
    resp = test_client.post(
        "/api/dictation/corrections",
        json={"kind": "intent", "text": "   ", "value": "code_exercise"},
    )
    assert resp.status_code == 400


def test_record_silently_drops_secret(test_client: TestClient, settings_path: Path) -> None:
    resp = test_client.post(
        "/api/dictation/corrections",
        json={"kind": "intent", "text": "token is sk-abcdef0123456789abcd", "value": "code_exercise"},
    )
    assert resp.status_code == 200
    assert resp.json() == {"recorded": False, "size": 0}
    assert test_client.get("/api/dictation/corrections").json()["size"] == 0
