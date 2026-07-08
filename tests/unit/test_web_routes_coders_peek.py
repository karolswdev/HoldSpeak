"""Peek route tests (HS-87-01) — `GET /api/coders/{key}/peek`.

The registry and the pane capture are both faked at their seams
(`holdspeak.agent_context.list_agent_sessions`, the coder_steering
runner); the route's own duties are pinned: key parsing, the honest
envelope (stale, awaiting), and typed absences instead of 500s.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.agent_context as agent_context
from holdspeak import coder_steering
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.coders import build_coders_router


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _session(**kw) -> SimpleNamespace:
    base = {
        "agent": "claude",
        "session_id": "abc",
        "updated_at": _iso(datetime.now(timezone.utc)),
        "awaiting_response": False,
        "question": None,
        "tmux_pane": "%3",
        "tmux_session": "hs",
        "tmux_window": "1",
        "tmux_pane_index": "0",
    }
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(build_coders_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def _register(monkeypatch, *sessions) -> None:
    monkeypatch.setattr(
        agent_context,
        "list_agent_sessions",
        lambda agent=None: [
            s for s in sessions if agent is None or s.agent == agent
        ],
    )


def test_peek_returns_the_pane_body_in_the_envelope(monkeypatch, client) -> None:
    _register(monkeypatch, _session(awaiting_response=True, question="ship it?"))
    monkeypatch.setattr(
        coder_steering,
        "peek_pane",
        lambda target, *, lines, last_hash: {
            "status": "live",
            "hash": "h1",
            "lines": [f"pane={target}", f"lines={lines}"],
        },
    )
    res = client.get("/api/coders/claude:abc/peek?lines=50")
    assert res.status_code == 200
    body = res.json()
    assert body["key"] == "claude:abc"
    assert body["awaiting_response"] is True
    assert body["question"] == "ship it?"
    assert body["stale"] is False
    assert body["peek"]["lines"] == ["pane=%3", "lines=50"]


def test_peek_passes_the_hash_gate_through(monkeypatch, client) -> None:
    seen: dict = {}

    def fake_peek(target, *, lines, last_hash):
        seen["last_hash"] = last_hash
        return {"status": "not_modified", "hash": last_hash}

    _register(monkeypatch, _session())
    monkeypatch.setattr(coder_steering, "peek_pane", fake_peek)
    res = client.get("/api/coders/claude:abc/peek?last_hash=deadbeef")
    assert res.json()["peek"] == {"status": "not_modified", "hash": "deadbeef"}
    assert seen["last_hash"] == "deadbeef"


def test_peek_unknown_session_is_a_typed_404(monkeypatch, client) -> None:
    _register(monkeypatch)
    res = client.get("/api/coders/claude:nope/peek")
    assert res.status_code == 404
    assert res.json() == {"status": "unknown_session", "key": "claude:nope"}


def test_peek_malformed_key_is_a_400(client) -> None:
    res = client.get("/api/coders/justakey/peek")
    assert res.status_code == 400
    assert "agent:session_id" in res.json()["error"]


def test_peek_record_without_tmux_is_no_pane(monkeypatch, client) -> None:
    _register(
        monkeypatch,
        _session(
            tmux_pane=None, tmux_session=None, tmux_window=None, tmux_pane_index=None
        ),
    )
    res = client.get("/api/coders/claude:abc/peek")
    assert res.status_code == 200
    assert res.json()["peek"] == {"status": "no_pane"}


def test_peek_marks_a_thirty_minute_old_record_stale(monkeypatch, client) -> None:
    old = datetime.now(timezone.utc) - timedelta(minutes=45)
    _register(monkeypatch, _session(updated_at=_iso(old)))
    monkeypatch.setattr(
        coder_steering,
        "peek_pane",
        lambda target, *, lines, last_hash: {"status": "live", "hash": "h", "lines": []},
    )
    res = client.get("/api/coders/claude:abc/peek")
    body = res.json()
    assert body["stale"] is True
    assert body["peek"]["status"] == "live"  # watching stays free, honestly marked


def test_peek_pane_gone_rides_the_envelope_not_a_500(monkeypatch, client) -> None:
    _register(monkeypatch, _session())
    monkeypatch.setattr(
        coder_steering,
        "peek_pane",
        lambda target, *, lines, last_hash: {
            "status": "pane_gone",
            "detail": "can't find pane %3",
        },
    )
    res = client.get("/api/coders/claude:abc/peek")
    assert res.status_code == 200
    assert res.json()["peek"]["status"] == "pane_gone"
