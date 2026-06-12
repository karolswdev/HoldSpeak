"""HS-56-03 — the actuator broadcasts the presence mascot consumes.

The aftercare file-issue route now broadcasts `actuator_proposed` (wire-safe:
the human preview, never the machine payload); a rejected decision broadcasts
`actuator_result`; the executor's new `on_result` observer fires on executed
and failed — purely observationally (a callback failure never breaks the
audited transition). The existing never-egress-unapproved tests are untouched.
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.db import get_database, reset_database
from holdspeak.meeting_session import IntelSnapshot, MeetingState, TranscriptSegment
from holdspeak.plugins.actuator_executor import ActuatorExecutor
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks


@pytest.fixture
def temp_db_dir():
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    reset_database()
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def db(temp_db_dir):
    reset_database()
    return get_database(temp_db_dir / "test.db")


@pytest.fixture
def server(db):
    return MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )


@pytest.fixture
def broadcasts(server, monkeypatch):
    sent: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        server, "broadcast", lambda message_type, data: sent.append((message_type, data))
    )
    return sent


@pytest.fixture
def client(server):
    return TestClient(server.app)


def _meeting_with_accepted_action(db, meeting_id="m-act"):
    started = datetime(2026, 6, 10, 10, 0, 0)
    state = MeetingState(
        id=meeting_id,
        started_at=started,
        ended_at=datetime(2026, 6, 10, 11, 0, 0),
        title="Actuator meeting",
        segments=[TranscriptSegment(text="we must fix the login bug", speaker="Me", start_time=0.0, end_time=10.0)],
    )
    state.intel = IntelSnapshot(
        timestamp=60.0,
        topics=[],
        action_items=[{
            "id": "a1",
            "task": "Fix the login bug",
            "owner": "Me",
            "due": None,
            "status": "pending",
            "review_state": "accepted",
            "source_timestamp": None,
            "created_at": started.isoformat(),
        }],
        summary="",
    )
    db.meetings.save_meeting(state)
    return meeting_id


def test_aftercare_route_broadcasts_proposed_wire_safely(client, db, broadcasts):
    meeting_id = _meeting_with_accepted_action(db)
    response = client.post(
        f"/api/meetings/{meeting_id}/aftercare/file-issue",
        json={"action_item_id": "a1", "repo": "acme/widgets"},
    )
    assert response.status_code == 200, response.text

    proposed = [d for (t, d) in broadcasts if t == "actuator_proposed"]
    assert len(proposed) == 1
    data = proposed[0]
    assert data["meeting_id"] == meeting_id
    assert data["target"] and data["action"] and data["preview"]
    # Wire safety: the machine payload never rides the broadcast.
    assert "payload" not in data


def test_rejected_decision_broadcasts_a_result(client, db, broadcasts):
    meeting_id = _meeting_with_accepted_action(db, "m-rej")
    created = client.post(
        f"/api/meetings/{meeting_id}/aftercare/file-issue",
        json={"action_item_id": "a1", "repo": "acme/widgets"},
    ).json()["proposal"]

    decided = client.post(
        f"/api/meetings/{meeting_id}/proposals/{created['id']}/decision",
        json={"decision": "rejected"},
    )
    assert decided.status_code == 200

    results = [d for (t, d) in broadcasts if t == "actuator_result"]
    assert len(results) == 1
    assert results[0]["status"] == "rejected"
    assert results[0]["id"] == created["id"]
    assert "payload" not in results[0]

    # An approval records the decision only — no result broadcast (execution
    # is the executor's separate, later job).
    meeting2 = _meeting_with_accepted_action(db, "m-app")
    created2 = client.post(
        f"/api/meetings/{meeting2}/aftercare/file-issue",
        json={"action_item_id": "a1", "repo": "acme/widgets"},
    ).json()["proposal"]
    client.post(
        f"/api/meetings/{meeting2}/proposals/{created2['id']}/decision",
        json={"decision": "approved"},
    )
    assert len([d for (t, d) in broadcasts if t == "actuator_result"]) == 1


def test_executor_on_result_fires_on_executed_and_failed(db):
    meeting_id = _meeting_with_accepted_action(db, "m-exec")
    seen: list[dict] = []

    def make(connector):
        return ActuatorExecutor(
            db,
            connector=connector,
            allow_actuators=True,
            actor="test",
            on_result=seen.append,
        )

    # executed
    p1 = db.actuators.record_proposal(
        meeting_id=meeting_id, window_id="w", plugin_id="x", plugin_version="1",
        idempotency_key="k1", target="github", action="create_issue",
        preview="Create issue: fix login", payload={"title": "fix login"},
        reversible=True, required_capabilities=["github:write"],
    )
    db.actuators.transition_proposal(p1.id, to_status="approved", actor="test")
    make(lambda view: {"ok": True}).execute(p1.id)
    assert seen[-1]["status"] == "executed" and seen[-1]["id"] == p1.id
    assert "payload" not in seen[-1]

    # failed (connector explodes) — the observer sees it, the audit stands.
    p2 = db.actuators.record_proposal(
        meeting_id=meeting_id, window_id="w", plugin_id="x", plugin_version="1",
        idempotency_key="k2", target="github", action="create_issue",
        preview="Create issue: second", payload={"title": "second"},
        reversible=True, required_capabilities=["github:write"],
    )
    db.actuators.transition_proposal(p2.id, to_status="approved", actor="test")

    def boom(_view):
        raise RuntimeError("connector down")

    updated = make(boom).execute(p2.id)
    assert updated.status == "failed"
    assert seen[-1]["status"] == "failed" and "connector down" in (seen[-1]["error"] or "")

    # An exploding observer never breaks the transition it reports on.
    p3 = db.actuators.record_proposal(
        meeting_id=meeting_id, window_id="w", plugin_id="x", plugin_version="1",
        idempotency_key="k3", target="github", action="create_issue",
        preview="Create issue: third", payload={"title": "third"},
        reversible=True, required_capabilities=["github:write"],
    )
    db.actuators.transition_proposal(p3.id, to_status="approved", actor="test")
    bad_observer = ActuatorExecutor(
        db, connector=lambda v: {"ok": True}, allow_actuators=True, actor="test",
        on_result=lambda _d: (_ for _ in ()).throw(RuntimeError("observer boom")),
    )
    final = bad_observer.execute(p3.id)
    assert final.status == "executed"


def test_qlippy_events_mirror_the_dashboard_decision_exactly():
    repo = Path(__file__).resolve().parents[2]
    events = (repo / "web" / "src" / "scripts" / "qlippy-events.js").read_text()
    dashboard = (repo / "web" / "src" / "scripts" / "dashboard-app.js").read_text()
    # The identical route + body the dashboard sends.
    assert "/proposals/${data.id}/decision" in events
    assert "JSON.stringify({ decision })" in events
    assert "JSON.stringify({ decision })" in dashboard
    # Sticky proposed cards; the egress badge naming the target (HS-62-01
    # retired the privacy paragraphs); never the payload.
    assert "sticky: true" in events
    assert 'egress: { scope: "cloud", label: data.target' in events
    assert "data.payload" not in events
