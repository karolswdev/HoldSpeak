"""HS-164-04: conductor integration -- two independent boundaries, event emission, projections.

Tests:
- TST-COND-001: A poisoned evaluate_due never stops run_due -- fault injection at block seam.
- TST-COND-002: A poisoned run_due never stops other conductor duties.
- TST-COND-003: Both blocks tick under normal conditions (no errors).
- TST-COND-004: steward.run_started emits on execute_phases transition.
- TST-COND-005: steward.step_completed emits per phase step.
- TST-COND-006: steward.intervention_required emits on bounds-exhausted.
- TST-COND-007: steward.intervention_required emits on max_actions cap.
- TST-COND-008: steward.configured emits on policy PUT.
- TST-COND-009: steward.intervention_required emits on circuit-open transition.
- TST-COND-010: Cadence projection -- review_due loop created for run with real effects.
- TST-COND-011: Cadence projection -- source_degraded loop for open-circuit watch.
- TST-COND-012: Cadence projection -- steward_intervention_required loop for intervention events.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

from holdspeak.db.schema import SCHEMA_SQL
from holdspeak.db.steward import (
    StewardCommandRepository,
    StewardPolicyRepository,
    StewardRunRepository,
    StewardStepRepository,
)
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.project_contracts import generate_pstpol_id
from holdspeak.services.project_steward_service import (
    EFFECT_KINDS,
    PHASES,
    ProjectStewardService,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _seed_project(
    conn: sqlite3.Connection,
    project_id: str = "proj-1",
    name: str = "Alpha",
    revision: int = 5,
) -> None:
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
    """Automations repo that records events for assertion."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self.events: list[dict] = []

    def append_event(self, event: dict) -> bool:
        self.events.append(event)
        return True

    def append_event_in_transaction(self, conn: Any, event: dict) -> bool:
        self.events.append(event)
        return True

    def get_event(self, event_id: str) -> Optional[dict]:
        for e in self.events:
            if e.get("id") == event_id:
                return e
        return None

    def list_events(self, **kw: Any) -> list:
        event_type = kw.get("event_type")
        if event_type:
            return [e for e in self.events if e.get("event_type") == event_type]
        return list(self.events)

    def list_pending_effects(self, action_kind: str) -> list:
        return []

    def list_watches(self) -> list:
        return []


class _FakeDB:
    """DB mock with real steward repos, event-recording automations, and _connection."""

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
    def collect_all(self, project_id: str) -> dict:
        return {}


class _FakeDelta:
    def open_review(self, principal: Any, project_id: str) -> dict:
        return {"id": "rev_test", "proposals": []}


def _principal() -> Principal:
    return Principal(PrincipalKind.OWNER, "test-conductor")


def _make_service(
    conn: sqlite3.Connection,
    *,
    collector: Any = None,
    delta: Any = None,
) -> tuple[_FakeDB, ProjectStewardService]:
    db = _FakeDB(conn)
    svc = ProjectStewardService(
        db,
        collector or _FakeCollector(),
        delta or _FakeDelta(),
    )
    return db, svc


def _seed_policy(
    conn: sqlite3.Connection,
    project_id: str = "proj-1",
    *,
    eligible: list[str] | None = None,
    max_retries: int = 3,
    max_actions: int = 10,
    enabled: bool = True,
) -> str:
    policy_id = generate_pstpol_id()
    conn.execute(
        "INSERT INTO steward_policies "
        "(id, project_id, eligible_effect_kinds_json, max_retries, "
        "max_actions_per_run, cooldown_seconds, bounds_json, enabled, "
        "unattended_enabled, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, 0, '{}', ?, 0, "
        "'2025-01-01T00:00:00', '2025-01-01T00:00:00')",
        (
            policy_id, project_id,
            json.dumps(eligible or list(EFFECT_KINDS)),
            max_retries, max_actions,
            1 if enabled else 0,
        ),
    )
    conn.commit()
    return policy_id


# ── TST-COND-001: poisoned evaluate_due never stops run_due ──────────


