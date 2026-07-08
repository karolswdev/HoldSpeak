"""Steer + audit routes (HS-87-03).

deliver() is exercised for real (fake runner via monkeypatched
resolve_pane_identity, fake transport via monkeypatched
send_text_to_pane, audit into a temp DB) — the route's duties pinned:
typed 409 refusals, the revocation frame, the audit read-back.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.agent_context as agent_context
import holdspeak.tmux_transport as tmux_transport
from holdspeak import coder_steering
from holdspeak.db import core as dbcore
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.coder_steering_routes import (
    build_coder_steering_router,
)


def _iso_now() -> str:
    return (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


def _session(**kw) -> SimpleNamespace:
    base = {
        "agent": "claude",
        "session_id": "abc",
        "updated_at": _iso_now(),
        "awaiting_response": True,
        "question": "ship it?",
        "tmux_pane": "%3",
        "tmux_session": "hs",
        "tmux_window": "1",
        "tmux_pane_index": "0",
    }
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture
def env(tmp_path, monkeypatch):
    coder_steering.clear_grants()
    dbcore.reset_database()
    db = dbcore.Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    frames: list = []
    app = FastAPI()
    app.include_router(
        build_coder_steering_router(
            WebContext(
                get_state=lambda: {},
                broadcast=lambda kind, data: frames.append(data),
            )
        )
    )
    sent: list[dict] = []
    monkeypatch.setattr(
        tmux_transport,
        "send_text_to_pane",
        lambda *, pane, text, submit=True, timeout_s=2.0: sent.append(
            {"pane": pane, "text": text, "submit": submit}
        ),
    )
    yield SimpleNamespace(
        client=TestClient(app), db=db, frames=frames, sent=sent, monkeypatch=monkeypatch
    )
    coder_steering.clear_grants()
    dbcore.reset_database()


def _register(monkeypatch, *sessions) -> None:
    monkeypatch.setattr(
        agent_context,
        "list_agent_sessions",
        lambda agent=None: [s for s in sessions if agent is None or s.agent == agent],
    )


def _pin_identity(monkeypatch, pane_id="%3") -> None:
    monkeypatch.setattr(
        coder_steering,
        "resolve_pane_identity",
        lambda target, runner=None: {"status": "ok", "pane_id": pane_id},
    )


def test_unarmed_steer_is_a_typed_409_and_audited(env) -> None:
    _register(env.monkeypatch, _session())
    res = env.client.post(
        "/api/coders/claude:abc/steer", json={"text": "do the thing"}
    )
    assert res.status_code == 409
    assert res.json()["status"] == "unarmed"
    assert env.sent == []
    trail = env.db.steering.list()
    assert len(trail) == 1
    assert trail[0].outcome == "unarmed"
    assert trail[0].session_key == "claude:abc"


def test_armed_steer_delivers_exactly_as_composed(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    env.client.post("/api/coders/claude:abc/arm", json={})
    text = "first line\nsecond line"
    res = env.client.post(
        "/api/coders/claude:abc/steer", json={"text": text, "submit": True}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "delivered"
    assert body["pane_id"] == "%3"
    assert env.sent == [{"pane": "%3", "text": text, "submit": True}]
    trail = env.db.steering.list()
    assert trail[0].outcome == "delivered"
    assert trail[0].agent == "claude"
    assert trail[0].pane_id == "%3"


def test_no_submit_steer_leaves_enter_unpressed(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    env.client.post("/api/coders/claude:abc/arm", json={})
    env.client.post(
        "/api/coders/claude:abc/steer", json={"text": "partial", "submit": False}
    )
    assert env.sent[0]["submit"] is False


def test_recycled_pane_steer_refuses_disarms_and_frames(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    env.client.post("/api/coders/claude:abc/arm", json={})
    env.frames.clear()
    _pin_identity(env.monkeypatch, "%99")  # the registry target moved
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "hi"})
    assert res.status_code == 409
    body = res.json()
    assert body["status"] == "pane_mismatch"
    assert body["revoked"] is True
    assert env.sent == []
    assert coder_steering.active_grants() == {}
    assert len(env.frames) == 1  # the disarm is visible everywhere
    trail = env.db.steering.list()
    assert trail[0].outcome == "pane_mismatch"


def test_empty_text_is_a_400(env) -> None:
    _register(env.monkeypatch, _session())
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "   "})
    assert res.status_code == 400


def test_audit_route_reads_the_trail_newest_first(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    env.client.post("/api/coders/claude:abc/steer", json={"text": "refused one"})
    env.client.post("/api/coders/claude:abc/arm", json={})
    env.client.post("/api/coders/claude:abc/steer", json={"text": "delivered one"})
    res = env.client.get("/api/coders/steering/audit?limit=10")
    assert res.status_code == 200
    audit = res.json()["audit"]
    assert [a["outcome"] for a in audit] == ["delivered", "unarmed"]
    assert audit[0]["text_head"] == "delivered one"
    assert "text" not in audit[0]  # heads and hashes only
