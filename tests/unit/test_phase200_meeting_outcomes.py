"""HS-200-12 -- connect a real meeting to reviewed outcomes.

Planned suite: ``phase200_meeting_outcomes``.

The ``reference_lying_test_doubles`` law governs this file.  The ONLY faked
seam is the provider engine's completion text (``ScriptedIntel``, a
``FakeIntel`` whose ``_chat_completion_text`` returns the JSON a model would
return).  Everything else is production code, end to end: the queue
repository, the bound executor (``intel_queue.process_next_intel_job``), the
REAL plugin host with the REAL ``decision_capture`` and
``action_owner_enforcer`` plugins (``build_bound_meeting_plugin_host``), the
artifact synthesis that writes ``structured_json``, the completion hook
(``_on_intel_complete``), ``ProposalBridgeService``, and the record chain.

What the file proves, per acceptance criterion:

  AC1  one meeting with a transcript -> proposals through the actual
       completion trigger and the actual intelligence services;
  AC2  each confirmed decision/action preserves the meeting, its transcript
       span and the extraction provenance (job, revision, model, host);
  AC3  an unknown owner/due stays typed unknown until supplied;
  AC4  Confirm, Edit and Dismiss call the canonical service and return its
       durable result;
  AC5  a repeated completion, a model retry and a lost acknowledgement mint
       no duplicate proposal and no duplicate decision/commitment -- three
       fences, each of which FAILED on the pre-fix tree (the capture is in
       pm/roadmap/holdspeak/phase-200-the-working-practice/evidence-story-12.md).
"""
from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState, TranscriptSegment
from tests.unit.test_hs172_loop_wire import _link_meeting_project, _seed_project
from tests.unit.test_meeting_deferred_admission import (
    OWNER,
    FakeIntel,
    _queue_rig,
    _rows,
)

pytestmark = pytest.mark.timeout(120, method="thread")

DEC = "decision_capture"
ACT = "action_owner_enforcer"

# The board's meeting (P4Review): six turns, two decisions, three actions.
SEGMENTS: tuple[tuple[float, float, str, str], ...] = (
    (0.0, 120.0, "Karol", "Let's start with the cut-over sequencing for the payments platform."),
    (120.0, 300.0, "Priya", "Cut-over runs on the read replica first, then we flip writes."),
    (300.0, 480.0, "Marek", "I think the freeze window should move to Sunday two in the morning."),
    (480.0, 660.0, "Priya", "I'll confirm the freeze window with the payments team."),
    (660.0, 840.0, "Marek", "Someone needs to write the rollback runbook before we go."),
    (840.0, 1020.0, "Karol", "We should also check the numbers again before Friday."),
)

# What the model returns for each extractor, in the REAL plugins' shapes
# (`decision_capture._SYSTEM_PROMPT`, `action_owner_enforcer._SYSTEM_PROMPT`).
DECISIONS_JSON = json.dumps({
    "decisions": [
        # A verbatim quote of turn 1 at a verified offset -> SUPPORTED.
        {"decision": "Cut-over runs on the read replica first", "rationale": None,
         "source_timestamp": 150.0},
        # A paraphrase of turn 2 at a verified offset -> LINKED.
        {"decision": "Freeze window moves to Sunday 02:00", "rationale": "less traffic",
         "source_timestamp": 400.0},
    ],
    "open_questions": [],
})
ACTIONS_JSON = json.dumps({
    "action_items": [
        # A quote of turn 3, no owner and no due from the model -> SUPPORTED,
        # OWNER UNKNOWN, DUE UNKNOWN.
        {"task": "Confirm the freeze window with the payments team", "owner": None, "due": None},
        # A paraphrase of turn 4 -> LINKED, both unknown.
        {"task": "Draft the rollback runbook", "owner": None, "due": None},
        # Nothing in the transcript says this -> UNSUPPORTED, no span.
        {"task": "Book the war room for the cut-over night", "owner": "Karol", "due": "Friday"},
    ],
})


