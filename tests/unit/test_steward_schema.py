"""HS-163-01: Steward ledger schema and repo layer.

Tests:
- TST-001: a fresh DB has steward_policies/runs/steps/commands with correct
  columns, defaults, FKs, indexes, and the STW-002 partial unique index.
- TST-002: policy CRUD: insert, get, get_for_project, update.
- TST-003: run lifecycle: insert, state transitions, list by state.
- TST-004: STW-002 refusal -- a second active run for the same project raises
  ActiveRunExistsError; different projects are independent; terminal runs
  free the slot.
- TST-005: step reconcile-by-idempotency-key -- insert a step with a key,
  retrieve it by key, update observed state, re-retrieve.
- TST-006: command records: insert, list by run.
- TST-007: reconcile-from-v70 -- a DB built from the v70 schema gains the
  steward tables after reconcile; repeated reconcile is idempotent.
"""
from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Optional

import pytest

from holdspeak.db.schema import SCHEMA_SQL, SCHEMA_VERSION
from holdspeak.db.reconcile import reconcile_schema
from holdspeak.db.steward import (
    ActiveRunExistsError,
    StewardCommandRepository,
    StewardPolicyRepository,
    StewardRunRepository,
    StewardStepRepository,
)
from holdspeak.project_contracts import (
    generate_pcmd_id,
    generate_pstpol_id,
    generate_pstrun_id,
    generate_pststep_id,
)


# -- Helpers ---------------------------------------------------------------

def _get_columns(conn: sqlite3.Connection, table: str) -> dict[str, dict]:
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return {
        row[1]: {
            "type": row[2],
            "notnull": row[3],
            "dflt_value": row[4],
            "pk": row[5],
        }
        for row in rows
    }


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone() is not None


def _index_exists(conn: sqlite3.Connection, index_name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
        (index_name,),
    ).fetchone() is not None


def _fk_tables(conn: sqlite3.Connection, table: str) -> set[str]:
    fk_rows = conn.execute(f'PRAGMA foreign_key_list("{table}")').fetchall()
    return {row[2] for row in fk_rows}


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


def _build_pre163_schema() -> str:
    """Return SCHEMA_SQL with HS-163-01 additions stripped out.

    Produces the v70 shape: no steward tables.
    """
    sql = SCHEMA_SQL
    marker = "\n-- HS-163-01: Steward policy"
    idx = sql.find(marker)
    if idx >= 0:
        sql = sql[:idx] + "\n"
    return sql


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


# -- TST-001: fresh DB has the right shape ---------------------------------

