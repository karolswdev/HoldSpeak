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
from datetime import datetime
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
            return subprocess.CompletedProcess(
                cmd, 0, stdout="[]", stderr="",
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


# ── POST /api/providers/github/validate-repo ─────────────────────────


class TestGitHubValidateRepo:
    def test_valid_repo(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/providers/github/validate-repo",
            json={"owner_repo": "acme/platform"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_missing_owner_repo_400(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/providers/github/validate-repo",
            json={},
        )
        assert resp.status_code == 400
        assert "owner_repo" in resp.json()["message"]

    def test_invalid_format(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/providers/github/validate-repo",
            json={"owner_repo": "no-slash"},
        )
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


# ── POST /api/watches/{id}/evaluate ──────────────────────────────────


class TestWatchEvaluate:
    def test_evaluate_unknown_watch_404(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post("/api/watches/watch-nonexistent/evaluate")
        assert resp.status_code == 404

    def test_evaluate_existing_watch(self, rig) -> None:
        """Seed a watch, baseline it, then evaluate through the route."""
        db, client, _log, _ctx = rig
        from holdspeak.services.reaction_service import ReactionService

        rs = ReactionService(db)
        rs.create_watch(
            OWNER,
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

    def test_discover_fails_when_unauthed(self, unauth_rig) -> None:
        _db, client = unauth_rig
        resp = client.get("/api/providers/github/discover")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "failed"
        assert body["error_code"] is not None


# ── Clarify-scope route ─────────────────────────────────────────────


class TestClarifyScope:
    """The clarify-scope route (HS-161-04 addition to setup routes)."""

    def test_clarify_scope_unknown_session_404(self, rig) -> None:
        _db, client, _log, _ctx = rig
        resp = client.post(
            "/api/project-setups/psetup_none/proposals/wprop_none/clarify-scope",
            json={},
        )
        assert resp.status_code == 404

    def test_clarify_scope_with_discovered_repos(self, rig) -> None:
        """Clarify without repo param triggers discovery."""
        _db, client, _log, _ctx = rig
        # Start a setup session
        resp = client.post("/api/project-setups")
        assert resp.status_code == 200
        session_id = resp.json()["id"]

        # Answer outcome
        client.post(
            f"/api/project-setups/{session_id}/answers",
            json={"question_id": "outcome", "payload": {"text": "Monitor PRs"}},
        )

        # Suggest to get proposals (with github connected)
        resp = client.post(f"/api/project-setups/{session_id}/suggest")
        assert resp.status_code == 200
        proposals = resp.json()["proposals"]
        gh_proposals = [p for p in proposals if p.get("provider_id") == "github"]
        assert len(gh_proposals) >= 1, "connected adapter should produce github proposals"

        proposal_id = gh_proposals[0]["id"]

        # Clarify scope (no repo param -> discovery)
        resp = client.post(
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/clarify-scope",
            json={},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["scope_state"] == "scoped"
        assert len(body["repositories"]) >= 1

    def test_clarify_scope_with_typed_repo(self, rig) -> None:
        """Clarify with repo param uses validate_repo."""
        _db, client, _log, _ctx = rig
        resp = client.post("/api/project-setups")
        session_id = resp.json()["id"]
        client.post(
            f"/api/project-setups/{session_id}/answers",
            json={"question_id": "outcome", "payload": {"text": "Watch CI"}},
        )
        resp = client.post(f"/api/project-setups/{session_id}/suggest")
        gh_proposals = [p for p in resp.json()["proposals"] if p.get("provider_id") == "github"]
        proposal_id = gh_proposals[0]["id"]

        resp = client.post(
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/clarify-scope",
            json={"repo": "acme/platform"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["scope_state"] == "scoped"
        assert "acme/platform" in body["repositories"]


# ── THE FULL COMPOUNDING LOOP THROUGH HTTP ───────────────────────────


class TestFullCompoundingLoop:
    """THE acceptance centerpiece: connect(fake) -> discover -> clarify
    -> test -> finalize -> evaluate -> the Delta review shows the PR
    transition.

    Every step goes through the HTTP routes, not by reaching into the DB.
    """

    def test_full_http_compounding_loop(self, rig) -> None:
        db, client, call_log, ctx = rig

        # ── 1. Connect (verify connection) ───────────────────────
        resp = client.get("/api/providers/github/connection")
        assert resp.status_code == 200
        assert resp.json()["state"] == "connected"

        # ── 2. Discover ──────────────────────────────────────────
        resp = client.get("/api/providers/github/discover")
        assert resp.status_code == 200
        discover_body = resp.json()
        assert discover_body["state"] == "ready"
        assert len(discover_body["items"]) >= 1

        # ── 3. Start setup + answer + suggest ─────────────────────
        resp = client.post("/api/project-setups")
        assert resp.status_code == 200
        session_id = resp.json()["id"]

        resp = client.post(
            f"/api/project-setups/{session_id}/answers",
            json={
                "question_id": "outcome",
                "payload": {"text": "Track CI health for the platform repo"},
            },
        )
        assert resp.status_code == 200

        resp = client.post(f"/api/project-setups/{session_id}/suggest")
        assert resp.status_code == 200
        proposals = resp.json()["proposals"]
        gh_proposals = [p for p in proposals if p.get("provider_id") == "github"]
        assert len(gh_proposals) >= 1
        proposal_id = gh_proposals[0]["id"]

        # ── 4. Select the github proposal ─────────────────────────
        resp = client.post(
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/select",
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "selected"

        # ── 5. Clarify repo scope ─────────────────────────────────
        resp = client.post(
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/clarify-scope",
            json={"repo": "acme/platform"},
        )
        assert resp.status_code == 200
        clarify_body = resp.json()
        assert clarify_body["scope_state"] == "scoped"
        assert "acme/platform" in clarify_body["repositories"]

        # ── 6. Test the proposal ──────────────────────────────────
        resp = client.post(
            f"/api/project-setups/{session_id}/proposals/{proposal_id}/test",
        )
        assert resp.status_code == 200
        test_body = resp.json()
        assert test_body["test_state"] == "passed", (
            f"test_proposal should pass for scoped github proposal; got {test_body}"
        )

        # ── 7. Finalize ──────────────────────────────────────────
        resp = client.post(
            f"/api/project-setups/{session_id}/finalize",
            json={"command_id": "cmd-compound-finalize"},
        )
        assert resp.status_code == 200
        finalize_body = resp.json()
        project_id = finalize_body.get("project_id") or finalize_body.get("id")
        assert project_id, f"finalize must return a project_id; got {finalize_body}"

        # ── 8. Verify project exists via HTTP ─────────────────────
        resp = client.get(f"/api/projects/{project_id}/room")
        assert resp.status_code == 200
        room = resp.json()
        assert room["project_id"] == project_id

        # ── 9. List watches for this project ──────────────────────
        resp = client.get(f"/api/projects/{project_id}/watches")
        assert resp.status_code == 200
        watches = resp.json()["watches"]
        assert len(watches) >= 1, "finalize should have created at least one watch"
        watch_id = watches[0]["id"]

        # ── 10. Baseline the watch ────────────────────────────────
        # Wire a snapshot_fetcher that returns baseline then transition
        evaluation_call = [0]

        def fetcher(principal: Any, **kwargs: Any) -> list[dict[str, Any]]:
            evaluation_call[0] += 1
            if evaluation_call[0] <= 1:
                return [{
                    "number": 42, "title": "Add routing upgrade",
                    "url": "https://github.com/acme/platform/pull/42",
                    "state": "open", "isDraft": False,
                    "reviewRequests": [], "reviewDecision": "",
                    "checks": "success", "headRefOid": "abc123",
                    "updatedAt": "2026-09-01T10:00:00Z",
                }]
            return [{
                "number": 42, "title": "Add routing upgrade",
                "url": "https://github.com/acme/platform/pull/42",
                "state": "open", "isDraft": False,
                "reviewRequests": [], "reviewDecision": "",
                "checks": "failure", "headRefOid": "abc123",
                "updatedAt": "2026-09-01T11:00:00Z",
            }]

        ctx.watch_service = WatchService(db, snapshot_fetcher=fetcher)

        resp = client.post(f"/api/watches/{watch_id}/baseline")
        assert resp.status_code == 200

        # ── 11. Evaluate -> transitions ──────────────────────────
        resp = client.post(f"/api/watches/{watch_id}/evaluate")
        assert resp.status_code == 200
        eval_body = resp.json()
        assert eval_body["success"] is True
        assert eval_body["state"] == "completed"
        assert eval_body["transitions"] >= 1

        # ── 12. The Delta review shows the PR transition ──────────
        # Open a review through the HTTP route
        resp = client.post(f"/api/projects/{project_id}/reviews")
        assert resp.status_code == 200
        review = resp.json()

        # The review must contain proposals including the watch transition
        proposals = review.get("proposals", [])
        watch_proposals = [
            p for p in proposals
            if p.get("proposal_kind") == "observation_attention"
        ]
        assert len(watch_proposals) >= 1, (
            f"The Delta review must show at least one observation_attention "
            f"proposal from the watch transition; got {len(watch_proposals)} "
            f"(total proposals: {len(proposals)})"
        )

        # The proposal carries transition facts
        wp = watch_proposals[0]
        patch = json.loads(wp["patch_json"])
        assert "event_type" in patch, (
            f"Proposal patch must carry event_type; got {patch}"
        )

        # The proposal traces to an observed_fact
        assert wp["producer_kind"] == "observed_fact"

        # ── 13. Verify via GET delta route ────────────────────────
        resp = client.get(f"/api/projects/{project_id}/delta")
        assert resp.status_code == 200
        delta = resp.json()
        # The open review should be reflected
        assert delta.get("open_review") is not None or "proposals" in delta
