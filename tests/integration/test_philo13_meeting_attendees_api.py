"""PHILO-13-14 C4: meeting list rows carry the people in the meeting.

The fixture uses the real calendar parser/conductor and event-linked
scheduled-recording route,
then persists meetings through ``Database.save_meeting``.  It deliberately
does not seed a list response or calendar row with a test double.
"""
from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip(
    "fastapi.testclient",
    reason="requires meeting/web dependencies (install with `.[meeting]`)",
)
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.requires_meeting]

from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
from holdspeak.config.integrations import CalendarConfig, CalendarSource
from holdspeak.db import Database, get_database, reset_database
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


def _calendar_feed(start: datetime) -> bytes:
    end = start + timedelta(hours=1)
    return f"""\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//HoldSpeak test//EN
BEGIN:VEVENT
UID:philo13-attendees
DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}
DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:Calendar planning
ATTENDEE:mailto:bob@example.com
ATTENDEE:mailto:alice@example.com
ATTENDEE:mailto:bob@example.com
END:VEVENT
END:VCALENDAR
""".encode("utf-8")


def _ingest_calendar_event(db: Database, tmp_path: Path):
    start = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(hours=2)
    feed = tmp_path / "work.ics"
    feed.write_bytes(_calendar_feed(start))

    config = MagicMock()
    config.calendar = CalendarConfig(
        sources=[
            CalendarSource(
                id="work",
                label="Work",
                url=str(feed),
                enabled=True,
            )
        ]
    )
    config.meeting.auto_record = "off"
    config.meeting.auto_record_lead_minutes = 5
    conductor = CalendarIngestConductor(
        db_factory=lambda: db,
        config_loader=lambda: config,
        tick_interval=9999,
    )
    assert conductor.refresh() is True
    events = db.calendar_events.list_all()
    assert len(events) == 1
    return events[0], start


def _seed_attendee_meeting(db: Database, client: TestClient, tmp_path: Path) -> str:
    event, start = _ingest_calendar_event(db, tmp_path)

    linked = client.post(
        "/api/scheduled-recordings",
        json={"calendar_event_id": event.id},
    )
    assert linked.status_code == 201, linked.text
    linked_event_id = linked.json()["schedule"]["calendar_event_id"]
    assert linked_event_id == event.id

    db.meetings.save_meeting(
        MeetingState(
            id="meeting-with-attendees",
            started_at=start.replace(tzinfo=None),
            ended_at=(start + timedelta(hours=1)).replace(tzinfo=None),
            title="Quarterly review",
            calendar_event_id=linked_event_id,
            segments=[
                TranscriptSegment(
                    text="Priya shared the plan",
                    speaker=" Priya ",
                    start_time=0.0,
                    end_time=10.0,
                ),
                TranscriptSegment(
                    text="Bob confirmed the date",
                    speaker="bob@example.com",
                    start_time=10.0,
                    end_time=20.0,
                ),
                TranscriptSegment(
                    text="Priya closed the discussion",
                    speaker="Priya",
                    start_time=20.0,
                    end_time=30.0,
                ),
                TranscriptSegment(
                    text="No speaker label",
                    speaker="   ",
                    start_time=30.0,
                    end_time=40.0,
                ),
                TranscriptSegment(
                    text="Zoe gave the final note",
                    speaker="Zoe, PhD",
                    start_time=40.0,
                    end_time=50.0,
                ),
            ],
        )
    )
    db.meetings.save_meeting(
        MeetingState(
            id="meeting-without-participants",
            started_at=start.replace(tzinfo=None) - timedelta(hours=1),
            ended_at=start.replace(tzinfo=None) - timedelta(minutes=30),
            title="Quiet review",
        )
    )
    return "meeting-with-attendees"


def _row(response, meeting_id: str) -> dict:
    assert response.status_code == 200, response.text
    rows = response.json()["meetings"]
    return next(row for row in rows if row["id"] == meeting_id)


def test_calendar_projection_preserves_ingested_attendees(
    db: Database, tmp_path: Path
) -> None:
    event, _ = _ingest_calendar_event(db, tmp_path)

    assert event.attendees == ("bob@example.com", "alice@example.com")