class ScriptedIntel(FakeIntel):
    """The one fake: the provider's completion text, chosen by the prompt."""

    def __init__(self) -> None:
        super().__init__()
        self.fail_plugins: set[str] = set()
        self.plugin_calls: list[str] = []

    def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
        system = str(messages[0].get("content") or "") if messages else ""
        plugin = DEC if "decisions and open questions" in system else ACT
        self.plugin_calls.append(plugin)
        if plugin in self.fail_plugins:
            raise RuntimeError(f"{plugin}: provider exploded")
        return DECISIONS_JSON if plugin == DEC else ACTIONS_JSON


def _rig(tmp_path, monkeypatch):
    """The deferred-admission rig with the REAL plugin host put back."""
    import holdspeak.meeting_plugins as meeting_plugins

    real_host_builder = meeting_plugins.build_bound_meeting_plugin_host
    db, _broker, _engine, _host, _requests = _queue_rig(
        tmp_path, monkeypatch, plugins=(DEC, ACT), chain=(DEC, ACT),
    )
    engine = ScriptedIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr(meeting_plugins, "build_bound_meeting_plugin_host", real_host_builder)
    return db, engine


def _meeting(db: Database, meeting_id: str, *, project_id: str | None = "prj-cutover") -> MeetingState:
    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 9, 7, 11, 0, 0),
        ended_at=datetime(2026, 9, 7, 11, 47, 0),
        title="Architecture review",
        tags=["architecture"],
        segments=[
            TranscriptSegment(text=text, speaker=speaker, start_time=start, end_time=end)
            for start, end, speaker, text in SEGMENTS
        ],
    )
    db.meetings.save_meeting(state)
    if project_id:
        _seed_project(db, project_id)
        _link_meeting_project(db, meeting_id, project_id)
    db.intel.enqueue_intel_job(
        meeting_id, transcript_hash=state.transcript_hash(), reason="stop handoff",
    )
    return state


def _drain(*, rounds: int = 12, **kwargs: Any) -> int:
    """Turn the REAL executor until it reports no progress."""
    from holdspeak.intel_queue import process_next_intel_job

    made = 0
    for _ in range(rounds):
        if not process_next_intel_job(**kwargs):
            break
        made += 1
    return made


def _latest_job(db: Database, meeting_id: str) -> Any:
    """The meeting's current job in any state (tolerant of the pre-fix tree,
    so a pre-fix run fails on a fence's OWN assertion, not on this read)."""
    reader = getattr(db.intel, "get_latest_intel_job", None)
    if reader is not None:
        return reader(meeting_id)
    rows = [j for j in db.intel.list_intel_jobs(status="all", limit=200) if j.meeting_id == meeting_id]
    rows.sort(key=lambda j: (j.updated_at, j.job_id or ""))
    return rows[-1] if rows else None


def _proposals(db: Database, meeting_id: str) -> list[dict[str, Any]]:
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    rows = ProposalBridgeService(db).list_meeting_proposals(meeting_id)
    return sorted(rows, key=lambda p: (p["created_at"], p["id"]))


def _by_text(rows: list[dict[str, Any]], needle: str) -> dict[str, Any]:
    hits = [p for p in rows if needle.lower() in str(p["text"]).lower()]
    assert len(hits) == 1, (needle, [p["text"] for p in rows])
    return hits[0]


def _count(db: Database, table: str, where: str = "", params: tuple = ()) -> int:
    with db._connection() as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table} {where}", params).fetchone()[0])


# ── AC1: the real chain ───────────────────────────────────────────────