class TestBlockIsolation:
    """Fault injection through the REAL conductor tick via the
    set_scheduler_services seam (HS-164-04 orchestrator round: the
    previous tests simulated the blocks inline and proved nothing)."""

    def _tick_with(self, monkeypatch, tmp_path, watch_svc, steward_svc):
        """Run the real _tick with injected scheduler services."""
        import holdspeak.workbench_conductor as wc
        from holdspeak.workbench_conductor import WorkbenchConductor

        # Isolate the tick's own db lookup to a fresh throwaway DB.
        import holdspeak.db as hsdb
        from holdspeak.db import Database
        fresh = Database(tmp_path / "conductor-tick.db")
        monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: fresh)

        wc.set_scheduler_services(watch_svc, steward_svc)
        try:
            conductor = WorkbenchConductor.__new__(WorkbenchConductor)
            conductor._last_check = {}
            conductor._tick()
        finally:
            wc.set_scheduler_services(None, None)

    def test_poisoned_evaluate_due_does_not_stop_run_due(
        self, tmp_path, monkeypatch,
    ) -> None:
        """TST-COND-001: evaluate_due raises; run_due still executes."""
        calls: list[str] = []

        class _PoisonWatch:
            def evaluate_due(self, principal):
                calls.append("evaluate_due")
                raise RuntimeError("poisoned evaluate_due")

        class _TrackSteward:
            def run_due(self, principal):
                calls.append("run_due")
                return []

            def project_cadence_projections(self, principal):
                calls.append("projections")
                return []

        self._tick_with(monkeypatch, tmp_path, _PoisonWatch(), _TrackSteward())
        assert calls == ["evaluate_due", "run_due", "projections"]

    def test_poisoned_run_due_does_not_stop_conductor(
        self, tmp_path, monkeypatch,
    ) -> None:
        """TST-COND-002: run_due raises; the tick still completes."""
        calls: list[str] = []

        class _TrackWatch:
            def evaluate_due(self, principal):
                calls.append("evaluate_due")
                return []

        class _PoisonSteward:
            def run_due(self, principal):
                calls.append("run_due")
                raise RuntimeError("poisoned run_due")

            def project_cadence_projections(self, principal):
                calls.append("projections")
                return []

        # Must NOT raise out of the tick.
        self._tick_with(monkeypatch, tmp_path, _TrackWatch(), _PoisonSteward())
        assert calls == ["evaluate_due", "run_due"]

    def test_conductor_tick_both_blocks_run(
        self, tmp_path, monkeypatch,
    ) -> None:
        """TST-COND-003: healthy services; watch block ticks before steward."""
        calls: list[str] = []

        class _W:
            def evaluate_due(self, principal):
                calls.append("evaluate_due")
                return [{"watch_id": "cw_x", "outcome": "evaluated"}]

        class _S:
            def run_due(self, principal):
                calls.append("run_due")
                return [{"outcome": "run_started"}]

            def project_cadence_projections(self, principal):
                calls.append("projections")
                return []

        self._tick_with(monkeypatch, tmp_path, _W(), _S())
        assert calls == ["evaluate_due", "run_due", "projections"]

    def test_not_wired_skips_honestly(self, tmp_path, monkeypatch) -> None:
        """Unwired schedulers skip; the tick never builds crippled services."""
        import holdspeak.workbench_conductor as wc
        from holdspeak.workbench_conductor import WorkbenchConductor
        import holdspeak.db as hsdb
        from holdspeak.db import Database
        fresh = Database(tmp_path / "conductor-tick.db")
        monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: fresh)

        wc.set_scheduler_services(None, None)
        conductor = WorkbenchConductor.__new__(WorkbenchConductor)
        conductor._last_check = {}
        conductor._tick()  # completes without raising, nothing constructed


class TestRunStartedEvent:
    """steward.run_started emits at the queued->running transition."""

    def test_run_started_emits(self, tmp_path) -> None:
        """TST-COND-004."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        _seed_policy(conn)
        p = _principal()

        run_id = svc.insert_run(p, "proj-1")
        svc.execute_phases(p, run_id, "proj-1")

        events = db.automations.events
        run_started = [
            e for e in events
            if e.get("event_type") == "steward.run_started"
        ]
        assert len(run_started) >= 1, f"No run_started event; events={[e['event_type'] for e in events]}"
        evt = run_started[0]
        assert evt["facts"]["run_id"] == run_id
        assert evt["facts"]["project_id"] == "proj-1"
        assert f"steward_run:{run_id}" in evt["refs"]


# ── TST-COND-005: steward.step_completed event ──────────────────────


class TestStepCompletedEvent:
    """steward.step_completed emits per phase step."""

    def test_step_completed_per_phase(self, tmp_path) -> None:
        """TST-COND-005."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        _seed_policy(conn)
        p = _principal()

        run_id = svc.insert_run(p, "proj-1")
        svc.execute_phases(p, run_id, "proj-1")

        events = db.automations.events
        step_completed = [
            e for e in events
            if e.get("event_type") == "steward.step_completed"
        ]
        # At least 6 phase steps (observe, compare, propose, act, verify, record)
        assert len(step_completed) >= len(PHASES), (
            f"Expected at least {len(PHASES)} step_completed events, "
            f"got {len(step_completed)}"
        )
        # Each has ref-oriented payload
        for evt in step_completed:
            assert "run_id" in evt["facts"]
            assert "phase" in evt["facts"]
            assert "step_id" in evt["facts"]


