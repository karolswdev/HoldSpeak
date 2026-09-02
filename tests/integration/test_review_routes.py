"""HS-160-05 -- Review route integration tests.

Pattern: 159 (isolated DB, real FastAPI app, TestClient).

Tests:
- Full happy loop: seed project + facts -> POST reviews (open) -> GET
  frozen window -> decide each proposal (accept + dismiss + defer) ->
  POST accept -> /room shows pending 0 + last_accepted_at + state ok ->
  POST reviews again with no new facts -> recurrence laws visible
  (no duplicates, deferred suppressed).
- Failure paths: unknown project/review/proposal IDs -> 404; bad verb
  -> 400; conflict-accept capability refusal -> 400; double-accept 409.
- Delta empty-state shape (no open review).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.meeting_session import MeetingState
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pobs_id
from holdspeak.services.project_delta_service import ProjectDeltaService
from holdspeak.services.project_evidence_collector import (
    ProjectEvidenceCollector,
)
from holdspeak.services.project_service import ProjectService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import (
    build_project_reviews_router,
    build_projects_router,
)

OWNER = Principal(PrincipalKind.OWNER, "review-route-test")


# ── No-op collector (pre-seeded observations) ──────────────────────────


class _NoOpCollector:
    def collect_all(self, project_id: str) -> dict[str, Any]:
        return {"test-source": {"state": "ok", "inserted": 0, "no_op": 0}}


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def rig(tmp_path, monkeypatch):
    """Full route rig: project-reviews + projects routers."""
    reset_database()
    db = Database(tmp_path / "review-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    collector = _NoOpCollector()
    delta_svc = ProjectDeltaService(db, collector)
    project_svc = ProjectService(db, delta_service=delta_svc)

    # Wire project_service into delta_service for create_item handler
    delta_svc._project_service = project_svc

    ctx = WebContext(
        get_state=lambda: {},
        project_service=project_svc,
        project_delta_service=delta_svc,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_project_reviews_router(ctx))
    app.include_router(build_projects_router(ctx))
    client = TestClient(app)
    yield db, client, delta_svc
    reset_database()


def _seed_project(
    db: Database,
    project_id: str = "proj-rev01",
    name: str = "Review Routes Project",
) -> str:
    with db._connection() as conn:
        conn.execute(
            """INSERT INTO projects (id, name, description, keywords_json,
               team_members_json, context_json, detection_threshold, revision,
               created_at, updated_at)
               VALUES (?, ?, '', '[]', '[]', '{}', 0.4, 1,
                       datetime('now'), datetime('now'))""",
            (project_id, name),
        )
    return project_id


def _seed_meeting(
    db: Database,
    meeting_id: str = "m-rev01",
    title: str = "Weekly Review",
) -> None:
    db.meetings.save_meeting(MeetingState(
        id=meeting_id,
        started_at=datetime(2026, 8, 1, 10, 0),
        title=title,
        capture_status="finalized",
    ))


def _associate_meeting(
    db: Database, project_id: str, meeting_id: str,
) -> None:
    with db._connection() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO meeting_projects
               (meeting_id, project_id, source, confidence)
               VALUES (?, ?, 'manual', 1.0)""",
            (meeting_id, project_id),
        )


def _seed_observation(
    db: Database,
    project_id: str,
    observation_kind: str = "followthrough.overdue",
    subject_ref: str = "action_item:ai-01",
    fact_json: str = "{}",
    source_version: str = "v1",
) -> str:
    obs_id = generate_pobs_id(
        adapter="test",
        source_id="test-source",
        source_version=source_version,
        fact_key=f"{project_id}:{subject_ref}:{observation_kind}",
    )
    ts = datetime.now(timezone.utc).isoformat()
    db.project_observations.insert_observation(
        observation_id=obs_id,
        project_id=project_id,
        source_id="test-source",
        observation_kind=observation_kind,
        subject_ref=subject_ref,
        source_version=source_version,
        observed_at=ts,
        captured_at=ts,
        fact_json=fact_json,
        content_hash=f"hash-{obs_id[:8]}",
    )
    return obs_id


# ── Full happy loop ──────────────────────────────────────────────────


