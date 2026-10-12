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
    assert [
        verb["arguments"]["verb"] for verb in action_card["lawful_verbs"] if verb["name"] == "follow_through.complete"
    ] == ["done", "dismiss", "snooze", "delegate"]
    # Hand to agent: the Door declares the agent.hand verb on an action item.
    assert action_card["lawful_verbs"][-1] == {
        "name": "agent.hand", "arguments": {"kind": "action", "id": "now-action"},
    }
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


# ── HS-150-02: board owner person projection ──────────────────────────


def test_board_card_carries_person_label_for_mapped_owner(db: Database, tmp_path: Path) -> None:
    """HS-150-02: mapped owner string -> person_label + person_relationship_id on card."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore

    store = EncryptedPeopleStore(tmp_path / "people-mapped.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Ewa"})
    people.link_owner_alias(OWNER, rel["id"], "Ewa")

    _insert_action(db, "mapped-card", owner="Ewa")

    projection = _door(db, people_service=people).get(OWNER)

    all_cards = [
        card
        for lane in ["now", "waiting", "unassigned", "overdue"]
        for card in projection["board"][lane]
    ]
    card = next(c for c in all_cards if c["id"] == "mapped-card")
    assert card["person_label"] == "Ewa"
    assert card["person_relationship_id"] == rel["id"]


def test_board_card_unmapped_owner_has_no_person_fields(db: Database, tmp_path: Path) -> None:
    """HS-150-02: unmapped owner string -> no person_label, byte-identical to today."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore

    store = EncryptedPeopleStore(tmp_path / "people-unmapped.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)

    _insert_action(db, "unmapped-card", owner="Stranger")

    projection = _door(db, people_service=people).get(OWNER)

    all_cards = [
        card
        for lane in ["now", "waiting", "unassigned", "overdue"]
        for card in projection["board"][lane]
    ]
    card = next(c for c in all_cards if c["id"] == "unmapped-card")
    assert "person_label" not in card
    assert "person_relationship_id" not in card


def test_board_person_projection_absent_when_sidecar_unavailable(db: Database) -> None:
    """HS-150-02: unavailable sidecar -> no person fields, no crash."""
    people = PeopleService(UnavailablePeopleStore())
    _insert_action(db, "unavail-card", owner="Ada")

    projection = _door(db, people_service=people).get(OWNER)

    all_cards = [
        card
        for lane in ["now", "waiting", "unassigned", "overdue"]
        for card in projection["board"][lane]
    ]
    card = next(c for c in all_cards if c["id"] == "unavail-card")
    assert "person_label" not in card
    assert "person_relationship_id" not in card


def test_board_person_index_memoizes_one_resolve_per_owner_string(
    db: Database, tmp_path: Path,
) -> None:
    """HS-150-02: multiple cards with same owner -> one resolve call."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from unittest.mock import patch

    store = EncryptedPeopleStore(tmp_path / "people-memo-owner.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Ada"})
    people.link_owner_alias(OWNER, rel["id"], "Ada")

    _insert_action(db, "card-1", owner="Ada")
    _insert_action(db, "card-2", owner="Ada")
    _insert_action(db, "card-3", owner="Grace")

    with patch.object(
        people, "resolve_relationship_by_owner",
        wraps=people.resolve_relationship_by_owner,
    ) as spy:
        _door(db, people_service=people).get(OWNER)

    # One call per distinct owner string: "Ada" and "Grace".
    assert spy.call_count == 2


def test_board_card_carries_created_at_for_staleness(db: Database) -> None:
    """HS-150-02: action cards carry created_at for client-side staleness computation."""
    today = date.today()
    _insert_action(db, "staleness-card", owner="Ada", due=(today + timedelta(days=5)).isoformat())
    # Set created_at on the action
    with db._connection() as conn:
        conn.execute(
            "UPDATE action_items SET created_at = ? WHERE id = ?",
            ("2026-08-25T10:00:00", "staleness-card"),
        )

    projection = _door(db).get(OWNER)

    all_cards = [
        card
        for lane in ["now", "waiting", "unassigned", "overdue"]
        for card in projection["board"][lane]
    ]
    card = next(c for c in all_cards if c["id"] == "staleness-card")
    assert card["created_at"] == "2026-08-25T10:00:00"


def test_observer_redaction_swallows_person_projection_fields(db: Database, tmp_path: Path) -> None:
    """HS-150-02 pin: pipeline_events result_summary carries NO person fields after a board call."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from holdspeak.services.observer import PipelineEvent

    store = EncryptedPeopleStore(tmp_path / "people-redact.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Secret"})
    people.link_owner_alias(OWNER, rel["id"], "Alice")

    _insert_action(db, "secret-card", owner="Alice")

    collected: list[PipelineEvent] = []

    class _Collector:
        def on_event(self, event: PipelineEvent) -> None:
            collected.append(event)

    ft = FollowThroughService(db, observer=_Collector(), people_projection=people)
    board = ft.board(OWNER)

    # The board itself has the mapped card.
    all_cards = board.now + board.waiting + board.unassigned + board.overdue
    alice_card = next((c for c in all_cards if c.owner == "Alice"), None)
    assert alice_card is not None

    # The observed event has the board result redacted.
    board_events = [
        e for e in collected
        if e.service == "FollowThroughService" and e.method == "board"
    ]
    assert len(board_events) == 1
    assert board_events[0].result_summary == '{"board":"redacted"}'
    # No person fields in the redacted summary.
    assert "Secret" not in board_events[0].result_summary
    assert "person_label" not in board_events[0].result_summary


