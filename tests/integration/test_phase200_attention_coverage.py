"""HS-200-07 (C4) — coverage over the REAL services.

Real Database, real ProjectService Room reads, real MondayBriefService:
a Room whose needs-you read fails leaves a coverage record with its
repair path, its last-known items survive, and the brief says what was
not observed instead of "Nothing material changed."

Run:
    HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider \\
        tests/integration/test_phase200_attention_coverage.py
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from holdspeak.db.core import Database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.monday_brief_service import MondayBriefService
from holdspeak.services.needs_you_aggregate import LastKnownStore, build_aggregate
from holdspeak.services.project_service import ProjectService

OWNER = Principal(PrincipalKind.OWNER, "test")


def _seed_projects(db: Database) -> None:
    db.projects.create_project(project_id="alpha", name="Q4 Platform")
    db.projects.create_project(project_id="beta", name="Governance")


def _seed_watch(
    db: Database, project_id: str, watch_id: str, *,
    last_error: str | None = None,
    last_success_at: str | None = None,
    snapshot: list[dict[str, Any]] | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, 'gh', 'pull_requests', 'gh pull_requests', ?, ?, 1, ?, ?, ?, "
            " datetime('now'), datetime('now'))",
            (
                watch_id,
                json.dumps({"repository": "karolswdev/HoldSpeak"}, sort_keys=True),
                json.dumps(snapshot or []),
                last_success_at,
                last_error,
                project_id,
            ),
        )


def _seed_owner_login(db: Database, login: str = "karolswdev") -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', ?, 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
            (login,),
        )


def test_real_rooms_report_coverage_and_a_failed_room_keeps_its_items(tmp_path):
    db = Database(tmp_path / "coverage.db")
    _seed_projects(db)
    _seed_owner_login(db)
    # connector_watches stores NAIVE UTC (project_service.aware_iso).
    recent = (datetime.now(timezone.utc).replace(tzinfo=None)
              - timedelta(minutes=10)).isoformat()
    _seed_watch(db, "alpha", "w-alpha", last_success_at=recent, snapshot=[
        {"number": 612, "title": "Rig settles animations",
         "state": "OPEN", "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
         "reviewRequests": ["karolswdev"], "updatedAt": recent},
    ])
    _seed_watch(db, "beta", "w-beta", last_success_at=recent)

    service = ProjectService(db)
    memory = LastKnownStore()
    healthy = build_aggregate(
        list_projects=service.list_projects, room=service.room,
        principal=OWNER, last_known=memory,
    )

    assert healthy["complete"] is True, healthy["coverage"]
    states = {row["source_id"]: row["state"] for row in healthy["coverage"]}
    assert states["project:alpha"] == "available"
    assert states["project:beta"] == "available"
    assert states["watch:w-alpha"] == "available"
    assert healthy["count"] == 1, healthy["items"]
    known_id = healthy["items"][0]["id"]

    # ── the real Room read for beta now fails; alpha stays healthy ──
    original = ProjectService._read_room_needs_you

    def failing(self, project_id: str):
        if project_id == "beta":
            raise RuntimeError("connector table locked")
        return original(self, project_id)

    ProjectService._read_room_needs_you = failing  # type: ignore[method-assign]
    try:
        partial = build_aggregate(
            list_projects=service.list_projects, room=service.room,
            principal=OWNER, last_known=memory,
        )
    finally:
        ProjectService._read_room_needs_you = original  # type: ignore[method-assign]

    assert partial["complete"] is False
    beta = {row["source_id"]: row for row in partial["coverage"]}["project:beta"]
    assert beta["state"] == "failed"
    assert beta["reason"] == "needsYou_read_failed"
    assert beta["repair"]["verb"] == "Retry"
    # alpha's item is still there, still counted, still traceable by id.
    assert [item["id"] for item in partial["items"]] == [known_id]


def test_a_cant_check_watch_is_a_failed_source_with_reconnect(tmp_path):
    db = Database(tmp_path / "coverage.db")
    db.projects.create_project(project_id="alpha", name="Q4 Platform")
    _seed_watch(db, "alpha", "w-alpha", last_error="401 Bad credentials")

    service = ProjectService(db)
    agg = build_aggregate(
        list_projects=service.list_projects, room=service.room,
        principal=OWNER, last_known=LastKnownStore(),
    )

    row = {r["source_id"]: r for r in agg["coverage"]}["watch:w-alpha"]
    assert row["state"] == "failed"
    assert row["kind"] == "watch"
    assert row["repair"] == {"token": "CANT CHECK", "verb": "Reconnect",
                             "href": "/settings"}
    assert agg["complete"] is False


def test_the_brief_names_what_was_not_observed(tmp_path):
    db = Database(tmp_path / "coverage.db")
    _seed_projects(db)
    original = ProjectService._read_room_needs_you

    def failing(self, project_id: str):
        if project_id == "beta":
            raise RuntimeError("connector table locked")
        return original(self, project_id)

    ProjectService._read_room_needs_you = failing  # type: ignore[method-assign]
    try:
        brief = MondayBriefService(db).generate(OWNER)
    finally:
        ProjectService._read_room_needs_you = original  # type: ignore[method-assign]

    waiting = brief.sections["waiting"]
    gaps = [item for item in waiting if item.source_ref.startswith("coverage:")]
    assert gaps, [item.text for item in waiting]
    assert gaps[0].text == "Not observed: Governance"
    assert "READ FAILED" in (gaps[0].detail or "")
    assert brief.headline != "Nothing material changed.", brief.headline


def test_a_healthy_desk_adds_no_coverage_rows_to_the_brief(tmp_path):
    db = Database(tmp_path / "coverage.db")
    _seed_projects(db)

    brief = MondayBriefService(db).generate(OWNER)

    assert not [i for i in brief.sections["waiting"]
                if i.source_ref.startswith("coverage:")]


def test_a_live_watch_checked_long_ago_is_stale_with_its_observed_time(tmp_path):
    db = Database(tmp_path / "coverage.db")
    db.projects.create_project(project_id="alpha", name="Q4 Platform")
    old = (datetime.now(timezone.utc).replace(tzinfo=None)
           - timedelta(hours=30)).isoformat()
    _seed_watch(db, "alpha", "w-alpha", last_success_at=old)

    service = ProjectService(db)
    agg = build_aggregate(
        list_projects=service.list_projects, room=service.room,
        principal=OWNER, last_known=LastKnownStore(),
    )

    row = {r["source_id"]: r for r in agg["coverage"]}["watch:w-alpha"]
    assert row["state"] == "stale"
    assert row["observed_at"], "a stale source still names when it was observed"
    assert row["repair"]["token"] == "STALE"
    assert agg["complete"] is False