class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has the HS-163-01 shape."""

    def test_schema_version_is_at_least_the_phase_floor(self) -> None:
        """SCHEMA_VERSION is informational and additive-only (HS-137): this
        phase was built at 73; later additive phases bump it (74 the
        calendar_event_projects join, 75 calendar_event_link_suppressions).
        The honest assertion is the floor, read from the real constant."""
        assert SCHEMA_VERSION >= 73

    def test_steward_tables_exist(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        for tbl in ("steward_policies", "steward_runs", "steward_steps", "steward_commands"):
            assert _table_exists(conn, tbl), f"Missing table: {tbl}"
        conn.close()

    def test_steward_policies_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "steward_policies")
        expected = [
            "id", "project_id", "eligible_effect_kinds_json",
            "yolo_flags_json", "max_retries", "max_actions_per_run",
            "cooldown_seconds", "bounds_json", "enabled",
            "created_at", "updated_at",
        ]
        for col in expected:
            assert col in cols, f"steward_policies missing column {col}"
        conn.close()

    def test_steward_runs_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "steward_runs")
        expected = [
            "id", "project_id", "policy_id", "state", "phase",
            "requested_by", "stop_requested_at", "watermark",
            "summary_json", "created_at", "updated_at",
            "started_at", "completed_at",
        ]
        for col in expected:
            assert col in cols, f"steward_runs missing column {col}"
        conn.close()

    def test_steward_steps_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "steward_steps")
        expected = [
            "id", "run_id", "phase", "seq", "state",
            "effect_kind", "idempotency_key",
            "expected_state_json", "observed_state_json",
            "receipt_json", "error_json",
            "created_at", "updated_at", "completed_at",
        ]
        for col in expected:
            assert col in cols, f"steward_steps missing column {col}"
        conn.close()

    def test_steward_commands_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "steward_commands")
        expected = [
            "id", "run_id", "step_id", "command_kind",
            "payload_json", "result_json", "created_at",
        ]
        for col in expected:
            assert col in cols, f"steward_commands missing column {col}"
        conn.close()

    def test_steward_runs_fk_to_projects(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "projects" in _fk_tables(conn, "steward_runs")
        conn.close()

    def test_steward_steps_fk_to_runs(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "steward_runs" in _fk_tables(conn, "steward_steps")
        conn.close()

    def test_steward_commands_fk_to_runs(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "steward_runs" in _fk_tables(conn, "steward_commands")
        conn.close()

    def test_stw002_partial_unique_index_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _index_exists(conn, "uq_steward_runs_one_active_per_project")
        conn.close()

    def test_steward_indexes_exist(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        for idx in (
            "idx_steward_policies_project",
            "idx_steward_runs_project",
            "idx_steward_steps_run",
            "idx_steward_steps_idempotency",
            "idx_steward_commands_run",
        ):
            assert _index_exists(conn, idx), f"Missing index: {idx}"
        conn.close()


# -- TST-002: policy CRUD -------------------------------------------------

class TestPolicyCRUD:
    """Steward policy insert, get, update truth table."""

    def test_insert_and_get_policy(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        pol_repo, _, _, _ = _make_repos(conn)
        pol_id = generate_pstpol_id()
        pol_repo.insert_policy(
            policy_id=pol_id,
            project_id="proj-1",
            eligible_effect_kinds_json='["draft_update"]',
            yolo_flags_json='{"auto_draft": true}',
            max_retries=5,
            max_actions_per_run=20,
            cooldown_seconds=60,
        )
        row = pol_repo.get_policy(pol_id)
        assert row is not None
        assert row["project_id"] == "proj-1"
        assert row["eligible_effect_kinds_json"] == '["draft_update"]'
        assert row["max_retries"] == 5
        assert row["max_actions_per_run"] == 20
        assert row["cooldown_seconds"] == 60
        assert row["enabled"] == 1
        conn.close()

    def test_get_policy_for_project(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        pol_repo, _, _, _ = _make_repos(conn)
        pol_id = generate_pstpol_id()
        pol_repo.insert_policy(policy_id=pol_id, project_id="proj-1")
        row = pol_repo.get_policy_for_project("proj-1")
        assert row is not None
        assert row["id"] == pol_id
        conn.close()

    def test_update_policy_fields(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        pol_repo, _, _, _ = _make_repos(conn)
        pol_id = generate_pstpol_id()
        pol_repo.insert_policy(policy_id=pol_id, project_id="proj-1")
        pol_repo.update_policy(
            pol_id,
            max_retries=10,
            enabled=0,
        )
        row = pol_repo.get_policy(pol_id)
        assert row is not None
        assert row["max_retries"] == 10
        assert row["enabled"] == 0
        conn.close()


# -- TST-003: run lifecycle -----------------------------------------------

class TestRunLifecycle:
    """Run insert, state transitions, list filtering."""

    def test_insert_run_defaults(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        pol_repo = _make_repos(conn)[0]
        run_id = generate_pstrun_id()
        run_repo.insert_run(
            run_id=run_id,
            project_id="proj-1",
            requested_by="manual",
        )
        row = run_repo.get_run(run_id)
        assert row is not None
        assert row["state"] == "queued"
        assert row["phase"] == "observe"
        assert row["requested_by"] == "manual"
        assert row["summary_json"] == "{}"
        conn.close()

    def test_state_transitions(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")

        # queued -> running
        run_repo.update_run_state(run_id, state="running", phase="observe")
        row = run_repo.get_run(run_id)
        assert row["state"] == "running"
        assert row["started_at"] is not None

        # running -> completed
        run_repo.update_run_state(
            run_id,
            state="completed",
            phase="record",
            summary_json='{"steps": 3}',
        )
        row = run_repo.get_run(run_id)
        assert row["state"] == "completed"
        assert row["phase"] == "record"
        assert row["completed_at"] is not None
        assert row["summary_json"] == '{"steps": 3}'
        conn.close()

    def test_list_runs_by_state(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        run_repo.update_run_state(r1, state="completed")
        run_repo.insert_run(run_id=r2, project_id="proj-1")

        all_runs = run_repo.list_runs("proj-1")
        assert len(all_runs) == 2

        queued = run_repo.list_runs("proj-1", state="queued")
        assert len(queued) == 1
        assert queued[0]["id"] == r2
        conn.close()

    def test_get_active_run(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")

        active = run_repo.get_active_run("proj-1")
        assert active is not None
        assert active["id"] == run_id

        run_repo.update_run_state(run_id, state="completed")
        assert run_repo.get_active_run("proj-1") is None
        conn.close()

    def test_request_stop(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        run_repo.update_run_state(run_id, state="running")
        run_repo.request_stop(run_id)
        row = run_repo.get_run(run_id)
        assert row["state"] == "stopping"
        assert row["stop_requested_at"] is not None
        conn.close()


# -- TST-004: STW-002 refusal ---------------------------------------------

class TestSTW002ActiveRunUniqueness:
    """A second active run for the same project raises ActiveRunExistsError."""

    def test_second_active_run_refused(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        with pytest.raises(ActiveRunExistsError):
            run_repo.insert_run(run_id=r2, project_id="proj-1")
        conn.close()

    def test_terminal_run_frees_slot(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        run_repo.update_run_state(r1, state="completed")
        # Now a second run should succeed
        run_repo.insert_run(run_id=r2, project_id="proj-1")
        assert run_repo.get_run(r2) is not None
        conn.close()

    def test_different_projects_independent(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_project(conn, "proj-2", "Beta")
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        # Different project -- should succeed
        run_repo.insert_run(run_id=r2, project_id="proj-2")
        assert run_repo.get_run(r2) is not None
        conn.close()

    def test_interrupted_run_frees_slot(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        run_repo.update_run_state(r1, state="interrupted")
        run_repo.insert_run(run_id=r2, project_id="proj-1")
        assert run_repo.get_run(r2) is not None
        conn.close()

    def test_failed_run_frees_slot(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        run_repo.update_run_state(r1, state="failed")
        run_repo.insert_run(run_id=r2, project_id="proj-1")
        assert run_repo.get_run(r2) is not None
        conn.close()

    def test_stopping_still_blocks(self, tmp_path: Path) -> None:
        """A 'stopping' run is still active -- it blocks new ones."""
        conn = _make_conn(tmp_path)
        _, run_repo, _, _ = _make_repos(conn)
        r1 = generate_pstrun_id()
        r2 = generate_pstrun_id()
        run_repo.insert_run(run_id=r1, project_id="proj-1")
        run_repo.request_stop(r1)
        row = run_repo.get_run(r1)
        assert row["state"] == "stopping"
        with pytest.raises(ActiveRunExistsError):
            run_repo.insert_run(run_id=r2, project_id="proj-1")
        conn.close()


# -- TST-005: step reconcile-by-idempotency-key ----------------------------

class TestStepReconcileByKey:
    """Step record carries idempotency_key + expected/observed for STW-005."""

    def test_insert_step_with_key(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, step_repo, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        step_id = generate_pststep_id()
        idem_key = "draft-update:proj-1:rev-6"
        step_repo.insert_step(
            step_id=step_id,
            run_id=run_id,
            phase="act",
            seq=1,
            state="pending",
            effect_kind="draft_update",
            idempotency_key=idem_key,
            expected_state_json='{"lifecycle": "draft", "draft_revision": 1}',
        )
        row = step_repo.get_step(step_id)
        assert row is not None
        assert row["idempotency_key"] == idem_key
        assert row["expected_state_json"] == '{"lifecycle": "draft", "draft_revision": 1}'
        assert row["observed_state_json"] == "{}"
        conn.close()

    def test_reconcile_by_key_lookup(self, tmp_path: Path) -> None:
        """STW-005: a step can be found by idempotency_key for reconciliation."""
        conn = _make_conn(tmp_path)
        _, run_repo, step_repo, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        step_id = generate_pststep_id()
        idem_key = "create-door-item:proj-1:pitem_abc123"
        step_repo.insert_step(
            step_id=step_id,
            run_id=run_id,
            phase="act",
            seq=2,
            effect_kind="create_door_item",
            idempotency_key=idem_key,
            expected_state_json='{"exists": false}',
        )
        # Reconcile lookup by key
        found = step_repo.get_step_by_idempotency_key(idem_key)
        assert found is not None
        assert found["id"] == step_id
        assert found["effect_kind"] == "create_door_item"
        assert found["expected_state_json"] == '{"exists": false}'
        conn.close()

    def test_update_observed_state(self, tmp_path: Path) -> None:
        """After execution, the step records observed state for verification."""
        conn = _make_conn(tmp_path)
        _, run_repo, step_repo, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        step_id = generate_pststep_id()
        idem_key = "draft-update:proj-1:rev-7"
        step_repo.insert_step(
            step_id=step_id,
            run_id=run_id,
            phase="verify",
            seq=1,
            effect_kind="draft_update",
            idempotency_key=idem_key,
            expected_state_json='{"lifecycle": "draft"}',
        )
        step_repo.update_step(
            step_id,
            state="completed",
            observed_state_json='{"lifecycle": "draft", "body_md": "..."}',
            receipt_json='{"update_id": "pupd_abc123"}',
        )
        row = step_repo.get_step(step_id)
        assert row["state"] == "completed"
        assert row["observed_state_json"] == '{"lifecycle": "draft", "body_md": "..."}'
        assert row["receipt_json"] == '{"update_id": "pupd_abc123"}'
        assert row["completed_at"] is not None

        # Re-retrieve by key to confirm reconcile path
        found = step_repo.get_step_by_idempotency_key(idem_key)
        assert found["state"] == "completed"
        assert found["observed_state_json"] == '{"lifecycle": "draft", "body_md": "..."}'
        conn.close()

    def test_step_with_error(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, step_repo, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        step_id = generate_pststep_id()
        step_repo.insert_step(
            step_id=step_id,
            run_id=run_id,
            phase="act",
            seq=1,
            effect_kind="refresh_source",
            idempotency_key="refresh:src-1:v3",
        )
        step_repo.update_step(
            step_id,
            state="failed",
            error_json='{"code": "SOURCE_TIMEOUT", "detail": "timed out after 30s"}',
        )
        row = step_repo.get_step(step_id)
        assert row["state"] == "failed"
        assert "SOURCE_TIMEOUT" in row["error_json"]
        assert row["completed_at"] is not None
        conn.close()

    def test_list_steps_by_phase(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, step_repo, _ = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        for i, phase in enumerate(["observe", "observe", "act"]):
            step_repo.insert_step(
                step_id=generate_pststep_id(),
                run_id=run_id,
                phase=phase,
                seq=i,
            )
        observe_steps = step_repo.list_steps(run_id, phase="observe")
        assert len(observe_steps) == 2
        act_steps = step_repo.list_steps(run_id, phase="act")
        assert len(act_steps) == 1
        conn.close()


# -- TST-006: command records -----------------------------------------------

class TestCommandRecords:
    """Steward command records: insert and list."""

    def test_insert_and_list_commands(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _, run_repo, step_repo, cmd_repo = _make_repos(conn)
        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        step_id = generate_pststep_id()
        step_repo.insert_step(step_id=step_id, run_id=run_id, phase="act", seq=1)

        c1 = generate_pcmd_id()
        c2 = generate_pcmd_id()
        cmd_repo.insert_command(
            command_id=c1,
            run_id=run_id,
            step_id=step_id,
            command_kind="draft_update",
            payload_json='{"project_id": "proj-1"}',
            result_json='{"update_id": "pupd_xyz"}',
        )
        cmd_repo.insert_command(
            command_id=c2,
            run_id=run_id,
            command_kind="refresh_source",
            payload_json='{"source_id": "psrc_abc"}',
        )
        cmds = cmd_repo.list_commands(run_id)
        assert len(cmds) == 2
        assert cmds[0]["command_kind"] in ("draft_update", "refresh_source")
        conn.close()


# -- TST-007: reconcile-from-v70 -------------------------------------------

class TestReconcileFromV70:
    """A DB built from v70 schema gains steward tables after reconcile."""

    def test_reconcile_adds_steward_tables(self, tmp_path: Path) -> None:
        """Build a v70 DB, reconcile, verify steward tables appear."""
        pre163 = _build_pre163_schema()
        db_path = tmp_path / "v70.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre163)
        conn.commit()

        # Verify steward tables do NOT exist yet
        for tbl in ("steward_policies", "steward_runs", "steward_steps", "steward_commands"):
            assert not _table_exists(conn, tbl), f"{tbl} should not exist before reconcile"

        # Reconcile
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        # Now all steward tables exist
        for tbl in ("steward_policies", "steward_runs", "steward_steps", "steward_commands"):
            assert _table_exists(conn, tbl), f"{tbl} missing after reconcile"

        # The partial unique index exists
        assert _index_exists(conn, "uq_steward_runs_one_active_per_project")

        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        """Running reconcile twice does not error or change anything the second time."""
        pre163 = _build_pre163_schema()
        db_path = tmp_path / "v70-idem.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre163)
        conn.commit()

        changed1 = reconcile_schema(conn, db_path=db_path)
        assert changed1 is True
        changed2 = reconcile_schema(conn, db_path=db_path)
        # Second reconcile should find nothing new
        assert changed2 is False
        conn.close()

    def test_reconciled_db_supports_steward_operations(self, tmp_path: Path) -> None:
        """After reconcile, the repo layer works on the reconciled DB."""
        pre163 = _build_pre163_schema()
        db_path = tmp_path / "v70-ops.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre163)
        conn.commit()
        reconcile_schema(conn, db_path=db_path)

        _seed_project(conn)
        _, run_repo, step_repo, cmd_repo = _make_repos(conn)

        run_id = generate_pstrun_id()
        run_repo.insert_run(run_id=run_id, project_id="proj-1")
        row = run_repo.get_run(run_id)
        assert row is not None
        assert row["state"] == "queued"

        step_id = generate_pststep_id()
        step_repo.insert_step(
            step_id=step_id,
            run_id=run_id,
            phase="observe",
            seq=0,
            idempotency_key="test-recon-key",
        )
        found = step_repo.get_step_by_idempotency_key("test-recon-key")
        assert found is not None
        assert found["id"] == step_id
        conn.close()
