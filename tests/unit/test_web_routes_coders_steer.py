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
from holdspeak.config import Config
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
    monkeypatch.setattr(
        Config, "load",
        classmethod(lambda cls: SimpleNamespace(control_mode="neutral")),
    )
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


def test_yolo_steers_registered_pane_without_an_arm_and_returns_receipt(env) -> None:
    env.monkeypatch.setattr(
        Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="yolo"))
    )
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    res = env.client.post(
        "/api/coders/claude:abc/steer",
        json={"text": "ship it", "expected_pane_id": "%3"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "delivered"
    assert body["policy"]["authority_basis"] == "control_posture"
    assert body["policy"]["reason_code"] == "registered_steering_posture_allowed"
    assert body["receipt"] == {
        "id": f"steering:{body['audit_id']}",
        "source_ref": "coder_session:claude:abc",
        "actual_destination": "%3",
        "authority_basis": "control_posture",
        "control_mode": "yolo",
        "policy_version": "operation-policy/v2",
        "effect_class": "terminal/type_text_and_keys",
        "outcome": "delivered",
    }
    assert coder_steering.active_grants() == {}
    trail = env.db.steering.list()
    assert trail[0].policy_snapshot["mode"] == "yolo"
    assert trail[0].operation["destination"] == "%3"
    projection = next(
        row for row in env.db.projections.list(limit=20)["projections"]
        if row["source_kind"] == "steering_audit"
    )
    assert projection["subject_ref"] == "coder_session:claude:abc"
    assert projection["authority_basis"] == "control_posture"
    assert projection["control_mode"] == "yolo"
    assert projection["policy_version"] == "operation-policy/v2"


def test_yolo_refuses_missing_or_changed_pane_identity_before_typing(env) -> None:
    env.monkeypatch.setattr(
        Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="yolo"))
    )
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    missing = env.client.post(
        "/api/coders/claude:abc/steer", json={"text": "no snapshot"}
    )
    assert missing.status_code == 409
    assert missing.json()["status"] == "pane_identity_required"
    _pin_identity(env.monkeypatch, "%99")
    changed = env.client.post(
        "/api/coders/claude:abc/steer",
        json={"text": "old pane", "expected_pane_id": "%3"},
    )
    assert changed.status_code == 409
    assert changed.json()["status"] == "pane_mismatch"
    assert changed.json().get("revoked") is not True
    assert env.sent == []


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


