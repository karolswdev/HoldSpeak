"""PHILO-6-02 round 3 — a brief line states only what the RECORD proves.

Astra's round-two check (``pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/
checks/lane-a-built-astra.md``, "Round two"):

* finding 1 — delegating, reopening or dating work stored ``Follow-up
  completed``: the fallback read the method NAME (``complete``) as the outcome
  of all six actions the method takes;
* finding 2 — "the last event is the outermost outcome" is false: the observer
  stores CALL-START time (``holdspeak/services/observer.py:113``) and the
  collector orders by that time, so a nested call sorts AFTER its parent. The
  round-2 positive control froze the clock, so insertion order decided and
  masked the field the collector reads;
* finding 4 — table words that claim more than the call proves (a cached
  brief is not a made brief; a reconciliation can change nothing).

Every producer below is REAL and observed by the REAL ``@observe_service`` +
``SQLiteObserver`` on an ADVANCING clock (each ``time.time()`` read moves the
clock 1 ms, so a nested call starts after its parent). The brief is the REAL
``MondayBriefService.generate``. Each asserted line is checked against the DB
state it names.
"""
from __future__ import annotations

import datetime
import json
from types import SimpleNamespace
from typing import Any

import pytest

import holdspeak.services.observer as observer_module
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.gate_service import GateService
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.project_service import ProjectService
from holdspeak.services.sqlite_observer import SQLiteObserver

from tests.unit.test_philo6_02_brief_truth import EVENTS_AT, GENERATED, OWNER

TITLE = "Keep retrieval local"


def _advancing_clock(monkeypatch) -> dict[str, float]:
    """The observer's clock moves 1 ms per read: never frozen."""
    now = {"t": EVENTS_AT.timestamp()}

    def tick() -> float:
        now["t"] += 0.001
        return now["t"]

    monkeypatch.setattr(observer_module, "time", SimpleNamespace(time=tick))
    return now


def _events(db: Database) -> list[dict[str, Any]]:
    with db._connection() as conn:
        return [
            dict(row)
            for row in conn.execute(
                """SELECT id, timestamp, service, method, correlation_id, error
                   FROM pipeline_events ORDER BY id ASC"""
            )
        ]


def _brief(db: Database, day: datetime.datetime = GENERATED) -> dict[str, list[str]]:
    brief = MondayBriefService(db).generate(OWNER, now=day)
    return {
        section: [item.text for item in items]
        for section, items in brief.sections.items()
    }


def _pipeline_changed(db: Database) -> list[str]:
    with db._connection() as conn:
        return [
            str(row["text"])
            for row in conn.execute(
                """SELECT text FROM monday_brief_items
                   WHERE section = 'changed' AND source_ref LIKE 'pipeline%'"""
            )
        ]


def _desk_decision(db: Database, decision_id: str = "philo603-present") -> str:
    db.desk_decisions.upsert(
        decision_id=decision_id,
        title=TITLE,
        status="accepted",
        decision_markdown="Keep retrieval local.",
    )
    return decision_id


# ── finding 2: the outermost call is the one that STARTED first ─────────────


def test_nested_success_keeps_the_parents_title_on_an_advancing_clock(
    tmp_path, monkeypatch
):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    decision_id = _desk_decision(db)
    record = DecisionRecordService(
        db, observer=SQLiteObserver(db._connection)
    ).create_from_desk(OWNER, decision_id)

    events = _events(db)
    parent = next(e for e in events if e["method"] == "create_from_desk")
    child = next(e for e in events if e["method"] == "create")
    # The real shape the collector reads: one correlation, the parent STARTED
    # first, and the child's receipt was INSERTED first (it finished first).
    assert parent["correlation_id"] == child["correlation_id"]
    assert parent["timestamp"] < child["timestamp"], (parent, child)
    assert child["id"] < parent["id"], (parent, child)

    changed = _brief(db)["changed"]
    # DB evidence: the record the line names exists, minted from this desk
    # decision.
    with db._connection() as conn:
        row = conn.execute(
            "SELECT source_type, source_id FROM decision_records WHERE id = ?",
            (record["id"],),
        ).fetchone()
    assert (row["source_type"], row["source_id"]) == ("desk", decision_id)
    assert f"Decision recorded: {TITLE}" in changed, changed
    # One operation, one line: the inner call is never the headline.
    assert _pipeline_changed(db) == [f"Decision recorded: {TITLE}"]


