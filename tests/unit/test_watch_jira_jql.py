"""HS-168-05 unit tests for the Jira empty-string issue_types defect.

(a) _compile_jql with issue_types=[""] produces NO issuetype clause.
(b) The clarify_jira_scope -> finalize path with no type chosen stores
    issue_types == [] in the watch query_json (not [""]).
(c) The Test path and the evaluation path compile identical JQL for
    the same stored query spec.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.reaction_service import ReactionService

OWNER = Principal(PrincipalKind.OWNER, "test-168-05")


@pytest.fixture
def db(tmp_path: Path):
    reset_database()
    _db = Database(tmp_path / "test-168-05.db")
    yield _db
    _db.close()
    reset_database()


# ── (a) _compile_jql belt: blank entries ignored ───────────────────


class TestCompileJqlBlanks:
    """_compile_jql must ignore blank/whitespace-only entries in every
    list field so a stored [""] compiles to no clause."""

    def test_issue_types_empty_string_no_clause(self):
        from holdspeak.services.watch_sources import _compile_jql

        jql = _compile_jql({"projects": ["KAN"], "issue_types": [""]})
        assert "issuetype" not in jql.lower(), (
            f"issue_types=[''] must produce no issuetype clause, got: {jql}"
        )
        assert "project in" in jql.lower(), (
            f"projects clause should still be present, got: {jql}"
        )

    def test_issue_types_whitespace_only_no_clause(self):
        from holdspeak.services.watch_sources import _compile_jql

        jql = _compile_jql({"projects": ["KAN"], "issue_types": ["  ", "\t"]})
        assert "issuetype" not in jql.lower(), (
            f"issue_types with whitespace-only entries must produce no clause, got: {jql}"
        )

    def test_status_categories_empty_string_no_clause(self):
        from holdspeak.services.watch_sources import _compile_jql

        jql = _compile_jql({"projects": ["KAN"], "status_categories": [""]})
        assert "statusCategory" not in jql, (
            f"status_categories=[''] must produce no clause, got: {jql}"
        )

    def test_priorities_empty_string_no_clause(self):
        from holdspeak.services.watch_sources import _compile_jql

        jql = _compile_jql({"priorities": ["", " "]})
        assert "priority" not in jql.lower(), (
            f"priorities with blanks must produce no clause, got: {jql}"
        )

    def test_mixed_valid_and_blank_keeps_valid(self):
        from holdspeak.services.watch_sources import _compile_jql

        jql = _compile_jql({"issue_types": ["", "Task", " ", "Bug"]})
        assert "issuetype in" in jql.lower()
        assert "Bug" in jql
        assert "Task" in jql
        # The empty strings must NOT appear as quoted values
        assert '""' not in jql and "''" not in jql, (
            f"Blank entries must not appear in the clause, got: {jql}"
        )

    def test_owners_stored_query_no_issuetype_clause(self):
        """The owner's actual stored query_json with issue_types:['']
        must compile cleanly -- no issuetype clause, valid JQL."""
        from holdspeak.services.watch_sources import _compile_jql

        owner_query = {
            "connection_ref": "karolsaneapple.atlassian.net|karolsane+apple@gmail.com",
            "issue_types": [""],
            "projects": ["KAN"],
            "status_categories": ["indeterminate", "new"],
        }
        jql = _compile_jql(owner_query)
        assert "issuetype" not in jql.lower(), (
            f"Owner's stored query must produce no issuetype clause, got: {jql}"
        )
        assert "project in" in jql.lower()
        assert "statusCategory in" in jql


# ── (b) Wizard flow: no type chosen -> issue_types == [] ───────────


class TestNoTypeChosenStoresEmptyList:
    """When no issue type is toggled in the wizard, the finalized
    watch's query_json must have no issue_types key, or issue_types=[]."""

    def _fake_jira_adapter(self):
        class FakeJiraAdapter:
            def list_connections(self, principal):
                return [{"state": "connected",
                         "connection_ref": "a.atlassian.net|u@x.com",
                         "external_connection_ref": "a.atlassian.net|u@x.com"}]
            def discover(self, principal, ref, *, kind="projects"):
                return {"state": "ready",
                        "items": [{"key": "KAN", "name": "Kanban"}]}
            def validate_scope(self, principal, ref, project_key):
                return {"valid": True, "key": project_key}
            def search(self, principal, ref, *, jql="", limit=50, enrich=False):
                return {"items": [
                    {"key": "KAN-1", "summary": "Item", "status": "Open",
                     "issue_type": "Task", "updated_at": "2026-09-01T00:00:00Z"},
                ], "calls": 1}
        return FakeJiraAdapter()

    def test_clarify_with_empty_issue_types_stores_empty_list(self, db):
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService

        svc = ProjectSetupService(
            db,
            project_service=ProjectService(db),
            watch_service=None,
            jira_adapter=self._fake_jira_adapter(),
        )

        session = svc.start_setup(OWNER)
        sid = session["id"]
        svc.answer(OWNER, sid, "outcome", {"text": "Track Jira"})
        proposals = svc.suggest(OWNER, sid)
        jira_proposals = [p for p in proposals if p.get("provider_id") == "jira"]
        assert len(jira_proposals) > 0
        pid = jira_proposals[0]["id"]

        # Clarify with NO issue types (empty list -- the wizard default)
        result = svc.clarify_jira_scope(
            OWNER, sid, pid,
            connection_ref="a.atlassian.net|u@x.com",
            projects=["KAN"],
            issue_types=[],
        )
        assert result["scope_state"] == "scoped"

        # Read back the proposal spec and verify scope
        proposal = svc._require_proposal(pid, sid)
        spec = json.loads(proposal["spec"]) if isinstance(proposal["spec"], str) else proposal["spec"]
        scope_types = spec["subject"]["scope"].get("issue_types", [])
        assert scope_types == [], (
            f"scope.issue_types should be [] when no type chosen, got: {scope_types}"
        )

    def test_finalize_no_types_query_has_no_issue_types(self, db):
        """Full clarify -> select -> test -> finalize: the stored
        query_json must NOT contain issue_types when none were chosen."""
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService
        from holdspeak.services.watch_service import WatchService

        def fake_fetcher(principal, *, connector_id, query_kind, query):
            return [{"key": "KAN-1", "summary": "Item", "status": "Open",
                     "issue_type": "Task", "updated_at": "2026-09-01T00:00:00Z"}]

        watch_svc = WatchService(db, snapshot_fetcher=fake_fetcher)
        project_svc = ProjectService(db)
        svc = ProjectSetupService(
            db,
            project_service=project_svc,
            watch_service=watch_svc,
            jira_adapter=self._fake_jira_adapter(),
        )

        session = svc.start_setup(OWNER)
        sid = session["id"]
        svc.answer(OWNER, sid, "outcome", {"text": "Track Jira"})
        svc.answer(OWNER, sid, "signals", {"text": "Issues"})
        proposals = svc.suggest(OWNER, sid)
        jira_proposals = [p for p in proposals if p.get("provider_id") == "jira"]
        assert len(jira_proposals) > 0
        pid = jira_proposals[0]["id"]

        svc.select_proposal(OWNER, sid, pid)

        # Clarify with empty issue_types
        svc.clarify_jira_scope(
            OWNER, sid, pid,
            connection_ref="a.atlassian.net|u@x.com",
            projects=["KAN"],
            issue_types=[],
        )

        # Test
        svc.test_proposal(OWNER, sid, pid)

        # Finalize
        result = svc.finalize(OWNER, sid)
        activated = result.get("activated_watches", [])
        assert len(activated) >= 1, "Should activate at least one watch"

        # Read the stored query_json
        wid = activated[0]["watch_id"]
        watch = db.automations.get_watch(wid)
        query = watch.get("query", {})
        stored_types = query.get("issue_types", [])
        assert stored_types == [] or "issue_types" not in query, (
            f"No types chosen -> query_json should have no issue_types "
            f"or issue_types=[], got: {stored_types}"
        )


