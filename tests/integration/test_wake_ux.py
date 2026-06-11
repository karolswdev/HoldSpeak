"""HS-60-03 — the armed UX: the one-shot Type-it route + the surface locks."""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.desktop_presence import _STATE_META, build_presence_window_view
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

_REPO = Path(__file__).resolve().parents[2]


def _client(on_wake_type=None):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
            on_wake_type=on_wake_type,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


# ── the one-shot Type-it route ───────────────────────────────────────────────


def test_type_route_types_once_and_burns_the_token():
    store = {"tok-1": "ship the fix."}

    def on_wake_type(token):
        return store.pop(token, None)

    client = _client(on_wake_type)
    first = client.post("/api/dictation/wake/type", json={"token": "tok-1"})
    assert first.status_code == 200
    assert first.json() == {"success": True, "typed": "ship the fix."}
    second = client.post("/api/dictation/wake/type", json={"token": "tok-1"})
    assert second.status_code == 404
    assert "already used" in second.json()["error"]


def test_type_route_refuses_without_a_token():
    client = _client(lambda token: "x")
    response = client.post("/api/dictation/wake/type", json={})
    assert response.status_code == 400


def test_type_route_503_without_a_runtime():
    client = _client(None)
    response = client.post("/api/dictation/wake/type", json={"token": "t"})
    assert response.status_code == 503


def test_type_route_never_accepts_client_text():
    # The payload carries text — it must be ignored; only the stored
    # preview can ever be typed.
    seen = {}

    def on_wake_type(token):
        seen["token"] = token
        return "the stored preview"

    client = _client(on_wake_type)
    response = client.post(
        "/api/dictation/wake/type",
        json={"token": "tok", "text": "rm -rf injected"},
    )
    assert response.json()["typed"] == "the stored preview"
    assert seen == {"token": "tok"}


# ── the armed state on the surfaces ──────────────────────────────────────────


def test_armed_is_a_first_class_presence_state():
    assert "armed" in _STATE_META
    view = build_presence_window_view({"state": "armed", "detail": "say it"})
    assert view.state == "armed"
    assert view.label == "Armed"
    assert view.visible is True  # an active window state, never hidden


def test_qlippy_dock_maps_armed():
    js = (_REPO / "web" / "src" / "scripts" / "qlippy.js").read_text()
    assert 'armed: "listening"' in js


def test_wake_preview_card_ships_with_the_safety_copy():
    js = (_REPO / "web" / "src" / "scripts" / "qlippy-events.js").read_text()
    assert "onWakePreview" in js
    assert '"wake_preview"' in js
    assert "Nothing has been typed" in js
    assert "/api/dictation/wake/type" in js
    assert "sticky: true" in js  # the preview waits for the user


def test_settings_section_states_the_honest_truths():
    page = (_REPO / "web" / "src" / "pages" / "settings.astro").read_text()
    assert "Wake word" in page
    assert "previewed, never typed" in page
    assert "downloads the detection models once" in page  # the egress note
    assert "a false detection would type into whatever app is focused" in page
    assert "Desktop presence too" in page  # the indicator recommendation
    for marker in (
        'x-model="settings.wake_word.model"',
        'x-model="settings.wake_word.action"',
        'x-model.number="settings.wake_word.threshold"',
        'x-model.number="settings.wake_word.armed_window_seconds"',
    ):
        assert marker in page, marker
