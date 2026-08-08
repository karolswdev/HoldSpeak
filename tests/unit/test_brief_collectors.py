"""Waiting-work collectors for the Monday Brief."""
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


# Breakage collectors ---------------------------------------------------------


def _breakage_event(
    service: MondayBriefService,
    *,
    event_id: str,
    timestamp: datetime,
    service_name: str = "SyncService",
    method: str = "push",
    error: str | None = "network unavailable",
    error_code: str | None = "NETWORK",
) -> None:
    with service._db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method, principal_kind, error, error_code)
               VALUES (?, ?, ?, ?, 'owner', ?, ?)""",
            (event_id, timestamp.timestamp(), service_name, method, error, error_code),
        )


def _breakage_window() -> tuple[str, str]:
    return ("2026-08-01T09:00:00", "2026-08-01T17:00:00")


def test_breakage_pipeline_event_with_error_appears(tmp_path):
    service = _service(tmp_path)
    _breakage_event(service, event_id="evt-failed", timestamp=datetime(2026, 8, 1, 12))

    items = service._collect_breakage(*_breakage_window())

    assert len(items) == 1
    assert items[0].section == "broke"
    assert items[0].text == "SyncService.push failed"
    assert items[0].detail == "NETWORK: network unavailable"
    assert items[0].source_ref == "pipeline-event:evt-failed"


def test_breakage_successful_events_do_not_appear(tmp_path):
    service = _service(tmp_path)
    _breakage_event(
        service,
        event_id="evt-success",
        timestamp=datetime(2026, 8, 1, 12),
        error=None,
        error_code=None,
    )

    assert service._collect_breakage(*_breakage_window()) == []


def test_breakage_repeated_service_method_failures_deduplicate(tmp_path):
    service = _service(tmp_path)
    _breakage_event(service, event_id="evt-first", timestamp=datetime(2026, 8, 1, 11))
    _breakage_event(
        service,
        event_id="evt-latest",
        timestamp=datetime(2026, 8, 1, 12),
        error="retry exhausted",
    )

    items = service._collect_breakage(*_breakage_window())

    assert len(items) == 1
    assert items[0].source_ref == "pipeline-event:evt-latest"
    assert items[0].detail == "NETWORK: retry exhausted"


def test_breakage_events_outside_window_are_excluded(tmp_path):
    service = _service(tmp_path)
    _breakage_event(service, event_id="evt-before", timestamp=datetime(2026, 8, 1, 8, 59))
    _breakage_event(service, event_id="evt-after", timestamp=datetime(2026, 8, 1, 17, 1))

    assert service._collect_breakage(*_breakage_window()) == []


def test_breakage_empty_window_has_no_items(tmp_path):
    service = _service(tmp_path)

    assert service._collect_breakage(*_breakage_window()) == []


# Owner-decision collectors ---------------------------------------------------


def _propose_actuator(service: MondayBriefService) -> str:
    proposal = service._db.actuators.record_proposal(
        meeting_id=None,
        origin="desk",
        window_id="",
        plugin_id="test",
        plugin_version="1",
        idempotency_key="brief-proposal-1",
        target="github",
        action="create_issue",
        preview="Create the follow-up issue",
        proposal_id="11111111-1111-1111-1111-111111111111",
    )
    return proposal.id


def test_proposed_decision_appears_in_decisions_section(tmp_path):
    service = _service(tmp_path)
    service._db.desk_decisions.upsert(
        decision_id="desk-decision-1", title="Choose the release train", status="proposed"
    )

    brief = service.generate(None, now=datetime(2026, 8, 3, 9, 30))

    assert [(item.text, item.source_ref) for item in brief.sections["decisions"]] == [
        ("Review decision: Choose the release train", "decision:desk-decision-1")
    ]


def test_pending_actuator_proposal_appears_in_decisions_section(tmp_path):
    service = _service(tmp_path)
    proposal_id = _propose_actuator(service)

    brief = service.generate(None, now=datetime(2026, 8, 3, 9, 30))

    assert [(item.text, item.source_ref) for item in brief.sections["decisions"]] == [
        ("Authorize github create_issue: Create the follow-up issue", f"actuator_proposal:{proposal_id}")
    ]


def test_accepted_decision_with_no_pending_review_is_excluded(tmp_path):
    service = _service(tmp_path)
    service._db.desk_decisions.upsert(
        decision_id="desk-decision-1", title="Already decided", status="accepted"
    )

    assert service._collect_decisions(None) == []


def test_decisions_are_ranked_by_urgency(tmp_path):
    service = _service(tmp_path)
    proposal_id = _propose_actuator(service)
    service._db.desk_decisions.upsert(
        decision_id="desk-decision-1", title="Choose a direction", status="proposed"
    )

    items = service._collect_decisions(None)

    assert [item.source_ref for item in items] == [
        f"actuator_proposal:{proposal_id}",
        "decision:desk-decision-1",
    ]
    assert [item.priority for item in items] == [300, 200]


def test_no_pending_decisions_leaves_empty_decisions_section(tmp_path):
    service = _service(tmp_path)

    brief = service.generate(None, now=datetime(2026, 8, 3, 9, 30))

    assert brief.sections["decisions"] == []


def test_breakage_failed_connector_run_appears(tmp_path):
    service = _service(tmp_path)
    with service._db._connection() as conn:
        conn.execute(
            """INSERT INTO connector_runs
               (connector_id, started_at, finished_at, succeeded, error)
               VALUES ('github', '2026-08-01T12:00:00', '2026-08-01T12:01:00', 0, 'token expired')"""
        )

    items = service._collect_breakage(*_breakage_window())

    assert len(items) == 1
    assert items[0].text == "Connector github failed"
    assert items[0].detail == "token expired"
    assert items[0].source_ref == "connector-run:1"
