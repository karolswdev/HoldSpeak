"""Unit tests for the activity pre-briefing nudge engine (HS-53-01)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from holdspeak.activity_nudges import (
    Nudge,
    NudgeCitation,
    compute_nudges,
)
from holdspeak.db import Database


def _seed_meeting(
    db: Database,
    *,
    meeting_id: str,
    started_at: datetime,
    ended_at: datetime | None,
    title: str = "Standup",
) -> None:
    """Seed a meeting row directly — tests don't need the full MeetingState path."""
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            """
            INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                meeting_id,
                started_at.isoformat(),
                ended_at.isoformat() if ended_at else None,
                title,
                ((ended_at - started_at).total_seconds() if ended_at else 0),
            ),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def db(tmp_path: Path) -> Database:
    return Database(tmp_path / "holdspeak.db")


@pytest.fixture
def now() -> datetime:
    return datetime(2026, 6, 8, 14, 0, 0)


def test_engine_returns_empty_when_activity_off(db: Database, now: datetime) -> None:
    db.activity.update_activity_privacy_settings(enabled=False)
    db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/karol/holdspeak/issues/53",
        title="Activity Pre-Briefing",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        last_seen_at=now - timedelta(minutes=15),
    )

    assert compute_nudges(db, now=now) == []


def test_engine_uses_previous_meeting_ended_at_as_window(
    db: Database, now: datetime
) -> None:
    _seed_meeting(
        db,
        meeting_id="m-prev",
        started_at=now - timedelta(hours=3),
        ended_at=now - timedelta(hours=2),
    )
    db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url="https://github.com/karol/holdspeak/issues/53",
        title="Activity Pre-Briefing",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        last_seen_at=now - timedelta(minutes=15),
    )
    db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="default",
        url="https://example.com/spec",
        title="Spec doc",
        last_seen_at=now - timedelta(minutes=45),
    )

    nudges = compute_nudges(db, now=now, limit=3)

    assert nudges, "engine should produce nudges when records are inside the window"
    window = next((n for n in nudges if n.kind == "window"), None)
    assert window is not None
    assert window.key == f"window:{(now - timedelta(hours=2)).isoformat(timespec='seconds')}"
    assert window.extras["since_source"] == "previous_meeting"
    assert window.window_record_count == 2
    assert window.citations  # source-cited


def test_engine_falls_back_to_recent_window_without_prior_meeting(
    db: Database, now: datetime
) -> None:
    db.activity.upsert_activity_record(
        source_browser="firefox",
        url="https://example.com/a",
        title="A",
        last_seen_at=now - timedelta(hours=2),
    )
    db.activity.upsert_activity_record(
        source_browser="firefox",
        url="https://example.com/b",
        title="B",
        last_seen_at=now - timedelta(hours=5),
    )

    nudges = compute_nudges(db, now=now)
    window = next((n for n in nudges if n.kind == "window"), None)
    assert window is not None
    assert window.extras["since_source"] == "recent_window"


def test_record_nudges_carry_source_citation(db: Database, now: datetime) -> None:
    record = db.activity.upsert_activity_record(
        source_browser="safari",
        source_profile="work",
        url="https://github.com/karol/holdspeak/issues/53",
        title="Activity Pre-Briefing",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        visit_count=4,
        last_seen_at=now - timedelta(minutes=15),
    )

    nudges = compute_nudges(db, now=now)
    record_nudges = [n for n in nudges if n.kind == "record"]
    assert record_nudges
    rn = record_nudges[0]
    assert rn.key == f"record:{record.id}"
    citation = rn.citations[0]
    assert citation.record_id == record.id
    assert citation.source_browser == "safari"
    assert citation.source_profile == "work"
    assert citation.entity_type == "github_issue"
    assert citation.entity_id == "karol/holdspeak#53"
    assert citation.last_seen_at is not None
    assert citation.visit_count == 4


def test_dismissed_nudge_stays_dismissed(db: Database, now: datetime) -> None:
    record = db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/karol/holdspeak/issues/53",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        last_seen_at=now - timedelta(minutes=10),
    )
    key = f"record:{record.id}"
    db.activity.dismiss_nudge(key)

    keys = {n.key for n in compute_nudges(db, now=now)}
    assert key not in keys

    # Dismissal persists across a fresh Database handle (new connection).
    same = Database(db.db_path)
    keys2 = {n.key for n in compute_nudges(same, now=now)}
    assert key not in keys2


def test_weak_signal_records_do_not_become_nudges(
    db: Database, now: datetime
) -> None:
    # A page-type record from > 3 days ago should not score above the floor.
    db.activity.upsert_activity_record(
        source_browser="firefox",
        url="https://example.com/old",
        title="Stale page",
        visit_count=1,
        last_seen_at=now - timedelta(days=5),
    )
    nudges = compute_nudges(db, now=now)
    # Outside the recent_window fallback (24h) → no records visible at all.
    assert [n for n in nudges if n.kind == "record"] == []


def test_relevance_ordering_prefers_entity_typed_recent(
    db: Database, now: datetime
) -> None:
    # A bare page seen 20h ago: low score (recency only).
    page = db.activity.upsert_activity_record(
        source_browser="firefox",
        url="https://example.com/article",
        title="An article",
        visit_count=1,
        last_seen_at=now - timedelta(hours=20),
    )
    # A github issue seen 1h ago: high recency + entity bonus.
    issue = db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/karol/holdspeak/issues/53",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        last_seen_at=now - timedelta(hours=1),
    )

    nudges = compute_nudges(db, now=now, limit=3)
    record_nudges = [n for n in nudges if n.kind == "record"]
    assert record_nudges[0].key == f"record:{issue.id}"
    # The page may or may not appear (lower score), but issue is first.
    assert any(n.key == f"record:{issue.id}" for n in record_nudges)


def test_project_match_boosts_score(db: Database, now: datetime) -> None:
    db.projects.create_project(project_id="proj-1", name="Project One")
    unmatched = db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://example.com/other",
        title="Other",
        last_seen_at=now - timedelta(hours=2),
    )
    matched = db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://example.com/proj",
        title="Proj",
        last_seen_at=now - timedelta(hours=2),
        project_id="proj-1",
    )

    nudges = compute_nudges(db, project_id="proj-1", now=now, limit=3)
    record_nudges = [n for n in nudges if n.kind == "record"]
    assert record_nudges
    # The project-matched record must outrank or equal the unmatched one.
    assert record_nudges[0].key == f"record:{matched.id}"


def test_limit_cap_is_respected(db: Database, now: datetime) -> None:
    for i in range(8):
        db.activity.upsert_activity_record(
            source_browser="safari",
            url=f"https://github.com/k/h/issues/{i}",
            entity_type="github_issue",
            entity_id=f"k/h#{i}",
            last_seen_at=now - timedelta(minutes=10 + i),
        )

    nudges = compute_nudges(db, now=now, limit=3)
    assert len(nudges) == 3


def test_nudge_serialization_is_jsonable(db: Database, now: datetime) -> None:
    db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/k/h/issues/1",
        entity_type="github_issue",
        entity_id="k/h#1",
        last_seen_at=now - timedelta(minutes=10),
    )
    nudges = compute_nudges(db, now=now)
    assert nudges
    payload = [n.to_dict() for n in nudges]
    # Keys present and stable.
    assert {"key", "kind", "title", "body", "score", "citations"} <= set(payload[0])
    import json

    json.dumps(payload)  # must not raise
