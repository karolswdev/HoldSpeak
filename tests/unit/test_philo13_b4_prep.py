"""PHILO-13-09 B4: the People brief finds a report's calendar and work.

The calendar row is minted by the real ICS ingest conductor and the meeting
action row is minted by the real meeting repository producer.  These fences
must fail on a head that only has the old brief fields.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as db_module
from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
from holdspeak.config import CalendarConfig, CalendarSource, Config
from holdspeak.db import Database, get_observer
from holdspeak.intel.models import ActionItem
from holdspeak.meeting_session.models import IntelSnapshot, MeetingState
from holdspeak.people import EncryptedPeopleStore
from holdspeak.people.keys import FileKeyStore
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService, PeopleServiceError
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes.people import build_people_router


OWNER = Principal(PrincipalKind.OWNER, "philo13-b4-owner")
@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "holdspeak.db")


@pytest.fixture
def people(tmp_path: Path) -> PeopleService:
    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", FileKeyStore(tmp_path / "people.key"))
    store.initialize()
    return PeopleService(store)


def _ingest_calendar(db: Database, tmp_path: Path, *, unrelated_count: int = 0) -> Any:
    starts = datetime.now(timezone.utc) + timedelta(days=3)
    event_blocks = [
        f"""BEGIN:VEVENT\r
