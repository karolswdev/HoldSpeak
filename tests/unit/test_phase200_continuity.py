"""HS-200-13 -- decisions and commitments carry into the next day.

Planned suite: ``phase200_continuity`` (the charter names it
``phase200_decision_continuity``; the brief and this module use the short
form, which is what the evidence file cites).

The chain under test is the one HS-200-12 mints -- a confirmed proposal ->
``decisions`` -> ``decision_records`` (+ sources) -> ``action_items`` ->
``decision_commitments`` -- read back by the recall service the Desk memory
face draws (posture 5), by the Room's attention producer (the arrival), and
by the carry mark HS-200-11's manifest builder reads.

Five acceptance criteria, each a fence here:

  AC1  recall returns the CURRENT decision first, with rationale and source;
  AC2  superseded and disputed records stay discoverable, never current;
  AC3  a commitment has an owner/date or typed unknowns, and ONE lawful next
       action; commitments are real attention items (source ``commitment``);
  AC4  naming an owner, setting a date, linking a PR or an artifact never
       flips a commitment's status -- only the receipted `done` does;
  AC5  the chain survives a restart: the carry mark and the last-known
       observation are read from the database by a fresh process.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.brief_carry import (
    carry_into_brief,
    consume_carries,
    pending_carries,
    pending_carry_refs,
    resolve_current,
)
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.follow_through_service import FollowThroughService
from holdspeak.services.needs_you_aggregate import LastKnownStore, build_aggregate
from holdspeak.services.project_service import ProjectService
from holdspeak.services.proposal_bridge_service import ProposalBridgeService
from holdspeak.services.recall_service import RecallService, due_token, next_action_for

OWNER = Principal(PrincipalKind.OWNER, "the-owner")

SAT = "2026-09-02"
SUN = "2026-09-07"
OLD_TEXT = "Freeze window is Saturday 02:00"
NEW_TEXT = "Freeze window is Sunday 02:00, not Saturday"
NEW_WHY = "Payments cannot drain the queue before 02:00 on a weekday."
CMT_TEXT = "Priya confirms the freeze window"


# ── seeds ────────────────────────────────────────────────────────────


def _db(tmp_path: Path, name: str = "continuity.db") -> Database:
    return Database(tmp_path / name)


def _seed_room(db: Database, project_id: str = "p-q4", name: str = "Q4 Platform") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects (id, name, created_at, updated_at) "
            "VALUES (?, ?, datetime('now'), datetime('now'))",
            (project_id, name),
        )


def _seed_meeting(db: Database, meeting_id: str, day: str, title: str, project_id: str = "p-q4") -> None:
    """A finalized meeting at 11:00 with four turns at the boards' minutes."""
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO meetings (id, started_at, ended_at, title, duration_seconds, "
            " intel_status, capture_status, provenance) "
            "VALUES (?, ?, ?, ?, 3600, 'complete', 'finalized', 'desktop')",
            (meeting_id, f"{day}T11:00:00", f"{day}T12:00:00", title),
        )
        conn.execute(
            "INSERT OR IGNORE INTO meeting_projects (meeting_id, project_id, source, confidence) "
            "VALUES (?, ?, 'auto', 0.9)",
            (meeting_id, project_id),
        )
        for start, text in ((0.0, "Let's start with the cut-over sequencing"),
                            (1080.0, "Cut-over runs on the read replica first"),
                            (1860.0, NEW_TEXT), (1980.0, CMT_TEXT)):
            conn.execute(
                "INSERT INTO segments (meeting_id, text, speaker, start_time, end_time) "
                "VALUES (?, ?, 'Marek', ?, ?)",
                (meeting_id, text, start, start + 60.0),
            )


def _propose(db: Database, meeting_id: str, kind: str, text: str, *, segment_index: int,
             rationale: str | None = None, owner: str | None = None, due: str | None = None) -> Any:
    prop = db.proposals.create_proposal(
        meeting_id=meeting_id, project_id="p-q4", kind=kind, text=text,
        source_plugin="decision_capture" if kind == "decision" else "action_owner_enforcer",
        segment_timestamp=1860.0, span_start=1860.0, span_end=1920.0,
        segment_index=segment_index, support="supported", rationale=rationale,
        owner_hint=owner, due_hint=due,
    )
    assert prop is not None
    return prop