def test_a_real_run_produces_proposals_through_the_drainer_and_the_bridge(tmp_path, monkeypatch):
    db, engine = _rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-outcomes")

    assert _drain() >= 1
    job = _latest_job(db, "m-outcomes")
    assert job is not None and job.status == "succeeded", job
    # The REAL plugins ran on the fake completion text, in chain order.
    assert engine.plugin_calls == [DEC, ACT], engine.plugin_calls
    # The REAL artifacts carry the real extractor's key -- `decision`, the
    # one the HS-172 bridge never read.
    arts = {a.plugin_id: a for a in db.plugins.list_artifacts("m-outcomes")}
    assert set(arts) >= {DEC, ACT}, sorted(arts)
    dec_struct = json.loads(arts[DEC].structured_json) if isinstance(arts[DEC].structured_json, str) else arts[DEC].structured_json
    assert all("decision" in d and "text" not in d for d in dec_struct["decisions"]), dec_struct

    rows = _proposals(db, "m-outcomes")
    assert [p["kind"] for p in rows].count("decision") == 2, rows
    assert [p["kind"] for p in rows].count("action") == 3, rows
    assert all(p["state"] == "proposed" and p["acceptance"] == "unreviewed" for p in rows)
    assert all(p["claim_kind"] == "proposal" for p in rows)

    # Every proposal is stamped with the extraction it came from.
    revision = state.transcript_hash()
    for p in rows:
        assert p["extraction_revision"] == revision, p
        assert p["job_id"] == job.job_id, p
        assert p["job_attempt"] == 1, p
        assert p["project_id"] == "prj-cutover"
        assert p["retry_key"], p

    # The evidence, per the deterministic mapping over the recorded turns.
    cut = _by_text(rows, "read replica")
    assert (cut["span_start"], cut["span_end"], cut["segment_index"]) == (120.0, 300.0, 1)
    assert cut["support"] == "supported" and cut["support_record"]["method"] == "field_mapping"
    assert cut["support_record"]["source_refs"] == ["meeting:m-outcomes#segment:1"]
    freeze = _by_text(rows, "Sunday 02:00")
    assert (freeze["span_start"], freeze["segment_index"]) == (300.0, 2)
    assert freeze["support"] == "source_linked" and freeze["support_record"] is None
    confirm = _by_text(rows, "payments team")
    assert confirm["segment_index"] == 3 and confirm["support"] == "supported"
    runbook = _by_text(rows, "rollback runbook")
    assert runbook["segment_index"] == 4 and runbook["support"] == "source_linked"
    war_room = _by_text(rows, "war room")
    assert war_room["segment_index"] is None and war_room["span_start"] is None
    assert war_room["support"] == "unknown"

    # The projection the face reads: one job, coverage N OF N, the Project.
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    review = ProposalBridgeService(db).meeting_review("m-outcomes")
    assert review["job"]["job_id"] == job.job_id and review["job"]["attempt"] == 1
    assert review["job"]["same_job"] is False
    assert review["coverage"] == {
        "turns": 6, "read": 6, "state": "available",
        "observed_at": review["coverage"]["observed_at"],
    }
    assert review["coverage"]["observed_at"]
    assert review["project"] == {"id": "prj-cutover", "name": "Test Project"}
    assert len(review["proposals"]) == 5


# ── AC2: provenance survives Confirm ──────────────────────────────────


def test_confirm_preserves_meeting_span_and_extraction_provenance(tmp_path, monkeypatch):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-prov")
    _drain()
    job = _latest_job(db, "m-prov")
    rows = _proposals(db, "m-prov")
    cut = _by_text(rows, "read replica")

    result = ProposalBridgeService(db).confirm_proposal(OWNER, cut["id"])
    assert "error" not in result and result["replayed"] is False
    with db._connection() as conn:
        decision = conn.execute("SELECT * FROM decisions WHERE id = ?", (result["decision_id"],)).fetchone()
        assert decision["source_meeting_id"] == "m-prov"
        assert decision["source_timestamp"] == 120.0          # the span, not the point
        assert decision["provenance_label"] == "anchored"
        assert decision["source_artifact_id"] == cut["source_artifact_id"]
        sources = {
            (r["source_type"], r["source_ref"])
            for r in conn.execute(
                "SELECT source_type, source_ref FROM decision_record_sources WHERE record_id = ?",
                (result["decision_record_id"],),
            )
        }
        assert ("meeting", "m-prov") in sources
        assert ("proposal", cut["id"]) in sources
        assert ("transcript", "meeting:m-prov#segment:1") in sources
        action = conn.execute("SELECT * FROM action_items WHERE id = ?", (result["action_item_id"],)).fetchone()
        assert action["meeting_id"] == "m-prov" and action["source_ref"] == "m-prov"
        assert action["source_timestamp"] == 120.0
        receipt = conn.execute(
            "SELECT facts_json FROM service_events WHERE event_type = 'proposal.confirmed' "
            "AND subject_ref = ?", (f"proposal:{cut['id']}",),
        ).fetchone()
    facts = json.loads(receipt["facts_json"])
    prov = facts["provenance"]
    assert prov["meeting_id"] == "m-prov"
    assert (prov["span_start"], prov["span_end"], prov["segment_index"]) == (120.0, 300.0, 1)
    assert prov["extraction_revision"] == job.transcript_hash
    assert prov["job_id"] == job.job_id and prov["job_attempt"] == 1
    assert prov["support"] == "supported"
    # The proposal row itself is the durable provenance record the Room joins on.
    kept = ProposalBridgeService(db).list_meeting_proposals("m-prov", state="confirmed")
    assert [p["id"] for p in kept] == [cut["id"]]
    assert kept[0]["decision_record_id"] == result["decision_record_id"]
    assert kept[0]["acceptance"] == "accepted"


