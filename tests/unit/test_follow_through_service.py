"""Unit coverage for the HS-125 follow-through board projection."""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sqlite3
from typing import Any

import pytest

import holdspeak.services.follow_through_service as follow_through_module
from holdspeak.cadence.collector import LoopCollector
from holdspeak.cadence.models import OpenLoop
from holdspeak.db.core import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.door_service import DoorService
from holdspeak.services.follow_through_service import FollowThroughCard, FollowThroughService
from holdspeak.services.refinement_thought_service import INBOX_DIRECTORY_ID, RefinementThoughtService


OWNER = Principal(PrincipalKind.OWNER, "follow-through-owner")


@pytest.fixture
def db(tmp_path: Path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _insert_action(
    db: Database,
    item_id: str,
    *,
    meeting_id: str = "meeting-1",
    task: str = "Follow up",
    owner: str | None = "Ada",
    due: str | None = None,
    status: str = "open",
    review_state: str = "accepted",
    source_timestamp: float | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            (meeting_id, "2026-08-01T09:00:00", "Planning"),
        )
        conn.execute(
            "INSERT INTO action_items "
            "(id, meeting_id, task, owner, due, status, review_state, source_timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (item_id, meeting_id, task, owner, due, status, review_state, source_timestamp),
        )


def _insert_segment(
    db: Database,
    *,
    meeting_id: str = "meeting-1",
    text: str = "Ada will follow up after the meeting.",
    speaker: str = "Ada",
    start_time: float = 30.0,
    end_time: float = 60.0,
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
            "VALUES (?, ?, ?, ?, ?)",
            (meeting_id, text, speaker, start_time, end_time),
        )


def _card_ids(cards: list[object]) -> list[str]:
    return [card.id for card in cards]  # type: ignore[attr-defined]


def _board_cards(service: FollowThroughService, *, owner: str | None = None) -> list[FollowThroughCard]:
    board = service.board(OWNER, owner=owner)
    return board.now + board.waiting + board.unassigned + board.overdue


def _add_note_task(db: Database) -> dict[str, Any]:
    db.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    thoughts = RefinementThoughtService(db)
    thoughts.create(
        OWNER, request_id="follow-through-note", raw_text="Send the project plan",
        initial_note={"id": "source-note", "title": "Project plan"},
    )
    return DoorService(
        FollowThroughService(db), thoughts, db.scheduled_recordings, db.calendar_events, db=db,
    ).add_item(
        OWNER, "Send the project plan", owner="Ada", due=date.today().isoformat(),
        source_type="note", source_ref="note:source-note",
    )


def _insert_accepted_decision(db: Database, decision_id: str = "decision-1") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("decision-meeting", "2026-08-01T09:00:00", "Decision meeting"),
        )
        conn.execute(
            """INSERT INTO decisions
               (id, text, decided_at, source_artifact_id, source_meeting_id, lifecycle)
               VALUES (?, ?, ?, ?, ?, 'recorded')""",
            (
                decision_id,
                "Ship the accountable commitment flow",
                "2026-08-01T09:30:00",
                "decision-artifact",
                "decision-meeting",
            ),
        )
    DecisionLifecycleService(db).transition(OWNER, decision_id, "accept")
    return decision_id


def test_empty_database_returns_empty_lanes(db: Database) -> None:
    board = FollowThroughService(db).board(OWNER)

    assert board.now == []
    assert board.waiting == []
    assert board.unassigned == []
    assert board.overdue == []


def test_past_open_action_is_overdue(db: Database) -> None:
    _insert_action(db, "past", due=(date.today() - timedelta(days=1)).isoformat())

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.overdue) == ["past"]


def test_action_due_today_is_now(db: Database) -> None:
    _insert_action(db, "today", due=date.today().isoformat())

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.now) == ["today"]


def test_action_due_in_five_days_is_waiting(db: Database) -> None:
    _insert_action(db, "later", due=(date.today() + timedelta(days=5)).isoformat())

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.waiting) == ["later"]


def test_ownerless_action_is_unassigned_regardless_of_due_date(db: Database) -> None:
    _insert_action(
        db,
        "unowned",
        owner=None,
        due=(date.today() - timedelta(days=1)).isoformat(),
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.unassigned) == ["unowned"]
    assert board.overdue == []


def test_done_action_is_excluded(db: Database) -> None:
    _insert_action(db, "done", due=date.today().isoformat(), status="done")

    board = FollowThroughService(db).board(OWNER)

    assert board.now == []
    assert board.waiting == []
    assert board.unassigned == []
    assert board.overdue == []