# ── merged from tests/unit/test_hs175_door_orphan.py (fast diet, by service) ────────

"""HS-175-02 -- orphan recording provenance in the Door wire.

Verify that _scheduled_recording_item produces correct FROM provenance
when the linked calendar event has left the upcoming projection (past event).
"""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


def _make_recording(
    recording_id: str = "rec-1",
    title: str = "Retro",
    fire_at: float | None = None,
    calendar_event_id: str = "ev-past",
    calendar_source_id: str = "src-work",
    born_from: str = "calendar_event",
) -> Any:
    """Create a minimal ScheduledRecording-like object."""
    now = time.time()
    rec = MagicMock()
    rec.id = recording_id
    rec.title = title
    rec.next_fire_at = fire_at or (now + 3600)
    rec.calendar_event_id = calendar_event_id
    rec.calendar_uid = f"uid-{calendar_event_id}"
    rec.calendar_source_id = calendar_source_id
    rec.born_from = born_from
    rec.duration_minutes = 60
    rec.state = "idle"
    rec.enabled = True
    return rec


def _make_event(
    event_id: str = "ev-past",
    title: str = "Retro",
    source_label: str = "WORK",
    starts_at: str | None = None,
) -> Any:
    """Create a minimal CalendarEvent-like object."""
    now = datetime.now(tz=timezone.utc)
    ev = MagicMock()
    ev.id = event_id
    ev.uid = f"uid-{event_id}"
    ev.title = title
    ev.starts_at = starts_at or (now - timedelta(days=1)).isoformat()
    ev.ends_at = (now - timedelta(days=1) + timedelta(hours=1)).isoformat()
    ev.location = None
    ev.meeting_url = None
    ev.source_id = "src-work"
    ev.source_label = source_label
    return ev


