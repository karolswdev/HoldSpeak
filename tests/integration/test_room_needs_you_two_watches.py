"""Owner, 2026-10-25: a Project with two Jira Watches that read the same
issues showed every overdue issue twice in the Room's NEEDS YOU (26 rows for
13 issues). One entity is one row; the count is the number of things.

Run:
    HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider \\
        tests/integration/test_room_needs_you_two_watches.py
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from holdspeak.db.core import Database
from holdspeak.services.project_service import ProjectService


def _seed_jira_watch(db: Database, project_id: str, watch_id: str, name: str, issues: list[dict]) -> None:
    recent = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)).isoformat()
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, created_at, updated_at) "
            "VALUES (?, 'jira', 'issues', ?, ?, ?, 1, ?, NULL, ?, datetime('now'), datetime('now'))",
            (watch_id, name, json.dumps({"project": "SAM1"}), json.dumps(issues), recent, project_id),
        )


def test_two_watches_reading_the_same_issues_make_one_row_each(tmp_path):
    db = Database(tmp_path / "room.db")
    db.projects.create_project(project_id="awesome", name="Awesomeness")
    due = (datetime.now(timezone.utc) - timedelta(days=48)).date().isoformat()
    issues = [
        {"key": "SAM1-7", "id": "SAM1-7", "summary": "Update benefits documentation", "due_at": due,
         "url": "https://example.atlassian.net/browse/SAM1-7"},
        {"key": "SAM1-13", "id": "SAM1-13", "summary": "Monitor employee feedback", "due_at": due,
         "url": "https://example.atlassian.net/browse/SAM1-13"},
    ]
    _seed_jira_watch(db, "awesome", "watch_risk", "Jira due risk", issues)
    _seed_jira_watch(db, "awesome", "watch_flow", "Jira delivery flow", issues)

    needs = ProjectService(db)._read_room_needs_you("awesome")
    titles = [row["title"] for row in needs["items"]]

    assert titles == ["SAM1-7 Update benefits documentation", "SAM1-13 Monitor employee feedback"]
    assert needs["count"] == 2
    # The kept row still names every Watch that read it (the Watch order is
    # the store's, so the kept one is whichever came first).
    first = needs["items"][0]
    assert first["watchId"] in {"watch_risk", "watch_flow"}
    assert sorted(first["watchIds"]) == ["watch_flow", "watch_risk"]
    assert first["watchIds"][0] == first["watchId"]


def test_fold_keeps_rows_without_an_entity():
    rows = [
        {"source": "delta", "title": "1 proposal waiting"},
        {"source": "delta", "title": "1 proposal waiting"},
        {"source": "jira", "entity_id": "SAM1-1", "title": "SAM1-1 A", "watchId": "w1"},
        {"source": "github", "entity_id": "SAM1-1", "title": "#1 A", "watchId": "w2"},
    ]
    folded = ProjectService._fold_watch_duplicates(rows)
    assert [r["title"] for r in folded] == ["1 proposal waiting", "1 proposal waiting", "SAM1-1 A", "#1 A"]