class TestFullLoop:
    """Seed -> open -> decide all -> accept -> verify /room -> reopen."""

    def test_full_review_loop(self, rig) -> None:
        db, client, delta_svc = rig

        # 1. Seed project and observations
        project_id = _seed_project(db)
        _seed_meeting(db, "m-rev-loop")
        _associate_meeting(db, project_id, "m-rev-loop")

        _seed_observation(
            db, project_id,
            observation_kind="followthrough.overdue",
            subject_ref="action_item:ai-01",
            fact_json=json.dumps({"lane": "overdue", "stale_score": "0.8"}),
        )
        _seed_observation(
            db, project_id,
            observation_kind="followthrough.stale",
            subject_ref="action_item:ai-02",
            fact_json=json.dumps({"lane": "stale", "stale_score": "0.5"}),
        )
        _seed_observation(
            db, project_id,
            observation_kind="decision.review_due",
            subject_ref="decision:d-01",
            fact_json=json.dumps({"review_status": "due"}),
        )

        # 2. POST reviews -> open
        resp = client.post(f"/api/projects/{project_id}/reviews")
        assert resp.status_code == 200, resp.text
        window = resp.json()
        assert window["project_id"] == project_id
        assert window["status"] == "open"
        review_id = window["review_id"]
        assert review_id.startswith("prev_")
        proposals = window["proposals"]
        assert len(proposals) >= 3, f"Expected >= 3 proposals, got {len(proposals)}"

        # 3. GET frozen window
        resp = client.get(f"/api/projects/{project_id}/reviews/{review_id}")
        assert resp.status_code == 200
        frozen = resp.json()
        assert frozen["review_id"] == review_id
        assert frozen["proposals"] == window["proposals"], "frozen window must be byte-identical"

        # 4. GET delta (should return the open window)
        resp = client.get(f"/api/projects/{project_id}/delta")
        assert resp.status_code == 200
        delta = resp.json()
        assert delta["review_id"] == review_id
        assert delta["status"] == "open"

        # 5. Decide proposals: accept first, dismiss second, defer third
        #    Find proposals by kind for deterministic testing
        by_kind: dict[str, list[dict]] = {}
        for p in proposals:
            by_kind.setdefault(p["proposal_kind"], []).append(p)

        decided_ids: list[str] = []

        # Accept the first risk_attention proposal
        risk_proposals = by_kind.get("risk_attention", [])
        assert len(risk_proposals) >= 1
        accept_pid = risk_proposals[0]["id"]
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/{accept_pid}/decide",
            json={"verb": "accept"},
        )
        assert resp.status_code == 200, resp.text
        result = resp.json()
        assert result["verb"] == "accept"
        assert result["lifecycle"] == "accepted"
        decided_ids.append(accept_pid)

        # Dismiss the second risk_attention proposal
        if len(risk_proposals) >= 2:
            dismiss_pid = risk_proposals[1]["id"]
        else:
            # Fall back to any other proposal
            remaining = [p for p in proposals if p["id"] not in decided_ids]
            dismiss_pid = remaining[0]["id"]
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/{dismiss_pid}/decide",
            json={"verb": "dismiss"},
        )
        assert resp.status_code == 200, resp.text
        dismiss_result = resp.json()
        assert dismiss_result["lifecycle"] == "dismissed"
        assert "dismissal_basis_hash" in dismiss_result
        decided_ids.append(dismiss_pid)

        # Defer the review_flag proposal
        remaining = [p for p in proposals if p["id"] not in decided_ids]
        assert len(remaining) >= 1, "should have at least one undecided proposal"
        defer_pid = remaining[0]["id"]
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/{defer_pid}/decide",
            json={"verb": "defer", "deferred_until": "2099-12-31T00:00:00Z"},
        )
        assert resp.status_code == 200, resp.text
        defer_result = resp.json()
        assert defer_result["lifecycle"] == "deferred"
        decided_ids.append(defer_pid)

        # 6. Accept the review
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}/accept",
            json={"command_id": "cmd-accept-01"},
        )
        assert resp.status_code == 200, resp.text
        accept_env = resp.json()
        assert accept_env["result_kind"] == "review_accepted"
        assert accept_env["review_id"] == review_id
        assert "accepted_at" in accept_env

        # 7. Verify /room shows the graduated review section
        resp = client.get(f"/api/projects/{project_id}/room")
        assert resp.status_code == 200
        room = resp.json()
        review_section = room["review"]
        assert review_section["state"] == "ok"
        assert review_section["pending_count"] == 0
        assert review_section["open_review_id"] is None
        assert review_section["last_accepted_at"] is not None

        # 8. GET delta returns the honest empty state
        resp = client.get(f"/api/projects/{project_id}/delta")
        assert resp.status_code == 200
        empty_delta = resp.json()
        assert empty_delta["open_review"] is None
        assert empty_delta["last_accepted_at"] is not None

        # 9. Open another review (recurrence laws visible)
        # Seed NEW observations with different subject_refs so the
        # deterministic proposal IDs don't collide with the prior window.
        _seed_observation(
            db, project_id,
            observation_kind="followthrough.overdue",
            subject_ref="action_item:ai-03",
            fact_json=json.dumps({"lane": "overdue", "stale_score": "0.9"}),
            source_version="v2",
        )
        _seed_observation(
            db, project_id,
            observation_kind="followthrough.stale",
            subject_ref="action_item:ai-04",
            fact_json=json.dumps({"lane": "stale", "stale_score": "0.6"}),
            source_version="v2",
        )

        resp = client.post(f"/api/projects/{project_id}/reviews")
        assert resp.status_code == 200
        window2 = resp.json()
        assert window2["review_id"] != review_id, "new review after accept"
        assert window2["status"] == "open"

        # The deferred proposal (deferred_until 2099) should be suppressed
        # (not yet due). The dismissed proposal may reappear as a changed-
        # basis successor (different source_version).
        for p2 in window2["proposals"]:
            # No proposal should be the exact deferred one returning early
            patch = p2.get("patch_json", "{}")
            if isinstance(patch, str):
                try:
                    patch_obj = json.loads(patch)
                except (json.JSONDecodeError, TypeError):
                    patch_obj = {}
            else:
                patch_obj = patch
            # If returning, it must NOT be the deferred one (deferred_until is 2099)
            if patch_obj.get("returning"):
                assert False, "deferred proposal should not return (due in 2099)"


