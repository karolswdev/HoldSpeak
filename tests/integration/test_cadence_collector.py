"""CAD-1-02 — the collector projects loops from meeting actions + pending proposals."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.cadence.collector import LoopCollector
from holdspeak.config import Config
from holdspeak.db import Database

NOW = datetime(2026, 6, 28, 10, 0, 0)


@pytest.fixture
def seeded_db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "c.db")
    with db._connection() as c:
        c.execute(
            "INSERT INTO meetings (id, title, started_at, created_at) "
            "VALUES ('m1','Platform sync','2026-06-27T14:00:00','2026-06-27T14:00:00')"
        )
        c.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at) "
            "VALUES ('a1','m1','File the watchdog issue','Karol','2026-06-30','pending','reviewed','2026-06-26T10:00:00')"
        )
        c.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, status, review_state, created_at) "
            "VALUES ('a2','m1','Maybe revisit retry budget',NULL,'pending','pending','2026-06-27T10:00:00')"
        )
    db.actuators.record_proposal(
        meeting_id="m1", window_id="m1:aftercare", plugin_id="github_issue_actuator",
        plugin_version="1.0", idempotency_key="k1", target="github", action="create_issue",
        preview="Create issue: watchdog around intel queue", reversible=False,
    )
    return db


def test_collect_projects_actions_and_proposals_with_evidence(seeded_db: Database):
    loops = LoopCollector(seeded_db).collect(now=NOW)
    assert len(loops) == 3
    by_source = {l.source_type for l in loops}
    assert by_source == {"meeting_action", "proposal"}
    a1 = seeded_db.cadence.get_loop_by_source("meeting_action", "a1")
    assert a1.evidence and a1.evidence[0].deep_link == "/meetings/m1#ai-a1"
    a2 = seeded_db.cadence.get_loop_by_source("meeting_action", "a2")
    assert a2.needs_review is True  # unreviewed extraction -> quiet review loop


def test_collect_is_idempotent(seeded_db: Database):
    LoopCollector(seeded_db).collect(now=NOW)
    LoopCollector(seeded_db).collect(now=NOW)
    assert len(seeded_db.cadence.list_loops()) == 3  # no dupes


def test_completing_an_action_closes_its_loop(seeded_db: Database):
    LoopCollector(seeded_db).collect(now=NOW)
    with seeded_db._connection() as c:
        c.execute("UPDATE action_items SET status='completed' WHERE id='a1'")
    LoopCollector(seeded_db).collect(now=NOW)
    assert seeded_db.cadence.get_loop_by_source("meeting_action", "a1").status == "closed"


def test_killed_loop_not_resurrected_by_collect(seeded_db: Database):
    LoopCollector(seeded_db).collect(now=NOW)
    loop = seeded_db.cadence.get_loop_by_source("meeting_action", "a1")
    seeded_db.cadence.set_status(loop.id, "killed")
    LoopCollector(seeded_db).collect(now=NOW)
    assert seeded_db.cadence.get_loop_by_source("meeting_action", "a1").status == "killed"


def test_scores_are_persisted_and_ordered(seeded_db: Database):
    LoopCollector(seeded_db).collect(now=NOW)
    loops = seeded_db.cadence.list_loops()  # ordered by score desc
    assert loops[0].stale_score >= loops[-1].stale_score
    assert all(l.stale_score != 0 or l.needs_review for l in loops)
