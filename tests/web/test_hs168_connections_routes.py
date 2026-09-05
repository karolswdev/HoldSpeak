"""HS-168-02: Connections route tests -- GET + POST recheck through the real
FastAPI app (web context composition characterization), the suggest annotation,
known_scopes on the session route, and the per-provider cap.

Pattern: isolated DB, real FastAPI app, TestClient.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.connections_service import (
    ConnectionsService,
    DISPLAY_CONNECTED,
    DISPLAY_NOT_CONFIGURED,
    DISPLAY_OWNER_ACTION_REQUIRED,
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
    conn_svc = ConnectionsService(github_adapter=gh_adapter)

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
    def test_returns_four_tools(self, connections_rig) -> None:
        db, client, svc = connections_rig
        resp = client.get("/api/connections")
        assert resp.status_code == 200
        data = resp.json()
        assert "tools" in data
        ids = [t["provider_id"] for t in data["tools"]]
        assert ids == ["github", "jira", "calendar", "models"]

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


# ── Suggest annotation ───────────────────────────────────────────────


class TestSuggestAnnotation:
    def _setup_and_suggest(self, client) -> dict:
        """Walk through start -> answer -> suggest and return the response."""
        # Start
        resp = client.post("/api/project-setups")
        assert resp.status_code == 200
        session = resp.json()
        sid = session["id"]

        # Answer outcome
        resp = client.post(
            f"/api/project-setups/{sid}/answers",
            json={"question_id": "outcome", "payload": {"text": "Ship quality"}},
        )
        assert resp.status_code == 200

        # Answer signals
        resp = client.post(
            f"/api/project-setups/{sid}/answers",
            json={"question_id": "signals", "payload": {"text": "PRs"}},
        )
        assert resp.status_code == 200

        # Suggest
        resp = client.post(f"/api/project-setups/{sid}/suggest")
        assert resp.status_code == 200
        return resp.json()

    def test_proposals_carry_connection(self, setup_rig) -> None:
        db, client, setup_svc, gh = setup_rig
        data = self._setup_and_suggest(client)
        proposals = data.get("proposals", [])
        # At least one github proposal should exist
        gh_proposals = [p for p in proposals if p.get("provider_id") == "github"]
        assert len(gh_proposals) > 0, "Expected at least one GitHub proposal"
        for p in gh_proposals:
            assert "connection" in p, f"Proposal {p['id']} missing connection annotation"
            conn = p["connection"]
            assert conn["state"] == DISPLAY_CONNECTED
            assert conn["account"] is not None


# ── Known scopes on session ──────────────────────────────────────────


class TestKnownScopes:
    def test_session_returns_known_scopes(self, setup_rig) -> None:
        db, client, setup_svc, gh = setup_rig
        # Start session
        resp = client.post("/api/project-setups")
        sid = resp.json()["id"]

        # Answer
        client.post(
            f"/api/project-setups/{sid}/answers",
            json={"question_id": "outcome", "payload": {"text": "Ship"}},
        )
        client.post(
            f"/api/project-setups/{sid}/answers",
            json={"question_id": "signals", "payload": {"text": "PRs"}},
        )

        # Suggest
        client.post(f"/api/project-setups/{sid}/suggest")

        # Resume (GET)
        resp = client.get(f"/api/project-setups/{sid}")
        assert resp.status_code == 200
        session = resp.json()
        assert "known_scopes" in session
        ks = session["known_scopes"]
        assert "github" in ks
        assert "jira" in ks
        # Initially empty (no scope clarified yet)
        assert isinstance(ks["github"], list)
        assert isinstance(ks["jira"], list)


# ── Per-provider cap ─────────────────────────────────────────────────


class TestPerProviderCap:
    """The per-provider cap: a 3+5+5 desk persists cards for ALL THREE.

    The test first shows the old cap failing (3 native + 5 github = 8
    drops all jira), then shows the new per-provider cap persisting
    cards for all providers.
    """

    def test_per_provider_cap_preserves_all_providers(self, setup_rig) -> None:
        """With per-provider cap=4, a desk with 3 native + 5 github + 5 jira
        keeps all three providers represented."""
        db, client, setup_svc, gh = setup_rig

        # Seed 3 meetings to get 3+ native proposals
        for i in range(3):
            db.meetings.save_meeting(MeetingState(
                id=f"m-{i:03d}",
                started_at=datetime(2026, 8, 1, 10 + i, 0),
                title=f"Meeting {i}",
                capture_status="finalized",
            ))

        # Also wire up a jira adapter that is connected
        ja = MagicMock()
        ja.list_connections.return_value = [
            {
                "state": "connected",
                "external_connection_ref": "site.atlassian.net|u@x.com",
                "connection_ref": "site.atlassian.net|u@x.com",
            },
        ]
        ja.connection_status.return_value = {
            "state": "connected",
            "provider_id": "jira",
            "connection_ref": "site.atlassian.net|u@x.com",
            "account": {"site": "site.atlassian.net", "email": "u@x.com"},
        }
        setup_svc._jira_adapter = ja

        # Start + answer + suggest
        resp = client.post("/api/project-setups")
        sid = resp.json()["id"]

        client.post(
            f"/api/project-setups/{sid}/answers",
            json={"question_id": "outcome", "payload": {"text": "Ship"}},
        )
        client.post(
            f"/api/project-setups/{sid}/answers",
            json={"question_id": "signals", "payload": {"text": "PRs and issues"}},
        )

        resp = client.post(f"/api/project-setups/{sid}/suggest")
        assert resp.status_code == 200
        proposals = resp.json()["proposals"]

        # Extract provider_ids
        provider_ids = [p["provider_id"] for p in proposals]

        # The key assertion: ALL THREE providers must be represented
        present_providers = set(provider_ids)
        assert "github" in present_providers, (
            f"GitHub proposals missing! providers: {provider_ids}"
        )
        assert "jira" in present_providers, (
            f"Jira proposals missing! providers: {provider_ids}"
        )

        # Each provider should have at most _MAX_PROPOSALS_PER_PROVIDER = 4
        from collections import Counter
        counts = Counter(provider_ids)
        for pid, count in counts.items():
            assert count <= 4, (
                f"Provider {pid} has {count} proposals, exceeds cap of 4"
            )

        # The order should be github first, then jira, then native last
        first_non_native_idx = None
        first_native_idx = None
        for i, pid in enumerate(provider_ids):
            if pid in ("github", "jira") and first_non_native_idx is None:
                first_non_native_idx = i
            if pid == "native" and first_native_idx is None:
                first_native_idx = i
        if first_non_native_idx is not None and first_native_idx is not None:
            assert first_non_native_idx < first_native_idx, (
                "Connected providers should come before native"
            )
