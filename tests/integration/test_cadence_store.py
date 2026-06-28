"""CAD-1-01 — CadenceRepository persistence + the source-projection invariants.

Real SQLite, no network, no model. Proves: schema v3 applies, upsert is idempotent
on (source_type, source_id), the user's lifecycle decisions survive re-projection
(killed stays killed), close_missing closes vanished sources without touching
user-decided loops, evidence cascades on loop delete, and policies round-trip.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.cadence.models import (
    CadencePolicy,
    EvidenceRef,
    NextBestAction,
    Nudge,
    OpenLoop,
)
from holdspeak.db import Database


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "cadence.db")


def _loop(source_id: str = "a1", **kw) -> OpenLoop:
    return OpenLoop(
        source_type="meeting_action",
        source_id=source_id,
        title=kw.pop("title", "File the issue"),
        project=kw.pop("project", "holdspeak"),
        evidence=kw.pop(
            "evidence",
            [EvidenceRef(kind="action_item", ref_id=source_id, label="Standup",
                         deep_link=f"/meetings/m1#ai-{source_id}")],
        ),
        **kw,
    )


def test_schema_v3_applies_and_loop_round_trips(db: Database):
    saved = db.cadence.upsert_loop(_loop())
    assert saved.id and saved.status == "open"
    assert len(saved.evidence) == 1 and saved.evidence[0].deep_link == "/meetings/m1#ai-a1"
    fetched = db.cadence.get_loop(saved.id)
    assert fetched is not None and fetched.title == "File the issue"


def test_upsert_is_idempotent_on_source_key(db: Database):
    a = db.cadence.upsert_loop(_loop())
    b = db.cadence.upsert_loop(_loop(title="File the issue (reworded)"))
    assert a.id == b.id  # one row
    assert b.title == "File the issue (reworded)"  # source fields update
    assert len(db.cadence.list_loops()) == 1


def test_killed_loop_survives_reprojection(db: Database):
    loop = db.cadence.upsert_loop(_loop())
    db.cadence.set_status(loop.id, "killed")
    again = db.cadence.upsert_loop(_loop(title="resurrected?"))
    assert again.status == "killed"  # never resurrected by re-collection
    assert db.cadence.list_loops() == []  # excludes terminal by default
    assert len(db.cadence.list_loops(include_terminal=True)) == 1


def test_snoozed_loop_keeps_snooze_through_reprojection(db: Database):
    loop = db.cadence.upsert_loop(_loop())
    db.cadence.snooze(loop.id, "2999-01-01T00:00:00")
    again = db.cadence.upsert_loop(_loop())
    assert again.status == "snoozed" and again.snoozed_until == "2999-01-01T00:00:00"


def test_close_missing_closes_vanished_but_spares_user_decided(db: Database):
    db.cadence.upsert_loop(_loop("a1"))
    killed = db.cadence.upsert_loop(_loop("a2"))
    db.cadence.set_status(killed.id, "killed")
    # only a2's source remains present; a1 vanished, a2 is killed
    closed = db.cadence.close_missing("meeting_action", present_source_ids=["a2"])
    assert closed == 1  # a1 closed
    assert db.cadence.get_loop_by_source("meeting_action", "a1").status == "closed"
    assert db.cadence.get_loop_by_source("meeting_action", "a2").status == "killed"  # spared


def test_evidence_cascades_on_loop_delete(db: Database):
    loop = db.cadence.upsert_loop(_loop())
    with db._connection() as conn:
        conn.execute("DELETE FROM cadence_loops WHERE id = ?", (loop.id,))
        remaining = conn.execute(
            "SELECT COUNT(*) AS n FROM cadence_evidence_refs WHERE loop_id = ?", (loop.id,)
        ).fetchone()["n"]
    assert remaining == 0


def test_next_action_and_nudge_persist(db: Database):
    loop = db.cadence.upsert_loop(_loop())
    aid = db.cadence.add_next_action(
        NextBestAction(loop_id=loop.id, kind="create_issue", title="Draft issue", confidence=0.9)
    )
    nid = db.cadence.record_nudge(
        Nudge(loop_id=loop.id, surface="cli", next_action_id=aid, title="File it")
    )
    assert aid and nid


def test_policies_round_trip(db: Database):
    db.cadence.upsert_policy(CadencePolicy(name="agent_blocker", config={"initial_delay_minutes": 5}))
    db.cadence.upsert_policy(CadencePolicy(name="agent_blocker", config={"initial_delay_minutes": 10}))
    got = db.cadence.get_policy("agent_blocker")
    assert got is not None and got.config["initial_delay_minutes"] == 10  # upsert updated
    assert len(db.cadence.list_policies()) == 1


def test_stale_score_and_nudge_bump_persist(db: Database):
    loop = db.cadence.upsert_loop(_loop())
    db.cadence.set_stale_score(loop.id, 42.5)
    db.cadence.bump_nudge(loop.id, at="2026-06-28T10:00:00")
    again = db.cadence.get_loop(loop.id)
    assert again.stale_score == 42.5 and again.nudge_count == 1
    assert again.last_nudged_at == "2026-06-28T10:00:00"