# ── AC3: unknowns stay unknown until supplied ─────────────────────────


def test_an_unknown_owner_or_due_stays_unknown_until_the_owner_supplies_it(tmp_path, monkeypatch):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-unknown")
    _drain()
    svc = ProposalBridgeService(db)
    rows = _proposals(db, "m-unknown")
    confirm = _by_text(rows, "payments team")
    assert [u["type"] for u in confirm["unknowns"]] == ["owner", "due"]
    assert confirm["owner"] is None and confirm["due"] is None
    war_room = _by_text(rows, "war room")
    assert war_room["unknowns"] == []            # the model supplied both
    decisions = [p for p in rows if p["kind"] == "decision"]
    assert all(p["unknowns"] == [] for p in decisions)

    # Confirmed as-is: nothing is invented for the record.
    runbook = _by_text(rows, "rollback runbook")
    result = svc.confirm_proposal(OWNER, runbook["id"])
    with db._connection() as conn:
        record = conn.execute("SELECT owner FROM decision_records WHERE id = ?", (result["decision_record_id"],)).fetchone()
        commitment = conn.execute("SELECT owner, due_at FROM decision_commitments WHERE id = ?", (result["commitment_id"],)).fetchone()
    assert record["owner"] is None
    assert commitment["owner"] is None and commitment["due_at"] is None

    # The owner supplies the owner: that unknown resolves; due stays unknown.
    edited = svc.edit_proposal(OWNER, confirm["id"], owner="Priya")
    assert edited["success"] is True
    assert [u["type"] for u in edited["proposal"]["unknowns"]] == ["due"]
    assert edited["proposal"]["owner"] == "Priya"
    assert edited["proposal"]["owner_hint"] is None       # the extraction original is kept
    assert edited["proposal"]["support"] == "supported"    # a supplied owner is not a text edit
    result = svc.confirm_proposal(OWNER, confirm["id"])
    with db._connection() as conn:
        commitment = conn.execute("SELECT owner, due_at FROM decision_commitments WHERE id = ?", (result["commitment_id"],)).fetchone()
    assert commitment["owner"] == "Priya" and commitment["due_at"] is None


# ── AC4: the three verbs return the durable result ────────────────────


