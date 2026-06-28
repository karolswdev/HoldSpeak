"""CAD-1-05 — the `holdspeak cadence` CLI."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from holdspeak.commands.cadence import run_cadence_command
from holdspeak.config import Config
from holdspeak.db import Database


class _Args:
    def __init__(self, action, **kw):
        self.cadence_action = action
        self.json = kw.get("json", False)
        self.all = kw.get("all", False)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    db = Database(tmp_path / "cli.db")
    with db._connection() as c:
        c.execute("INSERT INTO meetings (id, title, started_at, created_at) "
                  "VALUES ('m1','Standup','2026-06-27T14:00:00','2026-06-27T14:00:00')")
        c.execute("INSERT INTO action_items (id, meeting_id, task, owner, status, review_state, created_at) "
                  "VALUES ('a1','m1','File the issue','Karol','pending','reviewed','2026-06-26T10:00:00')")
    return db


def _run(action, db, **kw) -> str:
    buf = io.StringIO()
    rc = run_cadence_command(_Args(action, **kw), stream=buf, db=db, config=Config())
    assert rc == 0
    return buf.getvalue()


def test_run_now_works_with_cadence_disabled(db: Database):
    # Config() has cadence.enabled = False by default; run-now must still work.
    assert Config().cadence.enabled is False
    out = _run("run-now", db)
    assert "projected: 1" in out


def test_run_now_json_shape(db: Database):
    out = _run("run-now", db, json=True)
    data = json.loads(out)
    assert data["projected"] == 1 and "due" in data and "open_loops" in data


def test_loops_lists_by_staleness(db: Database):
    _run("run-now", db)  # project first
    out = _run("loops", db)
    assert "File the issue" in out


def test_loops_json_is_valid(db: Database):
    _run("run-now", db)
    data = json.loads(_run("loops", db, json=True))
    assert isinstance(data, list) and data[0]["title"] == "File the issue"


def test_status_reports_enabled_honestly(db: Database):
    out = _run("status", db)
    assert "enabled:        False" in out