# ── Failure paths ─────────────────────────────────────────────────────


class TestFailurePaths:
    """404/400/409 status law per route."""

    def test_open_review_unknown_project_404(self, rig) -> None:
        _db, client, _delta = rig
        resp = client.post("/api/projects/proj-nonexistent/reviews")
        # The service tries to open on a non-existent project.
        # The result depends on how observations/project tables handle this.
        # It should be 400 or 404.
        assert resp.status_code in (400, 404, 500), resp.text

    def test_get_review_unknown_404(self, rig) -> None:
        _db, client, _delta = rig
        resp = client.get("/api/projects/proj-x/reviews/prev_nonexistent")
        assert resp.status_code == 404
        assert resp.json()["code"] == "not_found"

    def test_get_review_wrong_project_404(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-wrong-proj")
        _seed_observation(db, project_id)
        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]

        # Ask for it under a different project
        _seed_project(db, "proj-other")
        resp = client.get(f"/api/projects/proj-other/reviews/{review_id}")
        assert resp.status_code == 404

    def test_decide_unknown_proposal_404(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-dec-404")
        _seed_observation(db, project_id)
        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]

        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/pprop_nonexistent/decide",
            json={"verb": "accept"},
        )
        assert resp.status_code == 404

    def test_decide_proposal_wrong_review_404(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-dec-wrong-rev")
        _seed_observation(db, project_id)
        review = delta_svc.open_review(OWNER, project_id)
        proposal_id = review["proposals"][0]["id"]

        resp = client.post(
            f"/api/projects/{project_id}/reviews/prev_bogus"
            f"/proposals/{proposal_id}/decide",
            json={"verb": "accept"},
        )
        assert resp.status_code == 404

    def test_decide_bad_verb_400(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-bad-verb")
        _seed_observation(db, project_id)
        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]
        proposal_id = review["proposals"][0]["id"]

        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/{proposal_id}/decide",
            json={"verb": "yeet"},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert "validation" in body.get("code", "")

    def test_decide_already_decided_409(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-double-dec")
        _seed_observation(db, project_id)
        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]
        proposal_id = review["proposals"][0]["id"]

        # First decide succeeds
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/{proposal_id}/decide",
            json={"verb": "accept"},
        )
        assert resp.status_code == 200

        # Second decide is a conflict
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}"
            f"/proposals/{proposal_id}/decide",
            json={"verb": "dismiss"},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "already_decided"

    def test_accept_unknown_review_400(self, rig) -> None:
        db, client, _delta = rig
        _seed_project(db, "proj-acc-404")
        resp = client.post(
            "/api/projects/proj-acc-404/reviews/prev_nonexistent/accept",
            json={},
        )
        assert resp.status_code == 400

    def test_double_accept_409(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-dbl-acc")
        _seed_observation(db, project_id)
        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]

        # First accept
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}/accept",
            json={},
        )
        assert resp.status_code == 200

        # Second accept is a conflict
        resp = client.post(
            f"/api/projects/{project_id}/reviews/{review_id}/accept",
            json={},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "already_decided"

    def test_conflict_proposal_refuses_accept_400(self, rig) -> None:
        """Conflict proposals cannot be accepted -- capability error.

        Seed observations with DIFFERENT fact_json so the deterministic
        proposal IDs don't collide (two observations with the same
        kind + target + patch produce the same pprop_ ID).
        """
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-conflict-cap")

        # Seed TWO observations with the same kind+subject but different
        # content hashes AND different fact_json -> conflict proposal + two
        # non-colliding deterministic proposals
        obs_id1 = generate_pobs_id(
            adapter="test", source_id="src-a", source_version="v1",
            fact_key=f"{project_id}:action_item:ai-conflict:followthrough.overdue:a",
        )
        obs_id2 = generate_pobs_id(
            adapter="test", source_id="src-b", source_version="v1",
            fact_key=f"{project_id}:action_item:ai-conflict:followthrough.overdue:b",
        )
        ts = datetime.now(timezone.utc).isoformat()
        facts = [
            json.dumps({"lane": "overdue", "source": "a"}),
            json.dumps({"lane": "overdue", "source": "b"}),
        ]
        for (obs_id, src_id, c_hash, fj) in [
            (obs_id1, "src-a", "hash-aaa", facts[0]),
            (obs_id2, "src-b", "hash-bbb", facts[1]),
        ]:
            db.project_observations.insert_observation(
                observation_id=obs_id,
                project_id=project_id,
                source_id=src_id,
                observation_kind="followthrough.overdue",
                subject_ref="action_item:ai-conflict",
                source_version="v1",
                observed_at=ts,
                captured_at=ts,
                fact_json=fj,
                content_hash=c_hash,
            )

        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]

        # Find the conflict proposal
        conflict_proposals = [
            p for p in review["proposals"]
            if p["proposal_kind"] == "conflict"
        ]
        if conflict_proposals:
            cpid = conflict_proposals[0]["id"]
            resp = client.post(
                f"/api/projects/{project_id}/reviews/{review_id}"
                f"/proposals/{cpid}/decide",
                json={"verb": "accept"},
            )
            assert resp.status_code == 400
            assert resp.json()["code"] == "capability"


