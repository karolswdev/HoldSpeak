"""HS-37-03 — web API for actuator-proposal approval.

Verifies the read-side `GET /api/meetings/{id}/proposals` and the decision
endpoint `POST /api/meetings/{id}/proposals/{pid}/decision`. The safety
invariant under test: **viewing or deciding a proposal performs no side
effect** — approval only flips DB state (execution is HS-37-04).
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

from holdspeak.db import Database, get_database, reset_database
from holdspeak.meeting_session import MeetingState
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
def seeded(db: Database):
    db.meetings.save_meeting(
        MeetingState(id="m-prop", started_at=datetime(2026, 6, 4, 10, 0, 0), title="Proposals test")
    )
    proposal = db.actuators.record_proposal(
        meeting_id="m-prop",
        window_id="m-prop:w1",
        plugin_id="followup_ticket_actuator",
        plugin_version="1.0.0",
        idempotency_key="prop-key-1",
        target="github",
        action="create_issue",
        preview="Open a follow-up issue for the unowned action item",
        payload={"repo": "acme/app", "title": "Follow up"},
        reversible=True,
        required_capabilities=["actuator"],
    )
    return proposal


@pytest.fixture
def client() -> TestClient:
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


@pytest.mark.integration
def test_list_proposals_returns_persisted(client, seeded) -> None:
    response = client.get("/api/meetings/m-prop/proposals")
    assert response.status_code == 200
    body = response.json()
    assert body["meeting_id"] == "m-prop"
    assert len(body["proposals"]) == 1
    p = body["proposals"][0]
    assert p["status"] == "proposed"
    assert p["target"] == "github"
    assert p["action"] == "create_issue"
    assert p["reversible"] is True
    # The exact machine payload is surfaced for review.
    assert p["payload"] == {"repo": "acme/app", "title": "Follow up"}


@pytest.mark.integration
def test_list_proposals_404_for_unknown_meeting(client, db) -> None:
    response = client.get("/api/meetings/nope/proposals")
    assert response.status_code == 404


@pytest.mark.integration
def test_approve_flips_state_and_audits(client, db, seeded) -> None:
    response = client.post(
        f"/api/meetings/m-prop/proposals/{seeded.id}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["proposal"]["status"] == "approved"
    assert body["proposal"]["decided_by"] == "karol"
    assert body["proposal"]["executed_at"] is None  # approval != execution

    # The DB reflects it + an audit entry was written.
    record = db.actuators.get_proposal(seeded.id)
    assert record.status == "approved"
    audit = db.actuators.list_audit(seeded.id)
    assert [(a.from_status, a.to_status) for a in audit] == [
        (None, "proposed"),
        ("proposed", "approved"),
    ]


@pytest.mark.integration
def test_reject_is_terminal(client, db, seeded) -> None:
    ok = client.post(
        f"/api/meetings/m-prop/proposals/{seeded.id}/decision",
        json={"decision": "rejected"},
    )
    assert ok.status_code == 200
    assert ok.json()["proposal"]["status"] == "rejected"

    # Deciding a terminal proposal is an illegal transition → 400.
    again = client.post(
        f"/api/meetings/m-prop/proposals/{seeded.id}/decision",
        json={"decision": "approved"},
    )
    assert again.status_code == 400
    assert "illegal" in again.json()["error"].lower()


@pytest.mark.integration
def test_invalid_decision_value_is_400(client, seeded) -> None:
    response = client.post(
        f"/api/meetings/m-prop/proposals/{seeded.id}/decision",
        json={"decision": "executed"},  # not a human decision
    )
    assert response.status_code == 400


@pytest.mark.integration
def test_decision_on_unknown_proposal_is_404(client, seeded) -> None:
    response = client.post(
        "/api/meetings/m-prop/proposals/does-not-exist/decision",
        json={"decision": "approved"},
    )
    assert response.status_code == 404


@pytest.mark.integration
def test_proposal_from_other_meeting_is_404(client, db, seeded) -> None:
    # A proposal id that exists but belongs to a different meeting must not
    # be decidable via this meeting's path.
    db.meetings.save_meeting(
        MeetingState(id="m-other", started_at=datetime(2026, 6, 4, 11, 0, 0), title="Other")
    )
    response = client.post(
        f"/api/meetings/m-other/proposals/{seeded.id}/decision",
        json={"decision": "approved"},
    )
    assert response.status_code == 404
    # The original proposal is untouched.
    assert db.actuators.get_proposal(seeded.id).status == "proposed"
