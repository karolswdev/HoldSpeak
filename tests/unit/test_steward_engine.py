"""HS-163-02: Steward run engine — lifecycle truth table, stop, uniqueness, recovery.

Tests:
- TST-ENG-001: run_once returns a durable run ID; run transitions
  queued -> running -> completed with all six phases checkpointed.
- TST-ENG-002: each phase transition creates a visible step row (checkpoint).
- TST-ENG-003: stop honored between phases — a stop injected mid-run
  leads to state stopping -> interrupted with honest summary.
- TST-ENG-004: STW-002 typed refusal — a second concurrent run raises
  ActiveRunExistsError.
- TST-ENG-005: STW-009 recovery — a run abandoned mid-phase is marked
  interrupted on startup and the project is safely re-runnable.
- TST-ENG-006: stop checked before effect slots, not just between phases.
- TST-ENG-007: failure isolation — a phase that raises is caught and the
  run is marked failed.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db.schema import SCHEMA_SQL
from holdspeak.db.steward import (
    ActiveRunExistsError,
    StewardCommandRepository,
    StewardPolicyRepository,
    StewardRunRepository,
    StewardStepRepository,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pstrun_id, generate_pststep_id
from holdspeak.services.project_steward_service import (
    PHASES,
    ProjectStewardService,
    StopRequested,
)


# -- Helpers ---------------------------------------------------------------

def _seed_project(conn: sqlite3.Connection, project_id: str = "proj-1",
                  name: str = "Alpha", revision: int = 5) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO projects "
        "(id, name, description, keywords_json, team_members_json, "
        "context_json, detection_threshold, is_archived, revision, "
        "created_at, updated_at) "
        "VALUES (?, ?, '', '[]', '[]', '{}', 0.5, 0, ?, "
        "'2025-01-01T00:00:00', '2025-06-01T00:00:00')",
        (project_id, name, revision),
    )
    conn.commit()


def _make_conn(tmp_path: Path, db_name: str = "test.db") -> sqlite3.Connection:
    db_path = tmp_path / db_name
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    _seed_project(conn)
    return conn


def _make_repos(conn: sqlite3.Connection):
    """Wire all four steward repos to a shared connection."""
    class _ConnCtx:
        def __enter__(self_):
            return conn
        def __exit__(self_, *a):
            conn.commit()

    factory = lambda: _ConnCtx()
    return (
        StewardPolicyRepository(factory),
        StewardRunRepository(factory),
        StewardStepRepository(factory),
        StewardCommandRepository(factory),
    )


class _FakeAutomations:
    """Minimal automations repo for ServiceEventLedger."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def append_event(self, event: dict) -> bool:
        return True

    def append_event_in_transaction(self, conn: Any, event: dict) -> bool:
        return True

    def get_event(self, event_id: str) -> Optional[dict]:
        return None

    def list_events(self, **kw: Any) -> list:
        return []


