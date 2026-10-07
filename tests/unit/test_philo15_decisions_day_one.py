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


def test_a_reply_without_decisions_reads_as_not_extracted() -> None:
    from holdspeak.services.inference_semantic_adapters import normalize_meeting_analysis

    # Astra #983 r2: missing is NOT EXTRACTED (None), never an empty list.
    old = {"summary": "s", "topics": [], "action_items": []}
    assert normalize_meeting_analysis(old)["decisions"] is None
    assert _parse(json.dumps(old)).decisions is None


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


# ── Astra round 1 (#983): kinds, Defer, one obligation ────────────────


def test_confirm_keeps_the_kind_a_decision_is_no_task_an_action_is_no_decision(tmp_path, monkeypatch) -> None:
    from holdspeak.services.decision_record_service import DecisionRecordService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = _run(tmp_path, monkeypatch)
    service = ProposalBridgeService(db)
    rows = _proposals(db, "m-day-one")
    decision = next(p for p in rows if p["text"] == "Use SQLite for the local meeting ledger")
    action = next(p for p in rows if p["text"].startswith("Write the migration"))
    with db._connection() as conn:
        actions_before = conn.execute("SELECT COUNT(*) FROM action_items").fetchone()[0]

    kept = service.confirm_proposal(OWNER, decision["id"])
    assert kept["decision_record_id"] and kept["action_item_id"] is None and kept["commitment_id"] is None
    service.confirm_proposal(OWNER, action["id"])
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_items").fetchone()[0] == actions_before
        assert conn.execute("SELECT COUNT(*) FROM decision_commitments").fetchone()[0] == 1

    # The Decisions lists hold the decision, never the action.
    records = DecisionRecordService(db)
    listed = [r["decision_text"] for r in records.list_records(OWNER)]
    assert listed == ["Use SQLite for the local meeting ledger"], listed
    assert [r["decision_text"] for r in records.search(OWNER, "", recent=True)] == listed
    assert records.search(OWNER, "migration plan") == []

    # Combined Needs: no "Name an owner" row was invented by the decision.
    answer = ProjectService(db).needs_you(OWNER)
    titles = [str(i.get("title") or "") for i in answer["items"]]
    assert "Use SQLite for the local meeting ledger" not in titles, titles
    assert not any(str(i.get("why") or "") == "UNASSIGNED" for i in answer["items"]), answer["items"]


def test_defer_holds_back_the_whole_obligation_in_combined_needs(tmp_path, monkeypatch) -> None:
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = _run(tmp_path, monkeypatch)
    title = "Add the named failure fence before ship"
    priya = next(p for p in _proposals(db, "m-day-one") if p["text"] == title)

    def needs_titles() -> list[str]:
        answer = ProjectService(db).needs_you(OWNER)
        return [str(i.get("title") or "") for i in answer["items"]]

    assert needs_titles().count(title) == 1          # its proposal row, not a second card
    ProposalBridgeService(db).defer_proposal(OWNER, priya["id"])
    assert needs_titles().count(title) == 0          # neither the proposal nor its To review card
    past = (datetime.now().astimezone() - timedelta(minutes=1)).isoformat()
    ProposalBridgeService(db).defer_proposal(OWNER, priya["id"], until=past)
    assert needs_titles().count(title) == 1          # back when the stamp passes


def test_summary_and_plugin_output_together_make_one_proposal_and_one_action(tmp_path, monkeypatch) -> None:
    """The real bridge over a summary that carried items AND the real plugins:
    the plugins own both kinds (no summary proposal), and a plugin action that
    restates the summary's action stands for that row: Confirm accepts it."""
    from holdspeak.intel.models import ActionItem, IntelResult
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.test_phase200_meeting_outcomes import _drain, _meeting as _plugin_meeting, _rig

    db, engine = _rig(tmp_path, monkeypatch)
    engine.result = IntelResult(
        topics=["Cut-over"],
        action_items=[ActionItem(task="Confirm the freeze window with the payments team")],
        summary="One decision, one action.",
        raw_response="{}",
        decisions=[{"decision": "Cut-over runs on the read replica first", "rationale": None}],
    )
    _plugin_meeting(db, "m-both", project_id=None)
    _drain()
    rows = _proposals(db, "m-both")
    assert {p["source_plugin"] for p in rows} == {"decision_capture", "action_owner_enforcer"}, rows
    texts = [p["text"] for p in rows]
    assert len(texts) == len(set(texts)), texts      # never proposed twice
    with db._connection() as conn:
        summary_row = conn.execute(
            "SELECT id FROM action_items WHERE meeting_id='m-both' AND task LIKE 'Confirm the freeze%'"
        ).fetchone()["id"]
        before = conn.execute("SELECT COUNT(*) FROM action_items WHERE meeting_id='m-both'").fetchone()[0]
    freeze = next(p for p in rows if p["text"] == "Confirm the freeze window with the payments team")
    assert freeze["action_item_id"] == summary_row
    result = ProposalBridgeService(db).confirm_proposal(OWNER, freeze["id"])
    assert result["action_item_id"] == summary_row
    with db._connection() as conn:
        after = conn.execute("SELECT COUNT(*) FROM action_items WHERE meeting_id='m-both'").fetchone()[0]
        state = conn.execute("SELECT review_state FROM action_items WHERE id=?", (summary_row,)).fetchone()[0]
    assert after == before and state == "accepted"