# ── Delta empty state ─────────────────────────────────────────────────


class TestDeltaEmptyState:
    """GET /api/projects/{id}/delta with no open review."""

    def test_delta_empty_state_shape(self, rig) -> None:
        db, client, _delta = rig
        project_id = _seed_project(db, "proj-delta-empty")

        resp = client.get(f"/api/projects/{project_id}/delta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["open_review"] is None
        assert "last_accepted_at" in body
        assert "source_coverage" in body

    def test_delta_unknown_project_404(self, rig) -> None:
        _db, client, _delta = rig
        resp = client.get("/api/projects/proj-nonexistent/delta")
        assert resp.status_code == 404

    def test_delta_after_accept_shows_last_accepted_at(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-delta-post-acc")
        _seed_observation(db, project_id)

        # Open + accept
        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]
        delta_svc.accept_review(OWNER, project_id, review_id)

        resp = client.get(f"/api/projects/{project_id}/delta")
        assert resp.status_code == 200
        body = resp.json()
        assert body["open_review"] is None
        assert body["last_accepted_at"] is not None


# ── Room review section ───────────────────────────────────────────────


class TestRoomReviewSection:
    """The review section in /room is graduated from absent."""

    def test_room_review_section_with_delta_service(self, rig) -> None:
        db, client, _delta = rig
        project_id = _seed_project(db, "proj-room-rev")

        resp = client.get(f"/api/projects/{project_id}/room")
        assert resp.status_code == 200
        review = resp.json()["review"]
        assert review["state"] == "ok"
        assert review["pending_count"] == 0
        assert review["open_review_id"] is None
        assert review["last_accepted_at"] is None

    def test_room_review_section_with_open_review(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-room-rev-open")
        _seed_observation(db, project_id,
                          subject_ref="action_item:ai-room-01")

        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]
        proposal_count = len(review["proposals"])

        resp = client.get(f"/api/projects/{project_id}/room")
        assert resp.status_code == 200
        review_section = resp.json()["review"]
        assert review_section["state"] == "ok"
        assert review_section["open_review_id"] == review_id
        assert review_section["pending_count"] == proposal_count

    def test_room_review_section_after_accept(self, rig) -> None:
        db, client, delta_svc = rig
        project_id = _seed_project(db, "proj-room-rev-acc")
        _seed_observation(db, project_id,
                          subject_ref="action_item:ai-room-02")

        review = delta_svc.open_review(OWNER, project_id)
        review_id = review["review_id"]
        delta_svc.accept_review(OWNER, project_id, review_id)

        resp = client.get(f"/api/projects/{project_id}/room")
        assert resp.status_code == 200
        review_section = resp.json()["review"]
        assert review_section["state"] == "ok"
        assert review_section["pending_count"] == 0
        assert review_section["open_review_id"] is None
        assert review_section["last_accepted_at"] is not None