def test_edit_in_place_drops_support_keeps_the_record_and_confirm_returns_the_ids(tmp_path, monkeypatch):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-edit")
    _drain()
    svc = ProposalBridgeService(db)
    cut = _by_text(_proposals(db, "m-edit"), "read replica")
    assert cut["support"] == "supported"

    edited = svc.edit_proposal(OWNER, cut["id"], text="Cut-over runs on the read replica first, writes stay frozen")
    assert edited["success"] is True
    p = edited["proposal"]
    assert p["text"].endswith("writes stay frozen")
    assert p["original_text"] == "Cut-over runs on the read replica first"
    assert p["support"] == "source_linked"                       # C2: an edit cannot keep SUPPORTED
    assert p["support_record"]["method"] == "field_mapping"       # the record is KEPT ...
    assert p["support_record"]["invalidation_reason"] == "text_edited"  # ... and stamped
    assert p["support_record"]["invalidated_at"]
    assert p["text_edited"] is True and p["edited_at"]
    assert (p["span_start"], p["segment_index"]) == (120.0, 1)    # the evidence stays
    # A second edit of the same sentence back is still an edit.
    unchanged = svc.edit_proposal(OWNER, cut["id"], text=p["text"])
    assert unchanged.get("unchanged") is True

    result = svc.confirm_proposal(OWNER, cut["id"])
    assert result["state"] == "confirmed"
    for key in ("decision_id", "decision_record_id", "action_item_id", "commitment_id"):
        assert result[key], key
    with db._connection() as conn:
        record = conn.execute("SELECT decision_text FROM decision_records WHERE id = ?", (result["decision_record_id"],)).fetchone()
        events = [r["event_type"] for r in conn.execute(
            "SELECT event_type FROM service_events WHERE subject_ref = ? ORDER BY rowid", (f"proposal:{cut['id']}",)
        )]
    assert record["decision_text"].endswith("writes stay frozen")
    assert events == ["proposal.edited", "proposal.confirmed"]
    # Edit after confirm is refused: a decided proposal is immutable.
    assert svc.edit_proposal(OWNER, cut["id"], text="x")["code"] == "confirmed"


def test_dismiss_returns_the_durable_state_and_writes_no_record(tmp_path, monkeypatch):
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-dismiss")
    _drain()
    svc = ProposalBridgeService(db)
    war_room = _by_text(_proposals(db, "m-dismiss"), "war room")
    result = svc.dismiss_proposal(OWNER, war_room["id"])
    assert result["state"] == "dismissed" and result["replayed"] is False
    assert result["proposal"]["acceptance"] == "rejected"
    assert _count(db, "decision_records") == 0
    again = svc.dismiss_proposal(OWNER, war_room["id"])
    assert again["state"] == "dismissed" and again["replayed"] is True
    assert svc.confirm_proposal(OWNER, war_room["id"])["code"] == "dismissed"
    assert svc.edit_proposal(OWNER, war_room["id"], text="x")["code"] == "dismissed"


# ── AC5: the three duplicate paths, fenced ────────────────────────────


def test_a_repeated_completion_mints_no_duplicate_proposal(tmp_path, monkeypatch):
    """Fence 1. The completion hook fires again for the same job -- a
    replayed close, a second drainer turn over the same artifacts."""
    from holdspeak.intel_queue import _on_intel_complete
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-repeat")
    _drain()
    job = _latest_job(db, "m-repeat")
    assert _count(db, "follow_through_proposals") == 5

    _on_intel_complete(db, "m-repeat", job)
    assert _count(db, "follow_through_proposals") == 5

    # The sharp edge: the owner has ALREADY confirmed one, then the
    # completion repeats.  Pre-fix the dedup index was partial over
    # 'proposed', so the confirmed proposal came back as a new one.
    cut = _by_text(_proposals(db, "m-repeat"), "read replica")
    ProposalBridgeService(db).confirm_proposal(OWNER, cut["id"])
    _on_intel_complete(db, "m-repeat", job)
    assert _count(db, "follow_through_proposals") == 5, _rows(db, "follow_through_proposals")
    assert _count(db, "follow_through_proposals", "WHERE state = 'proposed'") == 4
    assert _count(db, "decision_records") == 1


