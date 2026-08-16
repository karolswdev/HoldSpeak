"""HS-132-07 — PUT /api/meetings/{id} renames ONE archived meeting.

Get Info offered Rename for every primitive while meetings had no route to
take it, so the typed name died in the client. This is that route: it writes
the named meeting's title, refuses an empty one, and answers 404 for a
meeting that is not there.
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
from holdspeak.meeting_session import MeetingState, TranscriptSegment
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
def client(db):
    server = MeetingWebServer(
        WebRuntimeCallbacks(
            on_bookmark=lambda *_a, **_k: None,
            on_stop=lambda *_a, **_k: None,
            get_state=lambda: None,
        ),
        host="127.0.0.1",
    )
    return TestClient(server.app)


@pytest.fixture
def archive(db):
    for mid, title in (("m-1", "Standup"), ("m-2", "Retro")):
        db.meetings.save_meeting(
            MeetingState(
                id=mid,
                started_at=datetime(2026, 3, 1, 10, 0, 0),
                ended_at=datetime(2026, 3, 1, 11, 0, 0),
                title=title,
                tags=["planning"],
                segments=[
                    TranscriptSegment(
                        text="hello world", speaker="Alice", start_time=0.0, end_time=3.0
                    )
                ],
            )
        )
    return db


def test_rename_writes_the_named_meeting_only(client, archive):
    response = client.put("/api/meetings/m-1", json={"title": "Quarter review"})
    assert response.status_code == 200, response.text
    assert response.json()["meeting"]["title"] == "Quarter review"

    # The archive agrees, and the neighbour was not touched.
    assert archive.meetings.get_meeting("m-1").title == "Quarter review"
    assert archive.meetings.get_meeting("m-2").title == "Retro"


def test_rename_keeps_the_meeting_tags(client, archive):
    client.put("/api/meetings/m-1", json={"title": "Quarter review"})
    assert archive.meetings.get_meeting("m-1").tags == ["planning"]


def test_rename_refuses_an_empty_title(client, archive):
    response = client.put("/api/meetings/m-1", json={"title": "   "})
    assert response.status_code == 400
    assert "title" in response.json()["error"]
    assert archive.meetings.get_meeting("m-1").title == "Standup"


def test_rename_refuses_a_body_without_a_title(client, archive):
    assert client.put("/api/meetings/m-1", json={"tags": ["x"]}).status_code == 400


def test_rename_of_an_unknown_meeting_is_404(client, archive):
    assert client.put("/api/meetings/nope", json={"title": "X"}).status_code == 404
