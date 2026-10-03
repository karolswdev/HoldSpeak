#!/usr/bin/env python3
"""Mint the PHILO-13 B4 People preparation oracle through real producers.

The graph rig calls ``seed`` in its run-owned HOME.  The fixture deliberately
does not insert rows into either database: calendar data comes from the real
ICS conductor, meeting data from ``save_meeting``, People data from its HTTP
routes and encrypted store, and the project from ``ProjectService``.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import pwd
from typing import Any, Iterator


SCHEMA = "philo13-b4-people-prep@1"
OWNER_NAME = "philo13-b4-owner"
RELATIONSHIP_NAME = "Priya Sharma"
OWNER_ALIAS = "Priya"
EVENT_UID = "philo13-b4-priya@example.test"
EVENT_SOURCE_ID = "philo13-b4-calendar"
EVENT_TITLE = "1:1 Priya / Karol"
MEETING_ID = "philo13-b4-meeting"
PARKED_MEETING_ID = "philo13-b4-parked-meeting"
ACTION_ID = "philo13-b4-owned-action"


def _owner_home() -> Path:
    return Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()


def validate_isolated_db(db_path: Path, home: Path | None = None) -> tuple[Path, Path]:
    """Refuse a producer target that can reach the owner's desk."""
    raw_home = str(home) if home is not None else os.environ.get("HOME", "").strip()
    if not raw_home:
        raise ValueError("HOME must name an isolated fixture directory")
    isolated_home = Path(raw_home).expanduser()
    target = Path(db_path).expanduser()
    if not isolated_home.is_absolute() or not target.is_absolute():
        raise ValueError("fixture HOME and --db must be absolute paths")
    if isolated_home.is_symlink() or target.is_symlink():
        raise ValueError("fixture HOME and --db must not be symlinks")
    isolated_home = isolated_home.resolve()
    target = target.resolve()
    owner_home = _owner_home()
    if isolated_home == owner_home or isolated_home.is_relative_to(owner_home):
        raise ValueError("fixture HOME must be outside the owner's real HOME")
    if target == owner_home or target.is_relative_to(owner_home):
        raise ValueError("--db points into the owner's real HOME")
    if not target.is_relative_to(isolated_home) or target == isolated_home:
        raise ValueError("--db must be below the isolated HOME")
    isolated_home.mkdir(parents=True, exist_ok=True)
    return target, isolated_home


@contextmanager
def _file_key(home: Path) -> Iterator[Path]:
    keyfile = home / "people.key"
    before = os.environ.get("HOLDSPEAK_PEOPLE_KEYSTORE_FILE")
    os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = str(keyfile)
    try:
        yield keyfile
    finally:
        if before is None:
            os.environ.pop("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", None)
        else:
            os.environ["HOLDSPEAK_PEOPLE_KEYSTORE_FILE"] = before