class TestOrphanRecordingProvenance:
    """The FROM token on an orphan recording must carry the event title
    and source_label even when the event has left the upcoming projection."""

    def test_past_event_still_in_db(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When the calendar event exists in the DB but is past, the FROM
        token should carry its title and source_label."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database

        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()

        db = get_database()
        now = datetime.now(tz=timezone.utc)
        past = now - timedelta(days=1)

        with db._connection() as conn:
            # Insert a PAST calendar event
            conn.execute(
                "INSERT INTO calendar_events "
                "(id, uid, title, starts_at, ends_at, last_seen_at, "
                "subscription_revision, source_id, source_label) "
                "VALUES (?, ?, ?, ?, ?, ?, 'rev1', 'src-work', 'WORK')",
                (
                    "ev-past",
                    "uid-ev-past",
                    "Retro",
                    past.isoformat(),
                    (past + timedelta(hours=1)).isoformat(),
                    time.time(),
                ),
            )
            # Insert an armed recording linked to that past event
            fire_at = (now + timedelta(hours=1)).timestamp()
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, "
                "enabled, revision, created_at, next_fire_at, state, "
                "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
                "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
                "?, 'uid-ev-past', 'src-work', 'calendar_event')",
                ("rec-orphan", "Retro", time.time(), fire_at, "ev-past"),
            )
            conn.commit()

        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(
            now=[], waiting=[], unassigned=[], overdue=[]
        )
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        svc = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=None,
        )
        result = svc._upcoming(now)

        # The orphan recording should be in the upcoming list
        orphans = [
            item for item in result
            if item["source"] == "scheduled_recording" and item.get("from")
        ]
        assert len(orphans) >= 1, f"No orphan recording found: {result}"

        orphan = orphans[0]
        assert orphan["from"]["event_title"] == "Retro", (
            f"event_title wrong: {orphan['from']}"
        )
        assert orphan["from"]["source_label"] == "WORK", (
            f"source_label wrong: {orphan['from']}"
        )

    def test_event_gone_fallback_to_config_label(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When the calendar event is gone from the DB entirely, fall back
        to the source label from the configured CalendarSource."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database

        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()

        db = get_database()
        now = datetime.now(tz=timezone.utc)

        with db._connection() as conn:
            # NO calendar event in the DB -- it was deleted/expired.
            fire_at = (now + timedelta(hours=1)).timestamp()
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, "
                "enabled, revision, created_at, next_fire_at, state, "
                "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
                "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
                "?, 'uid-ev-gone', 'src-work', 'calendar_event')",
                ("rec-orphan2", "Team Sync", time.time(), fire_at, "ev-gone"),
            )
            conn.commit()

        from holdspeak.config.integrations import CalendarConfig, CalendarSource
        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        mock_config = MagicMock()
        mock_config.calendar = CalendarConfig(sources=[
            CalendarSource(id="src-work", label="WORK", url="/tmp/fake.ics", enabled=True),
        ])

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(
            now=[], waiting=[], unassigned=[], overdue=[]
        )
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        svc = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=lambda: mock_config,
        )
        result = svc._upcoming(now)

        orphans = [
            item for item in result
            if item["source"] == "scheduled_recording" and item.get("from")
        ]
        assert len(orphans) >= 1, f"No orphan recording found: {result}"

        orphan = orphans[0]
        assert orphan["from"]["source_label"] == "WORK", (
            f"source_label should fall back to config label: {orphan['from']}"
        )

    def test_no_empty_parens_when_source_label_empty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """When source_label is empty (no config, no event), the FROM token
        should not produce empty parentheses."""
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))

        import holdspeak.config as config_module
        import holdspeak.db.core as db_core
        from holdspeak.db import reset_database, get_database

        monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
        monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
        reset_database()

        db = get_database()
        now = datetime.now(tz=timezone.utc)

        with db._connection() as conn:
            fire_at = (now + timedelta(hours=1)).timestamp()
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, "
                "enabled, revision, created_at, next_fire_at, state, "
                "calendar_event_id, calendar_uid, calendar_source_id, born_from) "
                "VALUES (?, ?, '0 10 * * 1', 'UTC', 1, 60, 1, 1, ?, ?, 'idle', "
                "?, 'uid-ev-gone', '', 'calendar_event')",
                ("rec-orphan3", "Retro", time.time(), fire_at, "ev-gone2"),
            )
            conn.commit()

        from holdspeak.services.door_service import DoorService
        from holdspeak.services.follow_through_service import FollowThroughService
        from holdspeak.services.refinement_thought_service import RefinementThoughtService

        ft = MagicMock(spec=FollowThroughService)
        ft.board.return_value = MagicMock(
            now=[], waiting=[], unassigned=[], overdue=[]
        )
        ft.people_store_state.return_value = None
        rt = MagicMock(spec=RefinementThoughtService)
        rt.list_unfinished.return_value = {"items": [], "next_cursor": None}

        svc = DoorService(
            ft, rt,
            db.scheduled_recordings,
            db.calendar_events,
            db=db,
            config_loader=None,
        )
        result = svc._upcoming(now)

        orphans = [
            item for item in result
            if item["source"] == "scheduled_recording" and item.get("from")
        ]
        assert len(orphans) >= 1, f"No orphan recording found: {result}"

        orphan = orphans[0]
        # source_label should be empty string, never None
        assert orphan["from"]["source_label"] == "", (
            f"source_label should be empty: {orphan['from']}"
        )