# ── (c) Test and evaluation compile identical JQL ──────────────────


class TestTestEvalParity:
    """The Test path and the evaluation path must compile the same JQL
    for the same stored spec, so a passing Test means a working Watch."""

    def _fake_jira_adapter(self):
        class FakeJiraAdapter:
            def list_connections(self, principal):
                return [{"state": "connected",
                         "connection_ref": "a.atlassian.net|u@x.com",
                         "external_connection_ref": "a.atlassian.net|u@x.com"}]
            def discover(self, principal, ref, *, kind="projects"):
                return {"state": "ready",
                        "items": [{"key": "KAN", "name": "Kanban"}]}
            def validate_scope(self, principal, ref, project_key):
                return {"valid": True, "key": project_key}
            def search(self, principal, ref, *, jql="", limit=50, enrich=False):
                self.last_jql = jql
                return {"items": [
                    {"key": "KAN-1", "summary": "Item", "status": "Open",
                     "issue_type": "Task", "updated_at": "2026-09-01T00:00:00Z"},
                ], "calls": 1}
        return FakeJiraAdapter()

    def test_test_jql_matches_evaluation_jql(self, db):
        """The JQL compiled by test_proposal must match what _compile_jql
        produces from the finalized query_json."""
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService
        from holdspeak.services.watch_service import WatchService
        from holdspeak.services.watch_sources import _compile_jql

        adapter = self._fake_jira_adapter()

        def fake_fetcher(principal, *, connector_id, query_kind, query):
            return [{"key": "KAN-1", "summary": "Item", "status": "Open",
                     "issue_type": "Task", "updated_at": "2026-09-01T00:00:00Z"}]

        watch_svc = WatchService(db, snapshot_fetcher=fake_fetcher)
        project_svc = ProjectService(db)
        svc = ProjectSetupService(
            db,
            project_service=project_svc,
            watch_service=watch_svc,
            jira_adapter=adapter,
        )

        session = svc.start_setup(OWNER)
        sid = session["id"]
        svc.answer(OWNER, sid, "outcome", {"text": "Track Jira issues"})
        svc.answer(OWNER, sid, "signals", {"text": "Issues and blocks"})
        proposals = svc.suggest(OWNER, sid)
        jira_proposals = [p for p in proposals if p.get("provider_id") == "jira"]
        assert len(jira_proposals) > 0
        pid = jira_proposals[0]["id"]

        svc.select_proposal(OWNER, sid, pid)

        # Clarify with issue_types=["Task"] (a real selection)
        svc.clarify_jira_scope(
            OWNER, sid, pid,
            connection_ref="a.atlassian.net|u@x.com",
            projects=["KAN"],
            issue_types=["Task"],
        )

        # Test -- capture the JQL the adapter received
        svc.test_proposal(OWNER, sid, pid)
        test_jql = adapter.last_jql

        # Finalize
        result = svc.finalize(OWNER, sid)
        activated = result.get("activated_watches", [])
        assert len(activated) >= 1

        # Read the stored query_json and compile it
        wid = activated[0]["watch_id"]
        watch = db.automations.get_watch(wid)
        query = watch.get("query", {})
        eval_jql = _compile_jql(query)

        assert test_jql == eval_jql, (
            f"Test JQL and evaluation JQL must be identical.\n"
            f"  Test JQL: {test_jql}\n"
            f"  Eval JQL: {eval_jql}"
        )

    def test_parity_with_empty_issue_types(self, db):
        """With issue_types=[], both paths compile the same JQL
        (no issuetype clause)."""
        from holdspeak.services.project_service import ProjectService
        from holdspeak.services.project_setup_service import ProjectSetupService
        from holdspeak.services.watch_service import WatchService
        from holdspeak.services.watch_sources import _compile_jql

        adapter = self._fake_jira_adapter()

        def fake_fetcher(principal, *, connector_id, query_kind, query):
            return [{"key": "KAN-1", "summary": "Item", "status": "Open",
                     "issue_type": "Task", "updated_at": "2026-09-01T00:00:00Z"}]

        watch_svc = WatchService(db, snapshot_fetcher=fake_fetcher)
        project_svc = ProjectService(db)
        svc = ProjectSetupService(
            db,
            project_service=project_svc,
            watch_service=watch_svc,
            jira_adapter=adapter,
        )

        session = svc.start_setup(OWNER)
        sid = session["id"]
        svc.answer(OWNER, sid, "outcome", {"text": "Track Jira"})
        svc.answer(OWNER, sid, "signals", {"text": "Issues"})
        proposals = svc.suggest(OWNER, sid)
        jira_proposals = [p for p in proposals if p.get("provider_id") == "jira"]
        assert len(jira_proposals) > 0
        pid = jira_proposals[0]["id"]

        svc.select_proposal(OWNER, sid, pid)

        svc.clarify_jira_scope(
            OWNER, sid, pid,
            connection_ref="a.atlassian.net|u@x.com",
            projects=["KAN"],
            issue_types=[],
        )

        svc.test_proposal(OWNER, sid, pid)
        test_jql = adapter.last_jql

        result = svc.finalize(OWNER, sid)
        activated = result.get("activated_watches", [])
        assert len(activated) >= 1

        wid = activated[0]["watch_id"]
        watch = db.automations.get_watch(wid)
        query = watch.get("query", {})
        eval_jql = _compile_jql(query)

        assert test_jql == eval_jql, (
            f"Test JQL and evaluation JQL must be identical for empty issue_types.\n"
            f"  Test JQL: {test_jql}\n"
            f"  Eval JQL: {eval_jql}"
        )
        assert "issuetype" not in eval_jql.lower(), (
            f"No types chosen -> no issuetype clause, got: {eval_jql}"
        )


