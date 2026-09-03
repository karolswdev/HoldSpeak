from __future__ import annotations

import json
import subprocess

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError, ValidationError
from holdspeak.services.watch_sources import (
    GitHubWatchSource,
    JiraWatchSource,
    _compile_jql,
    fetch_watch_snapshot,
)


OWNER = Principal(PrincipalKind.OWNER, "watch-owner")


# ── GitHub (existing) ────────────────────────────────────────────────


def test_github_watch_source_owns_query_and_normalization() -> None:
    captured = {}

    def runner(command, **kwargs):  # noqa: ANN001
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, json.dumps([{
            "number": 17, "title": "Review me", "url": "https://github.com/acme/app/pull/17",
            "state": "OPEN", "isDraft": False,
            "reviewRequests": [{"login": "karol"}], "reviewDecision": "REVIEW_REQUIRED",
            "statusCheckRollup": [{"conclusion": "FAILURE"}],
            "headRefOid": "abc", "updatedAt": "2026-08-16T20:00:00Z",
        }]), "")

    rows = GitHubWatchSource(runner=runner).snapshot(
        OWNER, query_kind="pull_requests",
        query={"repository": "acme/app", "search": "review-requested:@me"},
    )
    assert captured["command"][:6] == ["gh", "pr", "list", "--repo", "acme/app", "--state"]
    assert captured["command"][-2:] == ["--search", "review-requested:@me"]
    assert rows[0]["reviewRequests"] == ["karol"]
    assert rows[0]["checks"] == "failing"


def test_github_watch_requires_a_scoped_repository() -> None:
    with pytest.raises(ValidationError, match="owner/name"):
        GitHubWatchSource(runner=lambda *_args, **_kwargs: None).snapshot(
            OWNER, query_kind="pull_requests", query={"repository": "everything"},
        )


# ── JQL compiler (HS-166-03) ─────────────────────────────────────────


class TestCompileJql:
    """Unit tests for _compile_jql -- pure, no adapter."""

    def test_empty_query(self) -> None:
        assert _compile_jql({}) == "ORDER BY updated DESC"

    def test_project_filter(self) -> None:
        jql = _compile_jql({"projects": ["KAN", "SAM1"]})
        assert 'project in ("KAN", "SAM1")' in jql
        assert jql.endswith("ORDER BY updated DESC")

    def test_issue_types(self) -> None:
        jql = _compile_jql({"issue_types": ["Task", "Bug"]})
        assert 'issuetype in ("Bug", "Task")' in jql

    def test_status_categories(self) -> None:
        jql = _compile_jql({"status_categories": ["indeterminate"]})
        assert 'statusCategory in ("indeterminate")' in jql

    def test_priorities(self) -> None:
        jql = _compile_jql({"priorities": ["High", "Highest"]})
        assert 'priority in ("High", "Highest")' in jql

    def test_assignees(self) -> None:
        jql = _compile_jql({"assignees": ["alice"]})
        assert 'assignee in ("alice")' in jql

    def test_labels(self) -> None:
        jql = _compile_jql({"labels": ["urgent"]})
        assert 'labels in ("urgent")' in jql

    def test_components(self) -> None:
        jql = _compile_jql({"components": ["backend"]})
        assert 'component in ("backend")' in jql

    def test_sprint(self) -> None:
        jql = _compile_jql({"sprint": "Sprint 5"})
        assert 'sprint = "Sprint 5"' in jql

    def test_due_within_days(self) -> None:
        jql = _compile_jql({"due_within_days": 7})
        assert "due <= 7d" in jql

    def test_inactive_days(self) -> None:
        jql = _compile_jql({"inactive_days": 14})
        assert "updated <= -14d" in jql

    def test_blocked_statuses(self) -> None:
        jql = _compile_jql({"blocked_statuses": ["Blocked"]})
        assert 'status in ("Blocked")' in jql

    def test_owner_jql_appended_verbatim(self) -> None:
        jql = _compile_jql({"jql": "labels = critical", "projects": ["KAN"]})
        assert 'project in ("KAN")' in jql
        assert "(labels = critical)" in jql
        assert " AND " in jql

    def test_quoting_with_double_quotes(self) -> None:
        jql = _compile_jql({"projects": ['My "Special" Project']})
        assert r'"My \"Special\" Project"' in jql

    def test_deterministic_ordering(self) -> None:
        """Multiple calls produce the same string."""
        q = {"projects": ["B", "A"], "priorities": ["High"]}
        assert _compile_jql(q) == _compile_jql(q)

    def test_combined_filters(self) -> None:
        jql = _compile_jql({
            "projects": ["KAN"],
            "issue_types": ["Task"],
            "status_categories": ["indeterminate"],
            "due_within_days": 7,
        })
        assert 'project in ("KAN")' in jql
        assert 'issuetype in ("Task")' in jql
        assert 'statusCategory in ("indeterminate")' in jql
        assert "due <= 7d" in jql
        assert jql.endswith("ORDER BY updated DESC")


