"""Betterment AG2: one press answers, one press allows.

An Answer (``kind: "answer"``) that names the agent's CURRENT ``wait_id``
carries its own authority for that one wait, in every Control mode: no ARM.
The route refuses a stale wait; the chokepoint (``coder_steering.deliver`` /
``deliver_keys``) checks the pane and the wait again before the keystroke.
A plain steer (no ``kind``) still needs its grant.

The routes and the chokepoint run for real (the pane identity and the tmux
send are the doubles, as in test_web_routes_coders_steer.py); the audit goes
into a temp DB.
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
from holdspeak.config import Config
from holdspeak.db import core as dbcore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.context import WebContext
from holdspeak.web.routes.system.coder_steering_routes import build_coder_steering_router

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
QUESTION = (
    "Should the rollback flag live in config/flags.yaml (shared with staging) "
    "or in an env var (per host)? Answer 1 for config, 2 for env."
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _asking(**kw) -> SimpleNamespace:
    """A Claude Code session that asks (a Stop with a question), on pane %3."""
    base = {
        "agent": "claude", "session_id": "abc", "updated_at": _now(),
        "awaiting_response": True, "question": QUESTION, "wait_id": "w1",
        "lifecycle": "waiting", "hook_event_name": "Stop",
        "tmux_pane": "%3", "tmux_session": "hs", "tmux_window": "1", "tmux_pane_index": "0",
    }
    base.update(kw)
    return SimpleNamespace(**base)


def _permission(**kw) -> SimpleNamespace:
    """The same session at a permission prompt (Wants to run)."""
    fields = {
        "question": "Claude needs your permission to use Bash", "wait_id": "w2",
        "hook_event_name": "Notification", "notification_type": "permission_prompt",
    }
    fields.update(kw)
    return _asking(**fields)


@pytest.fixture(params=["safe", "neutral", "yolo"])
def env(request, tmp_path, monkeypatch):
    coder_steering.clear_grants()
    dbcore.reset_database()
    db = dbcore.Database(tmp_path / "holdspeak.db")
    mode = request.param
    monkeypatch.setattr(Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode=mode)))
    monkeypatch.setattr("holdspeak.db.get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        coder_steering, "resolve_pane_identity",
        lambda target, runner=None: {"status": "ok", "pane_id": "%3"},
    )
    app = FastAPI()

    @app.middleware("http")
    async def owner_principal(req, call_next):
        req.state.principal = OWNER
        return await call_next(req)

    app.include_router(build_coder_steering_router(WebContext(get_state=lambda: {}, broadcast=lambda *_: None)))
    sent: list[dict] = []
    monkeypatch.setattr(
        tmux_transport, "send_text_to_pane",
        lambda *, pane, text, submit=True, timeout_s=2.0: sent.append({"pane": pane, "text": text, "submit": submit}),
    )
    monkeypatch.setattr(
        tmux_transport, "send_keys_to_pane",
        lambda *, pane, keys, timeout_s=2.0: sent.append({"pane": pane, "keys": list(keys)}),
    )
    yield SimpleNamespace(client=TestClient(app), db=db, sent=sent, monkeypatch=monkeypatch, mode=mode)
    coder_steering.clear_grants()
    dbcore.reset_database()


def _register(monkeypatch, *sessions) -> None:
    monkeypatch.setattr(
        agent_context, "list_agent_sessions",
        lambda agent=None: [s for s in sessions if agent is None or s.agent == agent],
    )


def test_an_answer_with_the_current_wait_sends_without_an_arm(env) -> None:
    _register(env.monkeypatch, _asking())
    assert coder_steering.active_grants() == {}
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "1", "kind": "answer", "wait_id": "w1"})
    assert res.status_code == 200, res.json()
    assert res.json()["status"] == "delivered"
    assert env.sent == [{"pane": "%3", "text": "1", "submit": True}]
    # No grant was made: the press was the authority for this one wait.
    assert coder_steering.active_grants() == {}
    assert env.db.steering.list()[0].outcome == "delivered"


def test_a_stale_wait_is_refused_and_nothing_is_typed(env) -> None:
    _register(env.monkeypatch, _asking(wait_id="w9"))
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "1", "kind": "answer", "wait_id": "w1"})
    assert res.status_code == 409
    assert res.json()["status"] == "wait_not_current"
    assert res.json()["wait_id"] == "w9"
    assert env.sent == []


def test_a_wait_that_changes_before_the_keystroke_is_refused_by_the_chokepoint(env) -> None:
    _register(env.monkeypatch, _asking())
    # The route read w1; by the keystroke a permission prompt took its place.
    env.monkeypatch.setattr(coder_steering, "current_wait_episode", lambda key: "w1|approve")
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "1", "kind": "answer", "wait_id": "w1"})
    assert res.status_code == 409
    assert res.json()["status"] == "wait_not_current"
    assert env.sent == []


def test_a_plain_steer_still_needs_its_grant(env) -> None:
    if env.mode == "yolo":
        pytest.skip("YOLO steers a registered pane by its posture (as built)")
    _register(env.monkeypatch, _asking())
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "also add a README line"})
    assert res.status_code == 409
    assert res.json()["status"] == "unarmed"
    assert env.sent == []


def test_allow_sends_enter_on_the_current_permission_wait_without_an_arm(env) -> None:
    _register(env.monkeypatch, _permission())
    res = env.client.post(
        "/api/coders/claude:abc/keys", json={"keys": ["Enter"], "kind": "answer", "wait_id": "w2"},
    )
    assert res.status_code == 200, res.json()
    assert res.json()["status"] == "delivered"
    assert env.sent == [{"pane": "%3", "keys": [("named", "Enter")]}]
    assert coder_steering.active_grants() == {}


def test_deny_on_a_stale_permission_wait_is_refused(env) -> None:
    _register(env.monkeypatch, _permission(wait_id="w3"))
    res = env.client.post(
        "/api/coders/claude:abc/keys", json={"keys": ["Escape"], "kind": "answer", "wait_id": "w2"},
    )
    assert res.status_code == 409
    assert res.json()["status"] == "wait_not_current"
    assert env.sent == []


def test_the_policy_names_the_press_as_the_authority() -> None:
    from holdspeak.delivery.commands import decode_decision, encode_decision
    from holdspeak.operation_policy import describe_operation, resolve_policy

    def op(fixed: bool):
        return describe_operation(
            operation_id="coder:claude:abc:type_text", family="coder_steering",
            effect_class="terminal/type_text_and_keys", actor="owner", destination="%3" if fixed else "unresolved_pane",
            data_classes=("typed_text",), resource_scope="claude:abc", fixed_destination=fixed,
            consequence="execute_now",
        )

    for mode in ("safe", "neutral", "yolo"):
        decision = resolve_policy(op(True), mode=mode, owner_answer=True).to_dict()
        assert (decision["outcome"], decision["authority_basis"]) == ("allowed", "owner_answer"), mode
        assert decode_decision({"decision": encode_decision(decision)})["authority_basis"] == "owner_answer"
    # No pane that proves itself: the press alone never authorizes.
    assert resolve_policy(op(False), mode="neutral", owner_answer=True).to_dict()["outcome"] == "grant_required"
