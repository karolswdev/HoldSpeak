"""Raw peek route tests (HS-111-11) — `GET /api/coders/{key}/peek?raw=1`.

The raw flag is an explicit opt-in on the SAME read route; the default
call must remain byte-identical to the pre-raw wire. The proof is
structural: the default-path fake refuses a `raw` kwarg outright, so
any leak of the flag into the legacy call is a TypeError, not a silent
behavior change. The consent spine (arm/steer/keys) is not touched
here — its own suites pass with zero edits.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.agent_context as agent_context
from holdspeak import coder_steering
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.coder_steering_routes import (
    build_coder_steering_router,
)


def _session() -> SimpleNamespace:
    return SimpleNamespace(
        agent="claude",
        session_id="abc",
        updated_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        awaiting_response=False,
        question=None,
        tmux_pane="%3",
        tmux_session="hs",
        tmux_window="1",
        tmux_pane_index="0",
    )


@pytest.fixture
def client(monkeypatch) -> TestClient:
    sessions = [_session()]
    monkeypatch.setattr(
        agent_context,
        "list_agent_sessions",
        lambda agent=None: [s for s in sessions if agent is None or s.agent == agent],
    )
    app = FastAPI()
    app.include_router(build_coder_steering_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def test_raw_1_opts_into_the_raw_peek(monkeypatch, client) -> None:
    seen: dict = {}

    def fake_peek(target, *, lines, last_hash, raw=False):
        seen.update(target=target, lines=lines, last_hash=last_hash, raw=raw)
        return {
            "status": "live",
            "hash": "h-raw",
            "raw": "\x1b[32mok\x1b[0m",
            "pane": {"width": 80, "height": 24, "cursor_x": 0, "cursor_y": 1},
        }

    monkeypatch.setattr(coder_steering, "peek_pane", fake_peek)
    res = client.get("/api/coders/claude:abc/peek?lines=50&raw=1")
    assert res.status_code == 200
    peek = res.json()["peek"]
    assert seen == {"target": "%3", "lines": 50, "last_hash": None, "raw": True}
    assert peek["raw"] == "\x1b[32mok\x1b[0m"
    assert peek["pane"]["height"] == 24


def test_default_call_never_learns_the_raw_flag(monkeypatch, client) -> None:
    """The legacy fake's signature HAS no raw kwarg — if the default
    path ever forwarded one, this would be a 500, not a 200."""

    def legacy_peek(target, *, lines, last_hash):
        return {"status": "live", "hash": "h", "lines": ["stripped"]}

    monkeypatch.setattr(coder_steering, "peek_pane", legacy_peek)
    res = client.get("/api/coders/claude:abc/peek")
    assert res.status_code == 200
    assert res.json()["peek"]["lines"] == ["stripped"]


def test_raw_0_is_the_stripped_default(monkeypatch, client) -> None:
    def legacy_peek(target, *, lines, last_hash):
        return {"status": "live", "hash": "h", "lines": ["stripped"]}

    monkeypatch.setattr(coder_steering, "peek_pane", legacy_peek)
    res = client.get("/api/coders/claude:abc/peek?raw=0")
    assert res.status_code == 200
    assert res.json()["peek"]["lines"] == ["stripped"]


def test_raw_hash_gate_rides_the_route(monkeypatch, client) -> None:
    seen: dict = {}

    def fake_peek(target, *, lines, last_hash, raw=False):
        seen["last_hash"] = last_hash
        return {"status": "not_modified", "hash": last_hash}

    monkeypatch.setattr(coder_steering, "peek_pane", fake_peek)
    res = client.get("/api/coders/claude:abc/peek?raw=1&last_hash=deadbeef")
    assert res.json()["peek"] == {"status": "not_modified", "hash": "deadbeef"}
    assert seen["last_hash"] == "deadbeef"


def test_relay_peek_forwards_the_raw_flag(monkeypatch, client) -> None:
    import holdspeak.coder_steering_relay as relay

    seen: dict = {}

    def fake_relay(node, verb, key, *, method="POST", body=None):
        seen.update(node=node, verb=verb, key=key, method=method)
        return {"status": "live"}

    monkeypatch.setattr(relay, "relay", fake_relay)
    monkeypatch.setattr(relay, "relay_http_code", lambda result: 200)
    res = client.get("/api/coders/relay/mini/peek?key=claude:abc&raw=1")
    assert res.status_code == 200
    assert seen["verb"] == "peek?lines=200&raw=1"


def test_relay_peek_default_omits_the_raw_flag(monkeypatch, client) -> None:
    import holdspeak.coder_steering_relay as relay

    seen: dict = {}

    def fake_relay(node, verb, key, *, method="POST", body=None):
        seen["verb"] = verb
        return {"status": "live"}

    monkeypatch.setattr(relay, "relay", fake_relay)
    monkeypatch.setattr(relay, "relay_http_code", lambda result: 200)
    client.get("/api/coders/relay/mini/peek?key=claude:abc")
    assert seen["verb"] == "peek?lines=200"
