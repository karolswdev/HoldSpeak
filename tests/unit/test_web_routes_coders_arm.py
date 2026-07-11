"""Arm / disarm / grants routes (HS-87-02).

The registry and tmux are faked at their seams; what's pinned here is
the route layer's own duty: staleness refused BY NAME, refusals as
typed 409s, the grant riding the peek envelope, and every arming
motion broadcasting its `scope:"coder"` frame.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.agent_context as agent_context
from holdspeak import coder_steering
from holdspeak.config import Config
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.coder_steering_routes import (
    build_coder_steering_router,
)


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


@pytest.fixture(autouse=True)
def _fresh_grants(monkeypatch):
    monkeypatch.setattr(
        Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="neutral"))
    )
    coder_steering.clear_grants()
    yield
    coder_steering.clear_grants()


@pytest.fixture
def frames() -> list:
    return []


@pytest.fixture
def client(frames) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_coder_steering_router(
            WebContext(
                get_state=lambda: {},
                broadcast=lambda kind, data: frames.append((kind, data)),
            )
        )
    )
    return TestClient(app)


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


def test_arm_pins_the_pane_and_frames_the_bus(monkeypatch, client, frames) -> None:
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch, "%3")
    res = client.post("/api/coders/claude:abc/arm", json={})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "armed"
    assert body["pane_id"] == "%3"
    assert body["expires_in_seconds"] == coder_steering.ARM_DEFAULT_TTL_SECONDS
    assert frames == [
        (
            "intel_status",
            {
                "state": "ready",
                "scope": "coder",
                "capability": {"kind": "coder", "id": "claude:abc", "name": "claude"},
            },
        )
    ]


def test_arm_refuses_a_stale_session_naming_the_staleness(
    monkeypatch, client, frames
) -> None:
    old = datetime.now(timezone.utc) - timedelta(minutes=45)
    _register(monkeypatch, _session(updated_at=_iso(old)))
    res = client.post("/api/coders/claude:abc/arm", json={})
    assert res.status_code == 409
    body = res.json()
    assert body["status"] == "stale_session"
    assert "stale session cannot be armed" in body["detail"]
    assert frames == []
    assert coder_steering.active_grants() == {}


def test_arm_refuses_a_session_that_never_saw_tmux(monkeypatch, client) -> None:
    _register(
        monkeypatch,
        _session(tmux_pane=None, tmux_session=None, tmux_window=None, tmux_pane_index=None),
    )
    res = client.post("/api/coders/claude:abc/arm", json={})
    assert res.status_code == 409
    assert res.json()["status"] == "no_pane"


def test_arm_refuses_when_the_pane_cannot_prove_itself(monkeypatch, client) -> None:
    _register(monkeypatch, _session())
    monkeypatch.setattr(
        coder_steering,
        "resolve_pane_identity",
        lambda target, runner=None: {"status": "pane_gone", "detail": "no such pane"},
    )
    res = client.post("/api/coders/claude:abc/arm", json={})
    assert res.status_code == 409
    assert res.json()["status"] == "pane_gone"


def test_arm_unknown_session_is_404(monkeypatch, client) -> None:
    _register(monkeypatch)
    assert client.post("/api/coders/claude:nope/arm", json={}).status_code == 404


def test_neutral_caps_future_arm_at_its_mode_preset(monkeypatch, client) -> None:
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch)
    res = client.post("/api/coders/claude:abc/arm", json={"ttl_seconds": 999_999})
    assert res.json()["expires_in_seconds"] == coder_steering.ARM_DEFAULT_TTL_SECONDS
    assert res.json()["control_mode"] == "neutral"
    assert res.json()["commitment"] == "Arm pane %3 for 15 minutes"


def test_yolo_allows_the_hard_one_hour_arm_ceiling(monkeypatch, client) -> None:
    monkeypatch.setattr(
        Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="yolo"))
    )
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch)
    res = client.post("/api/coders/claude:abc/arm", json={"ttl_seconds": 999_999})
    assert res.json()["expires_in_seconds"] == coder_steering.ARM_MAX_TTL_SECONDS


def test_disarm_is_immediate_idempotent_and_framed(
    monkeypatch, client, frames
) -> None:
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch)
    client.post("/api/coders/claude:abc/arm", json={})
    frames.clear()
    res = client.post("/api/coders/claude:abc/disarm")
    assert res.json() == {"status": "disarmed", "key": "claude:abc", "was_armed": True}
    assert len(frames) == 1
    again = client.post("/api/coders/claude:abc/disarm")
    assert again.json()["was_armed"] is False
    assert len(frames) == 1  # no motion, no frame


def test_peek_envelope_carries_the_grant_state(monkeypatch, client) -> None:
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch)
    monkeypatch.setattr(
        coder_steering,
        "peek_pane",
        lambda target, *, lines, last_hash: {"status": "live", "hash": "h", "lines": []},
    )
    before = client.get("/api/coders/claude:abc/peek").json()
    assert before["grant"] == {"armed": False, "expires_in_seconds": None}
    client.post("/api/coders/claude:abc/arm", json={})
    after = client.get("/api/coders/claude:abc/peek").json()
    assert after["grant"]["armed"] is True
    assert after["grant"]["expires_in_seconds"] > 0


def test_grants_route_lists_live_grants(monkeypatch, client) -> None:
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch, "%3")
    client.post("/api/coders/claude:abc/arm", json={})
    res = client.get("/api/coders/steering/grants")
    grants = res.json()["grants"]
    assert grants["claude:abc"]["pane_id"] == "%3"


def test_expiry_frames_ride_the_next_read(monkeypatch, client, frames) -> None:
    _register(monkeypatch, _session())
    _pin_identity(monkeypatch)
    client.post("/api/coders/claude:abc/arm", json={})
    frames.clear()
    # Force the grant past its window at the store level.
    with coder_steering._GRANTS_LOCK:
        coder_steering._GRANTS["claude:abc"]["expires_at"] = 0.0
    res = client.get("/api/coders/steering/grants")
    assert res.json()["grants"] == {}
    assert len(frames) == 1  # the expiry announced itself on the bus
    assert frames[0][1]["capability"]["id"] == "claude:abc"