def test_filtering_by_project_id(db: Database) -> None:
    _insert_action(db, "in-project", meeting_id="project-meeting")
    _insert_action(db, "outside-project", meeting_id="other-meeting")
    with db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES (?, ?)", ("project-1", "Project"))
        conn.execute(
            "INSERT INTO meeting_projects (meeting_id, project_id) VALUES (?, ?)",
            ("project-meeting", "project-1"),
        )

    board = FollowThroughService(db).board(OWNER, project_id="project-1")

    assert _card_ids(board.waiting) == ["in-project"]


def test_filtering_by_owner(db: Database) -> None:
    _insert_action(db, "ada", owner="Ada")
    _insert_action(db, "grace", owner="Grace")

    board = FollowThroughService(db).board(OWNER, owner="Grace")

    assert _card_ids(board.waiting) == ["grace"]


def test_commit_decision_creates_action_and_commitment(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)

    commitment = FollowThroughService(db).commit_decision(OWNER, decision_id)
    event = db.automations.list_events(event_type="decision.committed")[0]
    assert event["subject_ref"] == f"decision:{decision_id}"
    assert f'action_item:{commitment["action_item_id"]}' in event["refs"]

    assert commitment["decision_id"] == decision_id
    assert commitment["status"] == "open"
    with db._connection() as conn:
        action = conn.execute(
            "SELECT task, meeting_id FROM action_items WHERE id = ?",
            (commitment["action_item_id"],),
        ).fetchone()
        stored = conn.execute(
            "SELECT * FROM decision_commitments WHERE id = ?", (commitment["id"],)
        ).fetchone()
    assert action["task"] == "Ship the accountable commitment flow"
    assert action["meeting_id"] == "decision-meeting"
    assert stored["decision_id"] == decision_id
    assert stored["action_item_id"] == commitment["action_item_id"]


def test_commit_decision_keeps_owner_and_due_date(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)

    commitment = FollowThroughService(db).commit_decision(
        OWNER, decision_id, owner="Ada", due_at="2026-08-14"
    )

    assert commitment["owner"] == "Ada"
    assert commitment["due_at"] == "2026-08-14"
    with db._connection() as conn:
        action = conn.execute(
            "SELECT owner, due FROM action_items WHERE id = ?",
            (commitment["action_item_id"],),
        ).fetchone()
    assert dict(action) == {"owner": "Ada", "due": "2026-08-14"}


def test_board_shows_decision_on_commitment_card(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)
    commitment = FollowThroughService(db).commit_decision(OWNER, decision_id, owner="Ada")

    board = FollowThroughService(db).board(OWNER)
    card = next(card for card in board.waiting if card.id == commitment["action_item_id"])

    assert card.decision_id == decision_id
    assert card.source == "action_item"


def test_action_card_provenance_resolves_its_source_segment(db: Database) -> None:
    _insert_action(db, "with-source", source_timestamp=45.0)
    _insert_segment(db, text="Ada promised to follow up.", speaker="Ada")

    card = FollowThroughService(db).board(OWNER).waiting[0]

    assert card.provenance is not None
    assert card.provenance.available is True
    assert card.provenance.meeting_id == "meeting-1"
    assert card.provenance.segment_text == "Ada promised to follow up."
    assert card.provenance.segment_speaker == "Ada"
    assert card.provenance.segment_start == 30.0
    assert card.provenance.moment is None


def test_commitment_card_provenance_includes_decision_moment(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)
    _insert_segment(
        db,
        meeting_id="decision-meeting",
        text="We will ship the accountable commitment flow.",
        start_time=20.0,
        end_time=50.0,
    )
    with db._connection() as conn:
        conn.execute(
            "UPDATE decisions SET source_timestamp = ? WHERE id = ?",
            (30.0, decision_id),
        )
    commitment = FollowThroughService(db).commit_decision(OWNER, decision_id, owner="Ada")

    card = next(
        card
        for card in FollowThroughService(db).board(OWNER).waiting
        if card.id == commitment["action_item_id"]
    )

    assert card.provenance is not None
    assert card.provenance.available is True
    assert card.provenance.moment is not None
    assert card.provenance.moment["meeting_id"] == "decision-meeting"
    assert card.provenance.moment["text"] == "We will ship the accountable commitment flow."


def test_action_card_without_source_timestamp_has_unavailable_provenance(db: Database) -> None:
    _insert_action(db, "no-source")

    card = FollowThroughService(db).board(OWNER).waiting[0]

    assert card.provenance is not None
    assert card.provenance.available is False


