"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_provider_routes.py``: TestGitHubConnection, TestGitHubRecheck, test_unauthenticated_probe_returns_owner_action_required, test_recheck_also_degraded. Not collected.
"""
from __future__ import annotations
"""HS-161-04 -- Provider route integration tests through the REAL app.

Pattern: 159 (isolated DB, real FastAPI app, TestClient, fake runner injected).

Tests:
- Every provider route: success + failure paths.
- Recheck re-probes (probe count observable via fake runner).
- Discovery pagination on the wire.
- The auth-degraded path: fake-runner unauthenticated probe ->
  owner_action_required ON THE WIRE.
- THE FULL COMPOUNDING LOOP THROUGH HTTP: connect(fake) -> discover ->
  clarify -> test -> finalize -> evaluate -> the Delta shows the PR
  transition via the HTTP review routes.
"""

import json
import subprocess
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.github_provider import GitHubProviderAdapter
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_setup_service import ProjectSetupService
from holdspeak.services.watch_service import WatchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import (
    build_project_reviews_router,
    build_project_setup_router,
    build_projects_router,
    build_providers_router,
    build_watches_router,
)

OWNER = Principal(PrincipalKind.OWNER, "provider-route-test-owner")


# ── Fake runners ────────────────────────────────────────────────────


def _make_connected_runner(call_log: list[list[str]] | None = None):
    """A fake runner that simulates a connected gh CLI."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        if call_log is not None:
            call_log.append(list(cmd))
        if cmd[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout="Logged in to github.com account testuser (keyring)\n",
                stderr="",
            )
        if cmd[:3] == ["gh", "repo", "list"]:
            repos = [
                {"name": "platform", "owner": {"login": "acme"}, "visibility": "public"},
                {"name": "backend", "owner": {"login": "acme"}, "visibility": "private"},
                {"name": "docs", "owner": {"login": "acme"}, "visibility": "public"},
            ]
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(repos), stderr="",
            )
        if cmd[:3] == ["gh", "pr", "list"]:
            prs = [
                {
                    "number": 101,
                    "title": "Fix CI pipeline",
                    "url": "https://github.com/acme/platform/pull/101",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewRequests": [],
                    "reviewDecision": "",
                    "statusCheckRollup": [],
                    "headRefOid": "abc123def",
                    "updatedAt": "2026-09-01T10:00:00Z",
                },
                {
                    "number": 102,
                    "title": "Add feature flag",
                    "url": "https://github.com/acme/platform/pull/102",
                    "state": "OPEN",
                    "isDraft": False,
                    "reviewRequests": [],
                    "reviewDecision": "",
                    "statusCheckRollup": [],
                    "headRefOid": "def456abc",
                    "updatedAt": "2026-09-01T09:00:00Z",
                },
            ]
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(prs), stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return runner


def _make_unauth_runner():
    """A fake runner that simulates an unauthenticated gh CLI."""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = args[0] if args else kwargs.get("args", [])
        if cmd[:3] == ["gh", "auth", "status"]:
            return subprocess.CompletedProcess(
                cmd, 1,
                stdout="",
                stderr="You are not logged in to any GitHub hosts.",
            )
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not logged in")
    return runner


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path, monkeypatch):
    """Full route rig: providers + setup + watches + projects + reviews."""
    reset_database()
    db = Database(tmp_path / "provider-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    call_log: list[list[str]] = []
    runner = _make_connected_runner(call_log)
    adapter = GitHubProviderAdapter(db=db, runner=runner)

    project_svc = ProjectService(db)
    watch_svc = WatchService(db)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=watch_svc,
        github_adapter=adapter,
    )
    evidence_collector = ProjectEvidenceCollector(db)
    delta_svc = ProjectDeltaService(db, evidence_collector)

    ctx = WebContext(
        get_state=lambda: {},
        project_service=project_svc,
        watch_service=watch_svc,
        project_setup_service=setup_svc,
        github_provider=adapter,
        project_delta_service=delta_svc,
        project_evidence_collector=evidence_collector,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_providers_router(ctx))
    app.include_router(build_project_setup_router(ctx))
    app.include_router(build_watches_router(ctx))
    app.include_router(build_projects_router(ctx))
    app.include_router(build_project_reviews_router(ctx))
    client = TestClient(app)
    yield db, client, call_log, ctx
    reset_database()


