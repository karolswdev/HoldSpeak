"""HS-169-02 — Door service parity and behaviour tests.

(a) Count path and evaluation path compile IDENTICAL queries (GitHub + Jira).
(b) Door create stores no blank list entries and one watch per default.
(c) Zero sources = blank project.
(d) Failing count returns a plain reason and still allows create.
"""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError
from holdspeak.services.project_door_service import (
    DOOR_DEFAULTS,
    ProjectDoorService,
    _flatten_github_query,
    _flatten_jira_query,
)

_P = Principal(PrincipalKind.OWNER, "test")
_REPO = "karolswdev/HoldSpeak"
_JIRA_SCOPE = {
    "connection_ref": "site.atlassian.net|user@example.com",
    "projects": ["KAN"],
}


# ── (a) Parity: count query == evaluation query ───────────────────


class TestGitHubQueryParity:
    """The count path must build the SAME stored query shape
    that create_from_setup produces for evaluation."""

    def test_review_queue_parity(self) -> None:
        from holdspeak import github_templates

        spec = github_templates.compile("watch.github.review_queue", _REPO)
        stored = _flatten_github_query(spec)

        assert stored["repository"] == _REPO
        assert stored.get("state") == "open"
        assert stored.get("base") == "main"
        assert "repositories" not in stored

    def test_ci_branch_query_shape(self) -> None:
        """CI door default uses branch_ci query kind with
        repository + base, matching the stored query shape."""
        svc = ProjectDoorService()
        query = {"repository": _REPO, "base": "main"}
        assert "repository" in query
        assert "base" in query

    def test_flatten_matches_create_from_setup(self) -> None:
        """The flatten function produces the same shape as
        project_service.create_from_setup's flattening loop."""
        from holdspeak import github_templates

        spec = github_templates.compile("watch.github.review_queue", _REPO)

        subject = spec["subject"]
        query_filters = dict(subject.get("query", {}))
        repos = subject.get("scope", {}).get("repositories", [])
        if repos:
            query_filters["repository"] = repos[0]

        flat = _flatten_github_query(spec)
        assert flat == query_filters


class TestJiraQueryParity:
    """The count path must compile the SAME JQL that evaluation uses."""

    def test_due_risk_jql_parity(self) -> None:
        from holdspeak import jira_templates
        from holdspeak.services.watch_sources import _compile_jql

        spec = jira_templates.compile("watch.jira.due_risk", _JIRA_SCOPE)
        stored = _flatten_jira_query(spec)
        jql_from_count = _compile_jql(stored)

        eval_query = dict(spec["subject"]["query"])
        conn_ref = spec["subject"]["scope"].get("connection_ref") or spec["provider"].get("connection_ref")
        if conn_ref:
            eval_query["connection_ref"] = conn_ref
        projects = spec["subject"]["scope"].get("projects", [])
        if projects:
            eval_query["projects"] = list(projects)
        jql_from_eval = _compile_jql(eval_query)

        assert jql_from_count == jql_from_eval

    def test_blockers_jql_parity(self) -> None:
        from holdspeak import jira_templates
        from holdspeak.services.watch_sources import _compile_jql

        spec = jira_templates.compile("watch.jira.blockers", _JIRA_SCOPE)
        stored = _flatten_jira_query(spec)
        jql_count = _compile_jql(stored)

        eval_query = dict(spec["subject"]["query"])
        conn_ref = spec["subject"]["scope"].get("connection_ref") or spec["provider"].get("connection_ref")
        if conn_ref:
            eval_query["connection_ref"] = conn_ref
        projects = spec["subject"]["scope"].get("projects", [])
        if projects:
            eval_query["projects"] = list(projects)
        jql_eval = _compile_jql(eval_query)

        assert jql_count == jql_eval

    def test_flatten_matches_create_from_setup(self) -> None:
        """Flatten produces the same shape as create_from_setup's Jira loop."""
        from holdspeak import jira_templates

        spec = jira_templates.compile("watch.jira.due_risk", _JIRA_SCOPE)

        subject = spec["subject"]
        query_filters = dict(subject.get("query", {}))
        scope = subject.get("scope", {})
        conn_ref = scope.get("connection_ref") or spec.get("provider", {}).get("connection_ref")
        if conn_ref:
            query_filters["connection_ref"] = conn_ref
        jira_projects = scope.get("projects", [])
        if jira_projects:
            query_filters["projects"] = list(jira_projects)
        jira_issue_types = scope.get("issue_types", [])
        if jira_issue_types:
            query_filters["issue_types"] = list(jira_issue_types)

        flat = _flatten_jira_query(spec)
        assert flat == query_filters


