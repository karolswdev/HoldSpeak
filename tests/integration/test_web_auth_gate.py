"""Integration tests for the web-runtime auth gate + bind guard (HS-25-02).

Policy: enforced ONLY off-loopback. Loopback binds stay open; a non-loopback
bind requires a token both to bind and on every request (except /health and the
device-audio WS, which has its own PSK).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from holdspeak.web_server import MeetingWebServer


def _callbacks():
    return {
        "on_bookmark": MagicMock(return_value={"timestamp": 1.0, "label": "x"}),
        "on_stop": MagicMock(return_value={"status": "stopped"}),
        "get_state": MagicMock(return_value={"id": "t", "duration": 1, "bookmarks": []}),
    }


def test_loopback_runtime_is_open_no_token_required():
    cb = _callbacks()
    server = MeetingWebServer(host="127.0.0.1", auth_token="", **cb)
    client = TestClient(server.app)
    # Loopback: open exactly as before, even with no token configured.
    assert client.get("/health").status_code == 200
    assert client.get("/api/state").status_code == 200


def test_nonloopback_runtime_requires_token():
    cb = _callbacks()
    server = MeetingWebServer(host="0.0.0.0", auth_token="s3cret", **cb)
    client = TestClient(server.app)

    # No token → 401 on data routes.
    assert client.get("/api/state").status_code == 401
    # /health stays open for liveness probes.
    assert client.get("/health").status_code == 200
    # Valid token via header → allowed.
    assert client.get("/api/state", headers={"X-HoldSpeak-Token": "s3cret"}).status_code == 200
    # Valid token via Authorization: Bearer → allowed.
    assert client.get(
        "/api/state", headers={"Authorization": "Bearer s3cret"}
    ).status_code == 200
    # Valid token via ?token= (browser navigation over a tunnel) → allowed.
    assert client.get("/api/state?token=s3cret").status_code == 200
    # Wrong token → 401.
    assert client.get(
        "/api/state", headers={"X-HoldSpeak-Token": "nope"}
    ).status_code == 401
    # Static assets stay open (no secrets; needed to render a token prompt).
    # A missing asset is 404, never 401 — proving the gate let it through.
    assert client.get("/_built/does-not-exist.js").status_code != 401


def test_nonloopback_bind_without_token_is_refused():
    cb = _callbacks()
    server = MeetingWebServer(host="0.0.0.0", auth_token="", **cb)
    # The app constructs fine, but start() must refuse to expose it unauthenticated.
    with pytest.raises(RuntimeError, match="without an auth token"):
        server.start()