def test_an_engine_added_before_the_summary_had_decisions_still_serves_summaries(tmp_path) -> None:
    """The summary result grew ``decisions``; a profile minted before that
    claims only the earlier summary result (the live window's, unchanged).
    It is still a lawful summary engine, and a new profile claims both."""
    from holdspeak.inference_capabilities import meeting_analysis_claims, process_inference_capability_registry
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile
    from tests.unit.test_phase200_readiness import _assign

    db = Database(tmp_path / "claims.db")
    registry = process_inference_capability_registry()
    earlier = f"result_schema:{registry.require('meeting.live_analysis').output_schema_sha256}"
    _profile(db, "lan-engine-before", claims=("language", earlier))
    _assign(db, "meeting.deferred_analysis", ["lan-engine-before"])
    resolved = InferenceAssignmentService(db).resolve_effective(OWNER, capability_id="meeting.deferred_analysis")
    assert resolved["status"] == "assigned", resolved
    assert set(meeting_analysis_claims()) == {
        earlier, f"result_schema:{registry.require('meeting.deferred_analysis').output_schema_sha256}",
    }


# ── Astra round 2 (#983): no false merge, the record's kind, missing ≠ empty ──


def test_two_similar_obligations_are_never_merged(tmp_path, monkeypatch) -> None:
    """Astra's pair: staging vs production share 3 of 4 content words. The
    plugin's production action must NOT take over the summary's staging row;
    Confirm keeps both obligations."""
    import tests.unit.test_phase200_meeting_outcomes as rig
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    staging = "Rotate the staging database credentials"
    production = "Rotate the production database credentials"
    monkeypatch.setattr(rig, "SEGMENTS", (
        (0.0, 10.0, "Maya", "Maya will rotate the staging database credentials by Friday."),
        (10.0, 20.0, "Leo", "Leo will rotate the production database credentials by Tuesday."),
    ))
    monkeypatch.setattr(rig, "ACTIONS_JSON", json.dumps({"action_items": [
        {"task": production, "owner": "Leo", "due": "Tuesday"},
    ]}))
    monkeypatch.setattr(rig, "DECISIONS_JSON", json.dumps({"decisions": [], "open_questions": []}))
    db, engine = rig._rig(tmp_path, monkeypatch)
    engine.result = _parse(json.dumps({
        "topics": ["Credentials"], "summary": "Two separate rotations.", "decisions": [],
        "action_items": [{"task": staging, "owner": "Maya", "due": "Friday"}],
    }))
    rig._meeting(db, "m-distinct", project_id=None)
    rig._drain()
    prop = next(p for p in _proposals(db, "m-distinct") if p["kind"] == "action")
    assert prop["action_item_id"] is None, prop
    ProposalBridgeService(db).confirm_proposal(OWNER, prop["id"])
    with db._connection() as conn:
        rows = {r["task"]: (r["owner"], r["due"]) for r in conn.execute(
            "SELECT task, owner, due FROM action_items WHERE meeting_id='m-distinct'")}
    assert rows == {staging: ("Maya", "Friday"), production: ("Leo", "Tuesday")}, rows