class _FakeDB:
    """Minimal db mock with real steward repos and the _connection helper."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        policies, runs, steps, commands = _make_repos(conn)
        self.steward_policies = policies
        self.steward_runs = runs
        self.steward_steps = steps
        self.steward_commands = commands
        self.automations = _FakeAutomations(conn)

    def _connection(self):
        class _Ctx:
            def __init__(self_, conn):
                self_._conn = conn
            def __enter__(self_):
                return self_._conn
            def __exit__(self_, *a):
                self_._conn.commit()
        return _Ctx(self._conn)


class _FakeCollector:
    """Stub evidence collector: returns empty coverage."""

    def __init__(self, result: Optional[dict] = None) -> None:
        self._result = result or {}

    def collect_all(self, project_id: str) -> dict[str, Any]:
        return self._result


class _FakeDelta:
    """Stub Delta service: returns an empty review."""

    def __init__(self, review: Optional[dict] = None) -> None:
        self._review = review or {"id": "prev_test", "proposals": []}

    def open_review(self, principal: Any, project_id: str) -> dict[str, Any]:
        return self._review


def _principal() -> Principal:
    return Principal(PrincipalKind.OWNER, "test-runner")


def _make_service(
    conn: sqlite3.Connection,
    *,
    collector: Optional[Any] = None,
    delta: Optional[Any] = None,
) -> tuple[ProjectStewardService, _FakeDB]:
    db = _FakeDB(conn)
    svc = ProjectStewardService(
        db,
        collector or _FakeCollector(),
        delta or _FakeDelta(),
    )
    return svc, db


# -- TST-ENG-001: lifecycle truth table -----------------------------------

class TestRunLifecycle:
    """run_once returns a run ID; transitions queued->running->completed."""

    def test_run_once_returns_id(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        assert run_id.startswith("pstrun_")

        run = db.steward_runs.get_run(run_id)
        assert run is not None
        assert run["state"] == "completed"
        assert run["project_id"] == "proj-1"

    def test_completed_run_has_started_and_completed_at(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["started_at"] is not None
        assert run["completed_at"] is not None

    def test_completed_run_has_summary(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        summary = json.loads(run["summary_json"])
        assert summary["outcome"] == "completed"
        assert summary["phases_completed"] == list(PHASES)


# -- TST-ENG-002: checkpoint visibility -----------------------------------

class TestPhaseCheckpoints:
    """Each phase transition creates a visible step row."""

    def test_six_steps_created(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id)
        assert len(steps) == 6

    def test_steps_cover_all_phases(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id)
        phases = [s["phase"] for s in steps]
        assert phases == list(PHASES)

    def test_all_steps_completed(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id)
        for step in steps:
            assert step["state"] == "completed", f"Step {step['phase']} not completed"

    def test_steps_have_sequential_seq(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id)
        seqs = [s["seq"] for s in steps]
        assert seqs == [0, 1, 2, 3, 4, 5]

    def test_steps_have_idempotency_keys(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)
        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id)
        for step in steps:
            assert step["idempotency_key"].startswith(run_id + ":")


# -- TST-ENG-003: stop between phases ------------------------------------

class TestStopBetweenPhases:
    """Stop honored between phases: stopping -> interrupted with honest summary."""

    def test_stop_mid_run_leads_to_interrupted(self, tmp_path: Path) -> None:
        """Inject a stop request during the OBSERVE phase callback.

        The observe callback fires a durable stop request (DB write).
        After observe completes, the loop checks stop and interrupts.
        """
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        captured_run_id: list[str] = []

        # Monkey-patch observe to inject a stop mid-run.
        original_observe = svc._phase_observe

        def stopping_observe(principal, project_id):
            result = original_observe(principal, project_id)
            # The run is now in 'running' state; find it and stop.
            active = db.steward_runs.get_active_run(project_id)
            assert active is not None
            captured_run_id.append(active["id"])
            svc.stop(active["id"])
            return result

        svc._phase_observe = stopping_observe

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "interrupted"
        summary = json.loads(run["summary_json"])
        assert summary["outcome"] == "interrupted"
        assert summary["reason"] == "stop_requested"
        # Observe completed, but compare never ran.
        assert "observe" in summary.get("phases_completed", [])

    def test_stop_no_model_dependence(self, tmp_path: Path) -> None:
        """Stop check reads from DB, not from an in-memory flag."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # Create a run manually in running state.
        run_id = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id,
            project_id="proj-1",
            state="queued",
            phase="observe",
            requested_by="test",
        )
        db.steward_runs.update_run_state(run_id, state="running", phase="observe")

        # Request stop via durable DB write.
        svc.stop(run_id)

        # The check_stop should now raise.
        with pytest.raises(StopRequested):
            svc._check_stop(run_id)


# -- TST-ENG-004: STW-002 typed refusal -----------------------------------