# ── TST-COND-006: intervention_required on bounds-exhausted ──────────


class TestInterventionBoundsExhausted:
    """steward.intervention_required fires when retries exhausted."""

    def test_bounds_exhausted_intervention(self, tmp_path) -> None:
        """TST-COND-006."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        # Policy with 0 retries so first failure exhausts bounds
        _seed_policy(conn, max_retries=0, eligible=["refresh_sources"])
        p = _principal()

        run_id = svc.insert_run(p, "proj-1")

        # Make _apply_effect always fail
        def _failing_effect(*args, **kwargs):
            raise RuntimeError("Simulated effect failure")

        with patch.object(svc, "_apply_effect", side_effect=_failing_effect):
            svc.execute_phases(p, run_id, "proj-1")

        events = db.automations.events
        interventions = [
            e for e in events
            if e.get("event_type") == "steward.intervention_required"
               and e.get("facts", {}).get("reason") == "bounds_exhausted"
        ]
        assert len(interventions) >= 1, (
            f"No bounds_exhausted intervention; events={[e.get('event_type') for e in events]}"
        )
        evt = interventions[0]
        assert evt["facts"]["run_id"] == run_id
        assert evt["facts"]["project_id"] == "proj-1"
        assert evt["facts"]["attempts"] == 1  # 0 retries + 1 attempt


# ── TST-COND-007: intervention_required on max_actions cap ───────────


class TestInterventionMaxActions:
    """steward.intervention_required fires on max_actions cap hit."""

    def test_max_actions_cap_intervention(self, tmp_path) -> None:
        """TST-COND-007."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        # Policy with max_actions=0 so first effect hits the cap
        _seed_policy(conn, max_actions=0)
        p = _principal()

        run_id = svc.insert_run(p, "proj-1")
        svc.execute_phases(p, run_id, "proj-1")

        events = db.automations.events
        interventions = [
            e for e in events
            if e.get("event_type") == "steward.intervention_required"
               and e.get("facts", {}).get("reason") == "max_actions_per_run_exceeded"
        ]
        assert len(interventions) >= 1, (
            f"No max_actions intervention; events={[e.get('event_type') for e in events]}"
        )
        evt = interventions[0]
        assert evt["facts"]["run_id"] == run_id
        assert evt["facts"]["limit"] == 0


# ── TST-COND-008: steward.configured event ──────────────────────────


class TestConfiguredEvent:
    """steward.configured emits on policy PUT via the route."""

    def test_configured_event_on_policy_put(self, tmp_path, monkeypatch) -> None:
        """TST-COND-008."""
        from holdspeak.db import Database, reset_database
        from holdspeak.web.context import WebContext
        from holdspeak.web.routes import build_steward_router
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        import holdspeak.db as hsdb

        reset_database()
        db = Database(tmp_path / "configured-evt.db")
        monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)

        OWNER = Principal(PrincipalKind.OWNER, "test-configured")

        svc = ProjectStewardService(db, collector=None, delta=None)
        ctx = WebContext(get_state=lambda: {}, project_steward_service=svc)
        app = FastAPI()

        from starlette.middleware.base import BaseHTTPMiddleware

        class _OwnerMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                request.state.principal = OWNER
                return await call_next(request)

        app.add_middleware(_OwnerMiddleware)
        app.include_router(build_steward_router(ctx))
        client = TestClient(app)

        # Seed project
        with db._connection() as conn:
            conn.execute(
                "INSERT INTO projects "
                "(id, name, description, keywords_json, team_members_json, "
                "context_json, detection_threshold, revision, "
                "created_at, updated_at) "
                "VALUES ('proj-cfg', 'Config Test', '', '[]', '[]', '{}', 0.4, 1, "
                "'2025-01-01', '2025-01-01')",
            )

        resp = client.put(
            "/api/projects/proj-cfg/steward/policy",
            json={"enabled": True, "max_retries": 5},
        )
        assert resp.status_code == 200, resp.text

        # Check event was recorded
        events = db.automations.list_events(event_type="steward.configured")
        assert len(events) >= 1, "No steward.configured event emitted"
        evt = events[0]
        assert evt["facts"]["project_id"] == "proj-cfg"
        assert "policy_id" in evt["facts"]

        reset_database()