def test_nested_failure_stores_only_the_broke_line(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    with pytest.raises(KeyError):
        DecisionRecordService(
            db, observer=SQLiteObserver(db._connection)
        ).create_from_desk(OWNER, "philo603-absent")
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 0
    sections = _brief(db)
    assert _pipeline_changed(db) == [], sections["changed"]
    assert sections["broke"] == ["Decision did not record"], sections["broke"]


def test_an_existing_record_is_not_recorded_again(tmp_path, monkeypatch):
    """``create_from_desk`` returns the EXISTING record when one exists: the
    call succeeded but recorded nothing, so it makes no Changed line."""
    db = Database(tmp_path / "hub.db")
    decision_id = _desk_decision(db)
    DecisionRecordService(db).create_from_desk(OWNER, decision_id)  # unobserved
    _advancing_clock(monkeypatch)
    again = DecisionRecordService(
        db, observer=SQLiteObserver(db._connection)
    ).create_from_desk(OWNER, decision_id)
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0] == 1
    assert [e["method"] for e in _events(db)] == ["create_from_desk"], again
    changed = _brief(db)["changed"]
    assert _pipeline_changed(db) == [], changed


# ── finding 1: the follow-up line comes from the recorded ACTION ────────────


def _action(db: Database, card_id: str, *, status: str = "pending") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO action_items
               (id, meeting_id, task, owner, due, status, review_state,
                created_at, source_type, source_ref)
               VALUES (?, NULL, ?, NULL, NULL, ?, 'accepted', ?, 'thread', '')""",
            (card_id, f"Task {card_id}", status, "2026-09-24T00:00:00"),
        )
    return card_id


def _action_row(db: Database, card_id: str) -> dict[str, Any]:
    with db._connection() as conn:
        return dict(
            conn.execute(
                "SELECT status, owner, due FROM action_items WHERE id = ?", (card_id,)
            ).fetchone()
        )


def test_delegate_reopen_and_date_never_say_completed(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    service.complete(OWNER, _action(db, "ai-delegate"), "delegate", {"to": "Ana"})
    service.complete(OWNER, _action(db, "ai-reopen", status="done"), "reopen")
    service.complete(OWNER, _action(db, "ai-due"), "due", {"due_at": "2026-09-30"})

    # DB evidence: none of the three is complete.
    assert _action_row(db, "ai-delegate") == {"status": "pending", "owner": "Ana", "due": None}
    assert _action_row(db, "ai-reopen")["status"] == "open"
    assert _action_row(db, "ai-due") == {"status": "pending", "owner": None, "due": "2026-09-30"}

    _brief(db)
    changed = _pipeline_changed(db)
    assert [text for text in changed if "completed" in text.lower()] == [], changed
    assert sorted(changed) == sorted([
        "Follow-up delegated: Task ai-delegate",
        "Follow-up reopened: Task ai-reopen",
        "Follow-up date set: Task ai-due",
    ]), changed


def test_done_says_completed_and_a_replay_says_nothing(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    already = _action(db, "ai-already", status="done")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    service.complete(OWNER, _action(db, "ai-done"), "done")
    replay = service.complete(OWNER, already, "done")
    assert replay.get("replayed") is True
    assert _action_row(db, "ai-done")["status"] == "done"

    _brief(db)
    assert _pipeline_changed(db) == ["Follow-up completed: Task ai-done"]


def test_dismiss_and_snooze_make_no_line(tmp_path, monkeypatch):
    """No table row names these actions: the brief says nothing rather than
    a word the record does not prove."""
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    service.complete(OWNER, _action(db, "ai-dismiss"), "dismiss")
    service.complete(
        OWNER, _action(db, "ai-snooze"), "snooze", {"until": "2026-09-30"}
    )
    assert _action_row(db, "ai-dismiss")["status"] == "dismissed"
    _brief(db)
    assert _pipeline_changed(db) == []


def test_a_failed_follow_up_is_told_once_in_broke(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    service = FollowThroughService(db, observer=SQLiteObserver(db._connection))
    with pytest.raises(ValueError):
        service.complete(OWNER, "ai-absent", "done")
    sections = _brief(db)
    assert _pipeline_changed(db) == []
    assert sections["broke"] == ["Follow-up did not complete"], sections["broke"]


# ── finding 4: a cached brief, a reconciliation, an unknown call ────────────


def test_a_cached_brief_is_not_a_made_brief(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    observed = MondayBriefService(db, observer=SQLiteObserver(db._connection))
    # The day before: the two observed calls land (clock EVENTS_AT) inside the
    # NEXT day's lookback, the brief that reads them.
    thursday = GENERATED - datetime.timedelta(days=1)
    first = observed.generate(OWNER, now=thursday)
    cached = observed.generate(OWNER, now=thursday)
    assert cached.id == first.id  # the second call made nothing
    assert [e["method"] for e in _events(db)].count("generate") == 2
    texts = [t for items in _brief(db).values() for t in items]
    assert [t for t in texts if t.startswith("Brief made")] == [], texts


def test_a_reconciliation_that_changed_nothing_makes_no_line(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    observer = SQLiteObserver(db._connection)
    assert ProjectService(db, observer=observer).recover_ask_tasks_on_startup() == []
    flipped, recovered = GateService(db, observer=observer).invalidate_held_on_startup()
    assert (flipped, recovered) == ([], 0)
    assert {e["method"] for e in _events(db)} == {
        "recover_ask_tasks_on_startup", "invalidate_held_on_startup",
    }
    sections = _brief(db)
    assert _pipeline_changed(db) == [], sections["changed"]
    assert sections["broke"] == []


def test_an_unknown_success_writes_nothing_and_its_failure_names_the_object(
    tmp_path, monkeypatch
):
    """A lifecycle transition is outside the table: its success is omitted, its
    failure is ``<Object> did not complete`` (the service's object)."""
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService

    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    with pytest.raises(Exception):  # noqa: B017 - NotFound is the producer fact
        DecisionLifecycleService(
            db, observer=SQLiteObserver(db._connection)
        ).transition(OWNER, "philo603-absent", "accept")
    sections = _brief(db)
    assert _pipeline_changed(db) == []
    assert sections["broke"] == ["Decision did not complete"], sections["broke"]


# ── the coverage: every row that can write a Changed line, run for real ─────


def _run_desk_record(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    decision_id = _desk_decision(db)
    DecisionRecordService(db, observer=SQLiteObserver(db._connection)).create_from_desk(
        OWNER, decision_id
    )
    return f"Decision recorded: {TITLE}", lambda: _count(
        db, "SELECT COUNT(*) FROM decision_records WHERE source_id = ?", decision_id
    ) == 1


def _run_meeting_record(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    from tests.unit.test_decision_record_service import _accepted_meeting_decision

    _accepted_meeting_decision(db, "philo603-meeting")
    DecisionRecordService(db, observer=SQLiteObserver(db._connection)).create_from_meeting(
        OWNER, "philo603-meeting"
    )
    return "Decision recorded", lambda: _count(
        db, "SELECT COUNT(*) FROM decision_records WHERE source_id = ?", "philo603-meeting"
    ) == 1


def _run_plain_record(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    record = DecisionRecordService(db, observer=SQLiteObserver(db._connection)).create(
        OWNER, decision_text="Keep retrieval local.", source_type="desk",
        source_id="philo603-direct",
    )
    return "Decision recorded", lambda: _count(
        db, "SELECT COUNT(*) FROM decision_records WHERE id = ?", record["id"]
    ) == 1


def _run_summary_request(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
    from holdspeak.services.meeting_intel_service import MeetingIntelService
    from holdspeak.services.meeting_route_projection import project_route
    from tests.unit.test_meeting_deferred_admission import _queue_rig

    (tmp_path / "rig").mkdir()
    rig_db, *_ = _queue_rig(tmp_path / "rig", monkeypatch)
    meeting = MeetingState(
        id="m-queue",
        started_at=datetime.datetime(2026, 9, 25, 5, 0),
        ended_at=datetime.datetime(2026, 9, 25, 5, 30),
        title="Architecture review",
        tags=[],
        segments=[
            TranscriptSegment(text="we keep retrieval local", speaker="Me",
                              start_time=0.0, end_time=4.0)
        ],
    )
    rig_db.meetings.save_meeting(meeting)
    route = project_route(rig_db, invocation_id=f"meeting:{meeting.id}")
    admitted = MeetingIntelService(
        rig_db, observer=SQLiteObserver(rig_db._connection)
    ).run_intelligence(OWNER, meeting.id, expected_selection_hash=route["selection_hash"])
    assert admitted["state"] == "queued"
    return "Summary requested: Architecture review", (
        lambda: rig_db.intel.get_intel_job(meeting.id) is not None
    ), rig_db


def _follow_up(verb: str, payload: dict[str, Any] | None, status: str,
               line: str, proof: dict[str, Any]):
    def run(db: Database, tmp_path, monkeypatch) -> tuple[str, Any]:
        card = _action(db, f"ai-{verb}", status=status)
        FollowThroughService(db, observer=SQLiteObserver(db._connection)).complete(
            OWNER, card, verb, payload
        )
        return f"{line}: Task {card}", lambda: all(
            _action_row(db, card)[key] == value for key, value in proof.items()
        )

    return run


def _count(db: Database, sql: str, *args: Any) -> int:
    with db._connection() as conn:
        return int(conn.execute(sql, args).fetchone()[0])


# (service, method, discriminator) -> the producer that runs it for real.
PRODUCERS = {
    ("DecisionRecordService", "create_from_desk", None): _run_desk_record,
    ("DecisionRecordService", "create_from_meeting", None): _run_meeting_record,
    ("DecisionRecordService", "create", None): _run_plain_record,
    ("MeetingIntelService", "run_intelligence", None): _run_summary_request,
    ("FollowThroughService", "complete", "done"): _follow_up(
        "done", None, "pending", "Follow-up completed", {"status": "done"}),
    ("FollowThroughService", "complete", "delegate"): _follow_up(
        "delegate", {"to": "Ana"}, "pending", "Follow-up delegated", {"owner": "Ana"}),
    ("FollowThroughService", "complete", "reopen"): _follow_up(
        "reopen", None, "done", "Follow-up reopened", {"status": "open"}),
    ("FollowThroughService", "complete", "due"): _follow_up(
        "due", {"due_at": "2026-09-30"}, "pending", "Follow-up date set",
        {"due": "2026-09-30"}),
}


def test_every_changed_row_has_a_real_producer():
    from holdspeak.services.monday_brief_service import changed_line_rows

    assert sorted(changed_line_rows(), key=str) == sorted(PRODUCERS, key=str)


@pytest.mark.parametrize("row", sorted(PRODUCERS, key=str), ids=str)
def test_each_changed_row_names_a_change_the_db_holds(tmp_path, monkeypatch, row):
    db = Database(tmp_path / "hub.db")
    _advancing_clock(monkeypatch)
    produced = PRODUCERS[row](db, tmp_path, monkeypatch)
    line, proof = produced[0], produced[1]
    if len(produced) == 3:  # the summary rig keeps its own database
        db = produced[2]
    assert proof(), (row, "the change the line names is not in the DB")
    _brief(db)
    changed = _pipeline_changed(db)
    assert changed == [line], (row, changed)
    assert json.dumps(changed)  # plain strings only
