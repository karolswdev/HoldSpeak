"""HS-49-03 — close the loop: accepted action -> actuator proposal.

Verifies the aftercare "file this accepted action" path:
`POST /api/meetings/{id}/aftercare/file-issue` records a `proposed` GitHub-issue
proposal through the EXISTING propose -> approve -> execute flow — no new write
primitive, nothing leaves the machine until a separate approval + an enabled,
allow-listed, host-injected connector. An unapproved proposal never executes.
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
from holdspeak.meeting_session import IntelSnapshot, MeetingState
from holdspeak.plugins.actuator_executor import (
    ActuatorExecutionError,
    ActuatorExecutor,
    ActuatorPolicyError,
)
from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

ISSUE_ACTUATOR_ID = "github_issue_actuator"


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


def _action(item_id, task, *, owner=None, review_state="pending"):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": "Friday",
        "status": "pending",
        "review_state": review_state,
        "source_timestamp": None,
        "created_at": datetime(2026, 6, 5, 10, 0, 0).isoformat(),
    }


@pytest.fixture
def seeded(db: Database):
    db.meetings.save_meeting(
        MeetingState(
            id="m1",
            started_at=datetime(2026, 6, 5, 10, 0, 0),
            title="API design follow-up",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[
                    _action("a-accepted", "Wire the rate limiter", owner="Priya", review_state="accepted"),
                    _action("a-pending", "Pick a name", review_state="pending"),
                ],
            ),
        )
    )


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
def test_file_issue_creates_proposed_proposal(client, db, seeded) -> None:
    res = client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a-accepted", "repo": "acme/app"},
    )
    assert res.status_code == 200
    proposal = res.json()["proposal"]
    assert proposal["status"] == "proposed"  # nothing executed
    assert proposal["target"] == "github"
    assert proposal["action"] == "create_issue"
    assert proposal["payload"]["repo"] == "acme/app"
    assert "Wire the rate limiter" in proposal["payload"]["title"]
    assert proposal["plugin_id"] == ISSUE_ACTUATOR_ID
    # It shows up through the existing read endpoint.
    listed = client.get("/api/meetings/m1/proposals").json()["proposals"]
    assert [p["id"] for p in listed] == [proposal["id"]]


@pytest.mark.integration
def test_file_issue_requires_accepted(client, seeded) -> None:
    res = client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a-pending", "repo": "acme/app"},
    )
    assert res.status_code == 400
    assert "accepted" in res.json()["error"].lower()


@pytest.mark.integration
def test_file_issue_validates_repo_and_item(client, seeded) -> None:
    assert client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a-accepted", "repo": "  "},
    ).status_code == 400
    assert client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "ghost", "repo": "acme/app"},
    ).status_code == 404


@pytest.mark.integration
def test_file_issue_is_idempotent(client, seeded) -> None:
    first = client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a-accepted", "repo": "acme/app"},
    ).json()["proposal"]
    second = client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a-accepted", "repo": "acme/app"},
    ).json()["proposal"]
    assert first["id"] == second["id"]  # same (meeting, action) → one proposal


@pytest.mark.integration
def test_filed_proposal_never_executes_until_approved_and_enabled(client, db, seeded) -> None:
    proposal = client.post(
        "/api/meetings/m1/aftercare/file-issue",
        json={"action_item_id": "a-accepted", "repo": "acme/app"},
    ).json()["proposal"]
    pid = proposal["id"]

    calls: list = []

    def stub_connector(view):
        calls.append(view)
        return {"url": "https://github.com/acme/app/issues/7", "issue": 7}

    # A proposed (un-approved) proposal is refused by the executor — no egress.
    enabled = ActuatorExecutor(
        db, connector=stub_connector, allow_actuators=True, allowed_actuator_ids=[ISSUE_ACTUATOR_ID]
    )
    with pytest.raises(ActuatorExecutionError):
        enabled.execute(pid)
    assert calls == []

    # Approve it through the existing decision endpoint (flips state only).
    decided = client.post(
        f"/api/meetings/m1/proposals/{pid}/decision",
        json={"decision": "approved", "decided_by": "karol"},
    )
    assert decided.json()["proposal"]["status"] == "approved"

    # Even approved, execution is refused while actuators are off (no egress).
    disabled = ActuatorExecutor(db, connector=stub_connector, allow_actuators=False)
    with pytest.raises(ActuatorPolicyError):
        disabled.execute(pid)
    assert calls == []

    # Enabled + allow-listed + approved → the existing connector executes + audits.
    result = enabled.execute(pid)
    assert result.status == "executed"
    assert len(calls) == 1
    assert result.result["issue"] == 7
    audit = db.actuators.list_audit(pid)
    assert [a.to_status for a in audit] == ["proposed", "approved", "executed"]
