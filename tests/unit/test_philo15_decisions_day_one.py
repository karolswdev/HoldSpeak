"""PHILO-15 08 -- a meeting yields decisions and confirmable action items on day one.

Bounces B02 (no decision proposal from a summary), B03 (an action item from a
meeting in no Project cannot be confirmed) and the backend half of B13.

The one faked seam is the provider's completion TEXT: the real
``MeetingIntel`` parser reads it (``_analyze_once``), and the real queue, bound
executor, projection, proposal bridge, record chain and NEEDS YOU read do the
rest (the ``reference_lying_test_doubles`` law).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.intel.engine import MeetingIntel as _RealMeetingIntel
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from tests.unit.test_meeting_deferred_admission import OWNER, FakeIntel, _queue_rig

pytestmark = pytest.mark.timeout(120, method="thread")

# The rehearsal fixture (tests/fixtures/philo3_architect_meeting.txt), cut into
# the turns a transcript holds: three decisions, three action items.
SEGMENTS: tuple[tuple[float, float, str], ...] = (
    (0.0, 9.0, "Decision one: use SQLite for the local meeting ledger. Owner: Maya Chen."),
    (9.0, 14.0, "Action: Maya Chen will write the migration plan by Friday."),
    (14.0, 21.0, "Decision two: keep summary retrieval on the local desk after a hub restart."),
    (21.0, 26.0, "Action: Leo Martinez will test restart retrieval on Tuesday."),
    (26.0, 31.0, "Decision three: use a recorded provider reply for isolated rig tests."),
    (31.0, 35.0, "Action: Priya Shah will add the named failure fence before ship."),
)

# What a model returns for the summary prompt (the shape INTEL_SCHEMA asks for).
COMPLETION = json.dumps({
    "topics": ["Local meeting ledger", "Summary retrieval", "Rig tests"],
    "action_items": [
        {"task": "Write the migration plan", "owner": "Maya Chen", "due": "Friday"},
        {"task": "Test restart retrieval", "owner": "Leo Martinez", "due": "Tuesday"},
        {"task": "Add the named failure fence before ship", "owner": "Priya Shah", "due": None},
    ],
    "decisions": [
        {"decision": "Use SQLite for the local meeting ledger", "rationale": None},
        {"decision": "Keep summary retrieval on the local desk after a hub restart",
         "rationale": "It must survive a hub restart"},
        {"decision": "Use a recorded provider reply for isolated rig tests", "rationale": None},
    ],
    "summary": "Three decisions and three action items.",
})


def _parse(text: str) -> Any:
    """The REAL summary parser over a completion text."""
    engine = _RealMeetingIntel.__new__(_RealMeetingIntel)
    engine.temperature = 0.2
    engine.max_tokens = 512
    engine._chat_completion_text = lambda *a, **k: text  # type: ignore[method-assign]
    return _RealMeetingIntel._analyze_once(engine, "transcript")


class ParsedIntel(FakeIntel):
    """The provider's text, read by the real parser."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.result = _parse(text)


def _meeting(db: Database, meeting_id: str) -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 10, 7, 10, 52, 0),
        ended_at=datetime(2026, 10, 7, 10, 52, 35),
        title="philo3_architect_meeting",
        segments=[
            TranscriptSegment(text=text, speaker="Speaker", start_time=start, end_time=end)
            for start, end, text in SEGMENTS
        ],
    )
    db.meetings.save_meeting(state)
    db.intel.enqueue_intel_job(meeting_id, transcript_hash=state.transcript_hash(), reason="import")
    return state


def _run(tmp_path, monkeypatch, meeting_id: str = "m-day-one") -> Database:
    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    engine = ParsedIntel(COMPLETION)
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    _meeting(db, meeting_id)
    from holdspeak.intel_queue import process_next_intel_job

    for _ in range(6):
        if not process_next_intel_job():
            break
    return db


def _proposals(db: Database, meeting_id: str) -> list[dict[str, Any]]:
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    return ProposalBridgeService(db).list_meeting_proposals(meeting_id)


# ── the defaults ─────────────────────────────────────────────────────


def test_the_default_profile_runs_decision_capture() -> None:
    from holdspeak.config import MeetingConfig
    from holdspeak.plugins.router import preview_route_from_transcript

    config = MeetingConfig()
    assert config.intent_router_enabled is True
    assert config.routing_profile == "balanced"
    chain = preview_route_from_transcript(profile=None, transcript="We decided.", tags=None).to_dict()
    assert "decision_capture" in chain["plugin_chain"]


# ── the parser ───────────────────────────────────────────────────────


def test_the_summary_schema_asks_for_decisions() -> None:
    from holdspeak.intel.parsing import INTEL_JSON_SCHEMA, INTEL_SCHEMA, _json_only_messages

    assert "decisions" in INTEL_SCHEMA
    assert "decisions" in INTEL_JSON_SCHEMA["required"]
    prompt = _json_only_messages("t")[1]["content"]
    assert "decisions" in prompt


def test_the_parser_yields_the_decisions() -> None:
    result = _parse(COMPLETION)
    assert [d["decision"] for d in result.decisions] == [
        "Use SQLite for the local meeting ledger",
        "Keep summary retrieval on the local desk after a hub restart",
        "Use a recorded provider reply for isolated rig tests",
    ]
    assert result.decisions[1]["rationale"] == "It must survive a hub restart"
    assert [a.task for a in result.action_items][2] == "Add the named failure fence before ship"


