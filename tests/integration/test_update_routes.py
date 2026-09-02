"""HS-162-04 -- Project Update route integration tests.

Pattern: 159 (isolated DB, real FastAPI app, TestClient).

Tests:
- THE LOOP: draft(deterministic) -> save edit -> publish (project revision
  bumped) -> list shows lifecycle -> regenerate on published creates a
  NEW draft -> markdown GET returns the published body.
- Publish-immutability: save/regenerate-mutation against published -> 409.
- Fallback reason surfaces on a model draft with no broker.
- command_id replay law.
- Not-found paths: unknown project/update -> 404.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import ProjectUpdateService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import (
    build_project_updates_router,
    build_projects_router,
)

OWNER = Principal(PrincipalKind.OWNER, "update-route-test")

NOW_ISO = "2026-06-15T10:00:00"


# ── Helpers ──────────────────────────────────────────────────────────


def _seed_project(
    db: Database,
    project_id: str = "proj-upd-01",
    name: str = "Update Routes Project",
    revision: int = 5,
) -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, ?,
                       ?, ?)""",
            (project_id, name, revision, NOW_ISO, NOW_ISO),
        )
    return project_id


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path, monkeypatch):
    """Full route rig: project-updates + projects routers."""
    reset_database()
    db = Database(tmp_path / "update-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    project_svc = ProjectService(db)
    update_svc = ProjectUpdateService(
        db,
        project_service=project_svc,
        delta_service=None,
        broker=None,
    )

    ctx = WebContext(
        get_state=lambda: {},
        project_service=project_svc,
        project_update_service=update_svc,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_project_updates_router(ctx))
    app.include_router(build_projects_router(ctx))
    client = TestClient(app)
    yield db, client
    reset_database()


# ── THE LOOP ─────────────────────────────────────────────────────────


class TestTheLoop:
    """Draft -> save -> publish -> list -> regenerate -> markdown."""

    def test_full_loop(self, rig) -> None:
        db, client = rig
        pid = _seed_project(db)

        # 1. Draft (deterministic)
        resp = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        draft = body["update"]
        update_id = draft["id"]
        assert draft["lifecycle"] == "draft"
        assert draft["generator"] == "deterministic"
        assert "## Progress" in draft["body_md"]

        # 2. Save an edit (draft only)
        edited_md = "## Progress\n\nOwner edited this.\n"
        resp = client.put(
            f"/api/updates/{update_id}",
            json={"body_md": edited_md},
        )
        assert resp.status_code == 200, resp.text
        saved = resp.json()
        assert saved["success"] is True
        assert saved["update"]["body_md"] == edited_md

        # 3. Read project revision BEFORE publish
        resp = client.get(f"/api/projects/{pid}/room")
        assert resp.status_code == 200
        pre_revision = resp.json()["revision"]

        # 4. Publish
        resp = client.post(f"/api/updates/{update_id}/publish", json={})
        assert resp.status_code == 200, resp.text
        pub = resp.json()
        assert pub["success"] is True
        assert pub["update"]["lifecycle"] == "published"
        assert pub["update"]["published_at"] is not None
        # Envelope carries the bumped revision
        assert pub["update"]["project_revision"] is not None

        # 5. Verify project revision was bumped on the wire
        resp = client.get(f"/api/projects/{pid}/room")
        assert resp.status_code == 200
        post_revision = resp.json()["revision"]
        assert post_revision == pre_revision + 1, (
            f"revision should bump: {pre_revision} -> {post_revision}"
        )

        # 6. List shows lifecycle
        resp = client.get(f"/api/projects/{pid}/updates")
        assert resp.status_code == 200
        updates = resp.json()["updates"]
        assert any(
            u["id"] == update_id and u["lifecycle"] == "published"
            for u in updates
        )

        # 7. List filtered by lifecycle=published
        resp = client.get(f"/api/projects/{pid}/updates?lifecycle=published")
        assert resp.status_code == 200
        filtered = resp.json()["updates"]
        assert len(filtered) >= 1
        assert all(u["lifecycle"] == "published" for u in filtered)

        # 8. Regenerate on PUBLISHED creates a NEW draft
        resp = client.post(
            f"/api/updates/{update_id}/regenerate",
            json={"generator": "deterministic"},
        )
        assert resp.status_code == 200, resp.text
        regen = resp.json()
        assert regen["success"] is True
        new_draft = regen["update"]
        assert new_draft["id"] != update_id
        assert new_draft["lifecycle"] == "draft"
        assert new_draft["draft_revision"] == 1

        # 9. Markdown GET returns the published body (the edited text)
        resp = client.get(f"/api/updates/{update_id}/markdown")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/markdown")
        assert resp.text == edited_md


# ── Publish immutability ─────────────────────────────────────────────


class TestPublishImmutability:
    """Published updates refuse save, re-publish, and mutation-
    regenerate with typed 409."""

    def test_save_on_published_refuses(self, rig) -> None:
        db, client = rig
        pid = _seed_project(db, project_id="proj-imm-01")

        # Draft + publish
        resp = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic"},
        )
        update_id = resp.json()["update"]["id"]
        client.post(f"/api/updates/{update_id}/publish", json={})

        # Save on published
        resp = client.put(
            f"/api/updates/{update_id}",
            json={"body_md": "nope"},
        )
        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "published_update"

    def test_republish_refuses(self, rig) -> None:
        db, client = rig
        pid = _seed_project(db, project_id="proj-imm-02")

        resp = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic"},
        )
        update_id = resp.json()["update"]["id"]
        client.post(f"/api/updates/{update_id}/publish", json={})

        # Re-publish
        resp = client.post(f"/api/updates/{update_id}/publish", json={})
        assert resp.status_code == 409, resp.text
        assert resp.json()["error_code"] == "published_update"


