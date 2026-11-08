"""HS-168-02: Connections route tests -- GET + POST recheck through the real
FastAPI app (web context composition characterization), the suggest annotation,
known_scopes on the session route, and the per-provider cap.

Pattern: isolated DB, real FastAPI app, TestClient.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.connections_service import (
    ConnectionsService,
    DISPLAY_NOT_CONFIGURED,
)
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_setup_service import ProjectSetupService
from holdspeak.services.watch_service import WatchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import (
    build_connections_router,
    build_project_setup_router,
)

OWNER = Principal(PrincipalKind.OWNER, "conn-route-owner")


# ── Fake adapters for the connections service ────────────────────────

def _connected_gh() -> MagicMock:
    gh = MagicMock()
    gh.connection_status.return_value = {
        "state": "connected",
        "display": {"account": "testuser"},
        "error_code": None,
        "error_detail": None,
    }
    gh.discover.return_value = {"state": "ready", "items": []}
    return gh


def _probed_real_gh(db: Database) -> Any:
    """A real GitHubProviderAdapter whose ``gh auth status`` probe answered 'testuser'."""
    import subprocess

    from holdspeak.services.github_provider import GitHubProviderAdapter

    def runner(argv: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, stdout="Logged in to github.com account testuser (keyring)", stderr="")

    adapter = GitHubProviderAdapter(db=db, runner=runner)
    adapter.connection_status(OWNER)
    return adapter


def _disconnected_gh() -> MagicMock:
    gh = MagicMock()
    gh.connection_status.return_value = {
        "state": "disconnected",
        "display": {"recovery_hint": "gh auth login"},
        "error_code": "auth_required",
        "error_detail": "Not authenticated",
    }
    return gh


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def connections_rig(tmp_path, monkeypatch):
    """Minimal rig: connections router wired to a real FastAPI app."""
    reset_database()
    db = Database(tmp_path / "conn-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    conn_svc = ConnectionsService()  # no adapters -> all not_configured

    ctx = WebContext(
        get_state=lambda: {},
        connections_service=conn_svc,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_connections_router(ctx))
    client = TestClient(app)
    yield db, client, conn_svc
    reset_database()


@pytest.fixture
def setup_rig(tmp_path, monkeypatch):
    """Full rig with setup + connections for annotation + cap tests."""
    reset_database()
    db = Database(tmp_path / "setup-conn.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    gh_adapter = _connected_gh()
    # PHILO-9-02 B1 (Codex Astra r1 finding 8): the Connections list reads the
    # REAL adapter's stored probe -- probed once through the adapter's own
    # runner seam, never a double that invents the stored fields.
    conn_svc = ConnectionsService(github_adapter=_probed_real_gh(db))

    project_svc = ProjectService(db)
    watch_svc = WatchService(db)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=watch_svc,
        github_adapter=gh_adapter,
        connections_service=conn_svc,
    )

    ctx = WebContext(
        get_state=lambda: {},
        project_service=project_svc,
        project_setup_service=setup_svc,
        connections_service=conn_svc,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_connections_router(ctx))
    app.include_router(build_project_setup_router(ctx))
    client = TestClient(app)
    yield db, client, setup_svc, gh_adapter
    reset_database()


# ── GET /api/connections ─────────────────────────────────────────────


class TestListConnections:
    def test_returns_five_tools(self, connections_rig) -> None:
        db, client, svc = connections_rig
        resp = client.get("/api/connections")
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data
        ids = [t["provider_id"] for t in data["tools"]]
        assert ids == ["github", "jira", "confluence", "calendar", "models"]  # HS-174: Confluence is the third source

    def test_all_not_configured_when_no_adapters(self, connections_rig) -> None:
        db, client, svc = connections_rig
        resp = client.get("/api/connections")
        data = resp.json()
        for tool in data["tools"]:
            assert tool["state"] == DISPLAY_NOT_CONFIGURED


class TestRecheckConnection:
    def test_recheck_returns_entry(self, connections_rig) -> None:
        db, client, svc = connections_rig
        resp = client.post("/api/connections/github/recheck")
        assert resp.status_code == 200
        data = resp.json()
        assert data["provider_id"] == "github"

    def test_recheck_unknown_provider(self, connections_rig) -> None:
        db, client, svc = connections_rig
        resp = client.post("/api/connections/unknown_thing/recheck")
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == DISPLAY_NOT_CONFIGURED
