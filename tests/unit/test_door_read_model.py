"""Production-composition coverage for the Dashboard Door read model."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from holdspeak.calendar_ingest import CalendarEventCandidate
from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.door_service import DoorService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.people_service import PeopleService, UnavailablePeopleStore
from holdspeak.services.refinement_thought_service import (
    INBOX_DIRECTORY_ID,
    RefinementThoughtService,
)


OWNER = Principal(PrincipalKind.OWNER, "door-owner")
FIXED_NOW = datetime.now().astimezone().replace(
    hour=12, minute=0, second=0, microsecond=0
).astimezone(timezone.utc)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "door.db")
    database.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    yield database
    reset_database()


def _door(
    db: Database,
    *,
    now: datetime = FIXED_NOW,
    people_service: PeopleService | None = None,
    config_loader: object | None = None,
) -> DoorService:
    kwargs: dict = {}
    if config_loader is not None:
        kwargs["config_loader"] = config_loader
    return DoorService(
        FollowThroughService(db, people_projection=people_service),
        RefinementThoughtService(db),
        db.scheduled_recordings,
        db.calendar_events,
        clock=lambda: now,
        people_service=people_service,
        **kwargs,
    )


def _insert_action(
    db: Database,
    item_id: str,
    *,
    owner: str | None = "Ada",
    due: str | None = None,
    status: str = "open",
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("door-meeting", "2026-08-01T09:00:00", "Door planning"),
        )
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state)
               VALUES (?, 'door-meeting', ?, ?, ?, ?, 'accepted')""",
            (item_id, f"Task {item_id}", owner, due, status),
        )


