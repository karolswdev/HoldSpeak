"""HS-163-04 -- Project Steward route integration tests.

Pattern: 162 (isolated DB, real FastAPI app, TestClient).

Tests:
- IMMEDIATE-ID: POST /steward/runs returns the run_id before phase
  work completes (slow-phase fixture proves it).
- POLL-TO-COMPLETED: run -> poll until completed -> summary has effects + receipts.
- STOP-MID-RUN: POST stop -> poll shows interrupted.
- POLICY-ROUND-TRIP: PUT policy -> GET policy matches, validation failures.
- STW-002 ON THE WIRE: second active run -> 409.
- COMMAND-ID REPLAY: same command_id + same hash -> replay.
"""
from __future__ import annotations

import json
import time
import threading
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.project_steward_service import (
    EFFECT_KINDS,
    ProjectStewardService,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_steward_router

OWNER = Principal(PrincipalKind.OWNER, "steward-route-test")

NOW_ISO = "2026-09-01T10:00:00"


# ── Helpers ──────────────────────────────────────────────────────────


def _seed_project(
    db: Database,
    project_id: str = "proj-stw-01",
    name: str = "Steward Routes Project",
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
    """Full route rig: steward router with real service."""
    reset_database()
    db = Database(tmp_path / "steward-routes.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

    svc = ProjectStewardService(
        db,
        collector=None,  # collector/delta not needed for route-level tests
        delta=None,
    )

    ctx = WebContext(
        get_state=lambda: {},
        project_steward_service=svc,
    )

    app = FastAPI()

    from starlette.middleware.base import BaseHTTPMiddleware

    class _OwnerMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

    app.add_middleware(_OwnerMiddleware)
    app.include_router(build_steward_router(ctx))
    client = TestClient(app)
    yield db, client, svc
    reset_database()


# ── IMMEDIATE-ID CONTRACT ────────────────────────────────────────────


class TestImmediateId:
    """POST /steward/runs returns the run_id before phase work completes.

    Proven by patching execute_phases to sleep, then asserting the
    POST returns while the phase work is still running.
    """

    def test_post_returns_before_phases_complete(self, rig) -> None:
        db, client, svc = rig
        pid = _seed_project(db)

        phase_started = threading.Event()
        phase_release = threading.Event()

        original_execute = svc.execute_phases

        def slow_execute(principal, run_id, project_id):
            phase_started.set()
            phase_release.wait(timeout=10)
            original_execute(principal, run_id, project_id)

        with patch.object(svc, "execute_phases", side_effect=slow_execute):
            resp = client.post(
                f"/api/projects/{pid}/steward/runs",
                json={},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        assert body["run_id"] is not None
        run_id = body["run_id"]
        assert run_id.startswith("pstrun_")

        # The phase work should have started (daemon thread was spawned)
        assert phase_started.wait(timeout=5), "daemon thread did not start"

        # The run should still be queued or running (not completed)
        run = db.steward_runs.get_run(run_id)
        assert run is not None
        assert run["state"] in ("queued", "running")

        # Release the phase work so it completes
        phase_release.set()


# ── POLL-TO-COMPLETED ────────────────────────────────────────────────


class TestPollToCompleted:
    """Run -> poll until completed -> summary present."""

    def test_full_loop(self, rig) -> None:
        db, client, svc = rig
        pid = _seed_project(db)

        # Patch execute_phases to complete immediately with an honest
        # run record (no collaborators wired).
        def mock_execute(principal, run_id, project_id):
            """Simulate a successful run with steps."""
            from holdspeak.project_contracts import generate_pststep_id
            db.steward_runs.update_run_state(run_id, state="running", phase="observe")
            for i, phase in enumerate(("observe", "compare", "propose", "act", "verify", "record")):
                step_id = generate_pststep_id()
                db.steward_steps.insert_step(
                    step_id=step_id,
                    run_id=run_id,
                    phase=phase,
                    seq=i,
                    state="completed",
                    effect_kind=f"phase:{phase}",
                    idempotency_key=f"{run_id}:{phase}",
                )
                db.steward_steps.update_step(
                    step_id,
                    state="completed",
                    observed_state_json=json.dumps({"ok": True}),
                    receipt_json=json.dumps({"action": phase, "result": "ok"}),
                )
            summary = json.dumps({
                "outcome": "completed",
                "phases_completed": list(("observe", "compare", "propose", "act", "verify", "record")),
            })
            db.steward_runs.update_run_state(
                run_id, state="completed", summary_json=summary,
            )

        with patch.object(svc, "execute_phases", side_effect=mock_execute):
            # Start the run
            resp = client.post(
                f"/api/projects/{pid}/steward/runs",
                json={},
            )
            assert resp.status_code == 200, resp.text
            run_id = resp.json()["run_id"]

        # Wait for daemon thread to finish
        time.sleep(0.5)

        # Poll the run
        resp = client.get(f"/api/steward/runs/{run_id}")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        run = body["run"]
        steps = body["steps"]

        assert run["state"] == "completed"
        assert run["summary"]["outcome"] == "completed"
        assert len(steps) == 6

        # Each step has the required fields
        for step in steps:
            assert "id" in step
            assert "phase" in step
            assert "seq" in step
            assert "state" in step
            assert "effect_kind" in step
            assert "idempotency_key" in step
            assert "expected" in step
            assert "observed" in step
            assert "receipt" in step
            assert step["state"] == "completed"
            assert step["receipt"]["result"] == "ok"

    def test_list_runs(self, rig) -> None:
        db, client, svc = rig
        pid = _seed_project(db, project_id="proj-list-01")

        def mock_execute(principal, run_id, project_id):
            summary = json.dumps({"outcome": "completed"})
            db.steward_runs.update_run_state(
                run_id, state="completed", summary_json=summary,
            )

        with patch.object(svc, "execute_phases", side_effect=mock_execute):
            client.post(f"/api/projects/{pid}/steward/runs", json={})

        time.sleep(0.3)

        resp = client.get(f"/api/projects/{pid}/steward/runs")
        assert resp.status_code == 200, resp.text
        runs = resp.json()["runs"]
        assert len(runs) >= 1
        assert runs[0]["project_id"] == pid


# ── STOP MID-RUN ─────────────────────────────────────────────────────


class TestStopMidRun:
    """POST stop -> poll shows interrupted."""

    def test_stop_lands_interrupted(self, rig) -> None:
        db, client, svc = rig
        pid = _seed_project(db, project_id="proj-stop-01")

        phase_started = threading.Event()
        stop_done = threading.Event()

        def blocking_execute(principal, run_id, project_id):
            db.steward_runs.update_run_state(run_id, state="running", phase="observe")
            phase_started.set()
            # Wait for stop to be sent
            stop_done.wait(timeout=10)
            # Check stop and honor it
            run = db.steward_runs.get_run(run_id)
            if run and run["state"] == "stopping":
                summary = json.dumps({
                    "outcome": "interrupted",
                    "reason": "stop_requested",
                    "interrupted_phase": "observe",
                })
                db.steward_runs.update_run_state(
                    run_id, state="interrupted", summary_json=summary,
                )

        with patch.object(svc, "execute_phases", side_effect=blocking_execute):
            # Start the run
            resp = client.post(
                f"/api/projects/{pid}/steward/runs",
                json={},
            )
            assert resp.status_code == 200
            run_id = resp.json()["run_id"]

            # Wait for phase to start
            assert phase_started.wait(timeout=5)

            # Send stop
            resp = client.post(f"/api/steward/runs/{run_id}/stop")
            assert resp.status_code == 200, resp.text
            assert resp.json()["success"] is True

            # Release the phase work
            stop_done.set()

        # Wait for daemon to finish
        time.sleep(0.5)

        # Poll and verify interrupted
        resp = client.get(f"/api/steward/runs/{run_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["run"]["state"] == "interrupted"
        assert body["run"]["summary"]["outcome"] == "interrupted"

    def test_stop_unknown_run_404(self, rig) -> None:
        _, client, _ = rig
        resp = client.post("/api/steward/runs/pstrun_nonexistent00000000000000000/stop")
        assert resp.status_code == 404


# ── POLICY ROUND-TRIP ────────────────────────────────────────────────


class TestPolicyRoundTrip:
    """PUT policy -> GET policy matches, validation failures."""

    def test_create_and_get_policy(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-01")

        # Create policy
        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={
                "eligible_effect_kinds": ["refresh_sources", "draft_update"],
                "max_retries": 5,
                "max_actions_per_run": 20,
                "cooldown_seconds": 60,
                "bounds": {"max_proposals": 10},
                "enabled": True,
            },
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["success"] is True
        policy = body["policy"]
        assert policy["eligible_effect_kinds"] == ["refresh_sources", "draft_update"]
        assert policy["max_retries"] == 5
        assert policy["max_actions_per_run"] == 20
        assert policy["cooldown_seconds"] == 60
        assert policy["bounds"] == {"max_proposals": 10}
        assert policy["enabled"] is True

        # Get policy
        resp = client.get(f"/api/projects/{pid}/steward/policy")
        assert resp.status_code == 200
        got = resp.json()["policy"]
        assert got["id"] == policy["id"]
        assert got["eligible_effect_kinds"] == ["refresh_sources", "draft_update"]

    def test_update_existing_policy(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-02")

        # Create
        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"max_retries": 3},
        )
        assert resp.status_code == 200
        policy_id = resp.json()["policy"]["id"]

        # Update
        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"max_retries": 7},
        )
        assert resp.status_code == 200
        assert resp.json()["policy"]["id"] == policy_id
        assert resp.json()["policy"]["max_retries"] == 7

    def test_no_policy_returns_null(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-03")

        resp = client.get(f"/api/projects/{pid}/steward/policy")
        assert resp.status_code == 200
        assert resp.json()["policy"] is None

    def test_invalid_effect_kind_rejected(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-04")

        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"eligible_effect_kinds": ["nonexistent_kind"]},
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "validation_error"
        assert "nonexistent_kind" in resp.json()["message"]

    def test_negative_max_retries_rejected(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-05")

        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"max_retries": -1},
        )
        assert resp.status_code == 400
        assert resp.json()["code"] == "validation_error"

    def test_max_retries_ceiling(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-06")

        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"max_retries": 999},
        )
        assert resp.status_code == 400
        assert "100" in resp.json()["message"]

    def test_max_actions_ceiling(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-07")

        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"max_actions_per_run": 9999},
        )
        assert resp.status_code == 400
        assert "1000" in resp.json()["message"]

    def test_cooldown_ceiling(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-08")

        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"cooldown_seconds": 999999},
        )
        assert resp.status_code == 400
        assert "86400" in resp.json()["message"]

    def test_enabled_must_be_bool(self, rig) -> None:
        db, client, _ = rig
        pid = _seed_project(db, project_id="proj-pol-09")

        resp = client.put(
            f"/api/projects/{pid}/steward/policy",
            json={"enabled": "yes"},
        )
        assert resp.status_code == 400
        assert "boolean" in resp.json()["message"]


