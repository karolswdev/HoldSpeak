"""Production-composition coverage for the Dashboard Door read model."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

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
) -> DoorService:
    return DoorService(
        FollowThroughService(db, people_projection=people_service),
        RefinementThoughtService(db),
        db.scheduled_recordings,
        clock=lambda: now,
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
    assert "people" not in json.dumps(projection)
