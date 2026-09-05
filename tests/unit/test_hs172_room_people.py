"""HS-172-07 -- Room People service unit tests.

Verifies:
  - resolved identities with non-zero counts appear
  - unresolved identities are excluded (no UNKNOWN rows)
  - counts are correct per identity
  - no raw login leaks into the payload
  - no writes
  - display_name is shown as stored (no derivation)
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db import Database
from holdspeak.services.project_service import ProjectService
from holdspeak.services.room_people_service import room_people, _extract_identities


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture()
def db(tmp_path):
    db = Database(tmp_path / "test.db")
    return db


@pytest.fixture()
def project_service(db):
    from holdspeak.db import get_observer
    return ProjectService(db, observer=get_observer())


def _seed_project(db: Database, project_id: str = "proj-1", name: str = "Q4 Platform") -> str:
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO projects "
            "(id, name, description, keywords_json, team_members_json, "
            "context_json, detection_threshold, is_archived, revision, "
            "target_at, created_at, updated_at) "
            "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, 1, NULL, "
            "'2026-09-01T00:00:00', '2026-09-05T10:00:00')",
            (project_id, name),
        )
    return project_id


def _seed_watch(
    db: Database,
    project_id: str,
    watch_id: str,
    connector_id: str = "gh",
    query_kind: str = "pull_requests",
    query: dict | None = None,
    snapshot: list[dict[str, Any]] | None = None,
) -> None:
    with db._connection() as conn:
        conn.execute(
            "INSERT INTO connector_watches "
            "(id, connector_id, query_kind, name, query_json, snapshot_json, "
            " enabled, last_success_at, last_error, project_id, "
            " created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'), NULL, ?, "
            "datetime('now'), datetime('now'))",
            (
                watch_id,
                connector_id,
                query_kind,
                f"{connector_id} {query_kind}",
                json.dumps(query or {}, sort_keys=True),
                json.dumps(snapshot or []),
                project_id,
            ),
        )


def _make_people_service(relationships: list[dict[str, Any]]) -> MagicMock:
    """Create a mock people_service with resolve_relationship_by_watch_identity."""
    svc = MagicMock()
    alias_map: dict[str, dict[str, Any]] = {}
    for rel in relationships:
        for alias in rel.get("owner_aliases", []):
            alias_map[alias.lower()] = rel
        if rel.get("display_name"):
            alias_map[rel["display_name"].lower()] = rel

    def resolve(identity: str) -> dict[str, Any]:
        key = identity.lower().strip()
        rel = alias_map.get(key)
        if rel:
            return {"state": "ready", "relationship": {
                "id": rel["id"],
                "display_name": rel["display_name"],
            }}
        return {"state": "ready", "relationship": None}

    svc.resolve_relationship_by_watch_identity = resolve
    return svc


# ── Tests ─────────────────────────────────────────────────────────


class TestRoomPeopleResolved:
    """Resolved identities with non-zero counts appear."""

    def test_github_pr_reviewer_resolved(self, db, project_service):
        pid = _seed_project(db, "proj-gh")
        _seed_watch(db, pid, "w1", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        {"number": 1, "title": "feat A", "state": "OPEN",
                         "reviewRequests": ["ania-dev"], "updatedAt": "2026-09-04T10:00:00"},
                        {"number": 2, "title": "feat B", "state": "OPEN",
                         "reviewRequests": ["ania-dev"], "updatedAt": "2026-09-04T11:00:00"},
                    ])
        people = _make_people_service([
            {"id": "rel-1", "display_name": "Ania Kowalska", "owner_aliases": ["ania-dev"]},
        ])
        result = room_people(project_service, people, pid)
        assert len(result) == 1
        assert result[0]["relationship_id"] == "rel-1"
        assert result[0]["display_name"] == "Ania Kowalska"
        assert result[0]["prs_waiting"] == 2

    def test_jira_assignee_resolved(self, db, project_service):
        pid = _seed_project(db, "proj-jira")
        _seed_watch(db, pid, "w2", connector_id="jira", query_kind="issues",
                    query={"projects": ["GOV"]},
                    snapshot=[
                        {"key": "GOV-1", "summary": "task A", "assignee": "Marek",
                         "due_at": "2026-09-01"},
                        {"key": "GOV-2", "summary": "task B", "assignee": "Marek"},
                    ])
        people = _make_people_service([
            {"id": "rel-2", "display_name": "Marek Kubiak", "owner_aliases": ["Marek"]},
        ])
        result = room_people(project_service, people, pid)
        assert len(result) == 1
        assert result[0]["display_name"] == "Marek Kubiak"
        assert result[0].get("assignments_open", 0) == 2
        assert result[0].get("assignments_overdue", 0) == 1  # GOV-1 due in past

    def test_multiple_people_sorted(self, db, project_service):
        pid = _seed_project(db, "proj-multi")
        _seed_watch(db, pid, "w3", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        {"number": 1, "title": "feat", "state": "OPEN",
                         "reviewRequests": ["zebra-dev"], "updatedAt": "2026-09-04T10:00:00"},
                        {"number": 2, "title": "fix", "state": "OPEN",
                         "reviewRequests": ["alpha-dev"], "updatedAt": "2026-09-04T10:00:00"},
                    ])
        people = _make_people_service([
            {"id": "rel-z", "display_name": "Zebra Person", "owner_aliases": ["zebra-dev"]},
            {"id": "rel-a", "display_name": "Alpha Person", "owner_aliases": ["alpha-dev"]},
        ])
        result = room_people(project_service, people, pid)
        assert len(result) == 2
        # Sorted by display_name
        assert result[0]["display_name"] == "Alpha Person"
        assert result[1]["display_name"] == "Zebra Person"


class TestRoomPeopleUnresolved:
    """Unresolved identities are excluded (no UNKNOWN rows)."""

    def test_unresolved_excluded(self, db, project_service):
        pid = _seed_project(db, "proj-unresolved")
        _seed_watch(db, pid, "w4", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        {"number": 1, "title": "feat", "state": "OPEN",
                         "reviewRequests": ["unknown-dev"], "updatedAt": "2026-09-04T10:00:00"},
                    ])
        people = _make_people_service([])  # no relationships
        result = room_people(project_service, people, pid)
        assert len(result) == 0

    def test_no_raw_login_in_payload(self, db, project_service):
        pid = _seed_project(db, "proj-no-login")
        _seed_watch(db, pid, "w5", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        {"number": 1, "title": "feat", "state": "OPEN",
                         "reviewRequests": ["secret-login"], "updatedAt": "2026-09-04T10:00:00"},
                    ])
        people = _make_people_service([
            {"id": "rel-3", "display_name": "Real Name", "owner_aliases": ["secret-login"]},
        ])
        result = room_people(project_service, people, pid)
        # The raw login must NEVER appear
        payload_str = json.dumps(result)
        assert "secret-login" not in payload_str
        assert result[0]["display_name"] == "Real Name"


class TestRoomPeopleCounts:
    """Counts are correct per identity."""

    def test_zero_counts_excluded(self, db, project_service):
        """A person with all zero counts is excluded entirely."""
        pid = _seed_project(db, "proj-zero")
        _seed_watch(db, pid, "w6", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        # Closed PR: does not count
                        {"number": 1, "title": "old", "state": "CLOSED",
                         "reviewRequests": ["dev-1"], "updatedAt": "2026-09-01T10:00:00"},
                    ])
        people = _make_people_service([
            {"id": "rel-4", "display_name": "Closed PR Person", "owner_aliases": ["dev-1"]},
        ])
        result = room_people(project_service, people, pid)
        assert len(result) == 0

    def test_mixed_pr_and_jira(self, db, project_service):
        """A person with both PR reviews and Jira assignments."""
        pid = _seed_project(db, "proj-mixed")
        _seed_watch(db, pid, "w7a", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        {"number": 1, "title": "feat", "state": "OPEN",
                         "reviewRequests": ["ania"], "updatedAt": "2026-09-04T10:00:00"},
                    ])
        _seed_watch(db, pid, "w7b", connector_id="jira", query_kind="issues",
                    query={"projects": ["GOV"]},
                    snapshot=[
                        {"key": "GOV-5", "summary": "task", "assignee": "ania"},
                    ])
        people = _make_people_service([
            {"id": "rel-5", "display_name": "Ania K", "owner_aliases": ["ania"]},
        ])
        result = room_people(project_service, people, pid)
        assert len(result) == 1
        assert result[0]["prs_waiting"] == 1
        assert result[0]["assignments_open"] == 1


class TestRoomPeopleNoWrites:
    """The service never writes."""

    def test_no_writes(self, db, project_service):
        pid = _seed_project(db, "proj-nowrite")
        _seed_watch(db, pid, "w8", connector_id="gh", query_kind="pull_requests",
                    query={"repository": "org/repo"},
                    snapshot=[
                        {"number": 1, "title": "feat", "state": "OPEN",
                         "reviewRequests": ["dev-x"], "updatedAt": "2026-09-04T10:00:00"},
                    ])
        people = _make_people_service([
            {"id": "rel-6", "display_name": "Dev X", "owner_aliases": ["dev-x"]},
        ])
        # Count writes before
        with db._connection() as conn:
            changes_before = conn.total_changes
        room_people(project_service, people, pid)
        with db._connection() as conn:
            changes_after = conn.total_changes
        assert changes_after == changes_before


class TestRoomPeopleNoPeopleService:
    """When people_service is None, returns empty."""

    def test_none_service(self, db, project_service):
        pid = _seed_project(db, "proj-none")
        result = room_people(project_service, None, pid)
        assert result == []