def test_action_card_with_no_meeting_segments_has_unavailable_provenance(db: Database) -> None:
    _insert_action(db, "no-segments", source_timestamp=45.0)

    card = FollowThroughService(db).board(OWNER).waiting[0]

    assert card.provenance is not None
    assert card.provenance.available is False


def test_provenance_resolution_failure_is_unavailable_not_an_error(
    db: Database, monkeypatch: pytest.MonkeyPatch
) -> None:
    _insert_action(db, "resolver-failure", source_timestamp=45.0)

    def raise_resolution_error(*args: object, **kwargs: object) -> None:
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(db.decisions, "resolve_segment", raise_resolution_error)

    card = FollowThroughService(db).board(OWNER).waiting[0]

    assert card.provenance is not None
    assert card.provenance.available is False


def test_accepting_decision_without_commitment_remains_supported(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)

    with db._connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM decision_commitments WHERE decision_id = ?", (decision_id,)
        ).fetchone()[0]
    assert count == 0


def test_pending_review_action_with_past_due_is_unassigned_not_overdue(db: Database) -> None:
    _insert_action(
        db,
        "needs-review",
        due=(date.today() - timedelta(days=1)).isoformat(),
        review_state="pending",
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.unassigned) == ["needs-review"]
    assert board.overdue == []


def test_pipeline_pending_action_with_past_due_is_overdue(db: Database) -> None:
    # HS-132-14 walk finding: pipeline-persisted items carry "pending"
    # (db/meetings.py constrains to pending/done/dismissed; only
    # commit_decision writes "open"), so gating overdue on "open" alone
    # meant a meeting-born commitment could NEVER reach the Overdue lane.
    _insert_action(
        db,
        "pipeline-overdue",
        due=(date.today() - timedelta(days=6)).isoformat(),
        status="pending",
        review_state="accepted",
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.overdue) == ["pipeline-overdue"]


def test_accepted_review_action_with_past_due_is_overdue(db: Database) -> None:
    _insert_action(
        db,
        "reviewed-overdue",
        due=(date.today() - timedelta(days=1)).isoformat(),
        review_state="accepted",
    )

    board = FollowThroughService(db).board(OWNER)

    assert _card_ids(board.overdue) == ["reviewed-overdue"]


def test_due_lane_changes_as_today_advances(db: Database, monkeypatch: pytest.MonkeyPatch) -> None:
    start = date(2026, 8, 7)
    _insert_action(db, "time-travel", due=(start + timedelta(days=3)).isoformat())

    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return current_day[0]

    current_day = [start]
    monkeypatch.setattr(follow_through_module, "date", FrozenDate)
    service = FollowThroughService(db)

    assert _card_ids(service.board(OWNER).waiting) == ["time-travel"]
    current_day[0] = start + timedelta(days=1)
    assert _card_ids(service.board(OWNER).now) == ["time-travel"]
    current_day[0] = start + timedelta(days=4)
    assert _card_ids(service.board(OWNER).overdue) == ["time-travel"]


