"""Parked: the private brief waiting gather is replaced by Desk parity tests."""
from __future__ import annotations
from datetime import date, datetime, timedelta
from holdspeak.db.core import Database
from holdspeak.services.monday_brief_service import MondayBriefService


def _service(tmp_path):
    return MondayBriefService(Database(tmp_path / "brief.db"))


def _action(conn, item_id: str, task: str, *, owner: str | None, due: str | None) -> None:
    meeting_id = f"meeting-{item_id}"
    conn.execute(
        "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
        (meeting_id, "2026-08-01T09:00:00", "Planning"),
    )
    conn.execute(
        """INSERT INTO action_items
           (id, meeting_id, task, owner, due, status, review_state, created_at)
           VALUES (?, ?, ?, ?, ?, 'open', 'accepted', datetime('now'))""",
        (item_id, meeting_id, task, owner, due),
    )


def test_waiting_collects_overdue_follow_through(tmp_path):
    service = _service(tmp_path)
    with service._db._connection() as conn:
        _action(
            conn,
            "action-overdue",
            "Send the revised proposal",
            owner="Ada",
            due=(date.today() - timedelta(days=1)).isoformat(),
        )

    items = service._collect_waiting(None)

    overdue = next(item for item in items if item.source_ref == "action_item:action-overdue")
    assert overdue.section == "waiting"
    assert overdue.text == "Overdue: Send the revised proposal"
    assert overdue.priority == 300


def test_waiting_collects_high_priority_cadence_loops(tmp_path):
    service = _service(tmp_path)
    with service._db._connection() as conn:
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, priority, owner)
               VALUES ('loop-high', 'manual', 'source-1', 'Confirm launch owner', 'open', 'high', 'Ada')"""
        )
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, priority)
               VALUES ('loop-closed', 'manual', 'source-2', 'Already resolved', 'closed', 'urgent')"""
        )

    items = service._collect_waiting(None)

    assert [(item.text, item.source_ref, item.priority) for item in items] == [
        ("Open loop: Confirm launch owner", "cadence_loop:loop-high", 100)
    ]


def test_waiting_is_empty_without_pending_work(tmp_path):
    service = _service(tmp_path)

    assert service._collect_waiting(None) == []


def test_waiting_prioritizes_overdue_before_unassigned_and_loops(tmp_path):
    service = _service(tmp_path)
    with service._db._connection() as conn:
        _action(
            conn,
            "action-overdue",
            "Escalate incident",
            owner="Ada",
            due=(date.today() - timedelta(days=1)).isoformat(),
        )
        _action(conn, "action-unassigned", "Choose an owner", owner=None, due=None)
        conn.execute(
            """INSERT INTO cadence_loops
               (id, source_type, source_id, title, status, priority, owner)
               VALUES ('loop-urgent', 'manual', 'source-3', 'Renew contract', 'open', 'urgent', 'Ada')"""
        )

    items = service._collect_waiting(None)

    assert [item.source_ref for item in items] == [
        "action_item:action-overdue",
        "action_item:action-unassigned",
        "cadence_loop:loop-urgent",
    ]
    assert [item.priority for item in items] == [300, 200, 120]



def test_an_item_with_an_owner_is_never_named_unassigned(tmp_path):
    """Inventory gap 11: a meeting's action item is born `pending` review. With
    an owner it is "To review", never "Unassigned ... Needs an owner". The
    item is saved by the real producer (``save_meeting``)."""
    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState

    service = _service(tmp_path)
    start = datetime.now().replace(microsecond=0) - timedelta(hours=2)
    service._db.meetings.save_meeting(MeetingState(
        id="m-owned", started_at=start, ended_at=start + timedelta(minutes=30), title="Planning",
        intel=IntelSnapshot(timestamp=0.0, summary="Planned.", action_items=[
            ActionItem(task="Draft the migration runbook", owner="Dana"),
            ActionItem(task="Book the dry run"),
        ]), intel_status="completed"))

    by_text = {item.text: item.detail for item in service._collect_waiting(None)}

    assert by_text == {
        "To review: Draft the migration runbook": "Not reviewed",
        "Unassigned: Book the dry run": "Needs an owner",
    }
