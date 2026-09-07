"""HS-200-06 (phase200_claim_support) -- the axes on the real wire.

Real FastAPI app, isolated DB, TestClient (the 159/162 pattern).

- A drafted update reaches the face carrying kind, support and
  acceptance on every claim.
- A row written before HS-200-06 reaches the face migrated: source
  linked at most, unreviewed, stamped with the mapping version -- while
  its stored bytes stay exactly as they were.
- Saving an edit through PUT /api/updates/{id} invalidates the support
  of the sentence that changed and keeps its record.
- A published update refuses a claim review (the immutability law).
"""
from __future__ import annotations

import json
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.db.updates import PublishedUpdateError
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pupd_id
from holdspeak.services.project_service import ProjectService
from holdspeak.services.project_update_service import (
    ACCEPTANCE_ACCEPTED,
    ACCEPTANCE_UNREVIEWED,
    CLAIM_SUPPORT_MAPPING_VERSION,
    INVALIDATION_TEXT_EDITED,
    SUPPORT_SOURCE_LINKED,
    SUPPORT_SUPPORTED,
    SUPPORT_UNKNOWN,
    ProjectUpdateService,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes import (
    build_project_updates_router,
    build_projects_router,
)

OWNER = Principal(PrincipalKind.OWNER, "claim-support-wire")
NOW_ISO = "2026-06-15T10:00:00"

_LEGACY_CLAIMS = [
    {
        "refs": ["item:pitem_old_001"],
        "section": "progress",
        "span_id": "s_progress_0",
        "text": "Milestone: Launch -- planned",
    },
    {
        "refs": [],
        "section": "risks_blockers",
        "span_id": "s_risks_blockers_0",
        "text": "Model commentary with no backing.",
        "verified": False,
    },
]


def _seed_project(db: Database, project_id: str = "proj-c2-wire") -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects
               (id, name, description, keywords_json, team_members_json,
                context_json, detection_threshold, revision,
                created_at, updated_at)
               VALUES (?, 'C2 Wire', '', '[]', '[]', '{}', 0.4, 5, ?, ?)""",
            (project_id, NOW_ISO, NOW_ISO),
        )
    return project_id


def _seed_items(db: Database, project_id: str) -> None:
    items = [
        ("pitem_w200000000000000000000000000001", "milestone", "Launch v2.0",
         "planned", "high", "2026-07-01", 1.0),
        ("pitem_w200000000000000000000000000002", "risk", "Vendor lock-in",
         "open", "critical", None, 2.0),
    ]
    with db._connection() as conn:
        for item_id, kind, title, lifecycle, severity, due_at, sort_key in items:
            conn.execute(
                """INSERT INTO project_items
                   (id, project_id, item_type, title, lifecycle, severity,
                    due_at, sort_key, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (item_id, project_id, kind, title, lifecycle, severity,
                 due_at, sort_key, NOW_ISO, NOW_ISO),
            )


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "claim-support-wire.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    project_svc = ProjectService(db)
    update_svc = ProjectUpdateService(
        db, project_service=project_svc, delta_service=None, broker=None,
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
    yield db, TestClient(app), update_svc
    reset_database()


def _claims(update: dict[str, Any]) -> list[dict[str, Any]]:
    return json.loads(update["claims_json"])


class TestAxesOnTheWire:

    def test_drafted_claims_carry_all_three_axes(self, rig):
        db, client, _ = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        resp = client.post(
            f"/api/projects/{pid}/updates/draft",
            json={"generator": "deterministic"},
        )
        assert resp.status_code == 200, resp.text
        claims = _claims(resp.json()["update"])
        assert claims
        for claim in claims:
            assert claim["kind"]
            assert claim["support"] == SUPPORT_SUPPORTED
            assert claim["acceptance"] == ACCEPTANCE_UNREVIEWED
            assert claim["support_record"]["source_version"].startswith(
                f"project:{pid}@r"
            )

    def test_edit_through_the_wire_invalidates_support(self, rig):
        db, client, _ = rig
        pid = _seed_project(db)
        _seed_items(db, pid)

        draft = client.post(
            f"/api/projects/{pid}/updates/draft", json={},
        ).json()["update"]
        target = _claims(draft)[0]

        edited = draft["body_md"].replace(target["text"], "Owner rewrote it")
        resp = client.put(
            f"/api/updates/{draft['id']}", json={"body_md": edited},
        )
        assert resp.status_code == 200, resp.text
        after = {
            c["span_id"]: c for c in _claims(resp.json()["update"])
        }[target["span_id"]]
        assert after["support"] == SUPPORT_SOURCE_LINKED
        assert after["support_record"]["invalidation_reason"] == (
            INVALIDATION_TEXT_EDITED
        )
        assert after["support_record"]["source_version"] == (
            target["support_record"]["source_version"]
        )


class TestLegacyRowsOnTheWire:

    def _seed_legacy(self, db: Database, pid: str) -> str:
        update_id = generate_pupd_id()
        db.project_updates.insert_update(
            update_id=update_id,
            project_id=pid,
            project_revision=5,
            review_id=None,
            draft_revision=1,
            body_md="## Progress\n\n- Milestone: Launch -- planned\n",
            claims_json=json.dumps(_LEGACY_CLAIMS),
            source_manifest_json="{}",
            generator="deterministic",
        )
        return update_id

    def test_list_shows_migrated_axes_and_leaves_the_bytes_alone(self, rig):
        db, client, _ = rig
        pid = _seed_project(db)
        update_id = self._seed_legacy(db, pid)

        resp = client.get(f"/api/projects/{pid}/updates")
        assert resp.status_code == 200, resp.text
        row = next(
            u for u in resp.json()["updates"] if u["id"] == update_id
        )
        claims = {c["span_id"]: c for c in _claims(row)}
        assert claims["s_progress_0"]["support"] == SUPPORT_SOURCE_LINKED
        assert claims["s_progress_0"]["support_mapping_version"] == (
            CLAIM_SUPPORT_MAPPING_VERSION
        )
        assert claims["s_risks_blockers_0"]["support"] == SUPPORT_UNKNOWN
        for claim in claims.values():
            assert claim["acceptance"] == ACCEPTANCE_UNREVIEWED
            assert claim["support"] != SUPPORT_SUPPORTED

        with db._connection() as conn:
            stored = conn.execute(
                "SELECT claims_json FROM project_updates WHERE id = ?",
                (update_id,),
            ).fetchone()[0]
        assert json.loads(stored) == _LEGACY_CLAIMS


class TestPublishedImmutability:

    def test_a_published_update_refuses_a_claim_review(self, rig):
        db, client, svc = rig
        pid = _seed_project(db)
        _seed_items(db, pid)
        draft = client.post(
            f"/api/projects/{pid}/updates/draft", json={},
        ).json()["update"]
        span = _claims(draft)[0]["span_id"]

        assert client.post(
            f"/api/updates/{draft['id']}/publish", json={},
        ).status_code == 200

        with pytest.raises(PublishedUpdateError):
            svc.review_claim(
                OWNER, draft["id"], span, acceptance=ACCEPTANCE_ACCEPTED,
            )