@pytest.fixture
def unauth_rig(tmp_path, monkeypatch):
    """Rig with an unauthenticated runner for the degraded path test."""
    reset_database()
    db = Database(tmp_path / "provider-unauth.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    runner = _make_unauth_runner()
    adapter = GitHubProviderAdapter(db=db, runner=runner)

    ctx = WebContext(
        get_state=lambda: {},
        github_provider=adapter,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_providers_router(ctx))
    client = TestClient(app)
    yield db, client
    reset_database()


# ── GET /api/providers ──────────────────────────────────────────────


# ── GET /api/providers/github/connection ─────────────────────────────


class TestGitHubConnection:
    def test_connected_state(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers/github/connection")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "connected"
        assert body["display"]["account"] == "testuser"

    def test_connection_failure_state(self, unauth_rig) -> None:
        _db, client = unauth_rig
        resp = client.get("/api/providers/github/connection")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "owner_action_required"
        assert body["error_code"] == "authentication_required"


# ── POST /api/providers/github/connection/recheck ────────────────────


class TestGitHubRecheck:
    def test_recheck_re_probes(self, rig) -> None:
        """Recheck calls connection_status again; probe count observable."""
        _db, client, call_log, _ctx = rig
        # First probe
        client.get("/api/providers/github/connection")
        auth_count_before = sum(
            1 for c in call_log if c[:3] == ["gh", "auth", "status"]
        )

        # Recheck
        resp = client.post("/api/providers/github/connection/recheck")
        assert resp.status_code == 200
        assert resp.json()["state"] == "connected"

        auth_count_after = sum(
            1 for c in call_log if c[:3] == ["gh", "auth", "status"]
        )
        assert auth_count_after > auth_count_before, (
            "recheck must call connection_status again (observable via probe count)"
        )


# ── GET /api/providers/github/discover ───────────────────────────────


# ── POST /api/providers/github/validate-repo ─────────────────────────


# ── POST /api/watches/{id}/evaluate ──────────────────────────────────


# ── Auth-degraded path ───────────────────────────────────────────────


class TestAuthDegradedPath:
    """The auth-degraded wire proof: unauthenticated probe ->
    owner_action_required ON THE WIRE with typed body + correct status."""

    def test_unauthenticated_probe_returns_owner_action_required(
        self, unauth_rig,
    ) -> None:
        _db, client = unauth_rig
        resp = client.get("/api/providers/github/connection")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "owner_action_required"
        assert body["error_code"] == "authentication_required"
        assert body["error_detail"] == "gh auth login"
        assert body["display"]["recovery_hint"] == "gh auth login"

    def test_recheck_also_degraded(self, unauth_rig) -> None:
        _db, client = unauth_rig
        resp = client.post("/api/providers/github/connection/recheck")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "owner_action_required"
        assert body["error_code"] == "authentication_required"

# ── THE FULL COMPOUNDING LOOP THROUGH HTTP ───────────────────────────


# ════════════════════════════════════════════════════════════════════
# HS-166-01: Jira provider routes
# ════════════════════════════════════════════════════════════════════


def _make_jira_connected_runner(
    site: str = "alpha.atlassian.net",
    email: str = "user@example.com",
    call_log: list[list[str]] | None = None,
) -> Any:
    """recorded_from: acli 1.3.36-stable live, 2026-09-03"""
    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0]) if args else list(kwargs.get("args", []))
        if call_log is not None:
            call_log.append(cmd)
        if cmd[0:4] == ["acli", "jira", "auth", "switch"]:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=f"✓ Switched to account: {site} [{email}]",
                stderr="",
            )
        if cmd[0:4] == ["acli", "jira", "auth", "status"]:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=(
                    f"✓ Authenticated\n"
                    f"  Site: {site}\n"
                    f"  Email: {email}\n"
                    f"  Authentication Type: oauth\n"
                ),
                stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return runner


