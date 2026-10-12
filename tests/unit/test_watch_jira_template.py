"""HS-167-06 unit tests for walk-discovered defects.

(a) Jira blockers template: the "Blocked" status in query_defaults
    breaks the JQL on Jira projects that do not have that status.
    Fix: removed blocked_statuses from the template's query_defaults
    (the rule's entered_state clause matches client-side).

(b) Accept verb on conflict proposals: the decide_proposal route
    correctly returns 400 for conflict-kind proposals (HANDLER_MAP
    entry "refuse"). This is not a defect -- the runner must pick
    an acceptable proposal kind.

(c) Room projection: lifecycle and revision live under the room
    endpoint's top-level and project keys, not the flat project GET.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "test-167-06")


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    _db = Database(tmp_path / "test-167-06.db")
    yield _db
    _db.close()
    reset_database()


# ── (a) Jira blockers template no longer emits blocked_statuses JQL ─


class TestBlockersTemplateNoBlockedStatuses:
    """The watch.jira.blockers template must NOT include
    blocked_statuses in its query_defaults, because the status name
    "Blocked" is project-specific and breaks JQL on boards without it.

    The rule's entered_state clause for "Blocked" matches client-side
    (in the snapshot diff), so the JQL filter is not needed for
    correctness -- it only narrowed the snapshot fetch.
    """

    def test_blockers_template_query_defaults_no_blocked_statuses(self):
        from holdspeak.jira_templates import JIRA_TEMPLATES

        blockers_tmpl = None
        for t in JIRA_TEMPLATES:
            if t.template_id == "watch.jira.blockers":
                blockers_tmpl = t
                break
        assert blockers_tmpl is not None, "watch.jira.blockers template not found"

        # The template's query_defaults must NOT contain blocked_statuses.
        assert "blocked_statuses" not in blockers_tmpl.query_defaults, (
            f"watch.jira.blockers template still has blocked_statuses "
            f"in query_defaults: {blockers_tmpl.query_defaults}"
        )

    def test_compile_jql_skips_empty_blocked_statuses(self):
        """_compile_jql with an empty blocked_statuses list produces
        no status clause (the guard: `if blocked:`)."""
        from holdspeak.services.watch_sources import _compile_jql

        query = {
            "projects": ["KAN"],
            "status_categories": ["indeterminate", "new"],
            "blocked_statuses": [],
        }
        jql = _compile_jql(query)
        assert "status in" not in jql.lower(), (
            f"Empty blocked_statuses should not produce status clause: {jql}"
        )
        # But status_categories should still be present
        assert "statusCategory" in jql, f"Missing statusCategory clause: {jql}"

    def test_compile_jql_no_blocked_key_at_all(self):
        """_compile_jql without blocked_statuses key produces no status clause."""
        from holdspeak.services.watch_sources import _compile_jql

        query = {
            "projects": ["KAN"],
            "status_categories": ["indeterminate", "new"],
        }
        jql = _compile_jql(query)
        assert "status in" not in jql.lower(), (
            f"Missing blocked_statuses should not produce status clause: {jql}"
        )


# ── (b) Conflict proposals refuse accept (400) ─────────────────────


class TestConflictProposalRefusesAccept:
    """A proposal with proposal_kind='conflict' MUST refuse the accept
    verb with a ValidationError (code='capability'), surfaced as 400
    by the route. This is by design (HANDLER_MAP: 'refuse')."""

    def test_handler_map_conflict_refuses(self):
        from holdspeak.services.project_delta_service import HANDLER_MAP
        assert HANDLER_MAP["conflict"] == "refuse", (
            f"HANDLER_MAP['conflict'] should be 'refuse', "
            f"got {HANDLER_MAP['conflict']!r}"
        )

    def test_decide_accept_on_conflict_raises_validation(self, db):
        """Exercise the decide_proposal code path with a conflict-kind
        proposal and verb=accept. Expects ValidationError with code='capability'."""
        from holdspeak.services.project_delta_service import ProjectDeltaService
        from holdspeak.services.errors import ValidationError

        # collector is unused by decide_proposal; a None suffices.
        svc = ProjectDeltaService(db, collector=None)

        # Create a minimal project (room fields are columns on projects table)
        now_iso = datetime.now(timezone.utc).isoformat()
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, lifecycle, revision, "
                "created_at, updated_at) "
                "VALUES (?, ?, 'active', 1, ?, ?)",
                ("proj_test167b", "Test Project", now_iso, now_iso),
            )

        # Create a conflict-kind proposal through the DB
        review_id = "prev_test167b"
        proposal_id = "pprop_test167b_conflict"
        with db._connection() as conn:
            # Insert a review
            conn.execute(
                "INSERT INTO project_reviews "
                "(id, project_id, status, from_sequence, "
                "through_sequence, opened_at, source_manifest_json) "
                "VALUES (?, ?, 'open', 0, 0, ?, '{}')",
                (review_id, "proj_test167b", now_iso),
            )
            # Insert a conflict proposal
            conn.execute(
                "INSERT INTO project_proposals "
                "(id, project_id, review_window_key, proposal_kind, "
                "lifecycle, title, rationale, patch_json, "
                "materiality, created_at) "
                "VALUES (?, ?, ?, 'conflict', 'open', 'Test conflict', "
                "'{}', '{}', '0.5', ?)",
                (proposal_id, "proj_test167b", review_id, now_iso),
            )

        with pytest.raises(ValidationError) as exc_info:
            svc.decide_proposal(
                OWNER, "proj_test167b", proposal_id, "accept",
            )
        assert exc_info.value.code == "capability"

    def test_observation_attention_accepts(self, db):
        """An observation_attention proposal CAN be accepted (record_only handler)."""
        from holdspeak.services.project_delta_service import HANDLER_MAP
        assert HANDLER_MAP["observation_attention"] == "record_only"


# ── (c) Room projection shape ──────────────────────────────────────


class TestRoomProjectionShape:
    """The room() method returns lifecycle and revision at known paths."""

    def test_room_returns_lifecycle_and_revision(self, db):
        from holdspeak.services.project_service import ProjectService

        svc = ProjectService(db)

        # Create a project (room fields are columns on the projects table)
        now_iso = datetime.now(timezone.utc).isoformat()
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, lifecycle, revision, "
                "created_at, updated_at) "
                "VALUES (?, ?, 'active', 3, ?, ?)",
                ("proj_test167c", "Room Test", now_iso, now_iso),
            )

        room = svc.room(OWNER, "proj_test167c")

        # revision is a top-level key
        assert room["revision"] == 3, (
            f"Room revision should be 3, got {room.get('revision')}"
        )

        # lifecycle is under room["project"]["lifecycle"]
        assert room["project"]["lifecycle"] == "active", (
            f"Room lifecycle should be 'active', "
            f"got {room.get('project', {}).get('lifecycle')}"
        )
