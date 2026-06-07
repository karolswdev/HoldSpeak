"""HS-49-01 — web API for the meeting aftercare digest.

Verifies `GET /api/meetings/{id}/aftercare`: it aggregates open-by-owner,
decisions, and the since-last-meeting diff over real data, and it is a pure
read (no writes, no side effects). 404 for an unknown meeting.
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


def _action(item_id, task, *, owner=None, status="pending"):
    return {
        "id": item_id,
        "task": task,
        "owner": owner,
        "due": None,
        "status": status,
        "review_state": "pending",
        "source_timestamp": None,
        "created_at": datetime(2026, 6, 4, 10, 0, 0).isoformat(),
    }


@pytest.fixture
def seeded(db: Database):
    db.meetings.save_meeting(
        MeetingState(
            id="prior",
            started_at=datetime(2026, 6, 1, 9, 0, 0),
            title="Kickoff",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[_action("p1", "Set up CI", owner="Bob", status="done")],
            ),
        )
    )
    db.meetings.save_meeting(
        MeetingState(
            id="current",
            started_at=datetime(2026, 6, 4, 10, 0, 0),
            title="Follow-up",
            intel=IntelSnapshot(
                timestamp=0.0,
                action_items=[_action("c1", "Wire the API", owner="alice")],
            ),
        )
    )
    db.plugins.record_artifact(
        artifact_id="current-decisions",
        meeting_id="current",
        artifact_type="decisions",
        title="Decisions",
        structured_json={"decisions": [{"decision": "Adopt feature flags"}]},
        plugin_id="decision_capture",
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
def test_aftercare_aggregates_real_data(client, seeded) -> None:
    response = client.get("/api/meetings/current/aftercare")
    assert response.status_code == 200
    body = response.json()
    assert body["meeting_id"] == "current"
    assert body["is_empty"] is False
    assert body["open_items"]["total"] == 1
    assert body["open_items"]["by_owner"][0]["owner"] == "alice"
    assert [d["decision"] for d in body["decisions"]] == ["Adopt feature flags"]

    since = body["since_last_meeting"]
    assert since["previous_meeting"]["id"] == "prior"
    assert since["changed"] is True
    assert [a["task"] for a in since["new_actions"]] == ["Wire the API"]
    assert [d["decision"] for d in since["new_decisions"]] == ["Adopt feature flags"]
    assert [a["task"] for a in since["closed_actions"]] == ["Set up CI"]


@pytest.mark.integration
def test_aftercare_is_read_only(client, seeded, db) -> None:
    before = db.meetings.list_action_items(include_completed=True, meeting_id="current")
    client.get("/api/meetings/current/aftercare")
    after = db.meetings.list_action_items(include_completed=True, meeting_id="current")
    assert [(i.id, i.status) for i in before] == [(i.id, i.status) for i in after]


@pytest.mark.integration
def test_aftercare_404_for_unknown_meeting(client, db) -> None:
    response = client.get("/api/meetings/nope/aftercare")
    assert response.status_code == 404
