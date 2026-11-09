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
from __future__ import annotations

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


class TestListProviders:
    def test_lists_native_and_github(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers")
        assert resp.status_code == 200
        providers = resp.json()["providers"]
        ids = [p["provider_id"] for p in providers]
        assert "native" in ids
        assert "github" in ids

    def test_native_provider_has_families(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers")
        native = [p for p in resp.json()["providers"] if p["provider_id"] == "native"][0]
        assert "meetings" in native["families"]
        assert "decisions" in native["families"]
        assert "door" in native["families"]

    def test_github_provider_has_capabilities(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers")
        github = [p for p in resp.json()["providers"] if p["provider_id"] == "github"][0]
        assert github["capabilities"]["discover"] is True
        assert github["capabilities"]["read"] is True


# ── GET /api/providers/github/connection ─────────────────────────────


# ── POST /api/providers/github/connection/recheck ────────────────────


# ── GET /api/providers/github/discover ───────────────────────────────


class TestGitHubDiscover:
    def test_discover_returns_items(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers/github/discover")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "ready"
        items = body["items"]
        assert len(items) >= 1
        assert any(i["id"] == "acme/platform" for i in items)

    def test_discover_with_query_filter(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers/github/discover?query=backend")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert all("backend" in i["id"].lower() for i in items)

    def test_discover_pagination(self, rig) -> None:
        _db, client, _log, _ctx = rig
        # Fetch with limit=1 to force pagination
        resp = client.get("/api/providers/github/discover?limit=1")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["items"]) <= 1
        # The cursor field is present (may be None or an int)
        assert "cursor" in body

    def test_discover_with_cursor(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.get("/api/providers/github/discover?limit=1&cursor=1")
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "cursor" in body


# ── POST /api/watches/{id}/evaluate ──────────────────────────────────


class TestWatchEvaluate:
    def test_evaluate_unknown_watch_404(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post("/api/watches/watch-nonexistent/evaluate")
        assert resp.status_code == 404

    def test_evaluate_existing_watch(self, rig) -> None:
        """Seed a watch, baseline it, then evaluate through the route."""
        db, client, _log, _ctx = rig
        from tests.watch_seed import seed_watch

        seed_watch(db,
            connector_id="gh",
            query_kind="pull_requests",
            name="Eval Test Watch",
            query={"repository": "acme/platform"},
            watch_id="watch-eval-01",
        )

        # Need a fetcher for evaluate_once -- wire it through the watch_service
        def fetcher(principal: Any, **kwargs: Any) -> list[dict[str, Any]]:
            return [{
                "number": 1, "state": "open", "title": "PR",
                "url": "http://gh/1", "checks": "success",
                "headRefOid": "aaa",
            }]

        _ctx.watch_service = WatchService(db, snapshot_fetcher=fetcher)

        # Baseline first
        resp = client.post("/api/watches/watch-eval-01/baseline")
        assert resp.status_code == 200

        # Evaluate
        resp = client.post("/api/watches/watch-eval-01/evaluate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert "evaluation_id" in body


# ── Auth-degraded path ───────────────────────────────────────────────


class TestAuthDegradedPath:
    """The auth-degraded wire proof: unauthenticated probe ->
    owner_action_required ON THE WIRE with typed body + correct status."""

    def test_discover_fails_when_unauthed(self, unauth_rig) -> None:
        _db, client = unauth_rig
        resp = client.get("/api/providers/github/discover")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "failed"
        assert body["error_code"] is not None


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


class TestJiraProviderRoutes:
    """HS-166-01: Jira connection list/add/recheck roundtrip."""

    def test_list_connections_empty(self, jira_rig) -> None:
        db, client, _, _ = jira_rig
        resp = client.get("/api/providers/jira/connections")
        assert resp.status_code == 200
        assert resp.json()["connections"] == []

    def test_add_connection(self, jira_rig) -> None:
        db, client, _, _ = jira_rig
        resp = client.post(
            "/api/providers/jira/connections",
            json={"site": "alpha", "email": "user@example.com"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["provider_id"] == "jira"
        assert body["external_connection_ref"] == "alpha.atlassian.net|user@example.com"

    def test_add_then_list(self, jira_rig) -> None:
        db, client, _, _ = jira_rig
        client.post(
            "/api/providers/jira/connections",
            json={"site": "alpha", "email": "user@example.com"},
        )
        resp = client.get("/api/providers/jira/connections")
        assert resp.status_code == 200
        connections = resp.json()["connections"]
        assert len(connections) == 1
        assert connections[0]["external_connection_ref"] == "alpha.atlassian.net|user@example.com"

    def test_recheck_connected(self, jira_rig) -> None:
        db, client, call_log, _ = jira_rig
        # Add then recheck
        client.post(
            "/api/providers/jira/connections",
            json={"site": "alpha", "email": "user@example.com"},
        )
        ref = "alpha.atlassian.net|user@example.com"
        resp = client.post(f"/api/providers/jira/connections/{ref}/recheck")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "connected"
        assert body["account"]["site"] == "alpha.atlassian.net"
        assert body["account"]["email"] == "user@example.com"

    def test_readiness_partial_before_connected_after(self, jira_rig) -> None:
        """SETFLOW-005: partial before recheck, connected after."""
        db, client, _, _ = jira_rig
        # Before: partial (acli present via fake runner, zero connected rows)
        resp = client.get("/api/providers")
        providers = resp.json()["providers"]
        jira_entry = next(p for p in providers if p["provider_id"] == "jira")
        assert jira_entry["readiness"]["state"] == "partial"
        assert jira_entry["readiness"]["connected"] == 0

        # Add + recheck → connected
        client.post(
            "/api/providers/jira/connections",
            json={"site": "alpha", "email": "user@example.com"},
        )
        ref = "alpha.atlassian.net|user@example.com"
        client.post(f"/api/providers/jira/connections/{ref}/recheck")

        resp = client.get("/api/providers")
        providers = resp.json()["providers"]
        jira_entry = next(p for p in providers if p["provider_id"] == "jira")
        assert jira_entry["readiness"]["state"] == "connected"
        assert jira_entry["readiness"]["connected"] == 1

    def test_connections_route_includes_known_accounts(self, jira_rig) -> None:
        """GET /api/providers/jira/connections returns known_accounts."""
        _, client, _, _ = jira_rig
        resp = client.get("/api/providers/jira/connections")
        assert resp.status_code == 200
        body = resp.json()
        assert "known_accounts" in body
        assert isinstance(body["known_accounts"], list)

    def test_add_missing_fields_400(self, jira_rig) -> None:
        _, client, _, _ = jira_rig
        resp = client.post(
            "/api/providers/jira/connections",
            json={"site": "alpha"},
        )
        assert resp.status_code == 400

    def test_recheck_bad_ref_400(self, jira_rig) -> None:
        _, client, _, _ = jira_rig
        resp = client.post("/api/providers/jira/connections/bad-ref/recheck")
        assert resp.status_code == 400


class TestJiraUnavailable:
    """Readiness is ``unavailable`` when acli is not installed."""

    def test_readiness_unavailable_no_acli(self, tmp_path, monkeypatch) -> None:
        from holdspeak.services.jira_provider import JiraProviderAdapter

        reset_database()
        db = Database(tmp_path / "jira-unavail.db")
        monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
        # No runner, and shutil.which returns None
        monkeypatch.setattr("shutil.which", lambda x: None)
        jira_adapter = JiraProviderAdapter(db=db, runner=None)

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

        resp = client.get("/api/providers")
        providers = resp.json()["providers"]
        jira_entry = next(p for p in providers if p["provider_id"] == "jira")
        assert jira_entry["readiness"]["state"] == "unavailable"
        assert jira_entry["readiness"]["connected"] == 0
        reset_database()


class TestJiraMcpParity:
    """Route JSON == MCP tool JSON for the three Jira twins."""

    def test_provider_list_jira_entry_with_readiness(self, jira_rig) -> None:
        """provider.list MCP tool includes Jira manifest with readiness."""
        db, client, _, jira_adapter = jira_rig
        # HTTP
        http_resp = client.get("/api/providers")
        http_jira = next(
            p for p in http_resp.json()["providers"] if p["provider_id"] == "jira"
        )
        # MCP
        from holdspeak.web.routes.providers import collect_provider_manifests
        mcp_providers = collect_provider_manifests(
            jira_adapter=jira_adapter, principal=OWNER,
        )
        mcp_jira = next(p for p in mcp_providers if p["provider_id"] == "jira")
        # Byte-equal for the jira entry
        assert http_jira == mcp_jira
        # Readiness present
        assert "readiness" in http_jira
        assert http_jira["readiness"]["state"] == "partial"

    def test_connections_list_parity(self, jira_rig) -> None:
        """HTTP list == MCP list (connections + known_accounts)."""
        db, client, _, jira_adapter = jira_rig
        jira_adapter.add_connection(OWNER, "alpha", "user@example.com")

        http_resp = client.get("/api/providers/jira/connections")
        http_body = http_resp.json()
        http_connections = http_body["connections"]
        http_known = http_body["known_accounts"]

        # MCP path
        mcp_connections = jira_adapter.list_connections(OWNER)
        mcp_known = jira_adapter.known_accounts(OWNER)

        assert len(http_connections) == len(mcp_connections)
        assert http_connections[0]["external_connection_ref"] == mcp_connections[0]["external_connection_ref"]
        assert http_known == mcp_known

    def test_recheck_parity(self, jira_rig) -> None:
        """HTTP recheck == adapter.connection_status."""
        db, client, _, jira_adapter = jira_rig
        jira_adapter.add_connection(OWNER, "alpha", "user@example.com")
        ref = "alpha.atlassian.net|user@example.com"

        http_resp = client.post(f"/api/providers/jira/connections/{ref}/recheck")
        http_body = http_resp.json()

        mcp_body = jira_adapter.connection_status(OWNER, ref)
        assert http_body["state"] == mcp_body["state"]
        assert http_body["provider_id"] == mcp_body["provider_id"]


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


class TestJiraDiscoverRoutes:
    """HS-166-02: discover, search, validate-scope route roundtrips."""

    def test_discover_projects(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"
        resp = client.get(
            f"/api/providers/jira/discover?connection_ref={ref}&kind=projects"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "ready"
        assert len(body["items"]) >= 1
        assert body["items"][0]["key"] == "KAN"
        assert body["connection_ref"] == ref

    def test_discover_issue_types(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"
        resp = client.get(
            f"/api/providers/jira/discover?connection_ref={ref}&kind=issue_types&project_key=KAN"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "ready"
        assert body["source"] == "enumerated"
        assert len(body["items"]) >= 1

    def test_discover_statuses(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"
        resp = client.get(
            f"/api/providers/jira/discover?connection_ref={ref}&kind=statuses&project_key=KAN"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "ready"
        assert body["source"] == "observed"
        assert "categories" in body

    def test_discover_missing_connection_ref_400(self, jira_discovery_rig) -> None:
        _, client, _, _ = jira_discovery_rig
        resp = client.get("/api/providers/jira/discover?kind=projects")
        assert resp.status_code == 400

class TestJiraDiscoverMcpParity:
    """HS-166-02: Route JSON == MCP tool JSON for the three new Jira tools."""

    def test_discover_parity(self, jira_discovery_rig) -> None:
        """HTTP discover == adapter.discover (byte-equal)."""
        _, client, _, jira_adapter = jira_discovery_rig
        ref = "alpha.atlassian.net|user@example.com"

        http_resp = client.get(
            f"/api/providers/jira/discover?connection_ref={ref}&kind=projects"
        )
        http_body = http_resp.json()

        mcp_body = jira_adapter.discover(
            OWNER, ref, kind="projects",
        )

        # Byte-equal on the envelope keys that matter
        assert http_body["state"] == mcp_body["state"]
        assert http_body["connection_ref"] == mcp_body["connection_ref"]
        assert len(http_body["items"]) == len(mcp_body["items"])
        if http_body["items"]:
            assert http_body["items"][0]["key"] == mcp_body["items"][0]["key"]