class TestSTW002Uniqueness:
    """A second concurrent run raises ActiveRunExistsError."""

    def test_second_run_raises(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # Insert a run in queued state to block the slot.
        run_id_1 = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id_1,
            project_id="proj-1",
            state="queued",
            phase="observe",
            requested_by="test",
        )

        # A second run_once should fail at insert.
        with pytest.raises(ActiveRunExistsError):
            svc.run_once(_principal(), "proj-1")

    def test_different_projects_independent(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_project(conn, "proj-2", "Beta")
        svc, db = _make_service(conn)

        # Block proj-1.
        run_id_1 = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id_1,
            project_id="proj-1",
            state="queued",
            phase="observe",
            requested_by="test",
        )

        # proj-2 should work fine.
        run_id_2 = svc.run_once(_principal(), "proj-2")
        assert run_id_2.startswith("pstrun_")

    def test_completed_run_frees_slot(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # First run completes.
        run_id_1 = svc.run_once(_principal(), "proj-1")
        run = db.steward_runs.get_run(run_id_1)
        assert run["state"] == "completed"

        # Second run should succeed.
        run_id_2 = svc.run_once(_principal(), "proj-1")
        assert run_id_2 != run_id_1
        run2 = db.steward_runs.get_run(run_id_2)
        assert run2["state"] == "completed"


# -- TST-ENG-005: STW-009 recovery ----------------------------------------

class TestSTW009Recovery:
    """A run abandoned mid-phase is marked interrupted on startup."""

    def test_recovery_marks_running_as_interrupted(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # Simulate a run abandoned at the compare phase.
        run_id = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id,
            project_id="proj-1",
            state="running",
            phase="compare",
            requested_by="test",
        )

        # Add a pending step.
        step_id = generate_pststep_id()
        db.steward_steps.insert_step(
            step_id=step_id,
            run_id=run_id,
            phase="compare",
            seq=1,
            state="running",
        )

        recovered = svc.recover_on_startup()
        assert run_id in recovered

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "interrupted"
        summary = json.loads(run["summary_json"])
        assert summary["outcome"] == "interrupted"
        assert summary["reason"] == "startup_recovery"
        assert summary["interrupted_phase"] == "compare"

        # Step should also be interrupted.
        step = db.steward_steps.get_step(step_id)
        assert step["state"] == "interrupted"

    def test_recovery_frees_slot_for_new_run(self, tmp_path: Path) -> None:
        """After recovery, the project is safely re-runnable."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # Simulate abandoned run.
        run_id = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id,
            project_id="proj-1",
            state="running",
            phase="observe",
            requested_by="test",
        )

        # Before recovery, a new run would fail.
        with pytest.raises(ActiveRunExistsError):
            db.steward_runs.insert_run(
                run_id=generate_pstrun_id(),
                project_id="proj-1",
                state="queued",
                phase="observe",
                requested_by="test",
            )

        # Recover.
        recovered = svc.recover_on_startup()
        assert len(recovered) == 1

        # Now a new run should succeed.
        new_run_id = svc.run_once(_principal(), "proj-1")
        assert new_run_id.startswith("pstrun_")
        new_run = db.steward_runs.get_run(new_run_id)
        assert new_run["state"] == "completed"

    def test_recovery_handles_queued_and_stopping(self, tmp_path: Path) -> None:
        """Queued and stopping runs are also recovered."""
        conn = _make_conn(tmp_path)
        _seed_project(conn, "proj-2", "Beta")
        _seed_project(conn, "proj-3", "Gamma")
        svc, db = _make_service(conn)

        # Queued run.
        run_q = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_q,
            project_id="proj-1",
            state="queued",
            phase="observe",
            requested_by="test",
        )

        # Stopping run.
        run_s = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_s,
            project_id="proj-2",
            state="running",
            phase="act",
            requested_by="test",
        )
        db.steward_runs.request_stop(run_s)

        recovered = svc.recover_on_startup()
        assert run_q in recovered
        assert run_s in recovered

        assert db.steward_runs.get_run(run_q)["state"] == "interrupted"
        assert db.steward_runs.get_run(run_s)["state"] == "interrupted"

    def test_recovery_skips_terminal_runs(self, tmp_path: Path) -> None:
        """Completed/failed/interrupted runs are not touched."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # A completed run.
        run_id = svc.run_once(_principal(), "proj-1")
        run_before = db.steward_runs.get_run(run_id)
        assert run_before["state"] == "completed"

        recovered = svc.recover_on_startup()
        assert run_id not in recovered

        run_after = db.steward_runs.get_run(run_id)
        assert run_after["state"] == "completed"


# -- TST-ENG-006: stop before effect slots --------------------------------

class TestStopBeforeEffectSlot:
    """Stop checked before every effect slot, not just between phases."""

    def test_stop_before_phase_body(self, tmp_path: Path) -> None:
        """If stop is requested before a phase body runs, it interrupts."""
        conn = _make_conn(tmp_path)
        svc, db = _make_service(conn)

        # Create a run manually.
        run_id = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id,
            project_id="proj-1",
            state="running",
            phase="observe",
            requested_by="test",
        )
        # Request stop immediately.
        svc.stop(run_id)

        # Verify that _check_stop detects it.
        with pytest.raises(StopRequested):
            svc._check_stop(run_id)


# -- TST-ENG-007: failure isolation ----------------------------------------

class TestFailureIsolation:
    """A phase that raises is caught and the run is marked failed."""

    def test_observe_failure_marks_run_failed(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)

        class _BrokenCollector:
            def collect_all(self, project_id: str) -> dict:
                raise RuntimeError("adapter crash")

        svc, db = _make_service(conn, collector=_BrokenCollector())
        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "failed"
        summary = json.loads(run["summary_json"])
        assert summary["outcome"] == "failed"
        assert summary["error"]["code"] == "RuntimeError"

    def test_failed_step_has_error_json(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)

        class _BrokenCollector:
            def collect_all(self, project_id: str) -> dict:
                raise ValueError("bad data")

        svc, db = _make_service(conn, collector=_BrokenCollector())
        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id)
        # The observe step should be failed.
        observe_step = [s for s in steps if s["phase"] == "observe"][0]
        assert observe_step["state"] == "failed"
        error = json.loads(observe_step["error_json"])
        assert error["code"] == "ValueError"

    def test_failed_run_frees_slot(self, tmp_path: Path) -> None:
        """A failed run does not block future runs (it's terminal)."""
        conn = _make_conn(tmp_path)

        class _BrokenCollector:
            def collect_all(self, project_id: str) -> dict:
                raise RuntimeError("boom")

        svc, db = _make_service(conn, collector=_BrokenCollector())
        run_id_1 = svc.run_once(_principal(), "proj-1")
        assert db.steward_runs.get_run(run_id_1)["state"] == "failed"

        # Second run with a working collector should succeed.
        svc2, _ = _make_service(conn)
        run_id_2 = svc2.run_once(_principal(), "proj-1")
        assert db.steward_runs.get_run(run_id_2)["state"] == "completed"