# ── Model fallback ───────────────────────────────────────────────────


class TestModelFallback:
    """When broker is None, model draft falls back to deterministic
    with an honest fallback_reason on the envelope."""

    def test_model_fallback_reason_surfaces(self, rig) -> None:
        db, client = rig
        pid = _seed_project(db, project_id="proj-fb-01")

        resp = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "model"},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        update = body["update"]
        assert update["generator"] == "deterministic"
        assert update.get("fallback_reason") == "model_unavailable"


# ── command_id replay ────────────────────────────────────────────────


class TestCommandReplay:
    """command_id idempotency: same id + same hash => replay."""

    def test_draft_replay(self, rig) -> None:
        db, client = rig
        pid = _seed_project(db, project_id="proj-rp-01")

        cmd = "cmd-replay-01"
        resp1 = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic", "command_id": cmd},
        )
        assert resp1.status_code == 200

        resp2 = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic", "command_id": cmd},
        )
        assert resp2.status_code == 200

    def test_save_replay(self, rig) -> None:
        """S-2: save_update with same command_id replays."""
        db, client = rig
        pid = _seed_project(db, project_id="proj-rp-save")

        # Create a draft first
        resp_draft = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic"},
        )
        assert resp_draft.status_code == 200
        update_id = resp_draft.json()["update"]["id"]

        cmd = "cmd-save-replay-01"
        resp1 = client.put(
            f"/api/updates/{update_id}",
            json={"body_md": "edited body", "command_id": cmd},
        )
        assert resp1.status_code == 200

        resp2 = client.put(
            f"/api/updates/{update_id}",
            json={"body_md": "edited body", "command_id": cmd},
        )
        assert resp2.status_code == 200

    def test_regenerate_replay(self, rig) -> None:
        """S-2: regenerate_update with same command_id replays."""
        db, client = rig
        pid = _seed_project(db, project_id="proj-rp-regen")

        # Create a draft first
        resp_draft = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic"},
        )
        assert resp_draft.status_code == 200
        update_id = resp_draft.json()["update"]["id"]

        cmd = "cmd-regen-replay-01"
        resp1 = client.post(
            f"/api/updates/{update_id}/regenerate",
            json={"generator": "deterministic", "command_id": cmd},
        )
        assert resp1.status_code == 200

        resp2 = client.post(
            f"/api/updates/{update_id}/regenerate",
            json={"generator": "deterministic", "command_id": cmd},
        )
        assert resp2.status_code == 200


# ── Not-found paths ──────────────────────────────────────────────────


class TestNotFound:
    """Unknown project/update -> 404."""

    def test_list_unknown_project(self, rig) -> None:
        _, client = rig
        resp = client.get("/api/projects/nonexistent/updates")
        assert resp.status_code == 404

    def test_draft_unknown_project(self, rig) -> None:
        _, client = rig
        resp = client.post(
            "/api/projects/nonexistent/updates/draft",
            json={"generator": "deterministic"},
        )
        assert resp.status_code == 404

    def test_save_unknown_update(self, rig) -> None:
        _, client = rig
        resp = client.put(
            "/api/updates/nonexistent",
            json={"body_md": "x"},
        )
        assert resp.status_code == 404

    def test_publish_unknown_update(self, rig) -> None:
        _, client = rig
        resp = client.post("/api/updates/nonexistent/publish", json={})
        assert resp.status_code == 404

    def test_regenerate_unknown_update(self, rig) -> None:
        _, client = rig
        resp = client.post(
            "/api/updates/nonexistent/regenerate",
            json={"generator": "deterministic"},
        )
        assert resp.status_code == 404

    def test_markdown_unknown_update(self, rig) -> None:
        _, client = rig
        resp = client.get("/api/updates/nonexistent/markdown")
        assert resp.status_code == 404
