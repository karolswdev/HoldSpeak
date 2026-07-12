"""HSM-15-03 — the mesh inbox: one window over everything in flight + everything
pending the human nod.

`GET /api/mesh/inbox` aggregates the two REAL queues (deferred intel + MIR
plugin runs) and every `proposed` actuator proposal across meeting AND desk
origins. Aggregation only: seeding goes through the real repos, and the
envelope carries exactly what a companion needs to render and DECIDE (origin +
target pick the existing decision route; the payload never rides the wire).
"""
from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session.models import MeetingState
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_mesh_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_mesh_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def _proposal(db: Database, *, key: str, **overrides):
    kwargs = dict(
        meeting_id="m1",
        window_id="w1",
        plugin_id="followup_ticket_actuator",
        plugin_version="1.0.0",
        idempotency_key=key,
        target="github",
        action="create_issue",
        preview="Open a follow-up issue for the unowned action item",
        payload={"repo": "acme/app", "title": "Follow up"},
    )
    kwargs.update(overrides)
    return db.actuators.record_proposal(**kwargs)


def test_inbox_aggregates_jobs_and_pending_proposals(env) -> None:
    db, client = env
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Q3 kickoff", segments=[])
    )
    # In flight on the hub: one deferred intel job + one queued plugin run.
    db.intel.enqueue_intel_job("m1", transcript_hash="h1")
    db.plugins.enqueue_plugin_run_job(
        meeting_id="m1", window_id="w1", plugin_id="risk_register",
        plugin_version="1.0.0", transcript_hash="h1", idempotency_key="pj1",
    )
    # Pending the nod: a meeting proposal AND a desk-origin one (no meeting anchor).
    meeting_prop = _proposal(db, key="k-meeting")
    desk_prop = _proposal(db, key="k-desk", meeting_id=None, origin="desk",
                          target="slack", action="send_message",
                          preview="Digest → #eng-updates")
    # A decided proposal must NOT ride the approval lane.
    decided = _proposal(db, key="k-decided")
    db.actuators.transition_proposal(decided.id, to_status="rejected", actor="test")

    body = client.get("/api/mesh/inbox").json()

    by_kind = {j["kind"] for j in body["jobs"]}
    assert by_kind == {"intel", "plugin"}
    intel = next(j for j in body["jobs"] if j["kind"] == "intel")
    assert intel["status"] == "queued"
    assert intel["meeting_id"] == "m1"
    assert intel["label"] == "Q3 kickoff"
    plugin = next(j for j in body["jobs"] if j["kind"] == "plugin")
    assert plugin["label"] == "risk_register"
    assert plugin["status"] == "queued"
    # The DB id is an integer; the wire id must be a kind-prefixed STRING
    # (the companion's rows are string-typed and unique across lanes).
    assert isinstance(plugin["id"], str) and plugin["id"].startswith("plugin:")

    # The approval lane: both origins, newest first, the decided row absent,
    # and NO payload on the wire.
    ids = [p["id"] for p in body["proposals"]]
    assert set(ids) == {meeting_prop.id, desk_prop.id}
    desk_row = next(p for p in body["proposals"] if p["id"] == desk_prop.id)
    assert desk_row["origin"] == "desk"
    assert desk_row["meeting_id"] is None
    assert desk_row["target"] == "slack"
    assert desk_row["preview"] == "Digest → #eng-updates"
    assert desk_row["commitment"]["approve"] == "Approve and send to Slack"
    assert desk_row["authorization_state"] == "proposed"
    assert desk_row["operation"]["effect_class"] == "slack/send_message"
    assert desk_row["policy_snapshot"]["mode"] == "neutral"
    assert desk_row["policy_snapshot"]["policy_version"] == "operation-policy/v2"
    assert desk_row["policy_snapshot"]["next_state"] == "awaiting_authorization"
    for p in body["proposals"]:
        assert "payload" not in p

    assert body["counts"]["pending_approvals"] == 2
    assert body["counts"]["queued"] >= 1


def test_inbox_empty_hub_is_an_honest_empty(env) -> None:
    _, client = env
    body = client.get("/api/mesh/inbox").json()
    assert body["jobs"] == []
    assert body["proposals"] == []
    assert body["counts"]["pending_approvals"] == 0


def test_list_pending_proposals_spans_origins_and_only_proposed(env) -> None:
    db, _ = env
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="t", segments=[])
    )
    a = _proposal(db, key="a")
    b = _proposal(db, key="b", meeting_id=None, origin="desk", target="webhook")
    c = _proposal(db, key="c")
    db.actuators.transition_proposal(c.id, to_status="approved", actor="test")

    pending = db.actuators.list_pending_proposals()
    assert {p.id for p in pending} == {a.id, b.id}
    assert all(p.status == "proposed" for p in pending)