def test_a_model_retry_mints_no_duplicate_proposal_or_commitment(tmp_path, monkeypatch):
    """Fence 2. Attempt 1 extracts the decisions and the action extractor's
    provider fails; the job is retried.  The decisions attempt 1 produced
    reach the owner NOW (stamped attempt 1); he keeps one; attempt 2 succeeds
    and mints neither a second copy of the decisions nor a second record."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-retry")
    engine.fail_plugins = {ACT}

    _drain(rounds=3, retry_base_seconds=1, retry_max_seconds=2, retry_max_attempts=3)
    jobs = {r["job_id"]: r for r in _rows(db, "intel_jobs")}
    assert any(r["status"] == "failed" for r in jobs.values()), jobs
    queued = [r for r in jobs.values() if r["status"] == "queued"]
    assert len(queued) == 1 and queued[0]["origin_job_id"], jobs   # the same job's successor
    rows = _proposals(db, "m-retry")
    assert [p["kind"] for p in rows] == ["decision", "decision"], rows
    assert all(p["job_attempt"] == 1 for p in rows)
    review = ProposalBridgeService(db).meeting_review("m-retry")
    assert review["job"]["attempt"] == 2 and review["job"]["same_job"] is True
    assert review["coverage"]["state"] == "queued"

    cut = _by_text(rows, "read replica")
    first = ProposalBridgeService(db).confirm_proposal(OWNER, cut["id"])
    assert first["state"] == "confirmed"

    # Attempt 2: the provider recovers; the successor is due after 1s.
    engine.fail_plugins = set()
    time.sleep(1.3)
    _drain(rounds=6, include_scheduled=True, retry_base_seconds=1, retry_max_seconds=2, retry_max_attempts=3)
    job = _latest_job(db, "m-retry")
    assert job is not None and job.status == "succeeded", _rows(db, "intel_jobs")
    assert job.attempts == 2

    rows = _proposals(db, "m-retry")
    assert len(rows) == 5, [(p["kind"], p["text"], p["state"], p["job_attempt"]) for p in rows]
    assert sorted(p["kind"] for p in rows) == ["action", "action", "action", "decision", "decision"]
    kept = _by_text(rows, "read replica")
    assert kept["id"] == cut["id"] and kept["state"] == "confirmed" and kept["job_attempt"] == 1
    assert _by_text(rows, "Sunday 02:00")["job_attempt"] == 1
    assert all(p["job_attempt"] == 2 for p in rows if p["kind"] == "action")
    assert _count(db, "decision_records") == 1
    assert _count(db, "decision_commitments") == 1


def test_a_lost_acknowledgement_replays_the_same_durable_result(tmp_path, monkeypatch):
    """Fence 3. The browser's POST /confirm succeeded but the response never
    arrived; it retries.  Sequentially and concurrently, the record chain is
    minted once and the retry receives the ids the first call minted."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-ack")
    _drain()
    svc = ProposalBridgeService(db)
    rows = _proposals(db, "m-ack")
    cut = _by_text(rows, "read replica")

    first = svc.confirm_proposal(OWNER, cut["id"])
    retry = svc.confirm_proposal(OWNER, cut["id"])
    assert "error" not in retry, retry
    assert retry["replayed"] is True
    for key in ("decision_id", "decision_record_id", "action_item_id", "commitment_id"):
        assert retry[key] == first[key], key
    assert retry["proposal"]["acceptance"] == "accepted"

    # Two confirms in flight at once (a double click racing a retry).
    freeze = _by_text(rows, "Sunday 02:00")
    results: list[dict[str, Any]] = []
    gate = threading.Barrier(2)

    def go() -> None:
        gate.wait()
        results.append(ProposalBridgeService(db).confirm_proposal(OWNER, freeze["id"]))

    threads = [threading.Thread(target=go) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(10)
    assert len(results) == 2 and all("error" not in r for r in results), results
    assert sorted(r["replayed"] for r in results) == [False, True]
    assert len({r["decision_record_id"] for r in results}) == 1
    assert _count(db, "decision_records") == 2          # cut + freeze, once each
    assert _count(db, "decision_commitments") == 2
    assert _count(db, "follow_through_proposals", "WHERE state = 'confirmed'") == 2


# ── AC5, isolated from the upstream gaps ──────────────────────────────
#
# On the pre-fix tree the three fences above fail BEFORE their duplicate
# assertion, because the real chain produced no proposals at all (the
# bridge read `text` where `decision_capture` writes `decision`, and
# `action_owner_enforcer` failed its own closed schema).  The two companions
# below seed artifacts in the HS-172 shape the old bridge DID read, so the
# pre-fix failure is the duplicate itself.  The model-retry path has no
# seeded companion: pre-fix, nothing bridged a partial attempt, which is the
# C6 gap fence 2 names in its own first assertion.


def _seeded(db: Database, meeting_id: str) -> None:
    from tests.unit.test_hs172_loop_wire import _seed_action_artifact, _seed_decision_artifact

    state = MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 9, 7, 11, 0, 0),
        ended_at=datetime(2026, 9, 7, 11, 47, 0),
        title="Architecture review",
        segments=[
            TranscriptSegment(text=text, speaker=speaker, start_time=start, end_time=end)
            for start, end, speaker, text in SEGMENTS
        ],
    )
    db.meetings.save_meeting(state)
    _seed_decision_artifact(db, meeting_id, [
        {"text": "Cut-over runs on the read replica first", "source_timestamp": 150.0},
    ])
    _seed_action_artifact(db, meeting_id, [
        {"task": "Draft the rollback runbook", "owner": None, "due": None},
    ])


