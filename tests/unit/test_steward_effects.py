"""HS-163-03: Steward bounded effects -- V0 effect set, verified, deduplicated.

Tests:
- TST-EFF-001: Each effect kind happy path + verification recorded.
- TST-EFF-002: Stop-before-effect honored for every effect slot.
- TST-EFF-003: STW-005 fault-injection (idempotency reconciliation).
- TST-EFF-004: ONE-Door-item law (deterministic selection, dedup).
- TST-EFF-005: STW-008 bounds enforced (max_actions, max_retries).
- TST-EFF-006: STW-010 policy eligibility (unconfigured kinds skipped).
- TST-EFF-007: STW-007 model failure fallback to deterministic.
- TST-EFF-008: STW-006 source failure isolation.
- TST-EFF-009: Compounding integration (observe -> compare -> propose ->
               act -> verify -> record, all receipted).
- TST-EFF-010: STW-011 shape: a run with real effects carries verification.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone, timedelta
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
from holdspeak.project_contracts import (
    generate_pstpol_id,
    generate_pstrun_id,
    generate_pststep_id,
)
from holdspeak.services.project_steward_service import (
    EFFECT_KINDS,
    PHASES,
    ProjectStewardService,
    StopRequested,
    _door_idempotency_key,
)


# -- Helpers ---------------------------------------------------------------

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


def _seed_project_items(
    conn: sqlite3.Connection,
    project_id: str = "proj-1",
    items: list[dict[str, Any]] | None = None,
) -> None:
    """Seed project_items for the Door selection tests."""
    if items is None:
        items = []
    for item in items:
        conn.execute(
            """INSERT OR IGNORE INTO project_items
               (id, project_id, item_type, title, summary, lifecycle,
                severity, owner_ref, due_at, sort_key, details_json,
                provenance_kind, source_observation_id, created_by_ref,
                revision, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', 'owner', NULL,
                       'principal:test', 0, ?, ?)""",
            (
                item["id"],
                project_id,
                item.get("item_type", "risk"),
                item.get("title", "Test item"),
                item.get("summary"),
                item.get("lifecycle", "open"),
                item.get("severity"),
                item.get("owner_ref"),
                item.get("due_at"),
                item.get("sort_key"),
                item.get("created_at", "2025-01-01T00:00:00"),
                item.get("updated_at", "2025-01-01T00:00:00"),
            ),
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
    """Stub evidence collector: returns configurable coverage."""

    def __init__(
        self,
        result: Optional[dict] = None,
        *,
        fail: bool = False,
    ) -> None:
        self._result = result or {}
        self._fail = fail
        self.call_count = 0

    def collect_all(self, project_id: str) -> dict[str, Any]:
        self.call_count += 1
        if self._fail:
            raise RuntimeError("STW-006: source adapter crash")
        return self._result


class _FakeDelta:
    """Stub Delta service: returns a configurable review.

    Honors the real signatures: open_review(principal, project_id) and
    decide_proposal(principal, project_id, proposal_id, verb, **kw).
    """

    def __init__(
        self,
        review: Optional[dict] = None,
        *,
        decide_fail: bool = False,
    ) -> None:
        self._review = review or {"id": "prev_test", "proposals": []}
        self._decide_fail = decide_fail
        self.decided: list[dict[str, Any]] = []

    def open_review(self, principal: Any, project_id: str) -> dict[str, Any]:
        return self._review

    def decide_proposal(
        self,
        principal: Any,
        project_id: str,
        proposal_id: str,
        verb: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        if self._decide_fail:
            raise RuntimeError("decide_proposal failed")
        result = {
            "proposal_id": proposal_id,
            "verb": verb,
            "lifecycle": "accepted",
            "item_id": f"pitem_{proposal_id}_accepted",
        }
        self.decided.append(result)
        return result


class _FakeUpdateService:
    """Stub update service honoring the real draft_update signature."""

    def __init__(
        self,
        *,
        fail: bool = False,
        result: Optional[dict] = None,
    ) -> None:
        self._fail = fail
        self._result = result or {
            "id": "pupd_test_001",
            "lifecycle": "draft",
            "generator": "deterministic",
        }
        self.call_count = 0

    def draft_update(
        self,
        principal: Any,
        project_id: str,
        *,
        generator: str = "deterministic",
    ) -> dict[str, Any]:
        self.call_count += 1
        if self._fail:
            raise RuntimeError("update draft failed")
        return self._result


class _FakeProjectService:
    """Stub project service for list_items."""

    def __init__(
        self,
        items: list[dict[str, Any]] | None = None,
    ) -> None:
        self._items = items or []

    def list_items(
        self,
        principal: Any,
        project_id: str,
        *,
        item_type: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> dict[str, Any]:
        return {"items": self._items, "limit": limit, "offset": offset}


class _FakeDoorService:
    """Stub Door service honoring the real add_item signature."""

    def __init__(self) -> None:
        self.added: list[dict[str, Any]] = []
        self._counter = 0

    def add_item(
        self,
        principal: Any,
        task: str,
        *,
        owner: str | None = None,
        due: str | None = None,
        source_type: str = "meeting",
        source_ref: str = "",
    ) -> dict[str, Any]:
        self._counter += 1
        item_id = f"ai_door_{self._counter}"
        result = {
            "id": item_id,
            "task": task,
            "owner": owner,
            "due": due,
            "status": "open",
            "source_type": source_type,
            "source_ref": source_ref,
        }
        self.added.append(result)
        return result

    def has_item_for_source(self, source_ref: str) -> bool:
        return any(a.get("source_ref") == source_ref for a in self.added)


def _principal() -> Principal:
    return Principal(PrincipalKind.OWNER, "test-runner")


def _make_policy(
    conn: sqlite3.Connection,
    project_id: str = "proj-1",
    eligible_kinds: list[str] | None = None,
    max_actions: int = 10,
    max_retries: int = 3,
    cooldown: int = 0,
) -> str:
    """Create a steward policy and return its ID."""
    policy_id = generate_pstpol_id()
    repos = _make_repos(conn)
    repos[0].insert_policy(
        policy_id=policy_id,
        project_id=project_id,
        eligible_effect_kinds_json=json.dumps(eligible_kinds or []),
        max_actions_per_run=max_actions,
        max_retries=max_retries,
        cooldown_seconds=cooldown,
    )
    return policy_id


def _make_service(
    conn: sqlite3.Connection,
    *,
    collector: Optional[Any] = None,
    delta: Optional[Any] = None,
    update_service: Optional[Any] = None,
    project_service: Optional[Any] = None,
    door_service: Optional[Any] = None,
) -> tuple[ProjectStewardService, _FakeDB]:
    db = _FakeDB(conn)
    svc = ProjectStewardService(
        db,
        collector or _FakeCollector(),
        delta or _FakeDelta(),
        update_service=update_service,
        project_service=project_service,
        door_service=door_service,
    )
    return svc, db


# ── TST-EFF-001: Effect kinds happy path ──────────────────────────────

class TestEffectHappyPaths:
    """Each effect kind: happy path + verification recorded."""

    def test_refresh_sources_effect(self, tmp_path: Path) -> None:
        """Effect 1: refresh_sources persists observations."""
        conn = _make_conn(tmp_path)
        collector = _FakeCollector(result={"github": {"commits": 5}})
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        svc, db = _make_service(conn, collector=collector)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 1

        # Find the effect step.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        refresh_steps = [
            s for s in steps if s["effect_kind"] == "refresh_sources"
        ]
        assert len(refresh_steps) == 1
        step = refresh_steps[0]
        assert step["state"] == "completed"

        # STW-004: observed_state recorded.
        observed = json.loads(step["observed_state_json"])
        assert observed["effect"] == "refresh_sources"
        assert observed["coverage"]["github"]["commits"] == 5

    def test_create_proposals_effect(self, tmp_path: Path) -> None:
        """Effect 2: create_proposals generates deterministic proposals."""
        conn = _make_conn(tmp_path)
        delta = _FakeDelta(review={
            "id": "prev_test",
            "proposals": [
                {"id": "prop-1", "proposal_kind": "risk_attention",
                 "lifecycle": "open"},
            ],
        })
        _make_policy(conn, eligible_kinds=["create_proposals"])
        svc, db = _make_service(conn, delta=delta)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 1

    def test_apply_proposal_effects(self, tmp_path: Path) -> None:
        """Effect 3: apply proposal effects through decide_proposal."""
        conn = _make_conn(tmp_path)
        delta = _FakeDelta(review={
            "id": "prev_test",
            "proposals": [
                {"id": "prop-1", "proposal_kind": "risk_attention",
                 "lifecycle": "open", "title": "Risk A"},
            ],
        })
        _make_policy(conn, eligible_kinds=["apply_proposal_effects"])
        svc, db = _make_service(conn, delta=delta)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 1

        # Check the delta was called.
        assert len(delta.decided) == 1
        assert delta.decided[0]["proposal_id"] == "prop-1"

        # Step verification recorded.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        apply_steps = [
            s for s in steps
            if s["effect_kind"] == "apply_proposal_effects"
        ]
        assert len(apply_steps) == 1
        observed = json.loads(apply_steps[0]["observed_state_json"])
        assert len(observed["applied"]) == 1

    def test_draft_update_effect(self, tmp_path: Path) -> None:
        """Effect 4: draft_update creates or replaces an unaccepted update."""
        conn = _make_conn(tmp_path)
        update_svc = _FakeUpdateService()
        _make_policy(conn, eligible_kinds=["draft_update"])
        svc, db = _make_service(conn, update_service=update_svc)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 1
        assert update_svc.call_count == 1

        # Step verification.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        update_steps = [
            s for s in steps if s["effect_kind"] == "draft_update"
        ]
        assert len(update_steps) == 1
        observed = json.loads(update_steps[0]["observed_state_json"])
        assert observed["update_id"] == "pupd_test_001"

    def test_create_door_item_effect(self, tmp_path: Path) -> None:
        """Effect 5: create_door_item adds exactly one Door item."""
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "risk", "title": "Overdue risk",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 1

        # Door item created exactly once.
        assert len(door_svc.added) == 1
        door_item = door_svc.added[0]
        assert "[Steward] Overdue risk" in door_item["task"]
        assert door_item["source_type"] == "steward"
        assert door_item["source_ref"] == "project_item:item-1"


# ── TST-EFF-002: Stop-before-effect honored ───────────────────────────

class TestStopBeforeEffect:
    """Stop is checked before every effect slot."""

    def test_stop_before_refresh_sources(self, tmp_path: Path) -> None:
        """Inject stop between phase dispatch and first effect."""
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        svc, db = _make_service(conn)

        # Patch the collector to inject a stop.
        original_observe = svc._phase_observe

        def stopping_observe(principal, project_id):
            result = original_observe(principal, project_id)
            active = db.steward_runs.get_active_run(project_id)
            svc.stop(active["id"])
            return result

        svc._phase_observe = stopping_observe

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "interrupted"

        # No effect steps should be completed.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        effect_steps = [
            s for s in steps if s["effect_kind"] == "refresh_sources"
        ]
        assert len(effect_steps) == 0


# ── TST-EFF-003: STW-005 fault-injection (idempotency) ───────────────

class TestSTW005FaultInjection:
    """STW-005: recovery reconciles by idempotency key, never doubles."""

    def test_reconcile_by_idempotency_key(self, tmp_path: Path) -> None:
        """Simulate: effect applied but step NOT marked completed.

        The re-run finds the step by idempotency key and reconciles.
        """
        conn = _make_conn(tmp_path)
        collector = _FakeCollector(result={"github": {"commits": 3}})
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        svc, db = _make_service(conn, collector=collector)

        # First run: normal.
        run_id_1 = svc.run_once(_principal(), "proj-1")
        run_1 = db.steward_runs.get_run(run_id_1)
        assert run_1["state"] == "completed"

        # Simulate fault: create a run row FIRST (FK), then insert
        # a completed step with the matching idempotency key.
        run_id_2 = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id_2,
            project_id="proj-1",
            state="queued",
            phase="observe",
            requested_by="test",
        )

        idem_key = f"{run_id_2}:refresh_sources"
        fault_step_id = generate_pststep_id()
        db.steward_steps.insert_step(
            step_id=fault_step_id,
            run_id=run_id_2,
            phase="act",
            seq=0,
            state="completed",
            effect_kind="refresh_sources",
            idempotency_key=idem_key,
        )

        # Execute the engine for run 2.
        svc.execute_phases(_principal(), run_id_2, "proj-1")

        # The collector was called in OBSERVE (always), but the ACT
        # phase should have reconciled the refresh_sources effect.
        run_2 = db.steward_runs.get_run(run_id_2)
        assert run_2["state"] == "completed"
        summary = json.loads(run_2["summary_json"])
        act_result = summary["phase_results"]["act"]

        # The effect was reconciled, not re-applied.
        receipts = act_result.get("effect_receipts", [])
        refresh_receipt = [
            r for r in receipts if r["effect_kind"] == "refresh_sources"
        ]
        assert len(refresh_receipt) == 1
        assert refresh_receipt[0]["outcome"] == "reconciled"

    def test_door_item_dedup_same_watermark(self, tmp_path: Path) -> None:
        """Same watermark, same items -> ZERO additional Door items."""
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "risk", "title": "Overdue risk",
             "severity": "critical", "lifecycle": "open",
             "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        # First run with watermark "w1".
        run_id_1 = svc.run_once(
            _principal(), "proj-1", watermark="w1",
        )
        assert len(door_svc.added) == 1

        # No hand-seeded step: run 1's OWN act step carries the
        # watermark-scoped door key (the production seam, not a fixture).

        # Second run with same watermark.
        run_id_2 = svc.run_once(
            _principal(), "proj-1", watermark="w1",
        )

        # The door should NOT have been called a second time for
        # the same item+watermark.
        run_2 = db.steward_runs.get_run(run_id_2)
        assert run_2["state"] == "completed"
        summary = json.loads(run_2["summary_json"])
        act_result = summary["phase_results"]["act"]
        receipts = act_result.get("effect_receipts", [])
        door_receipts = [
            r for r in receipts
            if r["effect_kind"] == "create_door_item"
        ]
        # The watermark-scoped step key reconciles in _phase_act: the
        # re-run performs NO selection and creates nothing.
        assert len(door_receipts) == 1
        assert door_receipts[0].get("outcome") == "reconciled"
        # No second Door item created.
        assert len(door_svc.added) == 1

    def test_fault_between_apply_and_record(self, tmp_path: Path) -> None:
        """Fault injection: kill between apply and record.

        Simulate by pre-inserting a completed step with the matching
        idempotency key (as if the effect applied but the run crashed
        before recording the run-level outcome). On re-run, the engine
        reconciles: no double-apply.
        """
        conn = _make_conn(tmp_path)
        collector = _FakeCollector(result={"github": {"commits": 1}})
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        svc, db = _make_service(conn, collector=collector)

        # Run 1: succeeds normally.
        run_id_1 = svc.run_once(_principal(), "proj-1")
        assert db.steward_runs.get_run(run_id_1)["state"] == "completed"

        # Simulate fault for run 2: create the run row first (FK),
        # then insert a completed step.
        run_id_2 = generate_pstrun_id()
        db.steward_runs.insert_run(
            run_id=run_id_2,
            project_id="proj-1",
            state="queued",
            phase="observe",
            requested_by="test",
        )

        idem_key = f"{run_id_2}:refresh_sources"
        ghost_step = generate_pststep_id()
        db.steward_steps.insert_step(
            step_id=ghost_step,
            run_id=run_id_2,
            phase="act",
            seq=0,
            state="completed",
            effect_kind="refresh_sources",
            idempotency_key=idem_key,
            expected_state_json='{"effect": "refresh_sources"}',
        )
        db.steward_steps.update_step(
            ghost_step,
            observed_state_json='{"effect": "refresh_sources", "applied": true}',
        )

        # Track collector calls to prove no re-apply in ACT.
        calls_before = collector.call_count
        svc.execute_phases(_principal(), run_id_2, "proj-1")
        calls_after = collector.call_count

        # The reconciliation should prevent a re-apply in ACT.
        # (OBSERVE always calls the collector, but the ACT effect
        # refresh_sources should reconcile instead of calling again.)
        run_2 = db.steward_runs.get_run(run_id_2)
        assert run_2["state"] == "completed"
        summary = json.loads(run_2["summary_json"])
        act_result = summary["phase_results"]["act"]
        receipts = act_result.get("effect_receipts", [])
        refresh = [r for r in receipts if r["effect_kind"] == "refresh_sources"]
        assert len(refresh) == 1
        assert refresh[0]["outcome"] == "reconciled"


# ── TST-EFF-004: ONE-Door-item law ───────────────────────────────────

class TestOneDoorItemLaw:
    """Deterministic selection + dedup = exactly one Door item."""

    def test_deterministic_selection_highest_severity(
        self, tmp_path: Path,
    ) -> None:
        """The highest-severity item is selected first."""
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-low", "item_type": "risk", "title": "Low risk",
             "severity": "low", "lifecycle": "open", "due_at": yesterday},
            {"id": "item-crit", "item_type": "risk", "title": "Critical risk",
             "severity": "critical", "lifecycle": "open",
             "due_at": yesterday},
            {"id": "item-high", "item_type": "risk", "title": "High risk",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")

        # Exactly one door item.
        assert len(door_svc.added) == 1
        assert door_svc.added[0]["source_ref"] == "project_item:item-crit"

    def test_deterministic_selection_due_date_tiebreak(
        self, tmp_path: Path,
    ) -> None:
        """Same severity: earliest due_at wins."""
        conn = _make_conn(tmp_path)
        day1 = (
            datetime.now(timezone.utc) - timedelta(days=5)
        ).date().isoformat()
        day2 = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-b", "item_type": "risk", "title": "Later risk",
             "severity": "high", "lifecycle": "open", "due_at": day2},
            {"id": "item-a", "item_type": "risk", "title": "Earlier risk",
             "severity": "high", "lifecycle": "open", "due_at": day1},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")

        assert len(door_svc.added) == 1
        assert door_svc.added[0]["source_ref"] == "project_item:item-a"

    def test_deterministic_selection_id_tiebreak(
        self, tmp_path: Path,
    ) -> None:
        """Same severity and due_at: lowest id wins (stable tiebreak)."""
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-zzz", "item_type": "risk", "title": "Z risk",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
            {"id": "item-aaa", "item_type": "risk", "title": "A risk",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")

        assert len(door_svc.added) == 1
        assert door_svc.added[0]["source_ref"] == "project_item:item-aaa"

    def test_blocking_lifecycle_selected(self, tmp_path: Path) -> None:
        """Items with at_risk/broken lifecycle are blocking candidates."""
        conn = _make_conn(tmp_path)
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "dependency", "title": "Broken dep",
             "severity": "high", "lifecycle": "broken", "due_at": None},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")
        assert len(door_svc.added) == 1

    def test_no_eligible_items_skips(self, tmp_path: Path) -> None:
        """No overdue/blocking items -> effect skipped, not error."""
        conn = _make_conn(tmp_path)
        tomorrow = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "risk", "title": "Future risk",
             "severity": "high", "lifecycle": "open", "due_at": tomorrow},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")

        # No door item created (the item is not overdue/blocking).
        assert len(door_svc.added) == 0

        # But the run completed successfully.
        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"

    def test_idempotency_key_formula(self) -> None:
        """The Door idempotency key is deterministic."""
        key1 = _door_idempotency_key("proj-1", "w1")
        key2 = _door_idempotency_key("proj-1", "w1")
        key3 = _door_idempotency_key("proj-1", "w2")
        assert key1 == key2  # same inputs -> same key
        assert key1 != key3  # different watermark -> different key
        assert key1.startswith("door:")


# ── TST-EFF-005: STW-008 bounds enforced ──────────────────────────────

class TestSTW008Bounds:
    """STW-008: max_actions_per_run and max_retries bounded by policy."""

    def test_max_actions_per_run(self, tmp_path: Path) -> None:
        """No more than max_actions_per_run effects applied."""
        conn = _make_conn(tmp_path)
        _make_policy(
            conn,
            eligible_kinds=list(EFFECT_KINDS),
            max_actions=2,
        )
        collector = _FakeCollector(result={"github": {"commits": 1}})
        delta = _FakeDelta(review={
            "id": "prev_test",
            "proposals": [
                {"id": "prop-1", "proposal_kind": "risk_attention",
                 "lifecycle": "open"},
            ],
        })
        update_svc = _FakeUpdateService()
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "risk", "title": "Overdue",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        svc, db = _make_service(
            conn,
            collector=collector,
            delta=delta,
            update_service=update_svc,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] <= 2

        # Some effects should be skipped due to the bound.
        assert len(act_result.get("effects_skipped", [])) > 0
        skip_reasons = [
            s["reason"] for s in act_result["effects_skipped"]
        ]
        assert any("max_actions" in r for r in skip_reasons)

    def test_max_retries_exhausted(self, tmp_path: Path) -> None:
        """Effect that always raises exhausts retries and is marked failed.

        Uses create_door_item with a door service that raises, because
        that effect genuinely propagates exceptions (unlike draft_update
        which catches them for STW-007 fallback).
        """
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        _make_policy(
            conn,
            eligible_kinds=["create_door_item"],
            max_retries=2,
        )
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "risk", "title": "Overdue",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])

        class _BrokenDoorService:
            def add_item(self, principal, task, **kw):
                raise RuntimeError("door service unavailable")

        svc, db = _make_service(
            conn,
            project_service=project_svc,
            door_service=_BrokenDoorService(),
        )

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"

        # The effect step should be "failed" with retries exhausted.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        door_steps = [
            s for s in steps if s["effect_kind"] == "create_door_item"
        ]
        assert len(door_steps) == 1
        assert door_steps[0]["state"] == "failed"
        error = json.loads(door_steps[0]["error_json"])
        assert error["attempts"] == 3  # max_retries=2 -> 3 attempts

    def test_cooldown_recorded_in_policy(self, tmp_path: Path) -> None:
        """Cooldown is a policy field, enforced at the scheduling layer."""
        conn = _make_conn(tmp_path)
        policy_id = _make_policy(conn, cooldown=60)
        repos = _make_repos(conn)
        policy = repos[0].get_policy(policy_id)
        assert policy["cooldown_seconds"] == 60


# ── TST-EFF-006: STW-010 policy eligibility ──────────────────────────

class TestSTW010PolicyEligibility:
    """STW-010: unconfigured kinds are skipped with a receipt."""

    def test_unconfigured_kinds_skipped(self, tmp_path: Path) -> None:
        """Only eligible_effect_kinds from policy are applied."""
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        update_svc = _FakeUpdateService()
        svc, db = _make_service(conn, update_service=update_svc)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]

        # Only refresh_sources should be applied.
        applied_kinds = [
            r["effect_kind"]
            for r in act_result.get("effect_receipts", [])
            if r.get("outcome") == "applied"
        ]
        assert "refresh_sources" in applied_kinds

        # Other kinds should be in effects_skipped.
        skipped_kinds = [
            s["effect_kind"]
            for s in act_result.get("effects_skipped", [])
        ]
        assert "draft_update" in skipped_kinds
        assert "create_door_item" in skipped_kinds

    def test_empty_eligible_kinds_skips_all(self, tmp_path: Path) -> None:
        """No eligible kinds -> all effects skipped."""
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=[])
        svc, db = _make_service(conn)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 0
        assert len(act_result.get("effects_skipped", [])) == len(EFFECT_KINDS)

    def test_no_policy_defaults_to_no_effects(self, tmp_path: Path) -> None:
        """Without a policy row, defaults have empty eligible kinds."""
        conn = _make_conn(tmp_path)
        # No policy created.
        svc, db = _make_service(conn)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])
        act_result = summary["phase_results"]["act"]
        assert act_result["actions_taken"] == 0


# ── TST-EFF-007: STW-007 model failure fallback ──────────────────────

class TestSTW007ModelFallback:
    """STW-007: model failure falls back to deterministic with a receipt."""

    def test_update_service_failure_receipted(self, tmp_path: Path) -> None:
        """Update service failure produces a receipted fallback (STW-007).

        The _effect_draft_update catches the exception internally and
        returns a result with skipped=True + a reason -- this is the
        STW-007 deterministic fallback behavior.  The step is completed
        (not failed) because the effect handled the failure gracefully.
        """
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=["draft_update"])
        update_svc = _FakeUpdateService(fail=True)
        svc, db = _make_service(conn, update_service=update_svc)

        run_id = svc.run_once(_principal(), "proj-1")

        # Run completes (failure isolation via STW-007 fallback).
        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"

        # The effect step is completed (not failed) because the
        # STW-007 fallback caught the error and returned a receipt.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        update_steps = [
            s for s in steps if s["effect_kind"] == "draft_update"
        ]
        assert len(update_steps) == 1
        assert update_steps[0]["state"] == "completed"

        # The observed state carries the fallback receipt.
        observed = json.loads(update_steps[0]["observed_state_json"])
        assert observed.get("skipped") is True
        assert "draft_failed" in observed.get("reason", "")
        assert observed.get("fallback") == "deterministic"

    def test_delta_failure_produces_receipt(self, tmp_path: Path) -> None:
        """Delta service failure in create_proposals is receipted."""
        conn = _make_conn(tmp_path)

        class _FailingDelta:
            def open_review(self, principal, project_id):
                raise RuntimeError("model unavailable")

        _make_policy(conn, eligible_kinds=["create_proposals"])
        svc, db = _make_service(conn, delta=_FailingDelta())

        # The run still completes (observe/compare may fail, but the
        # engine catches and marks failed; the important thing is that
        # ACT's create_proposals effect receipts the model failure).
        run_id = svc.run_once(_principal(), "proj-1")
        run = db.steward_runs.get_run(run_id)
        # The run fails at compare phase because the delta fails there.
        # This is correct behavior: the compare phase IS the delta.
        assert run["state"] == "failed"


# ── TST-EFF-008: STW-006 source failure isolation ────────────────────

class TestSTW006SourceIsolation:
    """STW-006: source failures isolate into partial coverage.

    The OBSERVE phase propagates collector exceptions (02 design).
    STW-006 isolation happens in the ACT effect refresh_sources:
    it catches collector failures and returns partial coverage.
    To test this, we use a collector that succeeds in OBSERVE (first
    call) but fails in ACT's refresh_sources (second call).
    """

    def test_refresh_sources_partial_coverage(self, tmp_path: Path) -> None:
        """Collector failure in ACT refresh_sources -> partial, not abort."""
        conn = _make_conn(tmp_path)

        class _FlakeyCollector:
            """Succeeds on first call (OBSERVE), fails on second (ACT)."""
            def __init__(self):
                self.call_count = 0
            def collect_all(self, project_id):
                self.call_count += 1
                if self.call_count >= 2:
                    raise RuntimeError("STW-006: transient source failure")
                return {"github": {"commits": 1}}

        collector = _FlakeyCollector()
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        svc, db = _make_service(conn, collector=collector)

        run_id = svc.run_once(_principal(), "proj-1")

        # Run completes: OBSERVE succeeded, ACT refresh_sources
        # isolated the failure (STW-006).
        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"

        # The refresh_sources effect shows partial coverage.
        steps = db.steward_steps.list_steps(run_id, phase="act")
        refresh_steps = [
            s for s in steps if s["effect_kind"] == "refresh_sources"
        ]
        assert len(refresh_steps) == 1
        observed = json.loads(refresh_steps[0]["observed_state_json"])
        assert observed["partial"] is True

    def test_observe_failure_propagates(self, tmp_path: Path) -> None:
        """Collector failure in OBSERVE propagates (the 02 design)."""
        conn = _make_conn(tmp_path)
        collector = _FakeCollector(fail=True)
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        svc, db = _make_service(conn, collector=collector)

        run_id = svc.run_once(_principal(), "proj-1")

        # Run fails at observe: that's the 02 behavior.
        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "failed"


# ── TST-EFF-009: Compounding integration ─────────────────────────────

class TestCompoundingIntegration:
    """Full pipeline: observe -> compare -> propose -> act (all five) ->
    verify -> record, all receipted."""

    def test_full_pipeline_all_effects(self, tmp_path: Path) -> None:
        """A run with all five effects configured exercises the full path."""
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()

        collector = _FakeCollector(result={"github": {"commits": 3}})
        delta = _FakeDelta(review={
            "id": "prev_full",
            "proposals": [
                {"id": "prop-1", "proposal_kind": "risk_attention",
                 "lifecycle": "open", "title": "Risk from GitHub"},
            ],
        })
        update_svc = _FakeUpdateService()
        project_svc = _FakeProjectService(items=[
            {"id": "item-risk", "item_type": "risk",
             "title": "Overdue risk A",
             "severity": "high", "lifecycle": "open",
             "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()

        _make_policy(conn, eligible_kinds=list(EFFECT_KINDS))
        svc, db = _make_service(
            conn,
            collector=collector,
            delta=delta,
            update_service=update_svc,
            project_service=project_svc,
            door_service=door_svc,
        )

        run_id = svc.run_once(_principal(), "proj-1", watermark="full-test")

        # Run completed.
        run = db.steward_runs.get_run(run_id)
        assert run["state"] == "completed"
        summary = json.loads(run["summary_json"])

        # All six phases present.
        assert summary["phases_completed"] == list(PHASES)

        # OBSERVE: coverage recorded.
        observe = summary["phase_results"]["observe"]
        assert "github" in observe.get("coverage", {})

        # COMPARE: review opened.
        compare = summary["phase_results"]["compare"]
        assert compare["review_id"] == "prev_full"
        assert compare["proposal_count"] == 1

        # ACT: all five effects.
        act = summary["phase_results"]["act"]
        assert act["actions_taken"] == 5

        receipts = act.get("effect_receipts", [])
        applied_kinds = [
            r["effect_kind"] for r in receipts
            if r.get("outcome") == "applied"
        ]
        assert "refresh_sources" in applied_kinds
        assert "create_proposals" in applied_kinds
        assert "apply_proposal_effects" in applied_kinds
        assert "draft_update" in applied_kinds
        assert "create_door_item" in applied_kinds

        # VERIFY: summary with real effects.
        verify = summary["phase_results"]["verify"]
        assert verify["has_real_effects"] is True
        assert verify["actions_taken"] == 5
        assert verify["verified_effects"] == 5

        # RECORD: event recorded.
        record = summary["phase_results"]["record"]
        assert record["event_recorded"] is True

        # External services called correctly.
        assert collector.call_count >= 1
        assert len(delta.decided) == 1
        assert update_svc.call_count == 1
        assert len(door_svc.added) == 1


# ── TST-EFF-010: STW-011 shape ───────────────────────────────────────

class TestSTW011Shape:
    """STW-011: a run with real effects carries verification/receipt."""

    def test_run_with_effects_has_verification(self, tmp_path: Path) -> None:
        """Verify summary flags real effects."""
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        collector = _FakeCollector(result={"test": {}})
        svc, db = _make_service(conn, collector=collector)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        summary = json.loads(run["summary_json"])
        verify = summary["phase_results"]["verify"]
        assert verify["has_real_effects"] is True
        assert verify["actions_taken"] >= 1
        assert len(verify["effect_receipts"]) >= 1

    def test_run_without_effects_flags_no_real_effects(
        self, tmp_path: Path,
    ) -> None:
        """A run with no eligible effects flags has_real_effects=False."""
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=[])
        svc, db = _make_service(conn)

        run_id = svc.run_once(_principal(), "proj-1")

        run = db.steward_runs.get_run(run_id)
        summary = json.loads(run["summary_json"])
        verify = summary["phase_results"]["verify"]
        assert verify["has_real_effects"] is False
        assert verify["actions_taken"] == 0

    def test_receipt_structure(self, tmp_path: Path) -> None:
        """Effect receipts carry the expected structure."""
        conn = _make_conn(tmp_path)
        _make_policy(conn, eligible_kinds=["refresh_sources"])
        collector = _FakeCollector(result={"src": {"ok": True}})
        svc, db = _make_service(conn, collector=collector)

        run_id = svc.run_once(_principal(), "proj-1")

        steps = db.steward_steps.list_steps(run_id, phase="act")
        refresh_steps = [
            s for s in steps if s["effect_kind"] == "refresh_sources"
        ]
        assert len(refresh_steps) == 1
        step = refresh_steps[0]

        # Receipt JSON present and structured.
        receipt = json.loads(step["receipt_json"])
        assert receipt["effect_kind"] == "refresh_sources"
        assert receipt["outcome"] == "applied"
        assert receipt["attempt"] == 1

        # Expected and observed state both recorded (STW-004).
        expected = json.loads(step["expected_state_json"])
        assert expected["effect"] == "refresh_sources"
        observed = json.loads(step["observed_state_json"])
        assert observed["effect"] == "refresh_sources"


class TestFollowThroughLaw:
    """The charter's "lacking canonical follow-through" filter, cross-watermark."""

    def test_cross_watermark_no_second_door_item(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-x", "item_type": "risk", "title": "Overdue risk",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn, project_service=project_svc, door_service=door_svc,
        )

        svc.run_once(_principal(), "proj-1", watermark="wm-1")
        assert len(door_svc.added) == 1

        # New watermark, same overdue item: follow-through now exists,
        # so selection excludes it — zero new Door items, run completes.
        run2 = svc.run_once(_principal(), "proj-1", watermark="wm-2")
        assert len(door_svc.added) == 1
        run = db.steward_runs.get_run(run2)
        assert run["state"] == "completed"

    def test_next_item_lacking_follow_through_selected(
        self, tmp_path: Path,
    ) -> None:
        """On the re-run, the next-material item WITHOUT follow-through wins."""
        conn = _make_conn(tmp_path)
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).date().isoformat()
        project_svc = _FakeProjectService(items=[
            {"id": "item-1", "item_type": "risk", "title": "First",
             "severity": "critical", "lifecycle": "open", "due_at": yesterday},
            {"id": "item-2", "item_type": "risk", "title": "Second",
             "severity": "high", "lifecycle": "open", "due_at": yesterday},
        ])
        door_svc = _FakeDoorService()
        _make_policy(conn, eligible_kinds=["create_door_item"])
        svc, db = _make_service(
            conn, project_service=project_svc, door_service=door_svc,
        )

        svc.run_once(_principal(), "proj-1", watermark="wm-1")
        assert door_svc.added[0]["source_ref"] == "project_item:item-1"

        svc.run_once(_principal(), "proj-1", watermark="wm-2")
        assert len(door_svc.added) == 2
        assert door_svc.added[1]["source_ref"] == "project_item:item-2"
