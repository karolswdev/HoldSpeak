#!/usr/bin/env python3
"""Phase 53 dogfood: prove activity pre-briefing works end to end, no mic/LLM.

Drives the real engine + the dictation-context override directly over a fresh
on-disk database:

  1. compute-cited-nudge: seed a prior meeting + two activity records inside its
     window -> the engine returns a windowed, source-cited nudge plus a
     source-cited per-record nudge, each naming its browser/profile + entity.
  2. dismissal-persists: dismiss the record nudge -> it stays gone, even across a
     fresh Database handle (new connection).
  3. activity-off-empty: turn the activity privacy toggle off -> no nudges.
  4. select-injects-context: select a record id -> the dictation context bundle
     pins it at records[0] and records the selected id (the default daily path is
     untouched when nothing is selected).

Run from anywhere:
    .venv/bin/python pm/roadmap/holdspeak/phase-53-activity-prebriefing/dogfood.py
"""
from __future__ import annotations

import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from holdspeak.activity_context import build_activity_context
from holdspeak.activity_nudges import compute_nudges
from holdspeak.db import Database

PASS = True


def check(label: str, cond: bool) -> None:
    global PASS
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    if not cond:
        PASS = False


def seed_meeting(db: Database, *, meeting_id: str, started_at: datetime, ended_at: datetime) -> None:
    conn = sqlite3.connect(str(db.db_path))
    try:
        conn.execute(
            "INSERT INTO meetings (id, started_at, ended_at, title, duration_seconds) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                meeting_id,
                started_at.isoformat(),
                ended_at.isoformat(),
                "Standup",
                (ended_at - started_at).total_seconds(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


print("== Phase 53 dogfood: activity pre-briefing ==\n")

now = datetime(2026, 6, 8, 14, 0, 0)
tmp = Path(tempfile.mkdtemp()) / "holdspeak.db"
db = Database(tmp)

# A prior meeting that ended 2h ago -> the "since your last meeting" window.
seed_meeting(db, meeting_id="m-prev", started_at=now - timedelta(hours=3), ended_at=now - timedelta(hours=2))

# Two records inside the window: a github issue (entity-typed) + a spec page.
issue = db.activity.upsert_activity_record(
    source_browser="safari",
    source_profile="work",
    url="https://github.com/karol/holdspeak/issues/53",
    title="Activity Pre-Briefing",
    entity_type="github_issue",
    entity_id="karol/holdspeak#53",
    visit_count=4,
    last_seen_at=now - timedelta(minutes=15),
)
db.activity.upsert_activity_record(
    source_browser="safari",
    source_profile="work",
    url="https://example.com/spec",
    title="Spec doc",
    last_seen_at=now - timedelta(minutes=45),
)

print("-- 1. compute a windowed, source-cited nudge from real activity --")
nudges = compute_nudges(db, now=now, limit=3)
check("the engine returned nudges", bool(nudges))
window = next((n for n in nudges if n.kind == "window"), None)
record = next((n for n in nudges if n.kind == "record"), None)
check("there is a windowed summary nudge", window is not None)
check(
    "the window cites the previous meeting as its lower bound",
    bool(window and window.extras.get("since_source") == "previous_meeting"),
)
check("the window counts both records", bool(window and window.window_record_count == 2))
check("the window is source-cited", bool(window and window.citations))
check("there is a per-record nudge", record is not None)
check(
    "the record nudge names its browser/profile + entity",
    bool(
        record
        and record.citations
        and record.citations[0].source_browser == "safari"
        and record.citations[0].source_profile == "work"
        and record.citations[0].entity_id == "karol/holdspeak#53"
    ),
)

print("\n-- 2. a dismissed nudge stays dismissed (across a fresh handle) --")
assert record is not None
db.activity.dismiss_nudge(record.key)
after = compute_nudges(db, now=now, limit=3)
check("the dismissed nudge does not return", record.key not in {n.key for n in after})
reopened = Database(tmp)  # new connection, same file
again = compute_nudges(reopened, now=now, limit=3)
check("dismissal persists across a fresh Database handle", record.key not in {n.key for n in again})

print("\n-- 3. activity off -> no nudges --")
db.activity.update_activity_privacy_settings(enabled=False)
check("the engine returns nothing when activity is off", compute_nudges(db, now=now) == [])
db.activity.update_activity_privacy_settings(enabled=True)  # restore for step 4

print("\n-- 4. selecting a record injects it into the dictation context --")
default_bundle = build_activity_context(db=db, limit=20)
check(
    "the default daily path selects nothing (byte-identical)",
    default_bundle.selected_record_id is None,
)
selected = build_activity_context(db=db, limit=20, selected_record_id=issue.id)
check("the selected record id is recorded on the bundle", selected.selected_record_id == issue.id)
check("the selected record is pinned at records[0]", bool(selected.records) and selected.records[0]["id"] == issue.id)
check(
    "the pinned record carries its entity citation",
    bool(selected.records) and selected.records[0]["entity_id"] == "karol/holdspeak#53",
)

print()
print("RESULT: PASS" if PASS else "RESULT: FAIL")
sys.exit(0 if PASS else 1)
