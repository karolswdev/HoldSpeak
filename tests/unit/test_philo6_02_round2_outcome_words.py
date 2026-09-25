"""PHILO-6-02 round 2 — the brief's words follow the recorded OUTCOME.

Astra's check on built (``pm/roadmap/holdspeak-philo/phase-6-the-honest-morning/
checks/lane-a-built-astra.md``):

* finding 1 — a FAILED ``DecisionRecordService.create_from_desk`` (a missing
  decision) stored BOTH ``Decision recorded`` and ``Decision did not record``
  while the DB held zero decision records. A failed operation changed nothing:
  it makes no Changed row; its one line is the Broke row.
* finding 5 — the generic fallback exposed implementation vocabulary: a real
  missing-decision read stored ``Primitive: get decision did not complete``.

Every producer below is REAL and observed by the REAL ``@observe_service`` +
``SQLiteObserver``; the brief comes from the REAL brief routes. The latest
brief is written to the vitest fixture
(``web/src/desk/chair/__tests__/fixtures/philo6/brief-failed-ops.json``) with
``PHILO6_WRITE_FIXTURE=1`` BEFORE the asserts, so the rendered link
(``briefOutcome.philo602r2.test.tsx``) reads what this producer stored.
"""
from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import holdspeak.services.observer as observer_module
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.meeting_intel_service import MeetingIntelService
from holdspeak.services.meeting_route_projection import project_route
from holdspeak.services.primitive_service import PrimitiveService
from holdspeak.services.sqlite_observer import SQLiteObserver

from tests.unit.test_philo6_02_brief_truth import EVENTS_AT, OWNER, RAW, _hub, _stable

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "web/src/desk/chair/__tests__/fixtures/philo6/brief-failed-ops.json"
MISSING = "philo602-deliberately-absent"
MEETING_TITLE = "Architecture review"
# Success words the collector can write; none may come from a failed call.
SUCCESS_WORDS = (
    "Decision recorded",
    "Summary requested",
    "Brief triage saved",
    "Decision changed",
    "Decision loaded",
)
FAILURE_WORDS = (
    "Decision did not record",
    "Summary did not start",
    "Brief triage did not save",
    "Decision did not change",
    "Decision did not load",
)
IMPLEMENTATION_WORDS = re.compile(r"Primitive|Service|Lifecycle|[a-z]_[a-z]")


def _clock(monkeypatch) -> dict[str, float]:
    now = {"t": EVENTS_AT.timestamp()}
    monkeypatch.setattr(observer_module, "time", SimpleNamespace(time=lambda: now["t"]))
    return now


def _seed_failures(db: Database, client, monkeypatch) -> None:
    """Five real observed calls, each one FAILS; nothing is changed."""
    now = _clock(monkeypatch)
    observer = SQLiteObserver(db._connection)
    # finding 1: the real create_from_desk on a missing decision.
    with pytest.raises(KeyError):
        DecisionRecordService(db, observer=observer).create_from_desk(OWNER, MISSING)
    # the summary request, refused (no engine is assigned).
    now["t"] += 60
    meeting = MeetingState(
        id="m-arch",
        started_at=datetime.datetime(2026, 9, 25, 5, 0),
        ended_at=datetime.datetime(2026, 9, 25, 5, 30),
        title=MEETING_TITLE,
        tags=[],
        segments=[
            TranscriptSegment(text="we keep retrieval local", speaker="Me",
                              start_time=0.0, end_time=4.0)
        ],
    )
    db.meetings.save_meeting(meeting)
    route = project_route(db, invocation_id=f"meeting:{meeting.id}")
    with pytest.raises(Exception):  # noqa: B017 - the refusal is the producer fact
        MeetingIntelService(db, observer=observer).run_intelligence(
            OWNER, meeting.id, expected_selection_hash=route["selection_hash"]
        )
    # the brief triage on an unknown item (the PHILO-4-03 producer).
    now["t"] += 60
    assert client.post(
        "/api/brief/items/brief-item-missing/shelf", json={"state": "acknowledged"}
    ).status_code == 404
    # the generic line: a lifecycle transition on the missing decision.
    now["t"] += 60
    with pytest.raises(Exception):  # noqa: B017 - NotFound is the producer fact
        DecisionLifecycleService(db, observer=observer).transition(OWNER, MISSING, "accept")
    # finding 5: the desk decision read of the missing decision.
    now["t"] += 60
    with pytest.raises(Exception):  # noqa: B017 - NotFound is the producer fact
        PrimitiveService(db, observer=observer).get_decision(OWNER, MISSING)


def test_failed_operations_make_no_success_line(tmp_path, monkeypatch):
    db = Database(tmp_path / "hub.db")
    client = _hub(db, monkeypatch, tmp_path)
    _seed_failures(db, client, monkeypatch)
    with db._connection() as conn:
        errors = [
            (r["service"], r["method"])
            for r in conn.execute(
                "SELECT service, method FROM pipeline_events WHERE error IS NOT NULL"
            )
        ]
        records = conn.execute("SELECT COUNT(*) FROM decision_records").fetchone()[0]
    assert ("DecisionRecordService", "create_from_desk") in errors, errors
    assert ("PrimitiveService", "get_decision") in errors, errors
    assert records == 0

    generated = client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text
    latest = client.get("/api/brief/latest")
    assert latest.status_code == 200
    payload = _stable(latest.json())
    if os.environ.get("PHILO6_WRITE_FIXTURE") == "1":
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")

    with db._connection() as conn:
        stored = [
            (str(r["section"]), str(r["text"]), str(r["source_ref"] or ""))
            for r in conn.execute("SELECT section, text, source_ref FROM monday_brief_items")
        ]
    texts = [text for _section, text, _ref in stored]
    changed = [text for section, text, _ref in stored if section == "changed"]
    broke = [text for section, text, _ref in stored if section == "broke"]
    # A failed operation never yields a success line.
    assert [t for t in texts if t.startswith(SUCCESS_WORDS)] == [], stored
    # No Changed row comes from a pipeline receipt: every call failed.
    assert [
        (text, ref) for section, text, ref in stored
        if section == "changed" and ref.startswith("pipeline")
    ] == [], changed
    # The failure is told once, in Broke, in product words.
    for words in FAILURE_WORDS:
        assert any(t.startswith(words) for t in broke), (words, broke)
    # No implementation vocabulary reaches a stored item (finding 5).
    assert [t for t in texts if IMPLEMENTATION_WORDS.search(t) or RAW.search(t)] == [], texts

    recorded = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert recorded == payload, (
        "the vitest fixture drifted from the real producer; "
        "re-run with PHILO6_WRITE_FIXTURE=1"
    )