def test_seeded_repeated_completion_after_a_confirm_mints_no_duplicate(tmp_path: Any) -> None:
    from holdspeak.intel_queue import _on_intel_complete
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = Database(tmp_path / "seeded.db")
    _seeded(db, "m-seeded-repeat")
    _on_intel_complete(db, "m-seeded-repeat")
    assert _count(db, "follow_through_proposals") == 2
    cut = _by_text(_proposals(db, "m-seeded-repeat"), "read replica")
    ProposalBridgeService(db).confirm_proposal(OWNER, cut["id"])

    _on_intel_complete(db, "m-seeded-repeat")            # the completion repeats
    assert _count(db, "follow_through_proposals") == 2, _rows(db, "follow_through_proposals")
    assert _count(db, "follow_through_proposals", "WHERE state = 'proposed'") == 1


def test_seeded_lost_acknowledgement_replays_the_same_result(tmp_path: Any) -> None:
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db = Database(tmp_path / "seeded.db")
    _seeded(db, "m-seeded-ack")
    svc = ProposalBridgeService(db)
    created = svc.bridge_meeting_artifacts("m-seeded-ack")
    assert len(created) == 2
    first = svc.confirm_proposal(OWNER, created[0].id)
    retry = svc.confirm_proposal(OWNER, created[0].id)
    assert "error" not in retry, retry
    assert retry["decision_record_id"] == first["decision_record_id"]
    assert retry["commitment_id"] == first["commitment_id"]
    assert _count(db, "decision_records") == 1
    assert _count(db, "decision_commitments") == 1


# ── counsel-on-built (RATIFY-WITH-CONDITIONS), the fences ─────────────