# ── TST-COND-009: circuit-open intervention ──────────────────────────


class TestCircuitOpenIntervention:
    """steward.intervention_required emits on circuit-open transition."""

    def test_circuit_open_emits_intervention(self, tmp_path) -> None:
        """TST-COND-009."""
        from holdspeak.db.core import Database
        from holdspeak.services.watch_service import (
            CIRCUIT_FAILURE_THRESHOLD,
            WatchService,
        )
        from holdspeak.services.reaction_service import ReactionService

        db = Database(tmp_path / "circuit-int.db")
        p = Principal(PrincipalKind.OWNER, "test-circuit")

        # Create a watch
        svc = ReactionService(db)
        svc.create_watch(
            p,
            connector_id="gh",
            query_kind="pull_requests",
            name="Circuit watch",
            query={"repository": "acme/app"},
            watch_id="watch-ckt-01",
        )
        # Graduate it
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        past = (now - __import__("datetime").timedelta(minutes=5)).isoformat(
            timespec="seconds",
        )
        db.automations.update_watch_spec(
            "watch-ckt-01",
            state="active",
            schema_version="WatchSpec@1",
            evaluation_cadence_minutes=1,
            next_evaluation_at=past,
        )

        # Manually set circuit streak just below threshold
        with db._connection() as conn:
            conn.execute(
                "UPDATE connector_watches SET circuit_failure_streak = ?, "
                "circuit_state = 'closed' WHERE id = ?",
                (CIRCUIT_FAILURE_THRESHOLD - 1, "watch-ckt-01"),
            )

        # Create watch service with a failing fetcher
        class _FailFetcher:
            def fetch(self, *a, **kw):
                raise RuntimeError("Simulated fetch failure")

        ws = WatchService(db, snapshot_fetcher=_FailFetcher())
        outcomes = ws.evaluate_due(p)

        # The watch should have failed and tripped the circuit
        assert len(outcomes) >= 1
        failed = [o for o in outcomes if o.get("outcome") == "failed"]
        assert len(failed) >= 1

        # Check that intervention_required was emitted
        events = db.automations.list_events(
            event_type="steward.intervention_required",
        )
        circuit_events = [
            e for e in events
            if e.get("facts", {}).get("reason") == "circuit_open"
        ]
        assert len(circuit_events) >= 1, (
            f"No circuit_open intervention; all events={events}"
        )
        evt = circuit_events[0]
        assert evt["facts"]["watch_id"] == "watch-ckt-01"
        assert evt["facts"]["failure_streak"] >= CIRCUIT_FAILURE_THRESHOLD


# ── TST-COND-010..012: Cadence projections ───────────────────────────


