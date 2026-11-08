"""One morning brief (2026-11-08): the CLI and MCP ``cadence.brief`` read the
day's brief; the Cadence push brief is parked."""
from __future__ import annotations

import io
import json

from holdspeak.cadence.models import OpenLoop
from holdspeak.commands.cadence import run_cadence_command
from holdspeak.config import CadenceConfig, Config
from holdspeak.db import Database
from holdspeak.services.cadence_service import CadenceService
from holdspeak.services.monday_brief_service import brief_lines, todays_brief


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "brief.db")
    db.cadence.upsert_loop(OpenLoop(source_type="proposal", source_id="p1",
                                    title="Create issue: watchdog", stale_score=16.0, priority="high"))
    return db


def test_the_days_brief_names_a_high_loop_and_is_made_once(tmp_path) -> None:
    db = _db(tmp_path)
    brief = todays_brief(db)
    assert any("watchdog" in line for line in brief_lines(brief))
    assert todays_brief(db).id == brief.id


def test_the_cli_prints_the_days_brief(tmp_path) -> None:
    db = _db(tmp_path)
    buf = io.StringIO()

    class A:
        cadence_action = "brief"
        json = True

    assert run_cadence_command(A(), stream=buf, db=db, config=Config()) == 0
    out = json.loads(buf.getvalue())
    assert out["id"] == todays_brief(db).id and any("watchdog" in line for line in out["lines"])


def test_the_mcp_cadence_brief_is_the_days_brief(tmp_path) -> None:
    db = _db(tmp_path)
    payload = CadenceService(db, CadenceConfig()).brief(None)
    assert payload["id"] == todays_brief(db).id and payload["egress"]["scope"] == "local"
