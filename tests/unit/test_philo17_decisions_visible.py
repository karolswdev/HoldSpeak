"""PHILO-17 ("what did we decide yesterday?"): a meeting's decisions are
readable per meeting, and Intelligence → Decisions lists every decision on
the desk with its date and its meeting (``GET /api/decisions?scope=all``)."""
from __future__ import annotations

import datetime as dt

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.sqlite_observer import SQLiteObserver

from tests.unit.test_philo6_04_one_cause_one_row import _app

OWNER = Principal(PrincipalKind.OWNER, "philo17-owner")


def _meeting(db: Database, meeting_id: str, title: str, day: int, decisions: list[str]) -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id, title=title,
        started_at=dt.datetime(2026, 10, day, 9), ended_at=dt.datetime(2026, 10, day, 9, 30),
    ))
    if decisions:
        db.plugins.record_artifact(
            artifact_id=f"{meeting_id}-decisions", meeting_id=meeting_id, artifact_type="decisions",
            title="Meeting decisions", plugin_id="philo17",
            structured_json={"decisions": [{"decision": d, "rationale": "Agreed."} for d in decisions]},
        )


def _seed(db: Database) -> None:
    _meeting(db, "m-sync", "Ledger cutover sync", 9, ["Freeze the old ledger on Nov 5", "Run reconciliation nightly"])
    _meeting(db, "m-arch", "Architecture review", 8, ["Pilot OTel in billing"])
    db.desk_decisions.upsert(decision_id="d-adr", title="Use one schema", status="accepted",
                             decision_markdown="One schema.")


def test_decisions_per_meeting_are_that_meetings_only(tmp_path, monkeypatch):
    db = Database(tmp_path / "per-meeting.db")
    _seed(db)
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    body = client.get("/api/decisions", params={"meeting_id": "m-sync"}).json()

    assert sorted(d["text"] for d in body["decisions"]) == [
        "Freeze the old ledger on Nov 5", "Run reconciliation nightly"]
    assert {d["source_meeting_id"] for d in body["decisions"]} == {"m-sync"}


def test_scope_all_lists_every_decision_with_date_meeting_and_record(tmp_path, monkeypatch):
    db = Database(tmp_path / "ledger.db")
    _seed(db)
    freeze = next(d for d in db.decisions.list(meeting_id="m-sync") if d.text.startswith("Freeze"))
    record = DecisionRecordService(db).create_from_meeting(OWNER, freeze.id)
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    response = client.get("/api/decisions", params={"scope": "all"})

    assert response.status_code == 200
    rows = response.json()["decisions"]
    by_text = {row["text"]: row for row in rows}
    assert set(by_text) == {
        "Freeze the old ledger on Nov 5", "Run reconciliation nightly", "Pilot OTel in billing", "Use one schema"}
    sync = by_text["Freeze the old ledger on Nov 5"]
    assert (sync["source"], sync["meeting_id"], sync["meeting_title"]) == ("meeting", "m-sync", "Ledger cutover sync")
    assert sync["decided_at"].startswith("2026-10-09")
    assert sync["record_id"] == record["id"]
    assert by_text["Run reconciliation nightly"]["record_id"] is None
    desk = by_text["Use one schema"]
    assert (desk["source"], desk["meeting_id"], desk["meeting_title"]) == ("desk", None, None)
    assert desk["decided_at"]
    # Newest first.
    dates = [row["decided_at"] for row in rows]
    assert dates == sorted(dates, reverse=True)


def test_plain_list_still_answers_desk_decisions(tmp_path, monkeypatch):
    db = Database(tmp_path / "plain.db")
    _seed(db)
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    body = client.get("/api/decisions").json()

    assert [d["id"] for d in body["decisions"]] == ["d-adr"]
