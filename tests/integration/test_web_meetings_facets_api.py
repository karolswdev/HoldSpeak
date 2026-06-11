"""HS-55-04 — server-side facets on GET /api/meetings.

date_from / date_to / speaker / tag / has_open_actions filter in SQL over
the whole archive, compose with each other and with full-text ``search``,
and the no-params call keeps its exact pre-facet shape. Plus
``GET /api/meetings/facets`` (distinct speakers + tags) for the filter row.
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


def _meeting(db, mid, *, day, speaker, tags=(), text="hello world", open_action=False):
    started = datetime(2026, 3, day, 10, 0, 0)
    state = MeetingState(
        id=mid,
        started_at=started,
        ended_at=datetime(2026, 3, day, 11, 0, 0),
        title=f"meeting {mid}",
        tags=list(tags),
        segments=[
            TranscriptSegment(text=text, speaker=speaker, start_time=0.0, end_time=30.0)
        ],
    )
    if open_action:
        state.intel = IntelSnapshot(
            timestamp=60.0,
            topics=[],
            action_items=[
                {
                    "id": f"{mid}-a1",
                    "task": "follow up",
                    "owner": speaker,
                    "due": None,
                    "status": "pending",
                    "review_state": "pending",
                    "source_timestamp": None,
                    "created_at": started.isoformat(),
                }
            ],
            summary="",
        )
    db.meetings.save_meeting(state)


@pytest.fixture
def archive(db):
    _meeting(db, "m-early", day=1, speaker="Alice", tags=["planning"], text="zebra topic")
    _meeting(db, "m-mid", day=10, speaker="Bob", tags=["retro"], text="zebra and budget", open_action=True)
    _meeting(db, "m-late", day=20, speaker="Alice", tags=["planning", "q3"], text="quarter goals")
    return db


def _ids(payload):
    return {m["id"] for m in payload["meetings"]}


def test_each_facet_filters_alone(client, archive):
    assert _ids(client.get("/api/meetings", params={"speaker": "Alice"}).json()) == {"m-early", "m-late"}
    assert _ids(client.get("/api/meetings", params={"tag": "retro"}).json()) == {"m-mid"}
    assert _ids(client.get("/api/meetings", params={"has_open_actions": "true"}).json()) == {"m-mid"}
    assert _ids(client.get("/api/meetings", params={"date_from": "2026-03-05"}).json()) == {"m-mid", "m-late"}
    # A bare date_to is inclusive of the whole day.
    assert _ids(client.get("/api/meetings", params={"date_to": "2026-03-10"}).json()) == {"m-early", "m-mid"}


def test_facets_compose_with_each_other_and_with_search(client, archive):
    combined = client.get(
        "/api/meetings",
        params={"speaker": "Alice", "tag": "planning", "date_from": "2026-03-15"},
    ).json()
    assert _ids(combined) == {"m-late"}

    # search alone finds both zebra meetings; + speaker narrows to Alice's.
    search = client.get("/api/meetings", params={"search": "zebra"}).json()
    assert _ids(search) == {"m-early", "m-mid"}
    narrowed = client.get(
        "/api/meetings", params={"search": "zebra", "speaker": "Alice"}
    ).json()
    assert _ids(narrowed) == {"m-early"}
    # Search results carry the same summary shape (flat intel_status string).
    assert isinstance(search["meetings"][0]["intel_status"], str)


def test_facets_see_the_whole_archive_not_a_page(client, archive):
    # m-early is the oldest (outside a limit=1 first page) — the facet
    # still finds it because filtering happens in SQL.
    page = client.get(
        "/api/meetings", params={"limit": 1, "tag": "planning", "date_to": "2026-03-05"}
    ).json()
    assert _ids(page) == {"m-early"}


def test_no_params_keeps_the_existing_shape(client, archive):
    payload = client.get("/api/meetings").json()
    assert _ids(payload) == {"m-early", "m-mid", "m-late"}
    assert payload["total"] == 3
    row = payload["meetings"][0]
    for key in (
        "id", "started_at", "ended_at", "title", "duration_seconds",
        "segment_count", "action_item_count", "tags", "intel_status",
        "intel_status_detail",
    ):
        assert key in row


def test_facet_values_endpoint(client, archive):
    facets = client.get("/api/meetings/facets").json()
    assert facets["speakers"] == ["Alice", "Bob"]
    assert facets["tags"] == ["planning", "q3", "retro"]