# ── STW-002 ON THE WIRE ─────────────────────────────────────────────


class TestActiveRunConflict:
    """STW-002: second active run -> 409."""

    def test_second_run_409(self, rig) -> None:
        db, client, svc = rig
        pid = _seed_project(db, project_id="proj-002-01")

        phase_hold = threading.Event()

        def blocking_execute(principal, run_id, project_id):
            db.steward_runs.update_run_state(run_id, state="running", phase="observe")
            phase_hold.wait(timeout=10)

        with patch.object(svc, "execute_phases", side_effect=blocking_execute):
            # First run succeeds
            resp1 = client.post(
                f"/api/projects/{pid}/steward/runs",
                json={},
            )
            assert resp1.status_code == 200
            assert resp1.json()["success"] is True

            # Second run should be refused with 409
            resp2 = client.post(
                f"/api/projects/{pid}/steward/runs",
                json={},
            )
            assert resp2.status_code == 409, resp2.text
            assert resp2.json()["code"] == "active_run_exists"

            phase_hold.set()


# ── COMMAND-ID REPLAY ────────────────────────────────────────────────


class TestCommandReplay:
    """command_id idempotency: same id + same hash => replay."""

    def test_run_once_replay(self, rig) -> None:
        db, client, svc = rig
        pid = _seed_project(db, project_id="proj-rep-01")

        def mock_execute(principal, run_id, project_id):
            summary = json.dumps({"outcome": "completed"})
            db.steward_runs.update_run_state(
                run_id, state="completed", summary_json=summary,
            )

        cmd = "cmd-replay-stw-01"
        with patch.object(svc, "execute_phases", side_effect=mock_execute):
            resp1 = client.post(
                f"/api/projects/{pid}/steward/runs",
                json={"command_id": cmd},
            )
            assert resp1.status_code == 200
            run_id_1 = resp1.json()["run_id"]

        time.sleep(0.3)

        # Second call with same command_id should replay
        resp2 = client.post(
            f"/api/projects/{pid}/steward/runs",
            json={"command_id": cmd},
        )
        assert resp2.status_code == 200
        assert resp2.json()["run_id"] == run_id_1


# ── NOT-FOUND PATHS ─────────────────────────────────────────────────


class TestNotFound:
    """Unknown run -> 404."""

    def test_get_unknown_run(self, rig) -> None:
        _, client, _ = rig
        resp = client.get("/api/steward/runs/pstrun_nonexistent00000000000000000")
        assert resp.status_code == 404

    def test_stop_unknown_run(self, rig) -> None:
        _, client, _ = rig
        resp = client.post("/api/steward/runs/pstrun_nonexistent00000000000000000/stop")
        assert resp.status_code == 404