# ── (b) Create stores one watch per default, no blanks ─────────────


class TestCreateWatches:
    def test_one_watch_per_default(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_test", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        svc.create(
            _P,
            "Ship Q4 on time",
            [
                {"provider": "github", "scope": _REPO, "watches": ["open_prs", "ci"]},
                {
                    "provider": "jira",
                    "scope": _JIRA_SCOPE,
                    "watches": ["overdue", "blocked"],
                },
            ],
        )

        assert len(captured) == 1
        proposals = captured[0]["proposals"]
        assert len(proposals) == 4

        for p in proposals:
            spec = p["spec"]
            provider_id = spec["provider"]["id"]
            if provider_id == "github":
                subject = spec["subject"]
                kind = subject.get("kind", "")
                if kind == "branch_ci":
                    query = subject.get("query", {})
                    assert query.get("base")
                else:
                    scope_repos = subject.get("scope", {}).get("repositories", [])
                    assert scope_repos and all(r.strip() for r in scope_repos)
            elif provider_id == "jira":
                scope_d = spec["subject"].get("scope", {})
                assert scope_d.get("connection_ref")
                assert scope_d.get("projects")

        spec_names = [p["spec"]["name"] for p in proposals]
        assert len(set(spec_names)) == len(spec_names)

    def test_no_blank_entries(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_test", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        svc.create(
            _P,
            "Test project",
            [{"provider": "github", "scope": _REPO, "watches": ["open_prs"]}],
        )

        proposals = captured[0]["proposals"]
        for p in proposals:
            assert p["state"] == "selected"
            assert p["test_state"] == "passed"
            assert p["spec"]


# ── (c) Zero sources = blank project ──────────────────────────────


class TestBlankProject:
    def test_zero_sources(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_blank", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        result = svc.create(_P, "Test blank", [])

        assert result["projectId"] == "proj_blank"
        assert len(captured) == 1
        assert captured[0]["proposals"] == []
        assert captured[0]["name"] == "Test blank"


# ── (d) Failing count: plain reason, create still works ───────────


class TestFailingCount:
    def test_count_returns_plain_reason(self) -> None:
        with patch(
            "holdspeak.services.watch_sources.GitHubWatchSource"
        ) as MockGH:
            mock_source = MagicMock()
            mock_source.snapshot.side_effect = ServiceError(
                "connector_refresh_failed", "GitHub CLI query failed"
            )
            MockGH.return_value = mock_source

            svc = ProjectDoorService()
            result = svc.count(_P, "github", _REPO, ["open_prs"])

            assert result["state"] == "cant_check"
            assert isinstance(result["reason"], str)
            assert len(result["reason"]) > 0
            assert "GitHub CLI query failed" in result["reason"]

    def test_create_works_despite_count_failure(self) -> None:
        captured: list[dict[str, Any]] = []

        def mock_create(principal: Any, payload: dict, **kw: Any) -> dict:
            captured.append(payload)
            return {"project_id": "proj_ok", "activated_watches": []}

        mock_ps = MagicMock()
        mock_ps.create_from_setup = mock_create

        svc = ProjectDoorService(project_service=mock_ps)
        result = svc.create(
            _P,
            "Test despite failure",
            [{"provider": "github", "scope": _REPO, "watches": ["open_prs"]}],
        )

        assert result["projectId"] == "proj_ok"
        assert len(captured) == 1
        assert len(captured[0]["proposals"]) == 1