@pytest.fixture
def jira_rig(tmp_path, monkeypatch):
    """Route rig with both GitHub and Jira providers."""
    from holdspeak.services.jira_provider import JiraProviderAdapter

    reset_database()
    db = Database(tmp_path / "jira-provider-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    gh_call_log: list[list[str]] = []
    gh_runner = _make_connected_runner(gh_call_log)
    gh_adapter = GitHubProviderAdapter(db=db, runner=gh_runner)

    jira_call_log: list[list[str]] = []
    jira_runner = _make_jira_connected_runner(call_log=jira_call_log)
    jira_adapter = JiraProviderAdapter(db=db, runner=jira_runner)

    ctx = WebContext(
        get_state=lambda: {},
        github_provider=gh_adapter,
        jira_provider=jira_adapter,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_providers_router(ctx))
    client = TestClient(app)
    yield db, client, jira_call_log, jira_adapter
    reset_database()


# ════════════════════════════════════════════════════════════════════
# HS-166-02: Jira discovery + search + validate-scope routes
# ════════════════════════════════════════════════════════════════════


def _make_jira_discovery_runner(
    site: str = "alpha.atlassian.net",
    email: str = "user@example.com",
    call_log: list[list[str]] | None = None,
) -> Any:
    """recorded_from: acli 1.3.36-stable live, 2026-09-03

    A fake runner that handles switch + status + project list/view + search.
    """
    project_list = json.dumps([
        {
            "id": "10001", "key": "KAN", "name": "My Project",
            "projectTypeKey": "software", "style": "next-gen",
            "isPrivate": False,
            "lead": {"displayName": "Lead User", "accountId": "abc"},
            "issueTypes": None,
        },
    ])

    project_view = json.dumps({
        "id": "10001", "key": "KAN", "name": "My Project",
        "projectTypeKey": "software", "style": "next-gen",
        "issueTypes": [
            {"id": "10006", "name": "Task", "subtask": False, "hierarchyLevel": 0},
        ],
    })

    search_result = json.dumps([
        {
            "id": "10002", "key": "KAN-1",
            "fields": {
                "assignee": None,
                "issuetype": {"id": "10006", "name": "Task", "subtask": False},
                "priority": None,
                "status": {
                    "id": "10005", "name": "In Progress",
                    "statusCategory": {"id": 4, "key": "indeterminate", "name": "In Progress"},
                },
                "summary": "Task 1",
                "labels": [],
            },
        },
    ])

    def runner(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        cmd = list(args[0]) if args else list(kwargs.get("args", []))
        if call_log is not None:
            call_log.append(cmd)
        if cmd[0:4] == ["acli", "jira", "auth", "switch"]:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=f"✓ Switched to account: {site} [{email}]",
                stderr="",
            )
        if cmd[0:4] == ["acli", "jira", "auth", "status"]:
            return subprocess.CompletedProcess(
                cmd, 0,
                stdout=(
                    f"✓ Authenticated\n"
                    f"  Site: {site}\n"
                    f"  Email: {email}\n"
                    f"  Authentication Type: oauth\n"
                ),
                stderr="",
            )
        if cmd[0:4] == ["acli", "jira", "project", "list"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=project_list, stderr="",
            )
        if cmd[0:4] == ["acli", "jira", "project", "view"]:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=project_view, stderr="",
            )
        if cmd[0:4] == ["acli", "jira", "workitem", "search"]:
            if "--count" in cmd:
                return subprocess.CompletedProcess(
                    cmd, 0,
                    stdout="✓ Number of work items in the search: 1",
                    stderr="",
                )
            return subprocess.CompletedProcess(
                cmd, 0, stdout=search_result, stderr="",
            )
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return runner


@pytest.fixture
def jira_discovery_rig(tmp_path, monkeypatch):
    """Route rig with Jira adapter configured for discovery/search/validate."""
    from holdspeak.services.jira_provider import JiraProviderAdapter

    reset_database()
    db = Database(tmp_path / "jira-discovery-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    jira_call_log: list[list[str]] = []
    jira_runner = _make_jira_discovery_runner(call_log=jira_call_log)
    jira_adapter = JiraProviderAdapter(db=db, runner=jira_runner)

    # Add and connect a connection for the tests
    jira_adapter.add_connection(OWNER, "alpha", "user@example.com")
    ref = "alpha.atlassian.net|user@example.com"
    jira_adapter.connection_status(OWNER, ref)

    ctx = WebContext(
        get_state=lambda: {},
        jira_provider=jira_adapter,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_providers_router(ctx))
    client = TestClient(app)
    yield db, client, jira_call_log, jira_adapter
    reset_database()