def test_expired_grant_keeps_its_typed_refusal_and_receipt(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    env.client.post("/api/coders/claude:abc/arm", json={})
    with coder_steering._GRANTS_LOCK:
        coder_steering._GRANTS["claude:abc"]["expires_at"] = 0.0
    env.frames.clear()
    res = env.client.post(
        "/api/coders/claude:abc/steer", json={"text": "too late"}
    )
    assert res.status_code == 409
    assert res.json()["status"] == "expired"
    assert res.json()["receipt"]["outcome"] == "expired"
    assert coder_steering.active_grants() == {}
    assert len(env.frames) == 1


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


def test_rails_object_grounds_into_a_steer(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    # Fake the rails hydrator at its seam so the route folds it in.
    from holdspeak.grounding import GroundingBlock
    import holdspeak.grounding_rails as gr

    env.monkeypatch.setattr(
        gr,
        "hydrate_rails_refs",
        lambda refs, project_map=None, runner=None: (
            [GroundingBlock("rails:story", "HS-88-01", "HS-88-01 Rails", "hs/hs", "the story body")],
            [],
        ),
    )
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post(
        "/api/coders/claude:abc/steer",
        json={
            "text": "what does this story want?",
            "submit": False,
            "grounding": {"rails": [{"repo": "hs", "project": "hs", "kind": "story", "id": "HS-88-01"}]},
        },
    )
    assert res.status_code == 200
    sent = env.sent[0]["text"]
    assert '--- from rails:story: "HS-88-01 Rails" (hs/hs) ---' in sent
    assert "the story body" in sent
    assert env.db.steering.list()[0].grounding == ["rails:story:HS-88-01"]


def test_unknown_rails_ref_refuses_naming_the_id(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch)
    import holdspeak.grounding_rails as gr

    env.monkeypatch.setattr(
        gr,
        "hydrate_rails_refs",
        lambda refs, project_map=None, runner=None: ([], ["story:HS-99-99"]),
    )
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post(
        "/api/coders/claude:abc/steer",
        json={"text": "q", "grounding": {"rails": [{"repo": "hs", "project": "hs", "kind": "story", "id": "HS-99-99"}]}},
    )
    assert res.status_code == 400
    assert res.json()["unknown_ids"] == ["story:HS-99-99"]


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


# --- classify (HS-87-05): keep as note ------------------------------------


def test_keep_as_note_creates_a_real_note_with_lineage(env) -> None:
    _register(
        env.monkeypatch,
        _session(question="Should we merge #303?", awaiting_response=True),
    )
    res = env.client.post("/api/coders/claude:abc/keep-note", json={})
    assert res.status_code == 201
    note = res.json()["note"]
    assert "Should we merge #303?" in note["body_markdown"]
    # Lineage names the session, the agent, and the moment.
    assert "claude:abc" in note["body_markdown"]
    assert "claude" in note["tags"]
    # It files and opens like any primitive: it is really in the store.
    assert env.db.notes.get(note["id"]) is not None


def test_keep_as_note_accepts_an_override_title_and_body(env) -> None:
    _register(env.monkeypatch, _session(question="raw ask"))
    res = env.client.post(
        "/api/coders/claude:abc/keep-note",
        json={"title": "Merge decision", "body": "keep this instead"},
    )
    note = res.json()["note"]
    assert note["title"] == "Merge decision"
    assert "keep this instead" in note["body_markdown"]


def test_keep_as_note_refuses_when_there_is_nothing_to_keep(env) -> None:
    _register(
        env.monkeypatch,
        _session(question=None, last_assistant_text=None),
    )
    res = env.client.post("/api/coders/claude:abc/keep-note", json={})
    assert res.status_code == 400


def test_keep_as_note_unknown_session_is_404(env) -> None:
    _register(env.monkeypatch)
    res = env.client.post("/api/coders/claude:nope/keep-note", json={})
    assert res.status_code == 404


# --- key control route (HS-89-01) ------------------------------------------


def _capture_keys(env):
    keyed: list[dict] = []
    env.monkeypatch.setattr(
        tmux_transport,
        "send_keys_to_pane",
        lambda *, pane, keys, timeout_s=2.0: keyed.append({"pane": pane, "keys": keys}),
    )
    return keyed


def test_unarmed_keys_is_a_typed_409_and_audited(env) -> None:
    _register(env.monkeypatch, _session())
    keyed = _capture_keys(env)
    res = env.client.post("/api/coders/claude:abc/keys", json={"keys": ["C-c"]})
    assert res.status_code == 409
    assert res.json()["status"] == "unarmed"
    assert keyed == []
    trail = env.db.steering.list()
    assert trail[0].outcome == "unarmed"


def test_armed_keys_interrupt_reaches_the_verified_pane(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    keyed = _capture_keys(env)
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/keys", json={"keys": ["C-c"]})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "delivered" and body["pane_id"] == "%3"
    assert keyed == [{"pane": "%3", "keys": [("named", "C-c")]}]
    trail = env.db.steering.list()
    assert trail[0].outcome == "delivered" and trail[0].text_head == "C-c"


def test_yolo_keys_reach_the_expected_registered_pane_without_an_arm(env) -> None:
    env.monkeypatch.setattr(
        Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="yolo"))
    )
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    keyed = _capture_keys(env)
    res = env.client.post(
        "/api/coders/claude:abc/keys",
        json={"keys": ["C-c"], "expected_pane_id": "%3"},
    )
    assert res.status_code == 200
    assert res.json()["policy"]["authority_basis"] == "control_posture"
    assert keyed == [{"pane": "%3", "keys": [("named", "C-c")]}]
    assert coder_steering.active_grants() == {}


def test_unknown_key_is_refused_by_name_and_types_nothing(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    keyed = _capture_keys(env)
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/keys", json={"keys": ["sudo reboot"]})
    assert res.status_code == 409
    assert res.json()["status"] == "unknown_key"
    assert res.json()["detail"] == "sudo reboot"
    assert keyed == []


def test_recycled_pane_keys_refuse_disarm_and_frame(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    keyed = _capture_keys(env)
    env.client.post("/api/coders/claude:abc/arm", json={})
    env.frames.clear()
    _pin_identity(env.monkeypatch, "%99")  # the pane was recycled
    res = env.client.post("/api/coders/claude:abc/keys", json={"keys": ["C-c"]})
    assert res.status_code == 409
    assert res.json()["status"] == "pane_mismatch"
    assert res.json()["revoked"] is True
    assert keyed == []
    assert coder_steering.active_grants() == {}
    assert len(env.frames) == 1  # the disarm is visible everywhere


# --- attach to any pane: the pane:%N path (HS-89-02) ------------------------


def test_panes_discovery_lists_every_pane(env) -> None:
    env.monkeypatch.setattr(
        coder_steering,
        "list_panes",
        lambda: {"status": "ok", "panes": [
            {"pane_id": "%7", "session": "hand", "window": "0",
             "command": "bash", "title": "", "active": True}]},
    )
    res = env.client.get("/api/coders/steering/panes")
    assert res.status_code == 200
    assert res.json()["panes"][0]["pane_id"] == "%7"


def test_peek_any_pane_is_free_no_registry(env) -> None:
    # A hand-started pane (never registered) is watchable with NO grant,
    # resolved directly from its pane:%N key.
    env.monkeypatch.setattr(
        coder_steering, "peek_pane",
        lambda target, lines=200, last_hash=None: {"status": "live", "hash": "h", "lines": ["$ ok"]},
    )
    res = env.client.get("/api/coders/pane:%7/peek")
    assert res.status_code == 200
    body = res.json()
    assert body["agent"] == "pane" and body["peek"]["status"] == "live"
    assert body["grant"]["armed"] is False  # watching is free


def test_arm_and_key_control_any_pane_under_a_grant(env) -> None:
    _pin_identity(env.monkeypatch, "%7")  # the raw pane resolves to itself
    keyed = _capture_keys(env)
    arm = env.client.post("/api/coders/pane:%7/arm", json={})
    assert arm.status_code == 200 and arm.json()["status"] == "armed"
    res = env.client.post("/api/coders/pane:%7/keys", json={"keys": ["C-c"]})
    assert res.status_code == 200
    assert res.json()["status"] == "delivered" and res.json()["pane_id"] == "%7"
    assert keyed == [{"pane": "%7", "keys": [("named", "C-c")]}]
    trail = env.db.steering.list()
    assert trail[0].session_key == "pane:%7" and trail[0].text_head == "C-c"


def test_yolo_controls_an_exact_raw_pane_without_an_arm(env) -> None:
    env.monkeypatch.setattr(
        Config, "load", classmethod(lambda cls: SimpleNamespace(control_mode="yolo"))
    )
    _pin_identity(env.monkeypatch, "%7")
    keyed = _capture_keys(env)
    res = env.client.post("/api/coders/pane:%7/keys", json={"keys": ["C-c"]})
    assert res.status_code == 200
    assert res.json()["pane_id"] == "%7"
    assert res.json()["policy"]["authority_basis"] == "control_posture"
    assert keyed == [{"pane": "%7", "keys": [("named", "C-c")]}]


def test_a_bad_pane_key_is_a_400(env) -> None:
    for key in ("pane:", "pane:7", "pane:work", "pane:%7:0"):
        res = env.client.post(f"/api/coders/{key}/arm", json={})
        assert res.status_code == 400
        assert res.json()["error"] == "key must be pane:%N"


def test_registry_path_still_works_unchanged(env) -> None:
    # HS-89-02 must not regress Phase 87: an agent:session_id key steers
    # exactly as before.
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/steer", json={"text": "hi"})
    assert res.status_code == 200 and res.json()["pane_id"] == "%3"


# --- cross-machine relay routes (HS-89-03) ---------------------------------


def _capture_relay(env):
    calls: list[dict] = []

    def fake_relay(node, verb, key, *, method="POST", body=None):
        calls.append({"node": node, "verb": verb, "key": key, "method": method, "body": body})
        # canned "delivered on the far node"
        return {"status": "delivered", "pane_id": "%5", "node": node}

    from holdspeak import coder_steering_relay
    env.monkeypatch.setattr(coder_steering_relay, "relay", fake_relay)
    env.monkeypatch.setattr(coder_steering_relay, "relay_http_code", lambda r: 200)
    return calls


def test_relay_keys_forwards_node_key_and_sequence(env) -> None:
    calls = _capture_relay(env)
    res = env.client.post(
        "/api/coders/relay/beta/keys",
        json={"key": "pane:%5", "keys": ["C-c"], "expected_pane_id": "%5"},
    )
    assert res.status_code == 200
    assert res.json()["node"] == "beta"
    assert calls == [{"node": "beta", "verb": "keys", "key": "pane:%5",
                      "method": "POST", "body": {
                          "keys": ["C-c"], "expected_pane_id": "%5"}}]


def test_relay_steer_drops_key_from_the_forwarded_body(env) -> None:
    calls = _capture_relay(env)
    env.client.post("/api/coders/relay/beta/steer",
                    json={"key": "claude:x", "text": "ship it", "submit": False})
    assert calls[0]["verb"] == "steer" and calls[0]["key"] == "claude:x"
    assert calls[0]["body"] == {"text": "ship it", "submit": False}  # no key in the body


def test_relay_peek_is_a_get_with_the_key(env) -> None:
    calls = _capture_relay(env)
    env.client.get("/api/coders/relay/beta/peek", params={"key": "pane:%5", "lines": 50})
    assert calls[0]["method"] == "GET" and calls[0]["key"] == "pane:%5"
    assert calls[0]["verb"].startswith("peek?lines=50")


def test_relay_requires_a_key(env) -> None:
    _capture_relay(env)
    res = env.client.post("/api/coders/relay/beta/keys", json={"keys": ["C-c"]})
    assert res.status_code == 400


# --- the factory routes (HS-90-01) -----------------------------------------


def test_factory_spawn_returns_the_new_pane(env) -> None:
    from holdspeak import coder_factory
    env.monkeypatch.setattr(
        coder_factory, "spawn",
        lambda name, command=None: {"status": "spawned", "session": name, "pane_id": "%9"},
    )
    res = env.client.post("/api/coders/factory/spawn", json={"name": "work"})
    assert res.status_code == 200 and res.json()["pane_id"] == "%9"


def test_factory_spawn_bad_name_is_409(env) -> None:
    from holdspeak import coder_factory
    env.monkeypatch.setattr(
        coder_factory, "spawn",
        lambda name, command=None: {"status": "bad_name", "detail": "no"},
    )
    res = env.client.post("/api/coders/factory/spawn", json={"name": "a b"})
    assert res.status_code == 409 and res.json()["status"] == "bad_name"


def test_factory_rename_requires_target(env) -> None:
    res = env.client.post("/api/coders/factory/rename", json={"name": "x"})
    assert res.status_code == 400


def test_kill_unarmed_is_a_typed_409(env) -> None:
    _register(env.monkeypatch, _session())
    res = env.client.post("/api/coders/claude:abc/kill", json={})
    assert res.status_code == 409 and res.json()["status"] == "unarmed"


def test_armed_kill_ends_the_pane(env) -> None:
    _register(env.monkeypatch, _session())
    _pin_identity(env.monkeypatch, "%3")
    from holdspeak import coder_factory
    killed: list = []
    env.monkeypatch.setattr(
        coder_factory, "kill",
        lambda key, *, current_target, scope="pane", agent="": killed.append((key, scope))
        or {"status": "killed", "pane_id": "%3", "scope": scope},
    )
    env.client.post("/api/coders/claude:abc/arm", json={})
    res = env.client.post("/api/coders/claude:abc/kill", json={"scope": "session"})
    assert res.status_code == 200 and res.json()["status"] == "killed"
    assert killed == [("claude:abc", "session")]