def _confirm(db: Database, proposal_id: str, **kw: Any) -> dict[str, Any]:
    result = ProposalBridgeService(db).confirm_proposal(OWNER, proposal_id, **kw)
    assert "error" not in result, result
    return result


def _chain(db: Database) -> dict[str, Any]:
    """The board's story: Saturday decided on 09-02, Sunday on 09-07 with a
    rationale, one commitment; Saturday superseded by Sunday."""
    _seed_room(db)
    _seed_meeting(db, "m-sat", SAT, "Cut-over planning")
    _seed_meeting(db, "m-sun", SUN, "Architecture review")
    old = _confirm(db, _propose(db, "m-sat", "decision", OLD_TEXT, segment_index=2,
                                rationale="Least traffic on Saturday").id)
    new = _confirm(db, _propose(db, "m-sun", "decision", NEW_TEXT, segment_index=2,
                                rationale=NEW_WHY).id)
    cmt = _confirm(db, _propose(db, "m-sun", "action", CMT_TEXT, segment_index=3).id)
    DecisionRecordService(db).supersede(
        OWNER, old["decision_record_id"], new["decision_record_id"], "moved to Sunday",
    )
    return {"old": old, "new": new, "cmt": cmt}


def _status(db: Database, chain: dict[str, Any]) -> tuple[str, str]:
    with db._connection() as conn:
        c = conn.execute("SELECT status FROM decision_commitments WHERE id = ?",
                         (chain["cmt"]["commitment_id"],)).fetchone()
        a = conn.execute("SELECT status FROM action_items WHERE id = ?",
                         (chain["cmt"]["action_item_id"],)).fetchone()
    return str(c["status"]), str(a["status"])


def _events(db: Database) -> list[str]:
    with db._connection() as conn:
        return [str(r["event_type"]) for r in
                conn.execute("SELECT event_type FROM service_events ORDER BY rowid").fetchall()]


# ── AC1 ──────────────────────────────────────────────────────────────


def test_recall_returns_the_current_decision_first_with_rationale_and_source(tmp_path: Path) -> None:
    db = _db(tmp_path)
    chain = _chain(db)
    out = RecallService(db).recall(OWNER, "freeze window")

    assert [c["text"] for c in out["current"]] == [NEW_TEXT]
    card = out["current"][0]
    assert card["id"] == chain["new"]["decision_record_id"]
    assert card["rationale"] == NEW_WHY, "the extractor's rationale reaches the record (AC1)"
    assert card["axes"] == ["DECISION", "SUPPORTED", "ACCEPTED"]
    assert card["dec_token"] == "DEC 09-07"
    # The original source: the meeting and the transcript moment (11:00 + 31 min).
    assert card["source"]["token"] == "MTG 09-07 · 11:31"
    assert card["source"]["scope"] == "meeting:m-sun?segment=2"
    assert card["project"] == {"id": "p-q4", "name": "Q4 Platform"}
    assert card["carried"] is False
    # The head's one count: current + superseded + owed + the meetings that match.
    assert out["remembered"] == 1 + 1 + 1 + len(out["meetings"]) + len(out["also"])
    assert out["projects_searched"] == 1


