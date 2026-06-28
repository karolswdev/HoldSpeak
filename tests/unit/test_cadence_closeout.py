"""CAD-6 — stale-loop escalation + the end-of-day closeout ritual."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.cadence.closeout import (
    apply_decision,
    build_closeout,
    escalation_severity,
    render_closeout_text,
)
from holdspeak.cadence.models import OpenLoop
from holdspeak.commands.cadence import run_cadence_command
from holdspeak.config import Config
from holdspeak.db import Database

NOW = datetime(2026, 6, 28, 18, 0, 0)


def _loop(**kw) -> OpenLoop:
    return OpenLoop(source_type=kw.pop("source_type", "meeting_action"),
                    source_id=kw.pop("source_id", "x"), title=kw.pop("title", "t"), **kw)


def test_escalation_by_nudge_count_and_age():
    assert escalation_severity(_loop(nudge_count=0), now=NOW) == "normal"
    assert escalation_severity(_loop(nudge_count=3), now=NOW) == "persistent"
    assert escalation_severity(_loop(nudge_count=6), now=NOW) == "escalated"
    old = _loop(created_at="2026-06-23T10:00:00")  # 5 days
    assert escalation_severity(old, now=NOW) == "escalated"
    assert escalation_severity(_loop(needs_review=True, nudge_count=9), now=NOW) == "quiet"


@pytest.fixture
def db(tmp_path: Path) -> Database:
    d = Database(tmp_path / "co.db")
    d.cadence.upsert_loop(_loop(source_id="p1", source_type="proposal", title="Approve me"))
    d.cadence.upsert_loop(_loop(source_id="a1", title="Owned fresh", owner="Karol"))
    d.cadence.upsert_loop(_loop(source_id="a2", title="Unowned old"))
    # the repo stamps created_at=now on insert; age the loop realistically for escalation
    with d._connection() as c:
        c.execute("UPDATE cadence_loops SET created_at = '2026-06-22T00:00:00' "
                  "WHERE source_id = 'a2'")
    return d


def test_closeout_recommends_per_loop(db):
    co = build_closeout(db, now=NOW)
    assert co.open_count == 3 and not co.is_empty
    by_title = {r.loop.title: r.action for r in co.recs}
    assert by_title["Approve me"] == "approve"
    assert by_title["Owned fresh"] == "snooze"   # fresh + owned -> not today
    assert by_title["Unowned old"] == "kill"     # escalated + unowned -> kill candidate
    assert "End-of-day" in render_closeout_text(co)


def test_apply_decision_lifecycle(db):
    loop = db.cadence.get_loop_by_source("meeting_action", "a1")
    assert apply_decision(db, loop.id, "snooze", now=NOW) is True
    assert db.cadence.get_loop(loop.id).status == "snoozed"
    assert apply_decision(db, loop.id, "delegate") is True
    assert db.cadence.get_loop(loop.id).status == "delegated"
    assert apply_decision(db, loop.id, "kill") is True
    assert db.cadence.get_loop(loop.id).status == "killed"


def test_apply_decision_rejects_unknown_action_and_missing(db):
    loop = db.cadence.get_loop_by_source("proposal", "p1")
    assert apply_decision(db, loop.id, "explode") is False  # not an applyable action
    assert apply_decision(db, "nope", "kill") is False      # missing loop


def test_empty_closeout(tmp_path):
    d = Database(tmp_path / "e.db")
    co = build_closeout(d, now=NOW)
    assert co.is_empty and "clear" in render_closeout_text(co).lower()


def test_cli_closeout(db):
    buf = io.StringIO()
    class A: cadence_action = "closeout"; json = False
    rc = run_cadence_command(A(), stream=buf, db=db, config=Config())
    assert rc == 0 and "End-of-day" in buf.getvalue()