def test_a_successful_record_keeps_its_success_line(tmp_path, monkeypatch):
    """The positive control: the fence above is not vacuous."""
    db = Database(tmp_path / "hub.db")
    client = _hub(db, monkeypatch, tmp_path)
    _clock(monkeypatch)
    db.desk_decisions.upsert(
        decision_id="philo602-present",
        title="Keep retrieval local",
        status="accepted",
        decision_markdown="Keep retrieval local.",
    )
    record = DecisionRecordService(
        db, observer=SQLiteObserver(db._connection)
    ).create_from_desk(OWNER, "philo602-present")
    assert record["id"]
    generated = client.post("/api/brief/generate")
    assert generated.status_code == 200, generated.text
    changed = [i["text"] for i in generated.json()["sections"]["changed"]]
    assert "Decision recorded: Keep retrieval local" in changed, changed
    assert not any("did not" in text for text in changed), changed


# The observed producers of every retained Phase 5 and Phase 6 run
# (`pm/roadmap/holdspeak-philo/phase-5-*/assets/**/*.sqlite`,
# `phase-6-*/assets/**/*.sqlite`, `SELECT DISTINCT service, method FROM
# pipeline_events`, 2026-09-25).
OBSERVED = (
    ("AskService", "list_models"), ("AuthorityService", "get_policy"),
    ("DecisionLifecycleService", "get_decision"), ("DecisionRecordService", "create"),
    ("DecisionRecordService", "create_from_desk"),
    ("DecisionRecordService", "due_for_review"), ("DecisionRecordService", "get"),
    ("DeliveryService", "attempt_service"), ("DeliveryService", "launch_service"),
    ("DeliveryService", "launch_sweep"), ("DeskService", "health"),
    ("DeskService", "seed"), ("FollowThroughService", "board"),
    ("FollowThroughService", "people_store_state"),
    ("GateService", "invalidate_held_on_startup"),
    ("MeetingAftercareService", "get_aftercare"),
    ("MeetingAftercareService", "list_proposals"),
    ("MeetingIntelService", "get_recovery"), ("MeetingIntelService", "list_jobs"),
    ("MeetingIntelService", "run_intelligence"),
    ("MondayBriefService", "compute_lookahead"), ("MondayBriefService", "compute_window"),
    ("MondayBriefService", "generate"), ("MondayBriefService", "get_latest"),
    ("PluginJobService", "list"), ("PrimitiveService", "create_decision"),
    ("PrimitiveService", "get_decision"), ("PrimitiveService", "get_note"),
    ("PrimitiveService", "list_chains"), ("PrimitiveService", "list_decisions"),
    ("PrimitiveService", "list_directories"), ("PrimitiveService", "list_kbs"),
    ("PrimitiveService", "list_notes"), ("PrimitiveService", "list_workflows"),
    ("ProfileService", "list_inference_targets"), ("ProjectService", "list_projects"),
    ("ProjectService", "list_resource_relationships"),
    ("ProjectService", "recover_ask_tasks_on_startup"), ("ProjectionService", "list"),
    ("ReactionService", "process_pending"), ("ReactionService", "refresh_due_watches"),
    ("RecipeService", "list_recipes"), ("SettingsService", "get_redacted"),
    ("SettingsService", "get_settings"), ("SetupService", "set_onboarding_disposition"),
    ("SetupService", "status"), ("SyncService", "pull"),
    ("WorkbenchService", "list_workbenches"),
)


@pytest.mark.parametrize(("service", "method"), OBSERVED)
def test_every_observed_producer_has_a_human_line(tmp_path, service, method):
    from holdspeak.services.monday_brief_service import MondayBriefService

    brief = MondayBriefService(Database(tmp_path / "hub.db"))
    with brief._db._connection() as conn:
        change = brief._operation_text(conn, service, method, "{}", broke=False)
        broke = brief._operation_text(conn, service, method, "{}", broke=True)
    for line in (change, broke):
        assert not IMPLEMENTATION_WORDS.search(line), line
        assert not RAW.search(line), line
        assert line[:1].isupper(), line
    assert re.fullmatch(r"[A-Z][A-Za-z -]* did not [a-z]+", broke), broke


def test_the_service_objects_name_every_observed_service():
    """``<Object> did not <verb>`` needs a known object: enumerated, never a
    class name. Every ``@observe_service`` class in the package is named."""
    from holdspeak.services.monday_brief_service import _SERVICE_OBJECTS

    decorated: set[str] = set()
    pattern = re.compile(r"^@observe_service\s*\nclass (\w+)", re.MULTILINE)
    for path in (REPO / "holdspeak").rglob("*.py"):
        decorated.update(pattern.findall(path.read_text(encoding="utf-8")))
    assert decorated, "no @observe_service class found"
    assert sorted(decorated - set(_SERVICE_OBJECTS)) == []
