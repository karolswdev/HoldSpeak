"""HS-2-08 / spec §9.8 — web API intent-control endpoints.

Verifies the four `/api/intents/*` control endpoints surface the
correct callbacks (`on_get_intent_controls`, `on_set_intent_profile`,
`on_set_intent_override`, `on_route_preview`) and degrade cleanly
when the callbacks are not wired.
"""

from __future__ import annotations

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.web_server import MeetingWebServer


def _bare_server() -> MeetingWebServer:
    return MeetingWebServer(
        on_bookmark=lambda *_a, **_kw: None,
        on_stop=lambda *_a, **_kw: None,
        get_state=lambda: None,
        host="127.0.0.1",
    )


@pytest.fixture
def bare_client() -> TestClient:
    return TestClient(_bare_server().app)


@pytest.mark.integration
def test_intent_controls_get_returns_safe_default_when_callback_unset(bare_client) -> None:
    response = bare_client.get("/api/intents/control")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is False
    assert body["profile"] == "balanced"
    assert body["available_profiles"] == []
    assert body["supported_intents"] == []
    assert body["override_intents"] == []


@pytest.mark.integration
def test_intent_profile_put_returns_501_when_callback_unset(bare_client) -> None:
    response = bare_client.put("/api/intents/profile", json={"profile": "architect"})
    assert response.status_code == 501
    body = response.json()
    assert body["success"] is False


@pytest.mark.integration
def test_intent_override_put_returns_501_when_callback_unset(bare_client) -> None:
    response = bare_client.put(
        "/api/intents/override",
        json={"intents": ["incident", "comms"]},
    )
    assert response.status_code == 501


@pytest.mark.integration
def test_intent_preview_post_returns_501_when_callback_unset(bare_client) -> None:
    response = bare_client.post(
        "/api/intents/preview",
        json={"profile": "balanced", "transcript": "Architecture review."},
    )
    assert response.status_code == 501


@pytest.mark.integration
def test_intent_controls_get_invokes_callback_and_returns_payload() -> None:
    captured = {"calls": 0}

    def on_get():
        captured["calls"] += 1
        return {
            "enabled": True,
            "profile": "architect",
            "available_profiles": ["balanced", "architect"],
            "supported_intents": ["architecture", "delivery"],
            "override_intents": ["architecture"],
        }

    server = MeetingWebServer(
        on_bookmark=lambda *_a, **_kw: None,
        on_stop=lambda *_a, **_kw: None,
        get_state=lambda: None,
        on_get_intent_controls=on_get,
        host="127.0.0.1",
    )
    client = TestClient(server.app)

    response = client.get("/api/intents/control")
    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert body["profile"] == "architect"
    assert body["override_intents"] == ["architecture"]
    assert captured["calls"] == 1


@pytest.mark.integration
def test_intent_profile_put_invokes_callback_with_profile_string() -> None:
    captured: dict[str, object] = {}

    def on_set(profile: str):
        captured["profile"] = profile
        return {"profile": profile, "available_profiles": ["balanced", "architect"]}

    server = MeetingWebServer(
        on_bookmark=lambda *_a, **_kw: None,
        on_stop=lambda *_a, **_kw: None,
        get_state=lambda: None,
        on_set_intent_profile=on_set,
        host="127.0.0.1",
    )
    client = TestClient(server.app)

    response = client.put("/api/intents/profile", json={"profile": "architect"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["controls"]["profile"] == "architect"
    assert captured["profile"] == "architect"


@pytest.mark.integration
def test_intent_override_put_invokes_callback_with_intent_list() -> None:
    captured: dict[str, object] = {}

    def on_set(intents):
        captured["intents"] = list(intents) if intents is not None else None
        return {"override_intents": intents or []}

    server = MeetingWebServer(
        on_bookmark=lambda *_a, **_kw: None,
        on_stop=lambda *_a, **_kw: None,
        get_state=lambda: None,
        on_set_intent_override=on_set,
        host="127.0.0.1",
    )
    client = TestClient(server.app)

    response = client.put(
        "/api/intents/override",
        json={"intents": ["incident", "comms"]},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert captured["intents"] == ["incident", "comms"]


@pytest.mark.integration
def test_intent_preview_post_invokes_route_preview_callback() -> None:
    captured: dict[str, object] = {}

    def on_preview(**kwargs):
        captured.update(kwargs)
        return {
            "profile": kwargs.get("profile") or "balanced",
            "active_intents": ["architecture"],
            "plugin_chain": ["project_detector", "requirements_extractor"],
        }

    server = MeetingWebServer(
        on_bookmark=lambda *_a, **_kw: None,
        on_stop=lambda *_a, **_kw: None,
        get_state=lambda: None,
        on_route_preview=on_preview,
        host="127.0.0.1",
    )
    client = TestClient(server.app)

    response = client.post(
        "/api/intents/preview",
        json={
            "profile": "architect",
            "threshold": 0.7,
            "intent_scores": {"architecture": 0.9},
            "override_intents": ["architecture"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["route"]["profile"] == "architect"
    assert "architecture" in body["route"]["active_intents"]
    # Callback received the keyword args we expected.
    assert captured["profile"] == "architect"
    assert captured["threshold"] == 0.7
    assert captured["intent_scores"] == {"architecture": 0.9}
    assert captured["override_intents"] == ["architecture"]
