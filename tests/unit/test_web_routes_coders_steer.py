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


def _seed_meeting(db, mid="m_steer", title="Kickoff"):
    """A real meeting + intel row so grounding hydrates from the store."""
    from datetime import datetime

    from holdspeak.meeting_session import IntelSnapshot, MeetingState

    db.meetings.save_meeting(
        MeetingState(
            id=mid,
            started_at=datetime(2026, 7, 1, 10, 0, 0),
            ended_at=datetime(2026, 7, 1, 11, 0, 0),
            title=title,
            segments=[],
            intel=IntelSnapshot(
                timestamp=1.0,
                summary="We decided to ship Friday.",
                action_items=[],
            ),
        )
    )
    return mid


def test_grounded_steer_carries_the_object_into_the_pane(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    mid = _seed_meeting(env.db)
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post(
        "/api/coders/claude:abc/steer",
        json={
            "text": "summarize the decision",
            "submit": False,
            "grounding": {"meeting_ids": [mid]},
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "delivered"
    sent_text = env.sent[0]["text"]
    assert sent_text.startswith("summarize the decision")
    assert '--- from meeting: "Kickoff"' in sent_text
    assert "ship Friday" in sent_text
    assert sent_text.rstrip().endswith("(1 object grounded)")
    # The audit row names the ref that rode along.
    trail = env.db.steering.list()
    assert trail[0].grounding == [f"meeting:{mid}"]


def test_preview_returns_the_exact_send_text_without_delivering(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    mid = _seed_meeting(env.db)
    env.client.post("/api/coders/claude:abc/arm", json={})
    body = {
        "text": "the ask",
        "submit": False,
        "grounding": {"meeting_ids": [mid]},
    }
    preview = env.client.post(
        "/api/coders/claude:abc/steer", json={**body, "preview": True}
    ).json()
    assert preview["status"] == "preview"
    assert env.sent == []  # preview never types
    delivered = env.client.post("/api/coders/claude:abc/steer", json=body).json()
    assert delivered["status"] == "delivered"
    # executed == previewed: the pane got exactly the previewed text.
    assert env.sent[0]["text"] == preview["text"]


def test_over_cap_grounding_refuses_at_compose_time(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    # A giant artifact body blows the 8 KB steer cap.
    mid = _seed_meeting(env.db)
    env.db.plugins.record_artifact(
        artifact_id="big_art",
        meeting_id=mid,
        artifact_type="note",
        title="Huge",
        body_markdown="z" * 9000,
    )
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post(
        "/api/coders/claude:abc/steer",
        json={"text": "q", "grounding": {"artifact_ids": ["big_art"]}},
    )
    assert res.status_code == 409
    assert res.json()["status"] == "grounding_over_cap"
    assert env.sent == []


def test_unknown_grounding_ref_refuses_naming_the_id(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post(
        "/api/coders/claude:abc/steer",
        json={"text": "q", "grounding": {"meeting_ids": ["ghost"]}},
    )
    assert res.status_code == 400
    assert res.json()["unknown_ids"] == ["ghost"]


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