def _insert_loop(
    db: Database,
    loop_id: str,
    *,
    owner: str = "Ada",
    due: str | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, owner, due_at, status)
               VALUES (?, 'manual', ?, ?, ?, ?, 'open')""",
            (loop_id, f"source-{loop_id}", f"Loop {loop_id}", owner, due),
        )


def _working_thought(db: Database, request_id: str, *, title: str = "Door thought") -> dict[str, object]:
    return RefinementThoughtService(db).create(
        OWNER,
        request_id=request_id,
        raw_text=f"{title} body",
        source={"kind": "typed"},
        initial_note={"title": title, "body_markdown": f"{title} body"},
    )


def _scheduled(
    db: Database,
    title: str,
    *,
    enabled: bool,
    next_fire_at: float | None,
    duration_minutes: int = 30,
) -> str:
    return db.scheduled_recordings.create(
        title=title,
        cron_expr="0 9 * * *",
        enabled=enabled,
        next_fire_at=next_fire_at,
        duration_minutes=duration_minutes,
    ).id


def test_door_projection_composes_real_follow_through_thought_and_schedule_objects(db: Database) -> None:
    today = date.today()
    _insert_action(db, "overdue-action", due=(today - timedelta(days=1)).isoformat())
    _insert_action(db, "now-action", due=today.isoformat())
    _insert_action(db, "waiting-action", due=(today + timedelta(days=5)).isoformat())
    _insert_action(db, "unassigned-action", owner=None, due=today.isoformat())
    _insert_loop(db, "loop-now", due=today.isoformat())
    thought = _working_thought(db, "door-thought")
    schedule_id = _scheduled(
        db, "Door schedule", enabled=True, next_fire_at=FIXED_NOW.timestamp() + 3600
    )

    projection = _door(db).get(OWNER)

    assert list(projection["board"]) == ["now", "waiting", "unassigned", "overdue", "active"]
    assert {card["id"] for card in projection["board"]["now"]} == {"now-action", "loop-now"}
    assert [card["id"] for card in projection["board"]["waiting"]] == ["waiting-action"]
    assert [card["id"] for card in projection["board"]["unassigned"]] == ["unassigned-action"]
    assert [card["id"] for card in projection["board"]["overdue"]] == ["overdue-action"]
    assert projection["board"]["active"][0]["id"] == thought["id"]
    action_card = next(card for card in projection["board"]["now"] if card["id"] == "now-action")
    loop_card = next(card for card in projection["board"]["now"] if card["id"] == "loop-now")
    assert action_card["target_ref"] == "action_item:now-action"
    assert [verb["arguments"]["verb"] for verb in action_card["lawful_verbs"]] == [
        "done", "dismiss", "snooze", "delegate"
    ]
    assert loop_card["target_ref"] == "cadence_loop:loop-now"
    assert {verb["arguments"]["status"] for verb in loop_card["lawful_verbs"]} == {
        "closed", "killed"
    }
    assert projection["upcoming"][0]["id"] == schedule_id


def test_active_thoughts_keep_existing_continuity_and_only_lawful_complete_verb(db: Database) -> None:
    first = _working_thought(db, "thought-0", title="First Door thought")
    for index in range(1, 51):
        _working_thought(db, f"thought-{index}", title=f"Thought {index}")

    active = _door(db).get(OWNER)["board"]["active"]
    first_card = next(card for card in active if card["id"] == first["id"])

    assert len(active) == 51
    assert first_card["state"] == "working"
    assert first_card["continuity_state"] == "idle"
    assert first_card["open_ref"] == f"note:{first['working_note']['id']}"
    assert first_card["aggregate_revision"] == first["aggregate_revision"]
    assert first_card["lifecycle_revision"] == first["lifecycle_revision"]
    assert first_card["lawful_verbs"] == [{
        "name": "thought.complete",
        "arguments": {
            "thought_id": first["id"],
            "expected_aggregate_revision": first["aggregate_revision"],
            "expected_lifecycle_revision": first["lifecycle_revision"],
        },
        "required_arguments": ["request_id"],
    }]


def test_counts_equal_returned_lanes_and_today_timeline_over_generated_fixture_matrix(db: Database) -> None:
    today = date.today()
    for index in range(3):
        _insert_action(db, f"overdue-{index}", due=(today - timedelta(days=index + 1)).isoformat())
    for index in range(2):
        _insert_action(db, f"now-{index}", due=(today + timedelta(days=index)).isoformat())
    for index in range(4):
        _insert_action(db, f"waiting-{index}", due=(today + timedelta(days=index + 4)).isoformat())
    for index in range(5):
        _working_thought(db, f"matrix-thought-{index}")
    _scheduled(db, "Today one", enabled=True, next_fire_at=FIXED_NOW.timestamp() + 3600)
    _scheduled(db, "Today two", enabled=True, next_fire_at=FIXED_NOW.timestamp() + 7200)
    _scheduled(db, "Later", enabled=True, next_fire_at=FIXED_NOW.timestamp() + 86400 * 2)

    projection = _door(db).get(OWNER)

    assert projection["counts"] == {
        "overdue": len(projection["board"]["overdue"]),
        "now": len(projection["board"]["now"]),
        "waiting": len(projection["board"]["waiting"]),
        "active": len(projection["board"]["active"]),
        "upcoming_today": 2,
    }
    assert projection["counts"] == {
        "overdue": 3,
        "now": 2,
        "waiting": 4,
        "active": 5,
        "upcoming_today": 2,
    }


def test_upcoming_filters_and_orders_enabled_next_fire_records_with_calendar_ready_shape(db: Database) -> None:
    now = FIXED_NOW
    _scheduled(db, "Disabled", enabled=False, next_fire_at=now.timestamp() + 300)
    _scheduled(db, "Null", enabled=True, next_fire_at=None)
    _scheduled(db, "Past", enabled=True, next_fire_at=now.timestamp() - 1)
    later = _scheduled(db, "Later", enabled=True, next_fire_at=now.timestamp() + 7200)
    earlier = _scheduled(
        db,
        "Earlier",
        enabled=True,
        next_fire_at=now.timestamp() + 3600,
        duration_minutes=45,
    )

    upcoming = _door(db, now=now).get(OWNER)["upcoming"]

    assert [item["id"] for item in upcoming] == [earlier, later]
    assert upcoming[0] == {
        "id": earlier,
        "source": "scheduled_recording",
        "target_ref": f"scheduled_recording:{earlier}",
        "title": "Earlier",
        "starts_at": (now + timedelta(hours=1)).isoformat().replace("+00:00", "Z"),
        "ends_at": (now + timedelta(hours=1, minutes=45)).isoformat().replace("+00:00", "Z"),
        "location": None,
        "meeting_url": None,
        "state": "idle",
    }


def test_upcoming_merges_calendar_events_and_scheduled_recordings_in_one_stable_order(
    db: Database,
) -> None:
    same_time = FIXED_NOW + timedelta(hours=1)
    schedule_id = _scheduled(
        db, "Scheduled at same instant", enabled=True, next_fire_at=same_time.timestamp()
    )
    db.calendar_events.replace_projection(
        "calendar-revision",
        [
            CalendarEventCandidate(
                id="ce_later",
                uid="later",
                title="Later calendar event",
                starts_at=(FIXED_NOW + timedelta(hours=2)).isoformat().replace("+00:00", "Z"),
                ends_at=(FIXED_NOW + timedelta(hours=3)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
            CalendarEventCandidate(
                id="ce_same",
                uid="same",
                title="Calendar at same instant",
                starts_at=same_time.isoformat().replace("+00:00", "Z"),
                ends_at=(same_time + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location="Room 4",
                meeting_url="https://meet.example.test/door",
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
    )

    upcoming = _door(db).get(OWNER)["upcoming"]

    assert [item["id"] for item in upcoming] == ["ce_same", schedule_id, "ce_later"]
    assert upcoming[0] == {
        "id": "ce_same",
        "uid": "same",
        "source": "calendar_event",
        "target_ref": "calendar_event:ce_same",
        "title": "Calendar at same instant",
        "starts_at": same_time.isoformat().replace("+00:00", "Z"),
        "ends_at": (same_time + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
        "location": "Room 4",
        "meeting_url": "https://meet.example.test/door",
        "state": "scheduled",
        "source_id": "",
        "source_label": "",
    }


def test_calendar_timeline_rows_preserve_the_reserved_nullable_fields_and_do_not_change_counts_shape(
    db: Database,
) -> None:
    starts_at = FIXED_NOW + timedelta(hours=1)
    db.calendar_events.replace_projection(
        "calendar-revision",
        [
            CalendarEventCandidate(
                id="ce_nullable",
                uid="nullable",
                title="No location calendar event",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            )
        ],
        seen_at=FIXED_NOW.timestamp(),
    )

    projection = _door(db).get(OWNER)

    assert projection["upcoming"][0]["location"] is None
    assert projection["upcoming"][0]["meeting_url"] is None
    assert set(projection["counts"]) == {"overdue", "now", "waiting", "active", "upcoming_today"}
    assert projection["counts"]["upcoming_today"] == 1


def test_door_never_needs_refinement_thought_schema_fields_beyond_existing_projection(db: Database) -> None:
    _working_thought(db, "existing-projection")

    card = _door(db).get(OWNER)["board"]["active"][0]

    assert set(card) == {
        "id", "source", "target_ref", "open_ref", "title", "body_preview", "state",
        "continuity_state", "updated_at", "aggregate_revision", "lifecycle_revision",
        "filing_status", "lawful_verbs",
    }
    assert {"owner", "due", "priority"}.isdisjoint(card)


def test_door_preserves_people_unavailable_no_leak_no_crash(db: Database) -> None:
    _insert_action(db, "ordinary", due=date.today().isoformat())
    _working_thought(db, "ordinary-thought")

    projection = _door(
        db, people_service=PeopleService(UnavailablePeopleStore())
    ).get(OWNER)

    assert projection["board"]["now"][0]["id"] == "ordinary"
    assert all(card["source"] != "people_commitment" for lane in projection["board"].values() for card in lane)
    # L2 (HS-149-01): the people_store_state fact is deliberately carried
    # so the Door can render a named state instead of silent emptiness.
    # The no-leak invariant checks that no People CARDS appear, not that
    # the readiness state name is absent.
    all_cards = [card for lane in projection["board"].values() for card in lane]
    assert not any("people" in json.dumps(card) for card in all_cards)
    # The state field is present and names the unavailable sidecar.
    assert projection.get("people_store_state") == "unavailable"


def test_calendar_configured_false_on_empty_subscription(db: Database) -> None:
    from holdspeak.config import Config

    projection = _door(db, config_loader=lambda: Config()).get(OWNER)
    assert projection["calendar_configured"] is False


def test_calendar_configured_true_on_valid_https_subscription(db: Database) -> None:
    from holdspeak.config import Config
    from holdspeak.config.integrations import CalendarConfig, CalendarSource

    config = Config(calendar=CalendarConfig(sources=[
        CalendarSource(id="test-src", label="", url="https://example.com/calendar.ics", enabled=True)
    ]))
    projection = _door(db, config_loader=lambda: config).get(OWNER)
    assert projection["calendar_configured"] is True


def test_calendar_configured_false_when_no_config_loader(db: Database) -> None:
    projection = _door(db).get(OWNER)
    assert projection["calendar_configured"] is False


# ── HS-146-04: source_label projection + label fallback chain + no-dedupe ──


def test_calendar_event_projects_source_id_and_source_label(db: Database) -> None:
    """_calendar_event_item projects source_id and source_label from the DB row."""
    starts_at = FIXED_NOW + timedelta(hours=1)
    db.calendar_events.replace_projection(
        "rev-work",
        [
            CalendarEventCandidate(
                id="ce_labelled",
                uid="labelled",
                title="Labelled event",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="src-work",
        source_label="Work",
    )

    upcoming = _door(db).get(OWNER)["upcoming"]

    assert len(upcoming) == 1
    assert upcoming[0]["source_id"] == "src-work"
    assert upcoming[0]["source_label"] == "Work"


def test_source_label_fallback_chain(db: Database) -> None:
    """The label fallback chain: label -> hostname -> LOCAL."""
    from holdspeak.config.integrations import CalendarSource, _source_label

    # Explicit label wins.
    assert _source_label(CalendarSource(id="s1", label="Team", url="https://example.com/a.ics")) == "Team"
    # No label -> hostname from URL.
    assert _source_label(CalendarSource(id="s2", label="", url="https://cal.example.com/b.ics")) == "cal.example.com"
    # No label, no URL -> LOCAL.
    assert _source_label(CalendarSource(id="s3", label="", url="")) == "LOCAL"
    # File path -> LOCAL (no scheme, no hostname).
    assert _source_label(CalendarSource(id="s4", label="", url="/tmp/cal.ics")) == "LOCAL"


def test_no_dedupe_duplicate_uids_both_project(db: Database) -> None:
    """Two sources with the same UID both project (settled design row 6: no dedupe)."""
    starts_at = FIXED_NOW + timedelta(hours=1)
    starts_iso = starts_at.isoformat().replace("+00:00", "Z")
    ends_iso = (starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
    for source_id, source_label in [("src-a", "Source A"), ("src-b", "Source B")]:
        db.calendar_events.replace_projection(
            f"rev-{source_id}",
            [
                CalendarEventCandidate(
                    id=f"ce_{source_id}",
                    uid="shared-uid",
                    title="Same meeting",
                    starts_at=starts_iso,
                    ends_at=ends_iso,
                    location=None,
                    meeting_url=None,
                ),
            ],
            seen_at=FIXED_NOW.timestamp(),
            source_id=source_id,
            source_label=source_label,
        )

    upcoming = _door(db).get(OWNER)["upcoming"]

    calendar_events = [item for item in upcoming if item["source"] == "calendar_event"]
    assert len(calendar_events) == 2
    labels = {item["source_label"] for item in calendar_events}
    assert labels == {"Source A", "Source B"}


# ── HS-149-03: uid projection + person_label projection ──────────────────


def test_calendar_event_projects_uid(db: Database) -> None:
    """HS-149-03: _calendar_event_item projects uid for the picker/link flow."""
    starts_at = FIXED_NOW + timedelta(hours=1)
    db.calendar_events.replace_projection(
        "rev-uid",
        [
            CalendarEventCandidate(
                id="ce_uid",
                uid="uid-weekly-1on1",
                title="1:1 w/ Ewa",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="cal-outlook",
        source_label="Outlook",
    )

    upcoming = _door(db).get(OWNER)["upcoming"]

    assert len(upcoming) == 1
    assert upcoming[0]["uid"] == "uid-weekly-1on1"


def test_person_label_projected_for_linked_event(db: Database, tmp_path: Path) -> None:
    """HS-149-03: linked calendar series -> person_label on the event item."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore

    store = EncryptedPeopleStore(tmp_path / "people-label.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Ewa"})
    people.link_calendar_series(OWNER, rel["id"], "uid-weekly", "cal-work", "1:1 w/ Ewa")

    starts_at = FIXED_NOW + timedelta(hours=1)
    db.calendar_events.replace_projection(
        "rev-linked",
        [
            CalendarEventCandidate(
                id="ce_linked",
                uid="uid-weekly",
                title="1:1 w/ Ewa",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="cal-work",
        source_label="Work",
    )

    upcoming = _door(db, people_service=people).get(OWNER)["upcoming"]

    assert len(upcoming) == 1
    assert upcoming[0]["person_label"] == "Ewa"


def test_person_label_absent_for_unlinked_event(db: Database, tmp_path: Path) -> None:
    """HS-149-03: unlinked event -> no person_label field."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore

    store = EncryptedPeopleStore(tmp_path / "people-nolabel.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)

    starts_at = FIXED_NOW + timedelta(hours=1)
    db.calendar_events.replace_projection(
        "rev-unlinked",
        [
            CalendarEventCandidate(
                id="ce_unlinked",
                uid="uid-no-link",
                title="Team standup",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="cal-work",
        source_label="Work",
    )

    upcoming = _door(db, people_service=people).get(OWNER)["upcoming"]

    assert len(upcoming) == 1
    assert "person_label" not in upcoming[0]


def test_person_label_absent_when_sidecar_unavailable(db: Database) -> None:
    """HS-149-03: unavailable sidecar -> no person_label, Door never blocks."""
    people = PeopleService(UnavailablePeopleStore())

    starts_at = FIXED_NOW + timedelta(hours=1)
    db.calendar_events.replace_projection(
        "rev-unavail",
        [
            CalendarEventCandidate(
                id="ce_unavail",
                uid="uid-any",
                title="Some event",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="cal-work",
        source_label="Work",
    )

    upcoming = _door(db, people_service=people).get(OWNER)["upcoming"]

    assert len(upcoming) == 1
    assert "person_label" not in upcoming[0]


def test_person_label_memoization_single_resolve_per_series(db: Database, tmp_path: Path) -> None:
    """HS-149-03: multiple occurrences of the same series -> one resolve call."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from unittest.mock import patch

    store = EncryptedPeopleStore(tmp_path / "people-memo.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Jan"})
    people.link_calendar_series(OWNER, rel["id"], "uid-memo", "cal-1", "Recurring sync")

    starts_at = FIXED_NOW + timedelta(hours=1)
    # Insert two occurrences of the same series (same uid + source_id).
    db.calendar_events.replace_projection(
        "rev-memo",
        [
            CalendarEventCandidate(
                id="ce_memo_1",
                uid="uid-memo",
                title="Recurring sync",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
            CalendarEventCandidate(
                id="ce_memo_2",
                uid="uid-memo",
                title="Recurring sync",
                starts_at=(starts_at + timedelta(hours=168)).isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(hours=168, minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="cal-1",
    )

    with patch.object(people, "resolve_relationship_by_series", wraps=people.resolve_relationship_by_series) as spy:
        upcoming = _door(db, people_service=people).get(OWNER)["upcoming"]

    calendar_events = [item for item in upcoming if item["source"] == "calendar_event"]
    assert len(calendar_events) == 2
    assert all(item["person_label"] == "Jan" for item in calendar_events)
    # Pin: exactly one call per distinct (uid, source_id), not per event.
    assert spy.call_count == 1