# ── merged from tests/unit/test_hs175_door_week_local.py (fast diet, by service) ────────

"""HS-175 C8/C9 -- the arrival's WEEK strip buckets LOCAL days and carries
the local week's bounds.

Counsel H4-1: ``_week_strip`` bucketed on the stored UTC date, so a Monday
20:00 meeting at -06:00 was a TUE dot and Sunday evening was already next
week. The desk's clock is the hub's local zone (injectable here as
``local_tz``); the bounds ride so the THIS WEEK section is bounded to the
same week the strip draws (C9), and the armed row carries its recording
state so the face can withhold Cancel while recording (C2).
"""

import time
import time as time_module
from datetime import datetime, time as time_of_day, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

MINUS_SIX = timezone(timedelta(hours=-6))


def _isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.db import reset_database, get_database

    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    reset_database()
    return get_database()


def _seed_event(conn: Any, event_id: str, title: str, starts_at: datetime) -> None:
    starts_utc = starts_at.astimezone(timezone.utc)
    conn.execute(
        "INSERT INTO calendar_events "
        "(id, uid, title, starts_at, ends_at, meeting_url, last_seen_at, "
        "subscription_revision, source_id, source_label) "
        "VALUES (?, ?, ?, ?, ?, 'https://teams.example.com/x', ?, 'rev1', 'src-work', 'WORK')",
        (
            event_id, f"uid-{event_id}", title,
            starts_utc.isoformat(),
            (starts_utc + timedelta(hours=1)).isoformat(),
            time.time(),
        ),
    )


def _service(db: Any, now: datetime, local_tz: Any) -> Any:
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    ft = MagicMock(spec=FollowThroughService)
    ft.board.return_value = MagicMock(now=[], waiting=[], unassigned=[], overdue=[])
    ft.people_store_state.return_value = None
    rt = MagicMock(spec=RefinementThoughtService)
    rt.list_unfinished.return_value = {"items": [], "next_cursor": None}
    return DoorService(
        ft, rt, db.scheduled_recordings, db.calendar_events,
        db=db, config_loader=None, clock=lambda: now, local_tz=local_tz,
    )


