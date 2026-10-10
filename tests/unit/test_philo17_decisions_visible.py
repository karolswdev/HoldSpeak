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
    body = response.json()
    rows = body["decisions"]
    assert body["page"]["total"] == 4
    by_text = {row["text"]: row for row in rows}
    assert set(by_text) == {
        "Freeze the old ledger on Nov 5", "Run reconciliation nightly", "Pilot OTel in billing", "Use one schema"}
    sync = by_text["Freeze the old ledger on Nov 5"]
    assert (sync["source"], sync["meeting_id"], sync["meeting_title"]) == ("meeting", "m-sync", "Ledger cutover sync")
    assert sync["decided_at"].startswith("2026-10-09")
    assert sync["record_id"] == record["id"]
    assert sync["lifecycle"] == "active"  # the record's state wins over the row's
    assert by_text["Run reconciliation nightly"]["record_id"] is None
    desk = by_text["Use one schema"]
    assert (desk["source"], desk["meeting_id"], desk["meeting_title"]) == ("desk", None, None)
    assert desk["decided_at"]
    # Newest first.
    dates = [row["decided_at"] for row in rows]
    assert dates == sorted(dates, reverse=True)


def test_scope_all_pages_searches_and_reads_one_by_id(tmp_path, monkeypatch):
    db = Database(tmp_path / "pages.db")
    _seed(db)
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    first = client.get("/api/decisions", params={"scope": "all", "limit": 2}).json()
    second = client.get("/api/decisions", params={"scope": "all", "limit": 2, "offset": 2}).json()
    assert first["page"]["total"] == second["page"]["total"] == 4
    ids = [r["id"] for r in first["decisions"] + second["decisions"]]
    assert len(set(ids)) == 4

    found = client.get("/api/decisions", params={"scope": "all", "q": "cutover freeze"}).json()
    assert [r["text"] for r in found["decisions"]] == ["Freeze the old ledger on Nov 5"]
    assert found["page"]["total"] == 1

    oldest = second["decisions"][-1]
    one = client.get("/api/decisions", params={"scope": "all", "decision_id": oldest["id"], "limit": 1}).json()
    assert [r["id"] for r in one["decisions"]] == [oldest["id"]]

    mine = client.get("/api/decisions", params={"scope": "all", "meeting_id": "m-arch"}).json()
    assert [r["text"] for r in mine["decisions"]] == ["Pilot OTel in billing"]


def test_a_superseded_or_disputed_record_is_its_rows_state(tmp_path, monkeypatch):
    """Astra r1 (2): supersession and dispute change ``decision_records``
    only; the ledger row reads the record's state, not the source row's."""
    db = Database(tmp_path / "sealed.db")
    _seed(db)
    records = DecisionRecordService(db)
    sync = {d.text: d for d in db.decisions.list(meeting_id="m-sync")}
    old = records.create_from_meeting(OWNER, sync["Freeze the old ledger on Nov 5"].id)
    new = records.create_from_meeting(OWNER, sync["Run reconciliation nightly"].id)
    otel = records.create_from_meeting(OWNER, db.decisions.list(meeting_id="m-arch")[0].id)
    records.supersede(OWNER, old["id"], new["id"])
    records.dispute(OWNER, otel["id"], "Not agreed.")
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    rows = {r["text"]: r for r in client.get("/api/decisions", params={"scope": "all"}).json()["decisions"]}

    assert rows["Freeze the old ledger on Nov 5"]["lifecycle"] == "superseded"
    assert rows["Pilot OTel in billing"]["lifecycle"] == "disputed"
    assert rows["Run reconciliation nightly"]["lifecycle"] == "active"


def test_a_confirmed_action_is_never_a_decision(tmp_path, monkeypatch):
    """Astra r1 (1), through the real producers: confirming an ACTION writes a
    ``decisions`` row and an action-kind record; the ledger (the meeting's
    record and Intelligence) never lists it. The confirmed decision is listed
    with the record its proposal names (the identity MeetingDetail joins on)."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.test_philo15_decisions_day_one import OWNER as DAY_ONE_OWNER, _proposals, _run

    db = _run(tmp_path, monkeypatch)
    service = ProposalBridgeService(db)
    rows = _proposals(db, "m-day-one")
    decision = next(p for p in rows if p["text"] == "Use SQLite for the local meeting ledger")
    action = next(p for p in rows if p["text"].startswith("Write the migration"))
    kept = service.confirm_proposal(DAY_ONE_OWNER, decision["id"])
    service.confirm_proposal(DAY_ONE_OWNER, action["id"])
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    for params in ({"scope": "all"}, {"scope": "all", "meeting_id": "m-day-one"}):
        listed = client.get("/api/decisions", params=params).json()["decisions"]
        texts = [r["text"] for r in listed]
        assert not [t for t in texts if t.startswith("Write the migration")], texts
        confirmed = [r for r in listed if r["text"] == "Use SQLite for the local meeting ledger"]
        assert kept["decision_record_id"] in {r["record_id"] for r in confirmed}, confirmed


def test_plain_list_still_answers_desk_decisions(tmp_path, monkeypatch):
    db = Database(tmp_path / "plain.db")
    _seed(db)
    client = _app(db, SQLiteObserver(db._connection), monkeypatch)

    body = client.get("/api/decisions").json()

    assert [d["id"] for d in body["decisions"]] == ["d-adr"]
