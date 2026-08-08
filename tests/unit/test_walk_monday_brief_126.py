"""HS-126-09 end-to-end walk for the Monday Brief delivery path."""
from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from holdspeak.db.core import Database, reset_database
from holdspeak.mcp import tools
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBriefService


OWNER = Principal(PrincipalKind.OWNER, "monday-brief-walk-owner")
NOW = datetime.datetime(2026, 8, 3, 9, 30, tzinfo=datetime.UTC)


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(tools, "get_database", lambda: database)
    monkeypatch.setattr(tools, "get_observer", lambda: None)
    yield database
    reset_database()


def _seed_window(db: Database) -> None:
    timestamp = datetime.datetime(2026, 8, 1, 12, tzinfo=datetime.UTC).timestamp()
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method, principal_kind, args_summary,
                correlation_id, error)
               VALUES (?, ?, ?, ?, 'test', ?, ?, ?)""",
            ("write-note", timestamp, "NoteService", "create_note", '{"title":"Plan"}', "note-1", None),
        )
        conn.execute(
            """INSERT INTO pipeline_events
               (event_id, timestamp, service, method, principal_kind, args_summary,
                correlation_id, error)
               VALUES (?, ?, ?, ?, 'test', ?, ?, ?)""",
            ("failed-run", timestamp + 1, "WorkflowService", "run_workflow", "{}", "run-1", "connection reset"),
        )
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("brief-meeting", "2026-08-01T09:00:00", "Brief planning"),
        )
        conn.execute(
            """INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state)
               VALUES (?, ?, ?, ?, ?, 'open', 'accepted')""",
            ("overdue-action", "brief-meeting", "Call the customer", "Ada", (datetime.date.today() - datetime.timedelta(days=1)).isoformat()),
        )
    db.desk_decisions.upsert(
        decision_id="proposed-brief-decision",
        title="Adopt the Monday Brief",
        status="proposed",
    )


def test_walk_generates_and_delivers_all_four_sections(db: Database) -> None:
    _seed_window(db)
    service = MondayBriefService(db)

    brief = service.generate(OWNER, now=NOW)

    assert brief.sections["changed"]
    assert brief.sections["broke"]
    assert brief.sections["waiting"]
    assert brief.sections["decisions"]
    assert any(item.text == "NoteService.create_note" for item in brief.sections["changed"])
    assert brief.sections["broke"][0].text == "WorkflowService.run_workflow failed"
    assert any("Call the customer" in item.text for item in brief.sections["waiting"])
    assert any("Adopt the Monday Brief" in item.text for item in brief.sections["decisions"])

    mcp_brief = tools.dispatch("monday_brief.get", {}, OWNER)
    assert mcp_brief["id"] == brief.id
    assert any(item["source_ref"] == "pipeline:note-1" for item in mcp_brief["sections"]["changed"])

    regenerated = service.generate(OWNER, now=NOW + datetime.timedelta(hours=2))
    assert regenerated.id == brief.id


def test_walk_empty_window_is_honest(db: Database) -> None:
    brief = MondayBriefService(db).generate(OWNER, now=NOW)

    assert brief.headline == "Nothing material changed."
    assert brief.is_empty is True