def test_a_recall_miss_is_a_true_miss_with_the_projects_searched(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _chain(db)
    out = RecallService(db).recall(OWNER, "unfindablequasar")
    assert out["remembered"] == 0
    assert all(out[k] == [] for k in ("current", "superseded", "disputed", "owed", "meetings", "briefs", "also"))
    assert out["projects_searched"] == 1


def test_the_filters_narrow_without_lying(tmp_path: Path) -> None:
    db = _db(tmp_path)
    _chain(db)
    svc = RecallService(db)
    decisions = svc.recall(OWNER, "freeze window", filter="decisions")
    assert len(decisions["current"]) == 1 and decisions["owed"] == [] and decisions["meetings"] == []
    commitments = svc.recall(OWNER, "freeze window", filter="commitments")
    assert commitments["current"] == [] and [r["text"] for r in commitments["owed"]] == [CMT_TEXT]
    meetings = svc.recall(OWNER, "freeze window", filter="meetings")
    assert meetings["current"] == [] and {h["kind"] for h in meetings["meetings"]} == {"meeting"}
    with pytest.raises(Exception):
        svc.recall(OWNER, "freeze window", filter="everything")


# ── AC2 ──────────────────────────────────────────────────────────────


def test_superseded_and_disputed_records_are_discoverable_and_never_current(tmp_path: Path) -> None:
    db = _db(tmp_path)
    chain = _chain(db)
    svc = RecallService(db)

    out = svc.recall(OWNER, "freeze window", filter="decisions")
    assert [c["text"] for c in out["superseded"]] == [OLD_TEXT]
    old = out["superseded"][0]
    assert old["acceptance"] == "SUPERSEDED"
    assert old["successor"]["id"] == chain["new"]["decision_record_id"]
    assert old["successor"]["dec_token"] == "DEC 09-07", "`SUPERSEDED BY DEC 09-07` names the successor's day"
    assert old["dec_token"] == "DEC 09-02"
    assert old["supersession_reason"] == "moved to Sunday"
    assert all(c["id"] != old["id"] for c in out["current"])

    # Dispute the current one: it leaves CURRENT, is still found, never accented.
    records = DecisionRecordService(db)
    disputed = records.dispute(OWNER, chain["new"]["decision_record_id"], "Priya disagrees with the window")
    assert disputed["lifecycle"] == "disputed"
    assert disputed["dispute_reason"] == "Priya disagrees with the window"
    out = svc.recall(OWNER, "freeze window", filter="decisions")
    assert out["current"] == []
    assert [c["text"] for c in out["disputed"]] == [NEW_TEXT]
    assert out["disputed"][0]["acceptance"] == "DISPUTED"
    assert out["disputed"][0]["state"] == "disputed"
    assert "decision.disputed" in _events(db)
    # A dispute is sealed against edits, and a dispute ends by supersession.
    with pytest.raises(ValueError):
        records.update_record(OWNER, chain["new"]["decision_record_id"], {"decision_text": "x"})
    newest = records.create(OWNER, decision_text="Freeze window is Sunday 03:00", source_type="desk", source_id="desk-1")
    sealed = records.supersede(OWNER, chain["new"]["decision_record_id"], newest["id"], "agreed at 03:00")
    assert sealed["lifecycle"] == "superseded"


def test_a_decision_kind_chain_row_is_never_owed_and_an_action_is_never_a_decision(tmp_path: Path) -> None:
    """HS-200-12 mints the full chain for every proposal kind.  The recall
    draws each thing as what it is: a decision under CURRENT, a commitment
    under OWED -- never both."""
    db = _db(tmp_path)
    _chain(db)
    out = RecallService(db).recall(OWNER, "freeze window")
    assert [r["text"] for r in out["owed"]] == [CMT_TEXT]
    assert CMT_TEXT not in [c["text"] for c in out["current"] + out["superseded"] + out["disputed"]]
    room = ProjectService(db).room(OWNER, "p-q4")
    rows = [i for i in room["needsYou"]["items"] if i["source"] == "commitment"]
    assert [r["title"] for r in rows] == [CMT_TEXT]


# ── AC3 ──────────────────────────────────────────────────────────────


def test_an_owed_row_has_typed_unknowns_and_one_lawful_next_action(tmp_path: Path) -> None:
    db = _db(tmp_path)
    chain = _chain(db)
    svc = RecallService(db)
    ft = FollowThroughService(db)
    aid = chain["cmt"]["action_item_id"]

    row = svc.recall(OWNER, "confirms the freeze", filter="commitments")["owed"][0]
    assert row["owner_token"] == "OWNER · UNKNOWN" and row["due_token"] == "DUE · UNKNOWN"
    assert row["unknowns"] == ["owner", "due"]
    assert row["next_action"] == "name_owner"

    ft.complete(OWNER, aid, "delegate", {"to": "Priya"})
    row = svc.recall(OWNER, "confirms the freeze", filter="commitments")["owed"][0]
    assert row["owner_token"] == "OWNER · PRIYA" and row["unknowns"] == ["due"]
    assert row["next_action"] == "set_date"

    today = datetime.now().strftime("%Y-%m-%d")
    ft.complete(OWNER, aid, "due", {"due_at": today})
    row = svc.recall(OWNER, "confirms the freeze", filter="commitments")["owed"][0]
    assert row["due_token"] == "DUE TODAY" and row["unknowns"] == []
    assert row["next_action"] == "mark_done"
    with pytest.raises(ValueError):
        ft.complete(OWNER, aid, "due", {"due_at": "next Tuesday"})


def test_the_next_action_rule_and_the_due_token_are_pure() -> None:
    assert next_action_for(None, None) == "name_owner"
    assert next_action_for("Priya", None) == "set_date"
    assert next_action_for(None, "2026-09-07") == "name_owner"
    assert next_action_for("Priya", "2026-09-07") == "mark_done"
    now = datetime(2026, 9, 7, 9, 20)
    assert due_token(None, now) == ("DUE · UNKNOWN", "idle")
    assert due_token("2026-09-07", now) == ("DUE TODAY", "warn")
    assert due_token("2026-09-05", now) == ("OVERDUE · 2 D", "danger")
    assert due_token("2026-09-12", now) == ("DUE 09-12", "idle")


def test_commitments_are_real_attention_items(tmp_path: Path) -> None:
    """The Room's needs-you producer emits the commitment (HS-200-15 built
    the `commitment` source against synthetic rows); the aggregate ranks it
    by its due date and carries what its verbs need."""
    db = _db(tmp_path)
    chain = _chain(db)
    ps = ProjectService(db)
    aid = chain["cmt"]["action_item_id"]
    ft = FollowThroughService(db)
    ft.complete(OWNER, aid, "delegate", {"to": "Priya"})
    ft.complete(OWNER, aid, "due", {"due_at": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")})

    room = ps.room(OWNER, "p-q4")
    rows = [i for i in room["needsYou"]["items"] if i["source"] == "commitment"]
    assert len(rows) == 1
    assert rows[0]["why"] == "OVERDUE · 2 D" and rows[0]["kind"] == "commitment"
    assert rows[0]["next_action"] == "mark_done" and rows[0]["unknowns"] == []
    assert rows[0]["commitment_id"] == chain["cmt"]["commitment_id"]

    aggregate = build_aggregate(
        list_projects=ps.list_projects, room=ps.room, principal=OWNER,
        now=datetime.now(), last_known=LastKnownStore(),
    )
    items = [i for i in aggregate["items"] if i["source"] == "commitment"]
    assert len(items) == 1
    assert items[0]["rankClass"] == "overdue"
    assert items[0]["commitmentId"] == chain["cmt"]["commitment_id"]
    assert items[0]["actionItemId"] == aid
    assert items[0]["nextAction"] == "mark_done"
    assert any(c["kind"] == "commitment" and c["state"] == "available" for c in aggregate["coverage"])

    # Once done it leaves the arrival; a decision-kind chain row never enters it.
    ft.complete(OWNER, aid, "done")
    room = ps.room(OWNER, "p-q4")
    assert [i for i in room["needsYou"]["items"] if i["source"] == "commitment"] == []


# ── AC4 ──────────────────────────────────────────────────────────────


def test_assignment_and_association_never_complete_a_commitment(tmp_path: Path) -> None:
    db = _db(tmp_path)
    chain = _chain(db)
    ft = FollowThroughService(db)
    records = DecisionRecordService(db)
    aid = chain["cmt"]["action_item_id"]
    rid = chain["new"]["decision_record_id"]

    assert _status(db, chain) == ("open", "open")
    ft.complete(OWNER, aid, "delegate", {"to": "Priya"})
    assert _status(db, chain) == ("open", "open"), "naming an owner is not completion"
    ft.complete(OWNER, aid, "due", {"due_at": "2026-09-08"})
    assert _status(db, chain) == ("open", "open"), "setting a date is not completion"
    records.link_work(OWNER, rid, "pull_request", "karolswdev/HoldSpeak#612")
    records.link_work(OWNER, rid, "artifact", "artifact:a-runbook")
    assert _status(db, chain) == ("open", "open"), "linking a PR or an artifact is not completion"
    with db._connection() as conn:
        conn.execute("UPDATE action_items SET source_type = 'artifact', source_ref = 'artifact:a-runbook' WHERE id = ?", (aid,))
    assert _status(db, chain) == ("open", "open"), "an artifact association on the item is not completion"
    # The Room still owes it, with the owner and the date it now has.
    rows = [i for i in ProjectService(db).room(OWNER, "p-q4")["needsYou"]["items"] if i["source"] == "commitment"]
    assert len(rows) == 1 and rows[0]["owner"] == "Priya" and rows[0]["due_at"] == "2026-09-08"
    assert "commitment.completed" not in _events(db)

    # Only the explicit act completes, and it leaves a receipt naming the item.
    ft.complete(OWNER, aid, "done")
    assert _status(db, chain) == ("closed", "done")
    events = _events(db)
    assert events[-1] == "commitment.completed"
    with db._connection() as conn:
        last = conn.execute("SELECT facts_json, refs_json FROM service_events ORDER BY rowid DESC LIMIT 1").fetchone()
    facts = json.loads(last["facts_json"])
    assert facts["action_item_id"] == aid and facts["commitment_ids"] == [chain["cmt"]["commitment_id"]]
    assert f"commitment:{chain['cmt']['commitment_id']}" in json.loads(last["refs_json"])
    assert {"commitment.owner_named", "commitment.due_set"} <= set(events)


# ── AC5 ──────────────────────────────────────────────────────────────


def test_the_carry_mark_survives_a_restart_and_resolves_to_the_current_record(tmp_path: Path) -> None:
    db = _db(tmp_path)
    chain = _chain(db)
    mark = carry_into_brief(db, OWNER, chain["new"]["decision_record_id"])
    assert mark["replayed"] is False and mark["project_id"] == "p-q4"
    assert carry_into_brief(db, OWNER, chain["new"]["decision_record_id"])["replayed"] is True
    assert "decision.carried" in _events(db)
    assert RecallService(db).recall(OWNER, "freeze window", filter="decisions")["current"][0]["carried"] is True

    # "Restart": a fresh Database over the same file, nothing in memory.
    again = Database(tmp_path / "continuity.db")
    carried = pending_carries(again, "p-q4")
    assert len(carried) == 1
    row = carried[0]
    assert row["ref"] == f"decision_record:{chain['new']['decision_record_id']}"
    assert row["current_ref"] == row["ref"] and row["superseded"] is False
    assert row["text"] == NEW_TEXT and row["rationale"] == NEW_WHY and row["lifecycle"] == "active"

    # Superseded between the recall and the preparation: the mark resolves
    # to the successor at read time (C3: by reference, never a copy).
    records = DecisionRecordService(again)
    newest = records.create(OWNER, decision_text="Freeze window is Sunday 03:00", source_type="desk", source_id="desk-2")
    records.supersede(OWNER, chain["new"]["decision_record_id"], newest["id"], "agreed at 03:00")
    row = pending_carries(again, "p-q4")[0]
    assert row["current_record_id"] == newest["id"] and row["superseded"] is True
    assert row["resolved_through"] == [f"decision_record:{newest['id']}"]
    assert row["text"] == "Freeze window is Sunday 03:00"
    with again._connection() as conn:
        assert resolve_current(conn, chain["old"]["decision_record_id"])["record_id"] == newest["id"]

    # The brief that read it consumes it; a later recall may carry again.
    assert consume_carries(again, "p-q4", "brief-1") == 1
    assert pending_carries(again, "p-q4") == []
    assert pending_carry_refs(again, "p-q4") == set()
    assert carry_into_brief(again, OWNER, newest["id"], project_id="p-q4")["replayed"] is False


def test_the_last_known_observation_survives_a_restart(tmp_path: Path) -> None:
    """HS-200-15 left `LastKnownStore` process-local; a failed source after a
    restart replayed nothing.  With the durable store a fresh process still
    carries the last observation, marked as such."""
    db = _db(tmp_path)
    _seed_room(db)
    observed = "2026-09-07T08:41:00"
    items = [{"id": "p-q4:commitment:x", "projectId": "p-q4", "title": "Priya confirms the freeze window",
              "source": "commitment", "why": "DUE TODAY", "severity": "warning", "since": observed}]
    LastKnownStore(db_factory=lambda: db).remember("project:p-q4", items=items, observed_at=observed,
                                                   label="Q4 Platform", project_id="p-q4")

    fresh = LastKnownStore(db_factory=lambda: Database(tmp_path / "continuity.db"))
    recalled = fresh.recall("project:p-q4")
    assert recalled is not None and recalled["observed_at"] == observed
    assert recalled["items"] == items and fresh.source_ids() == ["project:p-q4"]
    assert LastKnownStore().recall("project:p-q4") is None, "without a factory the store is what it was"

    def failing_room(principal: Any, pid: str) -> dict[str, Any]:
        raise RuntimeError("room read failed")

    aggregate = build_aggregate(
        list_projects=lambda *_: [{"id": "p-q4", "name": "Q4 Platform"}], room=failing_room,
        principal=OWNER, now=datetime(2026, 9, 7, 9, 12), last_known=fresh,
    )
    assert aggregate["complete"] is False
    carried = [i for i in aggregate["items"] if i.get("fromLastObservation")]
    assert len(carried) == 1 and carried[0]["observedAt"] == observed
    assert carried[0]["title"] == "Priya confirms the freeze window"
    assert aggregate["coverage"][0]["observed_at"] == observed


# ── counsel-on-built fences (RATIFY-WITH-CONDITIONS, 2026-09-17) ─────


def test_one_carry_mark_per_current_record_across_a_supersession(tmp_path: Path) -> None:
    """P1-2 (counsel q1c): carry -> supersede -> the successor reads carried;
    a press on the successor is a replay; the seam receives ONE row."""
    db = _db(tmp_path)
    chain = _chain(db)
    records = DecisionRecordService(db)
    first = carry_into_brief(db, OWNER, chain["new"]["decision_record_id"])
    newest = records.create(OWNER, decision_text="Freeze window is Sunday 03:00", source_type="desk", source_id="d-3")
    with db._connection() as conn:
        conn.execute("INSERT INTO project_resources (project_id, resource_ref) VALUES ('p-q4', ?)",
                     (f"decision_record:{newest['id']}",))
    records.supersede(OWNER, chain["new"]["decision_record_id"], newest["id"], "03:00")

    out = RecallService(db).recall(OWNER, "freeze window", filter="decisions")
    assert [(c["id"], c["carried"]) for c in out["current"]] == [(newest["id"], True)]
    assert pending_carry_refs(db, "p-q4") == {f"decision_record:{newest['id']}"}
    again = carry_into_brief(db, OWNER, newest["id"], project_id="p-q4")
    assert again["replayed"] is True and again["id"] == first["id"]
    rows = pending_carries(db, "p-q4")
    assert len(rows) == 1 and rows[0]["current_record_id"] == newest["id"] and rows[0]["superseded"] is True
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM preparation_carries WHERE consumed_at IS NULL").fetchone()["n"] == 1
    assert _events(db).count("decision.carried") == 1


def test_only_a_current_record_can_be_carried_and_only_by_a_decider(tmp_path: Path) -> None:
    """P2: `not_current` at the service, and the DECIDE right; an
    UNAUTHENTICATED caller is refused by name (403 on the wire)."""
    from holdspeak.principals import UNAUTHENTICATED
    from holdspeak.services.brief_carry import RightRequired
    db = _db(tmp_path)
    chain = _chain(db)
    records = DecisionRecordService(db)
    with pytest.raises(ValueError, match="not_current"):
        carry_into_brief(db, OWNER, chain["old"]["decision_record_id"])
    records.dispute(OWNER, chain["new"]["decision_record_id"], "contested")
    with pytest.raises(ValueError, match="not_current"):
        carry_into_brief(db, OWNER, chain["new"]["decision_record_id"])
    agent = Principal(PrincipalKind.AGENT, "agent-x")
    for principal in (UNAUTHENTICATED, agent):
        with pytest.raises(RightRequired) as refused:
            carry_into_brief(db, principal, chain["new"]["decision_record_id"])
        assert refused.value.response["error"] == "principal_right_required"
        assert refused.value.response["principal"] == principal.name
        with pytest.raises(RightRequired):
            records.dispute(principal, chain["old"]["decision_record_id"], "x")
        with pytest.raises(RightRequired):
            records.supersede(principal, chain["new"]["decision_record_id"], chain["old"]["decision_record_id"])
    assert "decision.carried" not in _events(db)


def test_a_closed_commitment_refuses_every_act_but_reopen_and_done_replays(tmp_path: Path) -> None:
    """P1-3 (counsel q5): `due` takes a calendar day only (basic ISO
    normalised, past lawful); a closed item refuses due/delegate by name;
    `done` twice is a replay with one receipt; `reopen` is receipted."""
    db = _db(tmp_path)
    chain = _chain(db)
    ft = FollowThroughService(db)
    aid = chain["cmt"]["action_item_id"]

    for bad in ("2026-13-45", "tomorrow", "2026-09-20T10:00:00Z", "2026-9-2", ""):
        with pytest.raises(ValueError):
            ft.complete(OWNER, aid, "due", {"due_at": bad})
    ft.complete(OWNER, aid, "due", {"due_at": "20260920"})
    with db._connection() as conn:
        assert conn.execute("SELECT due FROM action_items WHERE id = ?", (aid,)).fetchone()["due"] == "2026-09-20"
    ft.complete(OWNER, aid, "due", {"due_at": "2020-01-01"})  # a past day is lawful
    assert _status(db, chain) == ("open", "open")

    ft.complete(OWNER, aid, "done")
    assert _events(db).count("commitment.completed") == 1
    replay = ft.complete(OWNER, aid, "done")
    assert replay["replayed"] is True
    assert _events(db).count("commitment.completed") == 1, "done twice writes one receipt"
    with pytest.raises(ValueError, match="commitment_closed"):
        ft.complete(OWNER, aid, "due", {"due_at": "2026-10-01"})
    with pytest.raises(ValueError, match="commitment_closed"):
        ft.complete(OWNER, aid, "delegate", {"to": "Bob"})
    with pytest.raises(ValueError, match="commitment_closed"):
        ft.complete(OWNER, aid, "dismiss")
    assert _status(db, chain) == ("closed", "done")

    ft.complete(OWNER, aid, "reopen")
    assert _status(db, chain) == ("open", "open")
    assert _events(db)[-1] == "commitment.reopened"
    ft.complete(OWNER, aid, "dismiss")
    assert _status(db, chain) == ("closed", "dismissed")
    assert ft.complete(OWNER, aid, "dismiss")["replayed"] is True
    assert _events(db).count("commitment.dismissed") == 1


def test_the_last_known_store_prunes_forgotten_sources_and_bounds_the_replay(tmp_path: Path) -> None:
    """P1-4 (counsel q4): fifty sources remembered a month ago and never
    listed again replay NOTHING on a project-list failure; a source the
    list still names keeps its original observed_at; two stores over one
    database agree on the newer row; the process shares one store."""
    from holdspeak.services.needs_you_aggregate import REPLAY_HORIZON_DAYS, shared_last_known
    db = _db(tmp_path)
    _seed_room(db)
    now = datetime(2026, 9, 7, 9, 12)
    stale_at = (now - timedelta(days=REPLAY_HORIZON_DAYS + 20)).isoformat()
    fresh_at = (now - timedelta(hours=1)).isoformat()
    store = LastKnownStore(db_factory=lambda: db)
    for i in range(50):
        store.remember(f"project:p-{i}", items=[{"id": str(i), "title": f"ghost {i}", "source": "github"}],
                       observed_at=stale_at, label=f"P{i}", project_id=f"p-{i}")
    store.remember("project:p-q4", items=[{"id": "q4:1", "title": "Priya confirms the freeze window", "source": "commitment"}],
                   observed_at=fresh_at, label="Q4 Platform", project_id="p-q4")

    def listing_fails(*_: Any) -> list[dict[str, Any]]:
        raise RuntimeError("list down")

    # Beyond the horizon: nothing replayed, nothing claimed.
    agg = build_aggregate(list_projects=listing_fails, room=lambda p, pid: {}, principal=OWNER, now=now, last_known=store)
    replayed = [i for i in agg["items"] if i.get("fromLastObservation")]
    assert [i["title"] for i in replayed] == ["Priya confirms the freeze window"]
    assert replayed[0]["observedAt"] == fresh_at, "the original observed_at survives"
    assert agg["complete"] is False

    # A successful list that names only p-q4 prunes the fifty.
    def failing_room(p: Any, pid: str) -> dict[str, Any]:
        raise RuntimeError("room down")
    agg = build_aggregate(list_projects=lambda *_: [{"id": "p-q4", "name": "Q4 Platform"}], room=failing_room,
                          principal=OWNER, now=now, last_known=store)
    assert store.source_ids() == ["project:p-q4"]
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) AS n FROM needs_you_last_known").fetchone()["n"] == 1
    assert [i["observedAt"] for i in agg["items"] if i.get("fromLastObservation")] == [fresh_at]

    # Two stores over one database: the newer durable row wins.
    other = LastKnownStore(db_factory=lambda: db)
    assert other.recall("project:p-q4", now=now)["observed_at"] == fresh_at
    later = now.isoformat()
    store.remember("project:p-q4", items=[], observed_at=later, label="Q4 Platform", project_id="p-q4")
    assert other.recall("project:p-q4", now=now)["observed_at"] == later

    # One store per process, bound to the database on first use.
    shared = shared_last_known(lambda: db)
    assert shared is shared_last_known(lambda: db) and shared.durable
    shared.clear()


# ── the routes ───────────────────────────────────────────────────────


def test_an_unauthenticated_carry_is_refused_by_name_on_the_wire(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from holdspeak.principals import UNAUTHENTICATED
    from holdspeak.web.routes.decision_records import build_decision_records_router
    import holdspeak.web.routes.decision_records as records_routes

    reset_database()
    db = _db(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(records_routes, "get_database", lambda *a, **k: db)
    chain = _chain(db)
    app = FastAPI()

    @app.middleware("http")
    async def _principal(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = UNAUTHENTICATED
        return await call_next(request)

    app.include_router(build_decision_records_router(None))
    http = TestClient(app)
    rid = chain["new"]["decision_record_id"]
    for path in (f"/api/decision-records/{rid}/carry", f"/api/decision-records/{rid}/dispute",
                 f"/api/decision-records/{chain['old']['decision_record_id']}/supersede"):
        response = http.post(path, json={"successor_id": rid})
        assert response.status_code == 403, (path, response.text)
        assert response.json()["error"] == "principal_right_required"
        assert response.json()["principal"] == "none"
    reset_database()


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.decision_records import build_decision_records_router
    from holdspeak.web.routes.memory import build_memory_router

    reset_database()
    db = _db(tmp_path)
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    # The records router bound `get_database` at import; point that name too.
    import holdspeak.web.routes.decision_records as records_routes
    monkeypatch.setattr(records_routes, "get_database", lambda *a, **k: db)
    app = FastAPI()

    @app.middleware("http")
    async def _principal(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_memory_router(WebContext(get_state=lambda: {}, memory_service=MemoryService(db))))
    app.include_router(build_decision_records_router(None))
    yield db, TestClient(app)
    reset_database()


def test_the_recall_and_lifecycle_routes(client) -> None:
    db, http = client
    chain = _chain(db)
    rid = chain["new"]["decision_record_id"]

    body = http.get("/api/memory/recall", params={"query": "freeze window"}).json()
    assert [c["text"] for c in body["current"]] == [NEW_TEXT]
    assert [c["text"] for c in body["superseded"]] == [OLD_TEXT]
    assert [r["text"] for r in body["owed"]] == [CMT_TEXT]
    assert http.get("/api/memory/recall", params={"query": ""}).status_code == 400
    assert http.get("/api/memory/recall", params={"query": "x", "filter": "nope"}).status_code == 400

    carried = http.post(f"/api/decision-records/{rid}/carry", json={}).json()
    assert carried["project_id"] == "p-q4" and carried["replayed"] is False
    assert http.post(f"/api/decision-records/{rid}/carry", json={}).json()["replayed"] is True
    assert http.post("/api/decision-records/record-missing/carry", json={}).status_code == 404
    old_id = chain["old"]["decision_record_id"]
    assert http.post(f"/api/decision-records/{old_id}/carry", json={}).status_code == 409, "not_current"

    disputed = http.post(f"/api/decision-records/{rid}/dispute", json={"reason": "contested"}).json()
    assert disputed["lifecycle"] == "disputed"
    body = http.get("/api/memory/recall", params={"query": "freeze window", "filter": "decisions"}).json()
    assert body["current"] == [] and [c["text"] for c in body["disputed"]] == [NEW_TEXT]

    newest = DecisionRecordService(db).create(OWNER, decision_text="Freeze window is Sunday 03:00",
                                              source_type="desk", source_id="desk-3")
    sealed = http.post(f"/api/decision-records/{rid}/supersede", json={"successor_id": newest["id"]}).json()
    assert sealed["lifecycle"] == "superseded"
    assert http.post(f"/api/decision-records/{rid}/supersede", json={"successor_id": newest["id"]}).status_code == 409