def test_a_reply_without_decisions_reads_as_none() -> None:
    from holdspeak.services.inference_semantic_adapters import normalize_meeting_analysis

    old = {"summary": "s", "topics": [], "action_items": []}
    assert normalize_meeting_analysis(old)["decisions"] == []
    assert _parse(json.dumps(old)).decisions == []


# ── the summary run, end to end ──────────────────────────────────────


def test_a_summary_run_yields_three_decisions_and_three_actions(tmp_path, monkeypatch) -> None:
    db = _run(tmp_path, monkeypatch)
    rows = _proposals(db, "m-day-one")
    decisions = sorted(p["text"] for p in rows if p["kind"] == "decision")
    actions = sorted(p["text"] for p in rows if p["kind"] == "action")
    assert decisions == sorted(d["decision"] for d in json.loads(COMPLETION)["decisions"])
    assert "Add the named failure fence before ship" in actions and len(actions) == 3
    assert {p["source_plugin"] for p in rows} == {"meeting_summary"}
    # Each action stands for the summary's own action row.
    with db._connection() as conn:
        ids = {str(r["id"]) for r in conn.execute(
            "SELECT id FROM action_items WHERE meeting_id='m-day-one'")}
    assert {p["action_item_id"] for p in rows if p["kind"] == "action"} == ids
    # An imported meeting has moments: an anchored action gets its moment.
    with db._connection() as conn:
        stamped = conn.execute(
            "SELECT source_timestamp FROM action_items WHERE task LIKE 'Add the named%'"
        ).fetchone()
    assert stamped["source_timestamp"] is not None


def test_the_review_says_what_each_extractor_did(tmp_path, monkeypatch) -> None:
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = _run(tmp_path, monkeypatch)
    review = ProposalBridgeService(db).meeting_review("m-day-one")
    assert review["extractors"][0] == {
        "id": "meeting_summary", "label": "Summary", "state": "ran", "count": 6, "reason": None,
    }
    assert all(row["state"] in {"ran", "skipped", "failed"} for row in review["extractors"])


def test_confirm_accepts_the_summary_row_and_decline_dismisses_it(tmp_path, monkeypatch) -> None:
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = _run(tmp_path, monkeypatch)
    service = ProposalBridgeService(db)
    rows = _proposals(db, "m-day-one")
    priya = next(p for p in rows if p["text"].startswith("Add the named"))
    leo = next(p for p in rows if p["text"].startswith("Test restart"))
    decision = next(p for p in rows if p["kind"] == "decision")

    with db._connection() as conn:
        before = conn.execute("SELECT COUNT(*) FROM action_items").fetchone()[0]
    result = service.confirm_proposal(OWNER, priya["id"])
    assert result["state"] == "confirmed"
    assert result["action_item_id"] == priya["action_item_id"]
    with db._connection() as conn:
        after = conn.execute("SELECT COUNT(*) FROM action_items").fetchone()[0]
        row = conn.execute(
            "SELECT review_state, status FROM action_items WHERE id=?", (priya["action_item_id"],)
        ).fetchone()
    assert after == before  # one obligation, one row
    assert (row["review_state"], row["status"]) == ("accepted", "open")

    assert service.confirm_proposal(OWNER, decision["id"])["decision_record_id"]
    assert service.dismiss_proposal(OWNER, leo["id"])["state"] == "dismissed"
    with db._connection() as conn:
        status = conn.execute(
            "SELECT status FROM action_items WHERE id=?", (leo["action_item_id"],)
        ).fetchone()["status"]
    assert status == "dismissed"


# ── NEEDS YOU: a meeting in no Project ───────────────────────────────


def test_an_unfiled_meeting_proposal_is_a_needs_row_until_deferred(tmp_path, monkeypatch) -> None:
    from holdspeak.services.needs_you_membership import compute_needs_you
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = _run(tmp_path, monkeypatch)
    service = ProjectService(db)
    rows = service.proposal_needs(project_id=None)
    assert len(rows) == 6
    priya = next(r for r in rows if r["title"].startswith("Add the named"))
    assert priya["meeting_id"] == "m-day-one" and priya["action_item_id"]

    # The aggregate carries them with the Room row shape; the To review card
    # of the same action is covered by its proposal row.
    from holdspeak.services.needs_you_aggregate import LastKnownStore, build_aggregate

    aggregate = build_aggregate(
        list_projects=lambda *a, **k: [], room=lambda *a, **k: {}, principal=OWNER,
        last_known=LastKnownStore(), unfiled_proposals=lambda: rows,
    )
    items = aggregate["items"]
    assert {i["proposalId"] for i in items} == {r["proposal_id"] for r in rows}
    card = {"id": priya["action_item_id"], "title": priya["title"], "owner": "Priya Shah"}
    result = compute_needs_you(door={"unassigned": [card]}, room_items=items, now=datetime(2026, 10, 7, 12))
    titles = [i["title"] for i in result["unmutedItems"]]
    assert titles.count(priya["title"]) == 1

    deferred = ProposalBridgeService(db).defer_proposal(OWNER, priya["proposal_id"])
    assert deferred["deferred_until"]
    assert priya["proposal_id"] not in {r["proposal_id"] for r in service.proposal_needs(project_id=None)}
    # A stamp in the past no longer hides it.
    past = (datetime.now().astimezone() - timedelta(minutes=1)).isoformat()
    ProposalBridgeService(db).defer_proposal(OWNER, priya["proposal_id"], until=past)
    assert priya["proposal_id"] in {r["proposal_id"] for r in service.proposal_needs(project_id=None)}