def test_accept_reviewed_confirms_only_supported_rows_without_unknowns(tmp_path, monkeypatch):
    """P1-1.  Five proposed: two decisions (SUPPORTED, LINKED), an action with
    unknowns, a LINKED action with unknowns, an UNSUPPORTED action with owner
    and due supplied by the model.  The bulk verb keeps the two decisions and
    leaves the three others, naming why."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-bulk")
    _drain()
    svc = ProposalBridgeService(db)
    result = svc.accept_reviewed(OWNER, "m-bulk")
    assert result["accepted_count"] == 2 and result["left_count"] == 3, result
    assert result["unsupported"] == 1 and result["unknown"] == 2 and result["prior"] == 0
    assert {r["reason"] for r in result["left"]} == {"unsupported", "unknown"}
    rows = _proposals(db, "m-bulk")
    assert {p["text"] for p in rows if p["state"] == "confirmed"} == {
        "Cut-over runs on the read replica first", "Freeze window moves to Sunday 02:00",
    }
    assert all(p["state"] == "proposed" for p in rows if p["kind"] == "action")
    assert _count(db, "decision_records") == 2
    # Supplying the unknowns makes a row eligible; the unsupported one never is.
    runbook = _by_text(rows, "rollback runbook")
    svc.edit_proposal(OWNER, runbook["id"], owner="Marek", due="Friday")
    again = svc.accept_reviewed(OWNER, "m-bulk")
    assert again["accepted_count"] == 1 and again["unknown"] == 1 and again["unsupported"] == 1
    assert _by_text(_proposals(db, "m-bulk"), "war room")["state"] == "proposed"


def test_a_changed_transcript_proposes_again_beside_the_earlier_decisions(tmp_path, monkeypatch):
    """P1-2, counsel's H3.  Same transcript: a re-run mints nothing, even
    over dismissed rows.  A speaker rename changes the transcript hash: the
    re-read proposes again BESIDE the earlier decisions, and the projection
    names the earlier revision's rows (``prior_revision``) so nothing is
    doubled silently.  A same-text row still OPEN from the earlier revision
    is not doubled either (the fingerprint belt over proposed rows), and the
    bulk verb holds it as ``prior``."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    state = _meeting(db, "m-rev")
    _drain()
    svc = ProposalBridgeService(db)
    rows = _proposals(db, "m-rev")
    left_open = _by_text(rows, "Sunday 02:00")
    for p in rows:
        if p["id"] != left_open["id"]:
            svc.dismiss_proposal(OWNER, p["id"])
    db.intel.enqueue_intel_job("m-rev", transcript_hash=state.transcript_hash(), reason="re-run")
    _drain()
    assert _count(db, "follow_through_proposals") == 5
    review = svc.meeting_review("m-rev")
    assert review["revision"] == state.transcript_hash()
    assert review["prior_revision"] == {"decided": 0, "open": 0}

    with db._connection() as conn:
        conn.execute("UPDATE segments SET speaker='Priya S.' WHERE meeting_id='m-rev' AND speaker='Priya'")
    changed = db.meetings.get_meeting("m-rev").transcript_hash()
    assert changed != state.transcript_hash()
    db.intel.enqueue_intel_job("m-rev", transcript_hash=changed, reason="re-run after rename")
    _drain()
    # Four decided rows are doubled by four new proposals; the open one is not.
    assert _count(db, "follow_through_proposals") == 9
    assert _count(db, "follow_through_proposals", "WHERE state = 'proposed'") == 5
    review = svc.meeting_review("m-rev")
    assert review["revision"] == changed
    assert review["prior_revision"] == {"decided": 4, "open": 1}
    prior = [p for p in review["proposals"] if p["extraction_revision"] != changed]
    assert len(prior) == 5
    assert [p["id"] for p in prior if p["state"] == "proposed"] == [left_open["id"]]
    current = [p for p in review["proposals"] if p["extraction_revision"] == changed]
    assert len(current) == 4 and all(p["state"] == "proposed" for p in current)
    # The bulk verb confirms the eligible NEW rows and holds the prior open one.
    result = svc.accept_reviewed(OWNER, "m-rev")
    assert result["prior"] == 1 and result["accepted_count"] == 1, result   # only the cut-over decision
    assert svc.meeting_review("m-rev")["prior_revision"] == {"decided": 4, "open": 1}


def test_supplied_owner_and_due_are_distinguishable_from_extracted(tmp_path, monkeypatch):
    """P1-3.  The projection says which values HE supplied."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-supplied")
    _drain()
    svc = ProposalBridgeService(db)
    rows = _proposals(db, "m-supplied")
    war_room = _by_text(rows, "war room")
    assert war_room["owner"] == "Karol" and war_room["owner_supplied"] is None
    confirm = _by_text(rows, "payments team")
    edited = svc.edit_proposal(OWNER, confirm["id"], owner="Priya")["proposal"]
    assert edited["owner"] == "Priya" and edited["owner_supplied"] == "Priya"
    assert edited["due"] is None and edited["due_supplied"] is None
    assert edited["owner_hint"] is None


def test_confirm_after_the_meeting_was_deleted_is_a_named_refusal(tmp_path, monkeypatch):
    """P2-i, counsel's H5.  Pre-fix: ``IntegrityError: FOREIGN KEY constraint
    failed`` out of the chain, a 500 on the route."""
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService

    db, _engine = _rig(tmp_path, monkeypatch)
    _meeting(db, "m-gone")
    _drain()
    svc = ProposalBridgeService(db)
    rows = _proposals(db, "m-gone")
    assert db.meetings.delete_meeting("m-gone") is True
    result = svc.confirm_proposal(OWNER, rows[0]["id"])
    assert result["code"] == "meeting_deleted", result
    assert result["error"].endswith(".")
    assert db.proposals.get_proposal(rows[0]["id"]).state == "proposed"
    assert _count(db, "decision_records") == 0
    assert _count(db, "service_events", "WHERE subject_ref = ?", (f"proposal:{rows[0]['id']}",)) == 0
    from holdspeak.web.routes.proposals import _status
    assert _status(result) == 409