def test_list_projects_real_transcript_and_calendar_attendees(
    client: TestClient, db: Database, tmp_path: Path
) -> None:
    meeting_id = _seed_attendee_meeting(db, client, tmp_path)

    row = _row(client.get("/api/meetings"), meeting_id)

    assert row["title"] == "Quarterly review"
    assert "Priya" not in row["title"]
    assert row["attendees"] == [
        "Priya",
        "Zoe, PhD",
        "alice@example.com",
        "bob@example.com",
    ]
    summary = next(
        item
        for item in db.meetings.list_meetings()
        if item.id == meeting_id
    )
    assert summary.attendees == row["attendees"]
    assert _row(client.get("/api/meetings"), meeting_id)["attendees"] == row["attendees"]


def test_search_and_parked_list_keep_the_attendees_contract(
    client: TestClient, db: Database, tmp_path: Path
) -> None:
    meeting_id = _seed_attendee_meeting(db, client, tmp_path)

    searched = _row(client.get("/api/meetings", params={"search": "Priya"}), meeting_id)
    assert searched["attendees"] == [
        "Priya",
        "Zoe, PhD",
        "alice@example.com",
        "bob@example.com",
    ]

    parked = client.delete(f"/api/meetings/{meeting_id}")
    assert parked.status_code == 200, parked.text
    parked_row = _row(
        client.get("/api/meetings", params={"parked": "true"}), meeting_id
    )
    assert parked_row["attendees"] == [
        "Priya",
        "Zoe, PhD",
        "alice@example.com",
        "bob@example.com",
    ]


def test_transcript_only_meeting_has_sorted_trimmed_attendees(
    client: TestClient, db: Database
) -> None:
    db.meetings.save_meeting(
        MeetingState(
            id="transcript-only",
            started_at=datetime(2026, 10, 3, 9, 0, 0),
            ended_at=datetime(2026, 10, 3, 9, 30, 0),
            title="Transcript only",
            segments=[
                TranscriptSegment("z", " Zed ", 0.0, 1.0),
                TranscriptSegment("blank", "  ", 1.0, 2.0),
                TranscriptSegment("a", "Alice", 2.0, 3.0),
                TranscriptSegment("z2", "Zoë, PhD", 3.0, 4.0),
            ],
        )
    )

    row = _row(client.get("/api/meetings"), "transcript-only")

    assert row["attendees"] == ["Alice", "Zed", "Zoë, PhD"]
    summary = next(
        item
        for item in db.meetings.list_meetings()
        if item.id == "transcript-only"
    )
    assert summary.attendees == row["attendees"]


def test_calendar_only_meeting_has_ingested_attendees(
    client: TestClient, db: Database, tmp_path: Path
) -> None:
    event, start = _ingest_calendar_event(db, tmp_path)
    linked = client.post(
        "/api/scheduled-recordings",
        json={"calendar_event_id": event.id},
    )
    assert linked.status_code == 201, linked.text
    db.meetings.save_meeting(
        MeetingState(
            id="calendar-only",
            started_at=start.replace(tzinfo=None),
            ended_at=(start + timedelta(hours=1)).replace(tzinfo=None),
            title="Calendar only",
            calendar_event_id=linked.json()["schedule"]["calendar_event_id"],
        )
    )

    row = _row(client.get("/api/meetings"), "calendar-only")

    assert row["attendees"] == ["alice@example.com", "bob@example.com"]
    summary = next(
        item
        for item in db.meetings.list_meetings()
        if item.id == "calendar-only"
    )
    assert summary.attendees == row["attendees"]


def test_meeting_without_participants_returns_empty_attendees(
    client: TestClient, db: Database
) -> None:
    db.meetings.save_meeting(
        MeetingState(
            id="meeting-without-participants",
            started_at=datetime(2026, 10, 3, 10, 0, 0),
            ended_at=datetime(2026, 10, 3, 10, 30, 0),
            title="Quiet review",
        )
    )

    row = _row(client.get("/api/meetings"), "meeting-without-participants")

    assert row["attendees"] == []