# ── (d) HS-168 legacy-side watch guard ──────────────────────────────


class TestLegacyWatchGuard:
    """refresh_due_watches must not evaluate watches that are paused,
    retired, or bound to an archived project.

    The guard lives in the repo query (list_enabled_legacy_watches); the
    service's _GRADUATED_STATES belt is defense-in-depth.
    """

    @staticmethod
    def _make_svc(db, *, fetcher=None):
        if fetcher is None:
            def fetcher(principal, **kwargs):
                return [{"number": 1, "state": "open", "title": "PR"}]
        return ReactionService(db, snapshot_fetcher=fetcher)

    @staticmethod
    def _make_watch_due(db, watch_id: str, minutes_ago: int = 60):
        """Push updated_at back so a legacy watch is due."""
        from datetime import timedelta as _td
        old = (datetime.now(timezone.utc) - _td(minutes=minutes_ago)).isoformat(
            timespec="seconds"
        )
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET updated_at=? WHERE id=?",
                (old, watch_id),
            )

    @staticmethod
    def _insert_project(db, project_id: str, *, archived: bool = False):
        """Insert a minimal project row."""
        lifecycle = "archived" if archived else "active"
        is_archived = 1 if archived else 0
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, is_archived, lifecycle) "
                "VALUES (?, ?, ?, ?)",
                (project_id, f"proj-{project_id}", is_archived, lifecycle),
            )

    @staticmethod
    def _set_watch_state(db, watch_id: str, state: str):
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET state=? WHERE id=?",
                (state, watch_id),
            )

    @staticmethod
    def _set_watch_project(db, watch_id: str, project_id: str):
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET project_id=? WHERE id=?",
                (project_id, watch_id),
            )

    def test_paused_watch_active_project_not_evaluated(self, db):
        """A paused watch on an active project must NOT be returned by
        the due selection and NOT evaluated by refresh_due_watches."""
        import asyncio
        from datetime import timezone as _tz

        svc = self._make_svc(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-paused-active",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        self._insert_project(db, "proj-active-1", archived=False)
        self._set_watch_project(db, "watch-paused-active", "proj-active-1")
        self._set_watch_state(db, "watch-paused-active", "paused")
        self._make_watch_due(db, "watch-paused-active")

        # Repo level: list_enabled_legacy_watches must exclude it
        repo_watches = db.automations.list_enabled_legacy_watches()
        repo_ids = [w["id"] for w in repo_watches]
        assert "watch-paused-active" not in repo_ids, (
            "list_enabled_legacy_watches must exclude paused watches"
        )

        # Service level: refresh_due_watches must produce no outcome
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        outcome_ids = [o["watch_id"] for o in outcomes]
        assert "watch-paused-active" not in outcome_ids, (
            "refresh_due_watches must not evaluate a paused watch"
        )

    def test_active_watch_archived_project_not_evaluated(self, db):
        """An enabled legacy watch (state='') on an archived project
        must NOT be evaluated by refresh_due_watches."""
        import asyncio

        svc = self._make_svc(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-on-archived",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        self._insert_project(db, "proj-archived-1", archived=True)
        self._set_watch_project(db, "watch-on-archived", "proj-archived-1")
        # state stays '' (legacy); enabled stays 1
        self._make_watch_due(db, "watch-on-archived")

        # Repo level
        repo_watches = db.automations.list_enabled_legacy_watches()
        repo_ids = [w["id"] for w in repo_watches]
        assert "watch-on-archived" not in repo_ids, (
            "list_enabled_legacy_watches must exclude watches on archived projects"
        )

        # Service level
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        outcome_ids = [o["watch_id"] for o in outcomes]
        assert "watch-on-archived" not in outcome_ids, (
            "refresh_due_watches must not evaluate a watch on an archived project"
        )

    def test_active_watch_active_project_still_evaluated(self, db):
        """Regression: an enabled legacy watch (state='') on an active
        project must still be evaluated normally."""
        import asyncio

        svc = self._make_svc(db)
        svc.create_watch(
            OWNER, connector_id="gh", query_kind="pull_requests",
            watch_id="watch-healthy",
            query={"repository": "acme/app", "refresh_interval_minutes": 15},
        )
        self._insert_project(db, "proj-active-2", archived=False)
        self._set_watch_project(db, "watch-healthy", "proj-active-2")
        self._make_watch_due(db, "watch-healthy")

        # Repo level: must appear
        repo_watches = db.automations.list_enabled_legacy_watches()
        repo_ids = [w["id"] for w in repo_watches]
        assert "watch-healthy" in repo_ids, (
            "list_enabled_legacy_watches must include active watches on active projects"
        )

        # Service level: must be refreshed
        outcomes = asyncio.run(svc.refresh_due_watches(OWNER))
        outcome_ids = [o["watch_id"] for o in outcomes]
        assert "watch-healthy" in outcome_ids, (
            "refresh_due_watches must evaluate a healthy legacy watch"
        )
        status = {o["watch_id"]: o["status"] for o in outcomes}
        assert status["watch-healthy"] == "refreshed"