def test_snoozed_action_loop_is_excluded_from_active_lanes(db: Database) -> None:
    _insert_action(db, "snoozed", due=(date.today() - timedelta(days=1)).isoformat())
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, snoozed_until)
               VALUES (?, 'meeting_action', ?, ?, 'snoozed', ?)""",
            (
                "loop-snoozed",
                "snoozed",
                "Follow up",
                (date.today() + timedelta(days=1)).isoformat(),
            ),
        )

    board = FollowThroughService(db).board(OWNER)

    assert board.now == []
    assert board.waiting == []
    assert board.unassigned == []
    assert board.overdue == []


def test_new_note_task_snooze_creates_one_durable_canonical_loop(db: Database) -> None:
    item = _add_note_task(db)
    item_id = str(item["id"])
    service = FollowThroughService(db)
    until = (date.today() + timedelta(days=1)).isoformat()
    assert _card_ids(_board_cards(service)) == [item_id]
    assert db.cadence.get_loop_by_source("meeting_action", item_id) is None
    with db._connection() as conn:
        before = dict(conn.execute("SELECT * FROM action_items WHERE id = ?", (item_id,)).fetchone())

    result = service.complete(OWNER, item_id, "snooze", {"until": until})

    loop = db.cadence.get_loop_by_source("meeting_action", item_id)
    assert loop is not None
    assert result["loop_ids"] == [loop.id]
    assert (loop.source_type, loop.source_id, loop.title) == ("meeting_action", item_id, item["task"])
    assert (loop.owner, loop.due_at) == (item["owner"], item["due"])
    assert (loop.status, loop.snoozed_until) == ("snoozed", until)
    assert _board_cards(service) == []

    replay = service.complete(OWNER, item_id, "snooze", {"until": until})
    assert replay["loop_ids"] == [loop.id]
    assert [saved.id for saved in db.cadence.list_loops(include_terminal=True)] == [loop.id]

    # Open Door tasks are outside the collector's pending-only action scan.
    # Its missing-source pass must retain the user's existing snooze.
    LoopCollector(db).collect()
    collected = db.cadence.get_loop_by_source("meeting_action", item_id)
    assert collected is not None
    assert (collected.id, collected.status, collected.snoozed_until) == (loop.id, "snoozed", until)
    # The actual source upsert also retains the lifecycle when it enriches it.
    projected = db.cadence.upsert_loop(OpenLoop(
        source_type="meeting_action", source_id=item_id, title=str(item["task"]),
        owner=str(item["owner"]), due_at=str(item["due"]), summary="Updated source",
    ))
    assert (projected.id, projected.status, projected.snoozed_until) == (loop.id, "snoozed", until)
    assert _board_cards(FollowThroughService(db)) == []
    with db._connection() as conn:
        after = dict(conn.execute("SELECT * FROM action_items WHERE id = ?", (item_id,)).fetchone())
    assert after == before


def test_collector_upsert_keeps_snoozed_action_identity_and_lifecycle(db: Database) -> None:
    _insert_action(db, "collector-snooze", status="pending", due=date.today().isoformat())
    service = FollowThroughService(db)
    until = (date.today() + timedelta(days=1)).isoformat()
    result = service.complete(OWNER, "collector-snooze", "snooze", {"until": until})

    collected = LoopCollector(db).collect()

    projected = next(loop for loop in collected if loop.source_id == "collector-snooze")
    assert result["loop_ids"] == [projected.id]
    assert projected.summary == "From Planning"
    assert (projected.status, projected.snoozed_until) == ("snoozed", until)
    assert _board_cards(service) == []


def test_snooze_survives_owner_filter_until_expiry_after_delegate(
    db: Database, monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_day = [date(2026, 10, 15)]

    class FrozenDate(date):
        @classmethod
        def today(cls) -> date:
            return current_day[0]

    monkeypatch.setattr(follow_through_module, "date", FrozenDate)
    _insert_action(db, "owner-snooze", owner="Ada", due=current_day[0].isoformat())
    service = FollowThroughService(db)
    until = (current_day[0] + timedelta(days=1)).isoformat()
    service.complete(OWNER, "owner-snooze", "snooze", {"until": until})
    service.complete(OWNER, "owner-snooze", "delegate", {"to": "Grace"})
    loop = db.cadence.get_loop_by_source("meeting_action", "owner-snooze")
    assert loop is not None and loop.owner == "Ada"
    ada_loop = db.cadence.upsert_loop(OpenLoop(
        source_type="proposal", source_id="ada-standalone", title="Ada's other task", owner="Ada",
    ))
    grace_loop = db.cadence.upsert_loop(OpenLoop(
        source_type="proposal", source_id="grace-standalone", title="Grace's other task", owner="Grace",
    ))

    assert _card_ids(_board_cards(service, owner="Grace")) == [grace_loop.id]
    assert _card_ids(_board_cards(service, owner="Ada")) == [ada_loop.id]

    current_day[0] += timedelta(days=1)
    cards = _board_cards(service, owner="Grace")
    assert {card.id for card in cards} == {"owner-snooze", grace_loop.id}
    action_card = next(card for card in cards if card.id == "owner-snooze")
    assert action_card.owner == "Grace"
    assert _card_ids(_board_cards(service, owner="Ada")) == [ada_loop.id]


@pytest.mark.parametrize("until", [" 2099-01-01 ", "2099-01-01T09:30:00Z", "tomorrow"])
def test_snooze_keeps_existing_nonempty_string_input_compatibility(db: Database, until: str) -> None:
    _insert_action(db, "new-snooze")

    result = FollowThroughService(db).complete(OWNER, "new-snooze", "snooze", {"until": until})

    loop = db.cadence.get_loop_by_source("meeting_action", "new-snooze")
    assert loop is not None
    assert result["loop_ids"] == [loop.id]
    assert (loop.status, loop.snoozed_until) == ("snoozed", until.strip())


@pytest.mark.parametrize("until", [None, "", " ", 123])
def test_refused_snooze_does_not_create_a_loop(db: Database, until: object) -> None:
    _insert_action(db, "refused-snooze")

    with pytest.raises(ValueError, match="snooze requires"):
        FollowThroughService(db).complete(OWNER, "refused-snooze", "snooze", {"until": until})

    assert db.cadence.list_loops(include_terminal=True) == []
    assert _card_ids(_board_cards(FollowThroughService(db))) == ["refused-snooze"]


def test_snooze_loop_creation_rolls_back_if_the_transition_fails(db: Database) -> None:
    _insert_action(db, "atomic-snooze")
    with db._connection() as conn:
        conn.execute("""CREATE TRIGGER refuse_snooze BEFORE UPDATE OF status ON cadence_loops
                        WHEN NEW.status = 'snoozed'
                        BEGIN SELECT RAISE(ABORT, 'snooze refused'); END""")

    with pytest.raises(sqlite3.IntegrityError, match="snooze refused"):
        FollowThroughService(db).complete(OWNER, "atomic-snooze", "snooze", {"until": "2099-01-01"})

    assert db.cadence.list_loops(include_terminal=True) == []
    assert _card_ids(_board_cards(FollowThroughService(db))) == ["atomic-snooze"]


@pytest.mark.parametrize("verb,payload", [
    ("done", None), ("dismiss", None), ("delegate", {"to": "Grace"}),
    ("due", {"due_at": "2099-01-01"}), ("reopen", None),
])
def test_unrelated_action_verbs_do_not_create_loops(db: Database, verb: str, payload: dict | None) -> None:
    _insert_action(db, "no-loop")

    result = FollowThroughService(db).complete(OWNER, "no-loop", verb, payload)

    assert result["loop_ids"] == []
    assert db.cadence.list_loops(include_terminal=True) == []


def test_collected_decision_is_represented_by_its_action_not_a_second_loop(db: Database) -> None:
    decision_id = _insert_accepted_decision(db)
    service = FollowThroughService(db)
    commitment = service.commit_decision(OWNER, decision_id, owner="Ada")
    LoopCollector(db).collect()
    decision_loop = db.cadence.get_loop_by_source("meeting_decision", decision_id)
    assert decision_loop is not None
    action_loop = db.cadence.upsert_loop(OpenLoop(
        source_type="meeting_action", source_id=commitment["action_item_id"],
        title=decision_loop.title, owner="Ada",
    ))
    standalone_id = _insert_accepted_decision(db, "standalone-decision")
    standalone_loop = db.cadence.upsert_loop(OpenLoop(
        source_type="meeting_decision", source_id=standalone_id,
        title=decision_loop.title, owner="Ada",
    ))
    unrelated_loop = db.cadence.upsert_loop(OpenLoop(
        source_type="proposal", source_id="same-text-proposal", title=decision_loop.title, owner="Ada",
    ))

    cards = _board_cards(service)
    assert {card.id for card in cards} == {commitment["action_item_id"], standalone_loop.id, unrelated_loop.id}
    action_card = next(card for card in cards if card.id == commitment["action_item_id"])
    assert (action_card.source, action_card.decision_id) == ("action_item", decision_id)
    standalone_card = next(card for card in cards if card.id == standalone_loop.id)
    assert (standalone_card.source, standalone_card.decision_id) == ("decision", standalone_id)

    service.complete(OWNER, commitment["action_item_id"], "delegate", {"to": "Grace"})
    assert {card.id for card in _board_cards(service, owner="Ada")} == {standalone_loop.id, unrelated_loop.id}
    assert _card_ids(_board_cards(service, owner="Grace")) == [commitment["action_item_id"]]

    result = service.complete(OWNER, commitment["action_item_id"], "done")
    assert result["loop_ids"] == [action_loop.id]
    assert result["commitment_ids"] == [commitment["id"]]
    assert {card.id for card in _board_cards(service)} == {standalone_loop.id, unrelated_loop.id}
    # The canonical action wins before the next collector closes its old loop.
    stale_decision_loop = db.cadence.get_loop(str(decision_loop.id))
    assert stale_decision_loop is not None and stale_decision_loop.status == "open"
    with db._connection() as conn:
        assert conn.execute("SELECT status FROM action_items WHERE id = ?", (commitment["action_item_id"],)).fetchone()[0] == "done"
        assert conn.execute("SELECT status FROM decision_commitments WHERE id = ?", (commitment["id"],)).fetchone()[0] == "closed"
