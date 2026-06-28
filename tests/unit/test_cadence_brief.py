"""CAD-5 — the daily push brief: deterministic + optional LLM polish + the trigger."""
from __future__ import annotations

import io
from datetime import datetime
from pathlib import Path

import pytest

from holdspeak.cadence.brief import (
    build_brief,
    polish_headline,
    render_brief_markdown,
    render_brief_text,
    should_send_daily_brief,
)
from holdspeak.cadence.models import OpenLoop
from holdspeak.commands.cadence import run_cadence_command
from holdspeak.config import Config
from holdspeak.db import Database

NOW = datetime(2026, 6, 28, 9, 0, 0)


@pytest.fixture
def db(tmp_path: Path) -> Database:
    d = Database(tmp_path / "brief.db")
    d.cadence.upsert_loop(OpenLoop(source_type="proposal", source_id="p1",
                                   title="Create issue: watchdog", stale_score=16.0))
    d.cadence.upsert_loop(OpenLoop(source_type="meeting_action", source_id="a1",
                                   title="File the migration doc", owner="Karol", stale_score=12.0))
    d.cadence.upsert_loop(OpenLoop(source_type="meeting_action", source_id="a2",
                                   title="Low confidence thing", needs_review=True, stale_score=5.0))
    return d


def test_brief_leads_with_top_move_and_excludes_review(db):
    brief = build_brief(db, now=NOW)
    assert not brief.is_empty
    assert brief.items[0].loop.title == "Create issue: watchdog"  # highest score
    assert all(not it.loop.needs_review for it in brief.items)    # review loop excluded
    assert brief.headline == brief.items[0].next_action.title + "."
    assert brief.generated_by == "deterministic"


def test_brief_respects_limit(db):
    assert len(build_brief(db, now=NOW, limit=1).items) == 1


def test_empty_brief(tmp_path):
    d = Database(tmp_path / "empty.db")
    brief = build_brief(d, now=NOW)
    assert brief.is_empty and "Nothing pressing" in brief.headline


def test_polish_no_llm_is_identity(db):
    brief = build_brief(db, now=NOW)
    original = brief.headline
    assert polish_headline(brief, llm=None).headline == original


def test_polish_with_llm_rewrites_headline(db):
    brief = build_brief(db, now=NOW)
    polished = polish_headline(brief, llm=lambda p: "Ship the watchdog today — it's your top win.")
    assert polished.headline == "Ship the watchdog today — it's your top win."
    assert polished.generated_by == "llm"


def test_polish_is_fail_closed_on_llm_error(db):
    brief = build_brief(db, now=NOW)
    original = brief.headline
    def boom(_):
        raise RuntimeError("model unavailable")
    out = polish_headline(brief, llm=boom)
    assert out.headline == original and out.generated_by == "deterministic"


def test_render_markdown_and_text_contain_headline(db):
    brief = build_brief(db, now=NOW)
    md = render_brief_markdown(brief)
    txt = render_brief_text(brief)
    assert "Morning Push" in md and brief.headline in md and "watchdog" in md
    assert "Morning Push" in txt and "watchdog" in txt


def test_trigger_fires_once_per_day_after_earliest_hour():
    # before the earliest hour -> no
    assert should_send_daily_brief(datetime(2026, 6, 28, 6, 0), last_sent_date=None, earliest_hour=8) is False
    # after the hour, never sent today -> yes
    assert should_send_daily_brief(datetime(2026, 6, 28, 9, 0), last_sent_date=None, earliest_hour=8) is True
    # already sent today -> no
    assert should_send_daily_brief(datetime(2026, 6, 28, 9, 0), last_sent_date="2026-06-28", earliest_hour=8) is False
    # a new day -> yes again
    assert should_send_daily_brief(datetime(2026, 6, 29, 9, 0), last_sent_date="2026-06-28", earliest_hour=8) is True


def test_cli_brief(db):
    buf = io.StringIO()
    class A: cadence_action = "brief"; json = False
    rc = run_cadence_command(A(), stream=buf, db=db, config=Config())
    assert rc == 0 and "Morning Push" in buf.getvalue() and "watchdog" in buf.getvalue()
