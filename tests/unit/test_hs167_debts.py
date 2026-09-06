"""HS-167-02 — the five functional debts, tested.

1. Population toggles persisted (jira_scope answer round-trip)
2. Enrichment receipted (OBSERVE step carries calls count)
3. The acli lock across processes (file lock + typed timeout)
4. The cadence write wire (policy PUT carries cadence, range-fenced)
5. The trigger route (wired -> runs; unwired -> typed refusal)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ── helpers ────────────────────────────────────────────────────────────

def _make_db(tmp_path: Path) -> Any:
    """Create an isolated HoldSpeak DB."""
    db_path = tmp_path / "holdspeak.db"
    from holdspeak.db.core import Database
    return Database(db_path=db_path)


def _owner() -> Any:
    from holdspeak.principals import Principal, PrincipalKind
    return Principal(PrincipalKind.OWNER, "test-owner")


# ── Debt 1: Population toggles persisted ──────────────────────────────


class TestDebt1PopulationToggles:
    """The jira_scope answer round-trips through project_setup_answer."""

    def test_jira_scope_answer_persists_and_resumes(self, tmp_path: Path) -> None:
        db = _make_db(tmp_path)
        from holdspeak.services.project_setup_service import (
            ProjectSetupService,
            Q_JIRA_SCOPE,
        )

        svc = ProjectSetupService(db)
        principal = _owner()

        # Start a session
        session = svc.start_setup(principal)
        session_id = session["id"]

        # Submit a jira_scope answer
        scope = {
            "connectionRef": "mysite.atlassian.net|me@example.com",
            "projects": ["KAN", "DEV"],
            "issueTypes": ["Bug", "Story"],
            "statusCategories": ["To Do", "In Progress"],
            "jql": "priority = High",
        }
        result = svc.answer(
            principal, session_id, Q_JIRA_SCOPE,
            {"text": json.dumps(scope)},
        )
        assert result["question_id"] == Q_JIRA_SCOPE

        # Resume: get_setup should return the jira_scope answer
        resumed = svc.get_setup(session_id)
        assert Q_JIRA_SCOPE in resumed["answers"]
        answer = resumed["answers"][Q_JIRA_SCOPE]
        # The scope JSON is stored in the answer's original field
        answer_data = answer.get("answer", {})
        if isinstance(answer_data, str):
            answer_data = json.loads(answer_data)
        original = answer_data.get("original", "")
        restored = json.loads(original)
        assert restored["projects"] == ["KAN", "DEV"]
        assert restored["connectionRef"] == "mysite.atlassian.net|me@example.com"

    def test_jira_scope_answer_multiple_revisions(self, tmp_path: Path) -> None:
        db = _make_db(tmp_path)
        from holdspeak.services.project_setup_service import (
            ProjectSetupService,
            Q_JIRA_SCOPE,
        )

        svc = ProjectSetupService(db)
        principal = _owner()

        session = svc.start_setup(principal)
        session_id = session["id"]

        # First answer
        svc.answer(
            principal, session_id, Q_JIRA_SCOPE,
            {"text": json.dumps({"connectionRef": "a|b", "projects": ["A"]})},
        )
        # Second answer (revision 2)
        svc.answer(
            principal, session_id, Q_JIRA_SCOPE,
            {"text": json.dumps({"connectionRef": "a|b", "projects": ["A", "B"]})},
        )

        # Resume should return the LATEST revision
        resumed = svc.get_setup(session_id)
        answer = resumed["answers"][Q_JIRA_SCOPE]
        answer_data = answer.get("answer", {})
        if isinstance(answer_data, str):
            answer_data = json.loads(answer_data)
        restored = json.loads(answer_data.get("original", ""))
        assert restored["projects"] == ["A", "B"]


# ── Debt 2: Enrichment receipted ──────────────────────────────────────


class TestDebt2EnrichmentReceipted:
    """The OBSERVE step carries the calls count from the evaluation."""

    def test_observe_step_carries_calls_count(self, tmp_path: Path) -> None:
        db = _make_db(tmp_path)
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector

        # Create a project and a watch with a known evaluation
        principal = _owner()
        project_id = "proj_test123"

        # Insert a minimal project row
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Test Project"),
            )

        # Create a watch bound to the project
        watch_id = "watch_test456"
        db.automations.create_watch(
            watch_id=watch_id,
            connector_id="jira",
            query_kind="issues",
            name="Test Watch",
            query={"connection_ref": "site|email"},
            enabled=True,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, state="active",
        )

        # Create a project_source binding
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO project_sources "
                "(id, project_id, source_ref, enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))",
                ("psrc_test789", project_id, f"watch:{watch_id}"),
            )

        # Create an evaluation with metadata_json containing calls=4
        db.automations.create_evaluation(
            evaluation_id="weval_test001",
            watch_id=watch_id,
            watch_revision=0,
            source_revision="abc123",
            trigger_kind="scheduled",
            state="completed",
            started_at="2026-09-03T00:00:00+00:00",
            completed_at="2026-09-03T00:00:01+00:00",
            metadata_json=json.dumps({"calls": 4}),
        )

        # Build the steward with a mock collector (we test the meta, not collection)
        mock_collector = MagicMock(spec=ProjectEvidenceCollector)
        mock_collector.collect_all.return_value = {"native:meetings": {"state": "ok"}}

        mock_delta = MagicMock()
        svc = ProjectStewardService(db, mock_collector, mock_delta)

        # Run the OBSERVE phase
        result = svc._phase_observe(principal, project_id)

        # The result should include calls=4
        assert result.get("calls") == 4
        assert result.get("source_meta", {}).get(watch_id, {}).get("calls") == 4

    def test_observe_step_receipt_json_set(self, tmp_path: Path) -> None:
        """A full run_once sets receipt_json on the OBSERVE step."""
        db = _make_db(tmp_path)
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
        from holdspeak.services.project_delta_service import ProjectDeltaService

        principal = _owner()
        project_id = "proj_receipt"

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Receipt Test"),
            )

        watch_id = "watch_receipt"
        db.automations.create_watch(
            watch_id=watch_id,
            connector_id="jira",
            query_kind="issues",
            name="Receipt Watch",
            query={},
            enabled=True,
        )
        db.automations.update_watch_spec(watch_id, project_id=project_id, state="active")

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO project_sources "
                "(id, project_id, source_ref, enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, 1, datetime('now'), datetime('now'))",
                ("psrc_receipt", project_id, f"watch:{watch_id}"),
            )

        db.automations.create_evaluation(
            evaluation_id="weval_receipt",
            watch_id=watch_id,
            source_revision="def456",
            trigger_kind="scheduled",
            state="completed",
            metadata_json=json.dumps({"calls": 4}),
        )

        mock_collector = MagicMock(spec=ProjectEvidenceCollector)
        mock_collector.collect_all.return_value = {}
        mock_delta = MagicMock()
        mock_delta.open_review.return_value = {"id": "rev1", "proposals": []}

        svc = ProjectStewardService(
            db, collector=mock_collector, delta=mock_delta,
        )

        run_id = svc.run_once(principal, project_id)

        # Read the OBSERVE step
        steps = db.steward_steps.list_steps(run_id)
        observe_step = next(
            (s for s in steps if s["phase"] == "observe"),
            None,
        )
        assert observe_step is not None
        receipt = json.loads(observe_step.get("receipt_json") or "{}")
        assert receipt.get("calls") == 4


# ── Debt 3: The acli lock across processes ────────────────────────────


class TestDebt3AcliFileLock:
    """The acli lock is a file lock with typed timeout."""

    def test_lock_acquires_and_releases(self, tmp_path: Path) -> None:
        """Basic acquire/release cycle works."""
        with patch(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            return_value=tmp_path / ".acli.lock",
        ):
            from holdspeak.services.jira_provider import _CrossProcessLock
            lock = _CrossProcessLock(timeout=2.0)
            with lock:
                # Lock is held
                assert (tmp_path / ".acli.lock").exists()
            # Lock released

    def test_lock_timeout_raises_typed_error(self, tmp_path: Path) -> None:
        """A second process holding the lock causes a typed timeout."""
        lockfile = tmp_path / ".acli.lock"

        # Hold the lock from a subprocess
        holder_script = textwrap.dedent(f"""\
            import fcntl, os, sys, time
            fd = os.open({str(lockfile)!r}, os.O_CREAT | os.O_RDWR)
            fcntl.flock(fd, fcntl.LOCK_EX)
            sys.stdout.write("locked\\n")
            sys.stdout.flush()
            time.sleep(10)
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        """)

        proc = subprocess.Popen(
            [sys.executable, "-c", holder_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        try:
            # Wait for the subprocess to acquire the lock
            line = proc.stdout.readline()
            assert b"locked" in line

            # Now try to acquire the lock with a short timeout
            with patch(
                "holdspeak.services.jira_provider._acli_lockfile_path",
                return_value=lockfile,
            ):
                from holdspeak.services.jira_provider import _CrossProcessLock
                from holdspeak.services.errors import ServiceError
                lock = _CrossProcessLock(timeout=0.3)
                with pytest.raises(ServiceError) as exc_info:
                    with lock:
                        pass
                assert exc_info.value.code == "lock_timeout"
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_lock_reentrancy_same_thread(self, tmp_path: Path) -> None:
        """The in-process RLock allows reentrant acquisition."""
        with patch(
            "holdspeak.services.jira_provider._acli_lockfile_path",
            return_value=tmp_path / ".acli.lock",
        ):
            from holdspeak.services.jira_provider import _CrossProcessLock
            lock = _CrossProcessLock(timeout=2.0)
            # RLock allows reentrancy within the same thread
            lock._rlock.acquire()
            lock._rlock.acquire()
            lock._rlock.release()
            lock._rlock.release()


# ── Debt 4: The cadence write wire ────────────────────────────────────


class TestDebt4CadenceWriteWire:
    """evaluation_cadence_minutes validation and write in policy PUT."""

    def test_cadence_range_fence_floor(self, tmp_path: Path) -> None:
        """Cadence below 1 is rejected."""
        db = _make_db(tmp_path)
        from holdspeak.web.routes.steward import build_steward_router
        from unittest.mock import AsyncMock

        # Build a mock context
        ctx = MagicMock()
        ctx.project_steward_service = MagicMock()
        ctx.project_steward_service._db = db
        router = build_steward_router(ctx)

        # Find the PUT policy handler
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.put(
            "/api/projects/proj1/steward/policy",
            json={"evaluation_cadence_minutes": 0},
        )
        assert response.status_code == 400
        body = response.json()
        assert "evaluation_cadence_minutes" in body.get("message", "")

    def test_cadence_range_fence_ceiling(self, tmp_path: Path) -> None:
        """Cadence above 10080 is rejected."""
        db = _make_db(tmp_path)

        ctx = MagicMock()
        ctx.project_steward_service = MagicMock()
        ctx.project_steward_service._db = db

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(build_steward_router(ctx))
        client = TestClient(app)

        response = client.put(
            "/api/projects/proj1/steward/policy",
            json={"evaluation_cadence_minutes": 10081},
        )
        assert response.status_code == 400

    def test_cadence_valid_updates_watches(self, tmp_path: Path) -> None:
        """A valid cadence value updates the project's watches."""
        db = _make_db(tmp_path)

        # Create project + policy + watch
        project_id = "proj_cadence"
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Cadence Test"),
            )

        watch_id = "watch_cadence"
        db.automations.create_watch(
            watch_id=watch_id,
            connector_id="gh",
            query_kind="pull_requests",
            name="Cadence Watch",
            query={},
            enabled=True,
        )
        db.automations.update_watch_spec(
            watch_id, project_id=project_id, state="active",
        )

        # Insert a policy
        db.steward_policies.insert_policy(
            policy_id="pol_cadence",
            project_id=project_id,
            enabled=1,
        )

        ctx = MagicMock()
        ctx.project_steward_service = MagicMock()
        ctx.project_steward_service._db = db

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(build_steward_router(ctx))
        client = TestClient(app)

        response = client.put(
            f"/api/projects/{project_id}/steward/policy",
            json={"evaluation_cadence_minutes": 120},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True

        # Verify the watch was updated
        watch = db.automations.get_watch(watch_id)
        assert watch["evaluation_cadence_minutes"] == 120


# ── Debt 5: The trigger route ─────────────────────────────────────────


class TestDebt5TriggerRoute:
    """The trigger route calls evaluate_due/run_due through the conductor seam."""

    def test_trigger_unwired_typed_refusal(self, tmp_path: Path) -> None:
        """When scheduler services are not wired, returns typed refusal."""
        db = _make_db(tmp_path)

        ctx = MagicMock()
        ctx.project_steward_service = MagicMock()
        ctx.project_steward_service._db = db

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(build_steward_router(ctx))
        client = TestClient(app)

        # Ensure the conductor services are NOT wired
        import holdspeak.workbench_conductor as conductor
        with patch.object(conductor, "_watch_service", None), \
             patch.object(conductor, "_steward_service", None):
            response = client.post("/api/steward/trigger")
            assert response.status_code == 503
            body = response.json()
            assert body["code"] == "scheduler_not_wired"

    def test_trigger_wired_runs(self, tmp_path: Path) -> None:
        """When wired, calls evaluate_due + run_due and returns outcomes."""
        db = _make_db(tmp_path)

        ctx = MagicMock()
        ctx.project_steward_service = MagicMock()
        ctx.project_steward_service._db = db

        from holdspeak.web.routes.steward import build_steward_router
        from starlette.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(build_steward_router(ctx))
        client = TestClient(app)

        mock_watch_svc = MagicMock()
        mock_watch_svc.evaluate_due.return_value = [
            {"watch_id": "w1", "outcome": "evaluated"},
        ]
        mock_steward_svc = MagicMock()
        mock_steward_svc.run_due.return_value = [
            {"effect_id": "e1", "outcome": "run_started"},
        ]

        import holdspeak.workbench_conductor as conductor
        with patch.object(conductor, "_watch_service", mock_watch_svc), \
             patch.object(conductor, "_steward_service", mock_steward_svc):
            response = client.post("/api/steward/trigger")
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert len(body["evaluate_outcomes"]) == 1
            assert len(body["run_outcomes"]) == 1
            mock_watch_svc.evaluate_due.assert_called_once()
            mock_steward_svc.run_due.assert_called_once()

    def test_trigger_same_watermark_creates_run_and_reconciles(self, tmp_path: Path) -> None:
        """The 163 same-watermark law: a second call creates a run that
        reconciles at the act step -- never route-level dedup."""
        db = _make_db(tmp_path)
        from holdspeak.services.project_steward_service import ProjectStewardService
        from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector

        principal = _owner()
        project_id = "proj_watermark"

        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects (id, name, created_at, updated_at) "
                "VALUES (?, ?, datetime('now'), datetime('now'))",
                (project_id, "Watermark Test"),
            )

        mock_collector = MagicMock(spec=ProjectEvidenceCollector)
        mock_collector.collect_all.return_value = {}
        mock_delta = MagicMock()
        mock_delta.open_review.return_value = {"id": "rev1", "proposals": []}

        svc = ProjectStewardService(
            db, collector=mock_collector, delta=mock_delta,
        )

        # First run with a watermark
        watermark = "watch:w1:rev1"
        run_id_1 = svc.run_once(principal, project_id, watermark=watermark)
        assert run_id_1

        # Second run with the SAME watermark -- must succeed (no route-level dedup)
        run_id_2 = svc.run_once(principal, project_id, watermark=watermark)
        assert run_id_2
        assert run_id_2 != run_id_1

        # Both runs exist
        runs = db.steward_runs.list_runs(project_id, limit=10)
        run_ids = {r["id"] for r in runs}
        assert run_id_1 in run_ids
        assert run_id_2 in run_ids