# ── JiraWatchSource (HS-166-03) ──────────────────────────────────────


# recorded_from: tests/unit/test_jira_provider.py fixtures (HS-166-02)
_FAKE_SEARCH_RESULT = {
    "state": "ready",
    "error_code": None,
    "error_detail": None,
    "connection_ref": "alpha.atlassian.net|user@example.com",
    "items": [
        {
            "key": "KAN-1",
            "id": "10002",
            "summary": "Task 1",
            "issue_type": "Task",
            "status": "In Progress",
            "status_category": "indeterminate",
            "assignee": None,
            "assignee_id": None,
            "priority": None,
            "labels": [],
            "url": "https://alpha.atlassian.net/browse/KAN-1",
            "due_at": "2026-09-10",
            "resolution": None,
            "resolved_at": None,
            "updated_at": "2026-09-02T20:02:24.980-0600",
            "created_at": "2026-09-02T20:02:24.540-0600",
            "status_changed_at": "2026-09-02T20:02:24.980-0600",
            "project_key": "KAN",
        },
        {
            "key": "KAN-2",
            "id": "10004",
            "summary": "Task 2",
            "issue_type": "Task",
            "status": "In Progress",
            "status_category": "indeterminate",
            "assignee": None,
            "assignee_id": None,
            "priority": None,
            "labels": [],
            "url": "https://alpha.atlassian.net/browse/KAN-2",
            "due_at": None,
            "resolution": None,
            "resolved_at": None,
            "updated_at": "2026-09-02T19:00:00.000-0600",
            "created_at": "2026-09-02T19:00:00.000-0600",
            "status_changed_at": "2026-09-02T19:00:00.000-0600",
            "project_key": "KAN",
        },
    ],
    "calls": 3,
}


class _FakeAdapter:
    """Fake JiraProviderAdapter for testing."""

    def __init__(self, result: dict | None = None, error: Exception | None = None):
        self._result = result or _FAKE_SEARCH_RESULT
        self._error = error
        self.calls: list[dict] = []

    def search(self, principal, connection_ref, *, jql, limit, enrich):
        self.calls.append({
            "connection_ref": connection_ref,
            "jql": jql,
            "limit": limit,
            "enrich": enrich,
        })
        if self._error:
            raise self._error
        return dict(self._result)


