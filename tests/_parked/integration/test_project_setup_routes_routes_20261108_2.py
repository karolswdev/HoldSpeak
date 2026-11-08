"""PARKED 20261108 (subtraction day, Lane R): tests of parked routes.

Moved from ``tests/integration/test_project_setup_routes.py``: test_list_all. Not collected.
"""
from __future__ import annotations
"""HS-159-04 -- Project Setup and Watch route integration tests.

Pattern: 153/154 (isolated DB, real FastAPI app, TestClient).

Tests:
- Full happy walk: start -> answer x2 -> suggest -> select -> test ->
  finalize -> created project visible via GET /api/projects/{id}/room
  with its watch binding.
- Failure paths: unknown session/proposal IDs -> 404; invalid answers
  -> 400; finalize with nothing selected = Blank success; abandon then
  finalize -> refusal (409); condition-validation refusal through PUT
  rules.
- Watch routes: list/get/update/pause/retire/test/baseline round-trips
  against a seeded graduated watch.
"""

from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_setup_service import ProjectSetupService
from holdspeak.services.reaction_service import ReactionService
from holdspeak.services.watch_service import WatchService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import (
    build_project_setup_router,
    build_projects_router,
    build_watches_router,
)

OWNER = Principal(PrincipalKind.OWNER, "route-test-owner")


# ── Fixtures ──────────────────────────────────────────────────────────


class _FakeGitHubAdapter:
    """HS-169-07: meeting proposals retired; use a GitHub adapter mock
    so _github_candidates returns at least one template proposal."""

    def connection_status(self, principal):
        return {"state": "connected", "display": {"account": "test"}}

    def snapshot(self, principal, spec):
        return [
            {"number": 1, "title": "Test PR", "state": "open",
             "headRefOid": "abc123", "updatedAt": "2026-09-01T00:00:00Z"},
        ]


def _fake_fetcher(principal, *, connector_id, query_kind, query):
    return [
        {"key": "ITEM-1", "title": "Test Item", "status": "Open",
         "due_at": "2026-09-10", "updated_at": "2026-09-01T00:00:00Z"},
    ]


@pytest.fixture
def rig(tmp_path, monkeypatch):
    """Full route rig: project-setup + watches + projects routers."""
    reset_database()
    db = Database(tmp_path / "setup-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    project_svc = ProjectService(db)
    watch_svc = WatchService(db, snapshot_fetcher=_fake_fetcher)
    setup_svc = ProjectSetupService(
        db,
        project_service=project_svc,
        watch_service=watch_svc,
        github_adapter=_FakeGitHubAdapter(),
    )

    ctx = WebContext(
        get_state=lambda: {},
        project_service=project_svc,
        watch_service=watch_svc,
        project_setup_service=setup_svc,
    )

    app = FastAPI()

    # Stamp OWNER principal on every request (the auth middleware
    # is not wired in test -- routes read request.state.principal).
    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_project_setup_router(ctx))
    app.include_router(build_watches_router(ctx))
    app.include_router(build_projects_router(ctx))
    client = TestClient(app)
    yield db, client
    reset_database()


def _seed_meeting(
    db: Database,
    meeting_id: str = "m-001",
    title: str = "Weekly standup",
) -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 1, 10, 0),
        title=title,
        capture_status="finalized",
    ))


# ── Watch route tests ─────────────────────────────────────────────────


def _seed_watch(
    db: Database,
    watch_id: str = "watch-rt-01",
    project_id: str | None = None,
) -> str:
    """Seed a graduated watch via ReactionService (the legacy creator)."""
    svc = ReactionService(db)
    svc.create_watch(
        OWNER,
        connector_id="gh",
        query_kind="pull_requests",
        name="Route test watch",
        query={"repository": "acme/app"},
        watch_id=watch_id,
    )
    if project_id:
        db.automations.update_watch_spec(watch_id, project_id=project_id)
    return watch_id


class TestWatchList:
    def test_list_all(self, rig) -> None:
        db, client = rig
        _seed_watch(db, "watch-list-a")
        _seed_watch(db, "watch-list-b")
        resp = client.get("/api/watches")
        assert resp.status_code == 200
        watches = resp.json()["watches"]
        ids = [w["id"] for w in watches]
        assert "watch-list-a" in ids
        assert "watch-list-b" in ids