UID:priya-1on1@example.test\r
DTSTART:{starts.strftime('%Y%m%dT%H%M%SZ')}\r
DTEND:{(starts + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%SZ')}\r
SUMMARY:1:1 Priya / Karol\r
END:VEVENT\r
"""
    ]
    for index in range(unrelated_count):
        distractor_start = datetime.now(timezone.utc) + timedelta(minutes=index + 1)
        event_blocks.append(
            f"""BEGIN:VEVENT\r
UID:distractor-{index}@example.test\r
DTSTART:{distractor_start.strftime('%Y%m%dT%H%M%SZ')}\r
DTEND:{(distractor_start + timedelta(minutes=15)).strftime('%Y%m%dT%H%M%SZ')}\r
SUMMARY:Team sync {index}\r
END:VEVENT\r
"""
        )
    ics = ("BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//HoldSpeak B4 test//EN\r\n" + "".join(event_blocks) + "END:VCALENDAR\r\n").encode()
    ics_path = tmp_path / "b4-calendar.ics"
    ics_path.write_bytes(ics)
    source = CalendarSource(id="b4-calendar", label="B4", url=str(ics_path), enabled=True)
    config = Config(calendar=CalendarConfig(sources=[source]))
    conductor = CalendarIngestConductor(
        db_factory=lambda: db,
        config_loader=lambda: config,
        tick_interval=9999,
    )
    assert conductor.refresh() is True
    event = next(event for event in db.calendar_events.list_all() if event.uid == "priya-1on1@example.test")
    return event


def _save_meeting(
    db: Database,
    event_id: str | None,
    *,
    meeting_id: str = "meeting-priya-1on1",
    actions: list[ActionItem] | None = None,
) -> None:
    """Use the real meeting persistence producer for the action rows."""
    db.meetings.save_meeting(
        MeetingState(
            id=meeting_id,
            started_at=datetime(2099, 11, 4, 16, tzinfo=timezone.utc),
            ended_at=datetime(2099, 11, 4, 16, 30, tzinfo=timezone.utc),
            title="1:1 Priya / Karol",
            calendar_event_id=event_id,
            intel=IntelSnapshot(
                timestamp=30.0,
                summary="Priya owns the dry-run follow-up.",
                action_items=actions or [
                    ActionItem(task="Send the dry-run report", owner="Priya", id="ai-priya"),
                    ActionItem(task="Review the dry-run report", owner="Karol", id="ai-karol"),
                    ActionItem(task="Already sent", owner="Priya", id="ai-done", status="done"),
                ],
            ),
        )
    )


def test_brief_suggests_alias_event_without_linking_and_returns_next_prep_data(
    db: Database, people: PeopleService, tmp_path: Path,
) -> None:
    event = _ingest_calendar(db, tmp_path)
    _save_meeting(db, event.id)
    _save_meeting(
        db,
        None,
        meeting_id="meeting-priya-unlinked",
        actions=[ActionItem(task="Send the unlinked report", owner="Priya", id="ai-unlinked")],
    )
    _save_meeting(
        db,
        None,
        meeting_id="meeting-priya-parked",
        actions=[ActionItem(task="Do not show parked work", owner="Priya", id="ai-parked")],
    )
    assert db.meetings.delete_meeting("meeting-priya-parked") is True
    project = ProjectService(db, observer=get_observer()).create_project(
        OWNER, {"name": "Dry-run project", "description": "B4 project"}
    )
    relationship = people.create_relationship(OWNER, {"display_name": "Priya Sharma"})
    people.link_owner_alias(OWNER, relationship["id"], "Priya")
    people.link_project(OWNER, relationship["id"], project["id"])
    session = people.create_one_on_one(OWNER, relationship["id"], {"agenda": "Review the dry-run"})
    people.add_agenda_item(OWNER, session["id"], {"body": "Review the dry-run report"})

    before = people.get_relationship(OWNER, relationship["id"])
    assert before["calendar_links"] in (None, [])

    brief = people.one_on_one_brief(OWNER, relationship["id"], db=db)

    assert brief["calendar_link_suggestions"] == [
        {
            "id": event.id,
            "uid": event.uid,
            "title": event.title,
            "starts_at": event.starts_at,
            "ends_at": event.ends_at,
            "source_id": event.source_id,
            "source_label": event.source_label,
        }
    ]
    assert brief["next_one_on_one"] is None
    assert {item["id"] for item in brief["open_meeting_actions"]} == {"ai-priya", "ai-unlinked"}
    assert all(item["meeting_id"] for item in brief["open_meeting_actions"])
    assert len(brief["agenda_items"]) == 1
    assert {
        key: brief["agenda_items"][0][key]
        for key in ("session_id", "relationship_id", "body", "state")
    } == {
        "session_id": session["id"],
        "relationship_id": relationship["id"],
        "body": "Review the dry-run report",
        "state": "open",
    }
    assert brief["projects"] == [{"id": project["id"], "name": "Dry-run project"}]

    # One explicit confirmation uses the existing write boundary.
    people.link_calendar_series(OWNER, relationship["id"], event.uid, event.source_id, event.title)
    linked_brief = people.one_on_one_brief(OWNER, relationship["id"], db=db)
    assert linked_brief["calendar_link_suggestions"] == []
    assert linked_brief["next_one_on_one"] == {
        "id": event.id,
        "uid": event.uid,
        "title": event.title,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "source_id": event.source_id,
        "source_label": event.source_label,
    }
    assert {item["id"] for item in linked_brief["open_meeting_actions"]} == {
        "ai-priya", "ai-unlinked",
    }
    assert all(item["owner"] == "Priya" for item in linked_brief["open_meeting_actions"])
    assert all(item["meeting_id"] for item in linked_brief["open_meeting_actions"])
    assert linked_brief["open_commitments"] == []


def test_calendar_suggestion_uses_explicit_alias_only(
    db: Database, people: PeopleService, tmp_path: Path,
) -> None:
    _ingest_calendar(db, tmp_path)
    relationship = people.create_relationship(OWNER, {"display_name": "Priya Sharma"})
    brief = people.one_on_one_brief(OWNER, relationship["id"], db=db)
    assert brief["calendar_link_suggestions"] == []


def test_linked_event_is_found_past_the_suggestion_page(
    db: Database, people: PeopleService, tmp_path: Path,
) -> None:
    event = _ingest_calendar(db, tmp_path, unrelated_count=51)
    relationship = people.create_relationship(OWNER, {"display_name": "Priya Sharma"})
    people.link_calendar_series(OWNER, relationship["id"], event.uid, event.source_id, event.title)

    brief = people.one_on_one_brief(OWNER, relationship["id"], db=db)

    assert brief["next_one_on_one"]["id"] == event.id


def test_plaintext_failure_uses_people_error_surface(people: PeopleService) -> None:
    class BrokenDatabase:
        def _connection(self) -> Any:
            raise RuntimeError("database unavailable")

    relationship = people.create_relationship(OWNER, {"display_name": "Priya Sharma"})

    with pytest.raises(PeopleServiceError, match="people_plaintext_unavailable"):
        people.one_on_one_brief(OWNER, relationship["id"], db=BrokenDatabase())


def test_people_routes_expose_the_extended_brief_read(
    db: Database, people: PeopleService, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = _ingest_calendar(db, tmp_path)
    _save_meeting(db, event.id)
    relationship = people.create_relationship(OWNER, {"display_name": "Priya Sharma"})
    people.link_owner_alias(OWNER, relationship["id"], "Priya")
    people.link_calendar_series(OWNER, relationship["id"], event.uid, event.source_id, event.title)
    monkeypatch.setattr(db_module, "get_database", lambda: db)

    app = FastAPI()

    @app.middleware("http")
    async def _stamp(request: Request, call_next: Any) -> Any:
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_people_router(WebContext(get_state=lambda: {}, people_service=people)))
    client = TestClient(app)

    brief = client.get(f"/api/people/relationships/{relationship['id']}/brief")
    assert brief.status_code == 200
    assert brief.json()["brief"]["next_one_on_one"]["uid"] == event.uid
    assert brief.json()["brief"]["open_meeting_actions"][0]["meeting_id"] == "meeting-priya-1on1"

    detail = client.get(f"/api/people/relationships/{relationship['id']}")
    assert detail.status_code == 200
    assert detail.json()["relationship"]["next_one_on_one"] == event.starts_at

    class BrokenDatabase:
        def _connection(self) -> Any:
            raise RuntimeError("database unavailable")

    monkeypatch.setattr(db_module, "get_database", lambda: BrokenDatabase())
    failed = client.get(f"/api/people/relationships/{relationship['id']}")
    assert failed.status_code == 503
    assert failed.json()["detail"] == "people_plaintext_unavailable"