class TestJiraWatchSource:
    """recorded_from: test_jira_provider.py fixtures (HS-166-02)"""

    def test_entity_shape(self) -> None:
        adapter = _FakeAdapter()
        entities = JiraWatchSource(adapter=adapter).snapshot(
            OWNER, query_kind="issues",
            query={"connection_ref": "alpha.atlassian.net|user@example.com",
                   "projects": ["KAN"]},
        )
        assert len(entities) == 2
        e = entities[0]
        assert e["id"] == "KAN-1"
        assert e["key"] == "KAN-1"
        assert e["title"] == "Task 1"
        assert e["status"] == "In Progress"
        assert e["status_category"] == "indeterminate"
        assert e["issue_type"] == "Task"
        assert e["due_at"] == "2026-09-10"
        assert e["project_key"] == "KAN"
        assert e["url"] == "https://alpha.atlassian.net/browse/KAN-1"

    def test_adapter_called_with_correct_params(self) -> None:
        adapter = _FakeAdapter()
        JiraWatchSource(adapter=adapter).snapshot(
            OWNER, query_kind="issues",
            query={"connection_ref": "alpha.atlassian.net|user@example.com",
                   "projects": ["KAN"], "limit": 25},
        )
        assert len(adapter.calls) == 1
        call = adapter.calls[0]
        assert call["connection_ref"] == "alpha.atlassian.net|user@example.com"
        assert call["enrich"] is True
        assert call["limit"] == 25
        assert 'project in ("KAN")' in call["jql"]

    def test_jql_compiled_from_query(self) -> None:
        adapter = _FakeAdapter()
        JiraWatchSource(adapter=adapter).snapshot(
            OWNER, query_kind="issues",
            query={"connection_ref": "alpha.atlassian.net|user@example.com",
                   "projects": ["KAN"], "status_categories": ["indeterminate"],
                   "jql": "labels = critical"},
        )
        jql = adapter.calls[0]["jql"]
        assert 'project in ("KAN")' in jql
        assert 'statusCategory in ("indeterminate")' in jql
        assert "(labels = critical)" in jql

    def test_wrong_query_kind_raises(self) -> None:
        with pytest.raises(ValidationError, match="issues"):
            JiraWatchSource(adapter=_FakeAdapter()).snapshot(
                OWNER, query_kind="pull_requests",
                query={"connection_ref": "a|b"},
            )

    def test_missing_connection_ref_raises(self) -> None:
        with pytest.raises(ValidationError, match="connection_ref"):
            JiraWatchSource(adapter=_FakeAdapter()).snapshot(
                OWNER, query_kind="issues", query={},
            )

    def test_typed_error_propagation(self) -> None:
        """Adapter errors propagate as ServiceError with typed codes."""
        adapter = _FakeAdapter(result={
            "state": "failed",
            "error_code": "query_invalid",
            "error_detail": "bad JQL syntax",
            "items": [],
        })
        with pytest.raises(ServiceError) as exc_info:
            JiraWatchSource(adapter=adapter).snapshot(
                OWNER, query_kind="issues",
                query={"connection_ref": "a.atlassian.net|u@x.com"},
            )
        assert "query_invalid" in str(exc_info.value.code) or "connector_query_invalid" in str(exc_info.value.code)

    def test_auth_error_propagation(self) -> None:
        adapter = _FakeAdapter(result={
            "state": "failed",
            "error_code": "authentication_required",
            "error_detail": "not logged in",
            "items": [],
        })
        with pytest.raises(ServiceError) as exc_info:
            JiraWatchSource(adapter=adapter).snapshot(
                OWNER, query_kind="issues",
                query={"connection_ref": "a.atlassian.net|u@x.com"},
            )
        assert "authentication_required" in str(exc_info.value.code)


# ── fetch_watch_snapshot registration (HS-166-03) ────────────────────


class TestFetchWatchSnapshot:

    def test_gh_still_works(self) -> None:
        """The gh path is unchanged."""
        def runner(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, "[]", "")
        result = fetch_watch_snapshot(
            OWNER, connector_id="gh", query_kind="pull_requests",
            query={"repository": "acme/app"}, github_runner=runner,
        )
        assert result == []

    def test_jira_dispatches(self) -> None:
        adapter = _FakeAdapter()
        result = fetch_watch_snapshot(
            OWNER, connector_id="jira", query_kind="issues",
            query={"connection_ref": "alpha.atlassian.net|user@example.com"},
            jira_adapter=adapter,
        )
        assert len(result) == 2

    def test_unknown_connector_still_raises(self) -> None:
        with pytest.raises(ServiceError, match="no local query adapter yet"):
            fetch_watch_snapshot(
                OWNER, connector_id="unknown", query_kind="things",
                query={},
            )


# ── HS-166-03: project_service scope flattening maps ─────────────────


class TestProjectServiceMaps:
    """The provider-to-connector and subject-to-query-kind maps are complete."""

    def test_provider_to_connector_jira(self) -> None:
        from holdspeak.services.project_service import _PROVIDER_TO_CONNECTOR
        assert _PROVIDER_TO_CONNECTOR["github"] == "gh"
        assert _PROVIDER_TO_CONNECTOR["jira"] == "jira"

    def test_subject_to_query_kind_issue(self) -> None:
        from holdspeak.services.project_service import _SUBJECT_TO_QUERY_KIND
        assert _SUBJECT_TO_QUERY_KIND["pull_request"] == "pull_requests"
        assert _SUBJECT_TO_QUERY_KIND["issue"] == "issues"