def _ics(path: Path, starts: datetime) -> None:
    def stamp(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    ends = starts + timedelta(minutes=30)
    path.write_text(
        "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//HoldSpeak B4//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{EVENT_UID}\r\nDTSTART:{stamp(starts)}\r\nDTEND:{stamp(ends)}\r\n"
        f"SUMMARY:{EVENT_TITLE}\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n",
        encoding="utf-8",
    )


def _save_meetings(db: Any, event: Any) -> None:
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState

    started = datetime.now(timezone.utc) + timedelta(days=2)
    db.meetings.save_meeting(
        MeetingState(
            id=MEETING_ID,
            started_at=started,
            ended_at=started + timedelta(minutes=30),
            title=EVENT_TITLE,
            calendar_event_id=event.id,
            intel=IntelSnapshot(
                timestamp=started.timestamp(),
                summary="Priya owns the report follow-up.",
                action_items=[
                    ActionItem(task="Send the dry-run report", owner=OWNER_ALIAS, id=ACTION_ID),
                    ActionItem(task="Review the dry-run report", owner=OWNER_NAME, id="philo13-b4-other-action"),
                    ActionItem(task="Already sent", owner=OWNER_ALIAS, id="philo13-b4-completed", status="done"),
                ],
            ),
        )
    )
    db.meetings.save_meeting(
        MeetingState(
            id=PARKED_MEETING_ID,
            started_at=started - timedelta(hours=1),
            ended_at=started - timedelta(minutes=30),
            title="Parked B4 meeting",
            intel=IntelSnapshot(
                timestamp=started.timestamp(),
                action_items=[ActionItem(
                    task="Do not show parked work", owner=OWNER_ALIAS,
                    id="philo13-b4-parked-action",
                )],
            ),
        )
    )
    if not db.meetings.delete_meeting(PARKED_MEETING_ID):
        raise RuntimeError("B4 parked meeting producer did not park its row")


@contextmanager
def _people_client(db: Any, people: Any) -> Iterator[Any]:
    from fastapi import FastAPI, Request
    from fastapi.testclient import TestClient
    import holdspeak.db as db_module
    from holdspeak.principals import Principal, PrincipalKind
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.people import build_people_router

    owner = Principal(PrincipalKind.OWNER, OWNER_NAME)
    app = FastAPI()

    @app.middleware("http")
    async def owner_middleware(request: Request, call_next: Any) -> Any:
        request.state.principal = owner
        return await call_next(request)

    app.include_router(build_people_router(WebContext(
        get_state=lambda: {}, people_service=people,
    )))
    previous = db_module.get_database
    db_module.get_database = lambda db_path=None: db  # type: ignore[assignment]
    try:
        with TestClient(app) as client:
            yield client
    finally:
        db_module.get_database = previous


def seed_people_prep(db_path: Path, *, home: Path | None = None) -> dict[str, Any]:
    """Create one isolated B4 oracle and return only stable producer refs."""
    db_path, isolated_home = validate_isolated_db(db_path, home)
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
    from holdspeak.config import CalendarConfig, CalendarSource, Config
    from holdspeak.db import Database
    from holdspeak.people import production_people_store
    from holdspeak.services.people_service import PeopleService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.principals import Principal, PrincipalKind

    with _file_key(isolated_home) as keyfile:
        db = Database(db_path)
        ics_path = isolated_home / "philo13-b4-calendar.ics"
        starts = datetime.now(timezone.utc) + timedelta(days=2)
        _ics(ics_path, starts)
        config_path = isolated_home / ".config" / "holdspeak" / "config.json"
        config = Config.load(config_path)
        config.calendar = CalendarConfig(sources=[CalendarSource(
            id=EVENT_SOURCE_ID, label="B4 calendar", url=str(ics_path), enabled=True,
        )])
        # The restarted hub runs the real ingest conductor too. Persist the
        # source so that its source-prune does not remove the fixture event.
        config.save(config_path)
        conductor = CalendarIngestConductor(
            db_factory=lambda: db, config_loader=lambda: config, tick_interval=9999,
        )
        if not conductor.refresh():
            raise RuntimeError("B4 calendar conductor did not refresh")
        event = next((item for item in db.calendar_events.list_all() if item.uid == EVENT_UID), None)
        if event is None:
            raise RuntimeError("B4 calendar conductor produced no Priya event")

        _save_meetings(db, event)
        store = production_people_store()
        store.initialize()
        people = PeopleService(store)
        owner = Principal(PrincipalKind.OWNER, OWNER_NAME)
        project = ProjectService(db).create_project(
            owner, {"name": "B4 Dry-run project", "description": "B4 report context"},
        )

        with _people_client(db, people) as client:
            response = client.post("/api/people/relationships", json={"display_name": RELATIONSHIP_NAME})
            if response.status_code != 201:
                raise RuntimeError(f"People relationship producer returned {response.status_code}: {response.text}")
            relationship = response.json()["relationship"]
            relationship_id = relationship["id"]
            response = client.post(
                f"/api/people/relationships/{relationship_id}/owner-aliases",
                json={"alias": OWNER_ALIAS},
            )
            if response.status_code != 200:
                raise RuntimeError(f"People alias producer returned {response.status_code}: {response.text}")
            people.link_project(owner, relationship_id, project["id"])
            response = client.post(
                f"/api/people/relationships/{relationship_id}/one-on-ones",
                json={"agenda": "Review the dry-run"},
            )
            if response.status_code != 201:
                raise RuntimeError(f"People session producer returned {response.status_code}: {response.text}")
            session_id = response.json()["one_on_one"]["id"]
            response = client.post(
                f"/api/people/one-on-ones/{session_id}/agenda",
                json={"body": "Review the dry-run report"},
            )
            if response.status_code != 201:
                raise RuntimeError(f"People agenda producer returned {response.status_code}: {response.text}")

        return {
            "schema": SCHEMA,
            "mode": "seed",
            "db": str(db_path),
            "home": str(isolated_home),
            "people_keystore": str(keyfile),
            "people_sidecar": str(store.path),
            "event_title": event.title,
            "ids": {
                "relationship_id": relationship_id,
                "event_id": event.id,
                "event_uid": event.uid,
                "event_source_id": event.source_id,
                "event_title": event.title,
                "project_id": project["id"],
                "meeting_id": MEETING_ID,
                "session_id": session_id,
                "action_id": ACTION_ID,
                "parked_meeting_id": PARKED_MEETING_ID,
            },
            "producers": {
                "calendar": "CalendarIngestConductor.refresh",
                "meeting": "Database.meetings.save_meeting",
                "people": "build_people_router + production_people_store",
                "project": "ProjectService.create_project",
            },
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    seed = subparsers.add_parser("seed")
    seed.add_argument("--db", required=True, type=Path)
    seed.add_argument("--home", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "seed":
        print(json.dumps(seed_people_prep(args.db, home=args.home), sort_keys=True))
        return 0
    raise ValueError(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