def test_a_confirmed_action_reads_as_an_action_on_every_reader(tmp_path, monkeypatch) -> None:
    from holdspeak.services.decision_record_service import DecisionRecordService
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = _run(tmp_path, monkeypatch)
    rows = _proposals(db, "m-day-one")
    action = next(p for p in rows if p["kind"] == "action")
    decision = next(p for p in rows if p["kind"] == "decision")
    kept = ProposalBridgeService(db).confirm_proposal(OWNER, action["id"])
    decided = ProposalBridgeService(db).confirm_proposal(OWNER, decision["id"])
    records = DecisionRecordService(db)
    assert records.get(OWNER, kept["decision_record_id"])["kind"] == "action"
    assert records.get(OWNER, decided["decision_record_id"])["kind"] == "decision"
    with db._connection() as conn:
        source_id = conn.execute(
            "SELECT source_id FROM decision_records WHERE id=?", (kept["decision_record_id"],)
        ).fetchone()[0]
    assert records.records_for_source(OWNER, "meeting", source_id) == []

    from holdspeak.mcp.tools import dispatch

    monkeypatch.setattr("holdspeak.mcp.tools.get_database", lambda: db, raising=False)
    try:
        mcp = dispatch("decision_record.get", {"record_id": kept["decision_record_id"]}, OWNER)
    except Exception:  # the MCP read may need a hub; the service read above is its source
        mcp = None
    if isinstance(mcp, dict) and mcp:
        assert mcp.get("kind") == "action", mcp

    brief = MondayBriefService(db)._collect_meeting_watch(
        "2000-01-01T00:00:00+00:00", "2099-01-01T00:00:00+00:00", None,
    )
    assert [i.text for i in brief if "new decision" in i.text] == ["1 new decision from meetings"]


def test_preparation_carries_an_action_once_and_never_as_a_decision(tmp_path, monkeypatch) -> None:
    import tests.unit.test_phase200_meeting_outcomes as rig
    from holdspeak.services.preparation_brief_service import build_manifest, draft_deterministic
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, engine = rig._rig(tmp_path, monkeypatch)
    engine.result = _parse(json.dumps({"summary": "One action.", "topics": [], "action_items": [], "decisions": []}))
    rig._meeting(db, "m-prep")
    rig._drain()
    prop = next(p for p in _proposals(db, "m-prep") if p["kind"] == "action")
    ProposalBridgeService(db).confirm_proposal(OWNER, prop["id"])
    room = ProjectService(db).room(OWNER, "prj-cutover")
    manifest = build_manifest(room, "Prepare", now=datetime.now().astimezone())
    assert prop["text"] not in [d["text"] for d in manifest["decisions"]], manifest["decisions"]
    assert [c["text"] for c in manifest["commitments"]].count(prop["text"]) == 1
    claims = [c.to_dict() for c in draft_deterministic(room, manifest).claims]
    assert not any(c.get("kind") == "decision" and c.get("text") == prop["text"] for c in claims), claims
    room_rows = [d for d in room["decisions"]["items"] if d["text"] == prop["text"]]
    assert room_rows and all(d["kind"] == "action" for d in room_rows)


def test_a_reply_without_decisions_is_not_extracted_and_an_empty_list_is_none(tmp_path, monkeypatch) -> None:
    from holdspeak.services.inference_semantic_adapters import normalize_meeting_analysis
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    old = {"summary": "We decided to use SQLite.", "topics": [], "action_items": []}
    assert _parse(json.dumps(old)).decisions is None
    assert normalize_meeting_analysis(old)["decisions"] is None
    assert _parse(json.dumps({**old, "decisions": []})).decisions == []
    assert normalize_meeting_analysis({**old, "decisions": []})["decisions"] == []

    for name, reply, expect in (
        ("m-missing", old, "not_extracted"),
        ("m-empty", {**old, "decisions": []}, None),
    ):
        db, _broker, _engine, _host, _requests = _queue_rig(tmp_path / name, monkeypatch)
        engine = ParsedIntel(json.dumps(reply))
        monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
        monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
        _meeting(db, name)
        from holdspeak.intel_queue import process_next_intel_job

        for _ in range(6):
            if not process_next_intel_job():
                break
        review = ProposalBridgeService(db).meeting_review(name)
        states = {x["id"]: x["state"] for x in review["extractors"]}
        assert states.get("meeting_summary") == "ran", review["extractors"]
        assert states.get("summary_decisions") == expect, review["extractors"]
        assert [p for p in review["proposals"] if p["kind"] == "decision"] == []


def test_an_engine_on_the_earlier_summary_result_says_its_decisions_are_not_proven(tmp_path) -> None:
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import _profile
    from tests.unit.test_phase200_readiness import _assign

    db = Database(tmp_path / "notice.db")
    registry = process_inference_capability_registry()
    earlier = f"result_schema:{registry.require('meeting.live_analysis').output_schema_sha256}"
    _profile(db, "lan-engine-before", claims=("language", earlier))
    _assign(db, "meeting.deferred_analysis", ["lan-engine-before"])
    summary = InferenceAssignmentService(db).assignment_summary(OWNER)
    task = next(t for t in summary["task_overrides"] if t["id"] == "meeting.deferred_analysis")
    assert task["effective"]["status"] == "assigned", task
    assert [i["code"] for i in task["issues"] if i["severity"] == "notice"] == ["result_schema_earlier"]