class TestLocalWeekBuckets:
    """The strip at -06:00: a Monday 20:00 local meeting is a MON dot."""

    def test_monday_evening_west_of_utc_is_a_monday_dot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        # Tuesday 2026-09-08 12:00 at -06:00.
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        with db._connection() as conn:
            # Monday 20:00 local == Tuesday 02:00Z: the UTC date lies.
            _seed_event(conn, "ev-mon-late", "Late standup",
                        datetime(2026, 9, 7, 20, 0, tzinfo=MINUS_SIX))
            # Sunday 22:00 local == Monday 04:00Z next week in UTC terms;
            # it is still THIS week's Sunday on the desk.
            _seed_event(conn, "ev-sun-late", "Sunday prep",
                        datetime(2026, 9, 13, 22, 0, tzinfo=MINUS_SIX))
            # Wednesday 09:00 local: an ordinary in-week day.
            _seed_event(conn, "ev-wed", "Design review",
                        datetime(2026, 9, 9, 9, 0, tzinfo=MINUS_SIX))
            conn.commit()

        week = _service(db, now, MINUS_SIX)._week_strip(
            now.astimezone(timezone.utc), True,
        )
        by_dow = {d["dow"]: d["count"] for d in week["days"]}
        assert by_dow == {
            "MON": 1, "TUE": 0, "WED": 1, "THU": 0, "FRI": 0, "SAT": 0, "SUN": 1,
        }, by_dow
        assert week["total"] == 3
        assert week["days"][0]["date"] == "2026-09-07"
        assert week["days"][6]["date"] == "2026-09-13"
        # The bounds are the local week as UTC instants (ends_at exclusive).
        assert week["starts_at"] == "2026-09-07T06:00:00+00:00"
        assert week["ends_at"] == "2026-09-14T06:00:00+00:00"

    def test_sunday_evening_is_still_this_week(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Counsel H4-1: at 18:00 local on Sunday the UTC strip was already
        next week. The local strip is still on Sunday."""
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 13, 18, 0, tzinfo=MINUS_SIX)  # Sunday 18:00, 00:00Z Monday
        with db._connection() as conn:
            _seed_event(conn, "ev-sun", "Sunday prep",
                        datetime(2026, 9, 13, 20, 0, tzinfo=MINUS_SIX))
            _seed_event(conn, "ev-next-mon", "Next Monday kickoff",
                        datetime(2026, 9, 14, 9, 0, tzinfo=MINUS_SIX))
            conn.commit()
        week = _service(db, now, MINUS_SIX)._week_strip(
            now.astimezone(timezone.utc), True,
        )
        assert week["days"][0]["date"] == "2026-09-07"
        by_dow = {d["dow"]: d["count"] for d in week["days"]}
        assert by_dow["SUN"] == 1 and week["total"] == 1, by_dow

    def test_next_week_event_stays_out_of_the_strip_but_in_upcoming(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """C9: the door's ``upcoming`` keeps the projection (the NEXT line may
        name next week's event); the strip and its ``ends_at`` bound exclude it."""
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        with db._connection() as conn:
            _seed_event(conn, "ev-wed", "Design review",
                        datetime(2026, 9, 9, 9, 0, tzinfo=MINUS_SIX))
            _seed_event(conn, "ev-next", "Next week planning",
                        datetime(2026, 9, 15, 10, 0, tzinfo=MINUS_SIX))
            conn.commit()
        svc = _service(db, now, MINUS_SIX)
        now_utc = now.astimezone(timezone.utc)
        week = svc._week_strip(now_utc, True)
        assert week["total"] == 1
        upcoming = [i["id"] for i in svc._upcoming(now_utc)]
        assert upcoming == ["ev-wed", "ev-next"]
        end = datetime.fromisoformat(week["ends_at"])
        in_week = [
            i["id"] for i in svc._upcoming(now_utc)
            if datetime.fromisoformat(i["starts_at"].replace("Z", "+00:00")) < end
        ]
        assert in_week == ["ev-wed"]

    def test_bounds_ride_without_a_calendar(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        week = _service(db, now, MINUS_SIX)._week_strip(
            now.astimezone(timezone.utc), False,
        )
        assert week["days"] == [] and week["total"] == 0
        assert week["has_calendar"] is False
        assert week["ends_at"] == "2026-09-14T06:00:00+00:00"

    def test_default_zone_is_the_hubs_local_clock(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        now = datetime.now().astimezone()
        svc = _service(db, now, None)
        assert svc._local_zone() == datetime.now().astimezone().tzinfo
        monday, next_monday = svc._local_week_bounds(now.astimezone(timezone.utc))
        assert monday.weekday() == 0 and (monday.hour, monday.minute) == (0, 0)
        # The bound carries the offset in force ON that day (per instant).
        assert monday.utcoffset() == datetime.combine(monday.date(), time_of_day.min).astimezone().utcoffset()
        assert (next_monday.date() - monday.date()).days == 7


class TestDstEdge:
    """Counsel re-read condition 4 (hunt H-C): the week that crosses a DST
    edge keeps every event on its true local day and the Monday bound at the
    offset in force on Monday -- never the fixed offset of `now`."""

    @staticmethod
    def _seed_pair(db: Any, zone: Any, monday: datetime, sunday: datetime) -> None:
        with db._connection() as conn:
            _seed_event(conn, "e-mon", "Monday 00:30", monday)
            _seed_event(conn, "e-sun", "Sunday 00:30", sunday)
            conn.commit()

    def test_fall_back_week_with_zoneinfo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Denver, Sun 2026-11-01 20:00 MST (after the fall-back). Monday Oct 26
        was MDT (-6): the bound is 06:00Z, not the fixed -7's 07:00Z."""
        db = _isolate(tmp_path, monkeypatch)
        denver = ZoneInfo("America/Denver")
        now = datetime(2026, 11, 1, 20, 0, tzinfo=denver)
        self._seed_pair(
            db, denver,
            datetime(2026, 10, 26, 0, 30, tzinfo=denver),  # Monday 00:30 MDT
            datetime(2026, 11, 1, 0, 30, tzinfo=denver),   # Sunday 00:30 MDT
        )
        strip = _service(db, now, denver)._week_strip(now.astimezone(timezone.utc), True)
        assert strip["starts_at"] == "2026-10-26T06:00:00+00:00"
        assert strip["ends_at"] == "2026-11-02T07:00:00+00:00"
        assert strip["total"] == 2
        assert [(d["dow"], d["count"]) for d in strip["days"] if d["count"]] == [("MON", 1), ("SUN", 1)]
        assert [d["date"] for d in strip["days"]][::6] == ["2026-10-26", "2026-11-01"]

    def test_fall_back_week_with_the_hubs_system_zone(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The production default (no injected zone) under TZ=America/Denver."""
        db = _isolate(tmp_path, monkeypatch)
        monkeypatch.setenv("TZ", "America/Denver")
        time_module.tzset()
        try:
            denver = ZoneInfo("America/Denver")
            now = datetime(2026, 11, 1, 20, 0, tzinfo=denver)
            # What production passes: a fixed-offset `now` from astimezone().
            now_fixed = now.astimezone()
            assert now_fixed.utcoffset() == timedelta(hours=-7)
            self._seed_pair(
                db, denver,
                datetime(2026, 10, 26, 0, 30, tzinfo=denver),
                datetime(2026, 11, 1, 0, 30, tzinfo=denver),
            )
            strip = _service(db, now_fixed, None)._week_strip(now_fixed.astimezone(timezone.utc), True)
            assert strip["starts_at"] == "2026-10-26T06:00:00+00:00"
            assert strip["total"] == 2
            assert [(d["dow"], d["count"]) for d in strip["days"] if d["count"]] == [("MON", 1), ("SUN", 1)]
        finally:
            monkeypatch.delenv("TZ", raising=False)
            time_module.tzset()

    def test_spring_forward_week_with_zoneinfo(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Denver, Sun 2026-03-08 20:00 MDT (after the spring-forward). Monday
        Mar 2 was MST (-7): the bound is 07:00Z; Sunday's 23:30 MDT is still SUN."""
        db = _isolate(tmp_path, monkeypatch)
        denver = ZoneInfo("America/Denver")
        now = datetime(2026, 3, 8, 20, 0, tzinfo=denver)
        self._seed_pair(
            db, denver,
            datetime(2026, 3, 2, 0, 30, tzinfo=denver),   # Monday 00:30 MST
            datetime(2026, 3, 8, 23, 30, tzinfo=denver),  # Sunday 23:30 MDT (05:30Z Monday)
        )
        strip = _service(db, now, denver)._week_strip(now.astimezone(timezone.utc), True)
        assert strip["starts_at"] == "2026-03-02T07:00:00+00:00"
        assert strip["ends_at"] == "2026-03-09T06:00:00+00:00"
        assert strip["total"] == 2
        assert [(d["dow"], d["count"]) for d in strip["days"] if d["count"]] == [("MON", 1), ("SUN", 1)]


class TestArmedRowState:
    """C2: the armed row carries the recording's state."""

    def test_armed_projection_carries_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        db = _isolate(tmp_path, monkeypatch)
        now = datetime(2026, 9, 8, 12, 0, tzinfo=MINUS_SIX)
        starts = datetime(2026, 9, 8, 14, 0, tzinfo=MINUS_SIX)
        with db._connection() as conn:
            _seed_event(conn, "ev-standup", "Standup", starts)
            conn.execute(
                "INSERT INTO scheduled_recordings "
                "(id, title, cron_expr, tz, one_shot, duration_minutes, enabled, "
                "revision, created_at, next_fire_at, state, calendar_event_id, "
                "calendar_uid, calendar_source_id, born_from) "
                "VALUES ('rec-1', 'Standup', '', 'UTC', 1, 60, 1, 1, ?, ?, 'recording', "
                "'ev-standup', 'uid-ev-standup', 'src-work', 'calendar_event')",
                (time.time(), (starts - timedelta(minutes=5)).timestamp()),
            )
            conn.commit()
        items = _service(db, now, MINUS_SIX)._upcoming(now.astimezone(timezone.utc))
        row = next(i for i in items if i["id"] == "ev-standup")
        assert row["armed"]["recording_id"] == "rec-1"
        assert row["armed"]["state"] == "recording"
        # arms_at is a UTC instant; the face formats it in the browser's zone.
        assert row["armed"]["arms_at"] == "2026-09-08T19:55:00Z"
