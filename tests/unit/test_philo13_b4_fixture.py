"""The PHILO-13 B4 graph oracle is minted by the real producers."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.people import production_people_store
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.people_service import PeopleService

from scripts.philo13_b4_fixture import seed_people_prep


OWNER = Principal(PrincipalKind.OWNER, "philo13-b4-owner")


def test_people_prep_fixture_uses_real_calendar_meeting_and_people_producers(
    tmp_path: Path, monkeypatch,
) -> None:
    home = tmp_path / "isolated-home"
    home.mkdir()
    db_path = home / "holdspeak.db"
    monkeypatch.setenv("HOME", str(home))

    result = seed_people_prep(db_path, home=home)

    assert result["schema"] == "philo13-b4-people-prep@1"
    ids = result["ids"]
    assert {
        "relationship_id", "event_id", "event_uid", "event_source_id",
        "project_id", "meeting_id", "session_id", "action_id",
        "parked_meeting_id",
    } <= ids.keys()
    assert result["people_keystore"] == str(home / "people.key")

    db = Database(db_path)
    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor
    from holdspeak.config import Config
    assert CalendarIngestConductor(
        db_factory=lambda: db,
        config_loader=lambda: Config.load(home / ".config/holdspeak/config.json"),
    ).refresh()
    assert db.calendar_events.get(ids["event_id"]).uid == ids["event_uid"]
    assert db.meetings.get_meeting(ids["meeting_id"]) is not None
    assert db.meetings.get_meeting(ids["parked_meeting_id"]) is None
    assert db.meetings.get_meeting(ids["parked_meeting_id"], include_parked=True).parked

    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", result["people_keystore"])
    store = production_people_store()
    assert store.path == home / "people.sidecar.sqlite3"
    brief = PeopleService(store).one_on_one_brief(OWNER, ids["relationship_id"], db=db)
    assert brief["calendar_link_suggestions"][0]["uid"] == ids["event_uid"]
    assert {item["id"] for item in brief["open_meeting_actions"]} == {ids["action_id"]}
    assert brief["open_meeting_actions"][0]["meeting_id"] == ids["meeting_id"]
    assert brief["agenda_items"][0]["body"] == "Review the dry-run report"
    assert brief["projects"][0]["id"] == ids["project_id"]