class TestCadenceProjections:
    """Cadence shows projections without owning schedule state."""

    def test_review_due_projection(self, tmp_path) -> None:
        """TST-COND-010: review_due loop for run with real effects."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        p = _principal()

        # Seed a run_completed event with has_real_effects=True
        from holdspeak.services.service_event_ledger import ServiceEventLedger
        ledger = ServiceEventLedger(db)
        ledger.append(
            p,
            event_type="steward.run_completed",
            producer="ProjectStewardService",
            subject_ref="steward_run:run-test-01",
            facts={
                "run_id": "run-test-01",
                "project_id": "proj-1",
                "has_real_effects": True,
                "actions_taken": 3,
            },
            refs=["project:proj-1", "steward_run:run-test-01"],
        )

        # Add cadence repo to the fake DB
        from holdspeak.db.cadence import CadenceRepository
        db.cadence = CadenceRepository.__new__(CadenceRepository)
        db.cadence._connection = db._connection

        results = svc.project_cadence_projections(p)
        review_results = [r for r in results if r.get("kind") == "review_due"]
        assert len(review_results) >= 1, f"No review_due projection; results={results}"
        assert review_results[0]["run_id"] == "run-test-01"

        # Verify the loop was created
        loop = db.cadence.get_loop_by_source("system", "steward_review:run-test-01")
        assert loop is not None
        assert loop.needs_review is True
        assert loop.project == "proj-1"

    def test_source_degraded_projection(self, tmp_path) -> None:
        """TST-COND-011: source_degraded loop for open-circuit watch."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        p = _principal()

        # Mock list_watches to return a watch with open circuit
        db.automations.list_watches = lambda: [
            {
                "id": "watch-deg-01",
                "circuit_state": "open",
                "bound_project_id": "proj-1",
            }
        ]

        # Add cadence repo
        from holdspeak.db.cadence import CadenceRepository
        db.cadence = CadenceRepository.__new__(CadenceRepository)
        db.cadence._connection = db._connection

        results = svc.project_cadence_projections(p)
        degraded = [r for r in results if r.get("kind") == "source_degraded"]
        assert len(degraded) >= 1, f"No source_degraded projection; results={results}"
        assert degraded[0]["watch_id"] == "watch-deg-01"

        loop = db.cadence.get_loop_by_source("system", "steward_degraded:watch-deg-01")
        assert loop is not None
        assert loop.priority == "high"

    def test_degraded_loop_healed_on_circuit_close(self, tmp_path) -> None:
        """Counsel S-2: a closed circuit heals its stale degraded loop."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        p = _principal()

        from holdspeak.db.cadence import CadenceRepository
        db.cadence = CadenceRepository.__new__(CadenceRepository)
        db.cadence._connection = db._connection

        # Tick 1: circuit open -> degraded loop upserted.
        db.automations.list_watches = lambda: [
            {"id": "watch-heal-01", "circuit_state": "open",
             "bound_project_id": "proj-1"},
        ]
        svc.project_cadence_projections(p)
        loop = db.cadence.get_loop_by_source(
            "system", "steward_degraded:watch-heal-01")
        assert loop is not None and loop.status not in ("closed", "killed")

        # Tick 2: circuit closed -> the stale loop is healed.
        db.automations.list_watches = lambda: [
            {"id": "watch-heal-01", "circuit_state": "closed",
             "bound_project_id": "proj-1"},
        ]
        results = svc.project_cadence_projections(p)
        healed = [r for r in results
                  if r.get("kind") == "source_degraded_healed"
                  and not r.get("error")]
        assert len(healed) == 1 and healed[0]["watch_id"] == "watch-heal-01"
        loop2 = db.cadence.get_loop_by_source(
            "system", "steward_degraded:watch-heal-01")
        assert loop2.status == "closed"

        # Idempotent: a third pass heals nothing further.
        results3 = svc.project_cadence_projections(p)
        healed3 = [r for r in results3
                   if r.get("kind") == "source_degraded_healed"
                   and not r.get("error")]
        assert healed3 == []

    def test_intervention_required_projection(self, tmp_path) -> None:
        """TST-COND-012: intervention_required loop for intervention events."""
        conn = _make_conn(tmp_path)
        db, svc = _make_service(conn)
        p = _principal()

        # Seed an intervention event
        from holdspeak.services.service_event_ledger import ServiceEventLedger
        ledger = ServiceEventLedger(db)
        ledger.append(
            p,
            event_type="steward.intervention_required",
            producer="ProjectStewardService",
            subject_ref="steward_run:run-int-01",
            facts={
                "reason": "bounds_exhausted",
                "run_id": "run-int-01",
                "project_id": "proj-1",
            },
            refs=["project:proj-1", "steward_run:run-int-01"],
        )

        # Add cadence repo
        from holdspeak.db.cadence import CadenceRepository
        db.cadence = CadenceRepository.__new__(CadenceRepository)
        db.cadence._connection = db._connection

        results = svc.project_cadence_projections(p)
        interventions = [
            r for r in results
            if r.get("kind") == "steward_intervention_required"
        ]
        assert len(interventions) >= 1, (
            f"No intervention projection; results={results}"
        )
        assert interventions[0]["reason"] == "bounds_exhausted"

        source_id = "steward_intervention:steward_run:run-int-01:bounds_exhausted"
        loop = db.cadence.get_loop_by_source("system", source_id)
        assert loop is not None
        assert loop.priority == "urgent"
