"""HS-164-01: Unattended bookkeeping schema — cadence, opt-in, circuit.

Tests:
- TST-001: a fresh DB has the HS-164-01 columns with correct types and defaults.
- TST-002: opt-in is explicit, default OFF; update round-trips; disabling is
  immediate and durable.
- TST-003: circuit state round-trips through the repo layer (closed/open/
  half_open); get_watch_circuit reads back what was written.
- TST-004: evaluation_cadence_minutes round-trips via update_watch_spec.
- TST-005: reconcile-from-v71 (pre-164) adds the new columns; repeated
  reconcile is idempotent.
- TST-006: reconciled DB supports the repo layer (policy opt-in + circuit
  update on a reconciled DB).
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
from holdspeak.db.steward import StewardPolicyRepository
from holdspeak.db.automations import AutomationRepository
from holdspeak.project_contracts import generate_pstpol_id


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


def _build_pre164_schema() -> str:
    """Return SCHEMA_SQL with HS-164-01 additions stripped out.

    Produces the v71 shape: connector_watches without cadence/circuit columns,
    steward_policies without unattended_enabled.
    """
    sql = SCHEMA_SQL

    # Strip HS-164-01 columns from connector_watches.
    sql = re.sub(
        r",\n    -- HS-164-01: unattended bookkeeping \(cadence \+ circuit\)\.\n"
        r"    evaluation_cadence_minutes INTEGER NOT NULL DEFAULT 60,\n"
        r"    circuit_state TEXT NOT NULL DEFAULT 'closed',\n"
        r"    circuit_failure_streak INTEGER NOT NULL DEFAULT 0,\n"
        r"    circuit_opened_at TEXT",
        "",
        sql,
        count=1,
    )

    # Strip HS-164-01 column from steward_policies.
    sql = re.sub(
        r"\n    -- HS-164-01: explicit per-project unattended opt-in \(default OFF\)\.\n"
        r"    unattended_enabled INTEGER NOT NULL DEFAULT 0,",
        "",
        sql,
        count=1,
    )

    return sql


def _seed_project(conn: sqlite3.Connection) -> None:
    """Insert a minimal project row for FK satisfaction."""
    conn.execute(
        "INSERT OR IGNORE INTO projects (id, name) VALUES (?, ?)",
        ("proj-1", "Test Project"),
    )
    conn.commit()


def _seed_watch(conn: sqlite3.Connection, watch_id: str = "watch-1") -> None:
    """Insert a minimal connector_watches row for FK/circuit testing."""
    conn.execute(
        "INSERT OR IGNORE INTO connector_watches "
        "(id, connector_id, query_kind) VALUES (?, ?, ?)",
        (watch_id, "conn-1", "github.issues"),
    )
    conn.commit()


def _make_policy_repo(conn: sqlite3.Connection) -> StewardPolicyRepository:
    @contextmanager
    def _ctx():
        yield conn
        conn.commit()
    return StewardPolicyRepository(_ctx)


def _make_automation_repo(conn: sqlite3.Connection) -> AutomationRepository:
    @contextmanager
    def _ctx():
        yield conn
        conn.commit()
    return AutomationRepository(_ctx)


def _make_conn(tmp_path: Path, db_name: str = "test.db") -> sqlite3.Connection:
    db_path = tmp_path / db_name
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    return conn


# -- TST-001: fresh DB has the right shape ---------------------------------

class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has the HS-164-01 columns."""

    def test_schema_version_is_72(self) -> None:
        assert SCHEMA_VERSION == 72

    def test_connector_watches_has_cadence_column(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        cols = _get_columns(conn, "connector_watches")
        assert "evaluation_cadence_minutes" in cols
        assert cols["evaluation_cadence_minutes"]["type"] == "INTEGER"
        assert cols["evaluation_cadence_minutes"]["notnull"] == 1
        assert cols["evaluation_cadence_minutes"]["dflt_value"] == "60"
        conn.close()

    def test_connector_watches_has_circuit_columns(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        cols = _get_columns(conn, "connector_watches")

        assert "circuit_state" in cols
        assert cols["circuit_state"]["type"] == "TEXT"
        assert cols["circuit_state"]["notnull"] == 1
        assert cols["circuit_state"]["dflt_value"] == "'closed'"

        assert "circuit_failure_streak" in cols
        assert cols["circuit_failure_streak"]["type"] == "INTEGER"
        assert cols["circuit_failure_streak"]["notnull"] == 1
        assert cols["circuit_failure_streak"]["dflt_value"] == "0"

        assert "circuit_opened_at" in cols
        assert cols["circuit_opened_at"]["type"] == "TEXT"
        assert cols["circuit_opened_at"]["notnull"] == 0  # nullable
        conn.close()

    def test_steward_policies_has_unattended_enabled(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        cols = _get_columns(conn, "steward_policies")
        assert "unattended_enabled" in cols
        assert cols["unattended_enabled"]["type"] == "INTEGER"
        assert cols["unattended_enabled"]["notnull"] == 1
        assert cols["unattended_enabled"]["dflt_value"] == "0"
        conn.close()

    def test_default_values_on_insert(self, tmp_path: Path) -> None:
        """Inserting a watch row without explicit 164 columns gets the defaults."""
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        row = conn.execute(
            "SELECT evaluation_cadence_minutes, circuit_state, "
            "circuit_failure_streak, circuit_opened_at "
            "FROM connector_watches WHERE id = 'watch-1'"
        ).fetchone()
        assert row["evaluation_cadence_minutes"] == 60
        assert row["circuit_state"] == "closed"
        assert row["circuit_failure_streak"] == 0
        assert row["circuit_opened_at"] is None
        conn.close()


# -- TST-002: opt-in explicit, default OFF, disable durable ----------------

class TestOptIn:
    """The unattended_enabled flag on steward_policies."""

    def test_default_off(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_project(conn)
        repo = _make_policy_repo(conn)
        pid = generate_pstpol_id()
        repo.insert_policy(policy_id=pid, project_id="proj-1")
        row = repo.get_policy(pid)
        assert row is not None
        assert row["unattended_enabled"] == 0
        conn.close()

    def test_explicit_enable(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_project(conn)
        repo = _make_policy_repo(conn)
        pid = generate_pstpol_id()
        repo.insert_policy(
            policy_id=pid, project_id="proj-1", unattended_enabled=1
        )
        row = repo.get_policy(pid)
        assert row is not None
        assert row["unattended_enabled"] == 1
        conn.close()

    def test_disable_is_immediate_and_durable(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_project(conn)
        repo = _make_policy_repo(conn)
        pid = generate_pstpol_id()
        repo.insert_policy(
            policy_id=pid, project_id="proj-1", unattended_enabled=1
        )
        # Disable
        repo.update_policy(pid, unattended_enabled=0)
        row = repo.get_policy(pid)
        assert row is not None
        assert row["unattended_enabled"] == 0

        # Re-read from a fresh cursor to prove durability
        row2 = conn.execute(
            "SELECT unattended_enabled FROM steward_policies WHERE id = ?",
            (pid,),
        ).fetchone()
        assert row2["unattended_enabled"] == 0
        conn.close()

    def test_update_round_trip(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_project(conn)
        repo = _make_policy_repo(conn)
        pid = generate_pstpol_id()
        repo.insert_policy(policy_id=pid, project_id="proj-1")
        assert repo.get_policy(pid)["unattended_enabled"] == 0

        repo.update_policy(pid, unattended_enabled=1)
        assert repo.get_policy(pid)["unattended_enabled"] == 1

        repo.update_policy(pid, unattended_enabled=0)
        assert repo.get_policy(pid)["unattended_enabled"] == 0
        conn.close()


# -- TST-003: circuit state round-trip -------------------------------------

class TestCircuitState:
    """Durable circuit state on connector_watches through the repo layer."""

    def test_circuit_defaults_on_fresh_watch(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        repo = _make_automation_repo(conn)
        circuit = repo.get_watch_circuit("watch-1")
        assert circuit is not None
        assert circuit["circuit_state"] == "closed"
        assert circuit["circuit_failure_streak"] == 0
        assert circuit["circuit_opened_at"] is None
        conn.close()

    def test_open_circuit_round_trip(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        repo = _make_automation_repo(conn)
        ok = repo.update_watch_circuit(
            "watch-1",
            circuit_state="open",
            circuit_failure_streak=3,
            circuit_opened_at="2026-09-01T12:00:00+00:00",
        )
        assert ok is True
        circuit = repo.get_watch_circuit("watch-1")
        assert circuit["circuit_state"] == "open"
        assert circuit["circuit_failure_streak"] == 3
        assert circuit["circuit_opened_at"] == "2026-09-01T12:00:00+00:00"
        conn.close()

    def test_half_open_then_close(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        repo = _make_automation_repo(conn)

        # Open
        repo.update_watch_circuit(
            "watch-1",
            circuit_state="open",
            circuit_failure_streak=5,
            circuit_opened_at="2026-09-01T12:00:00+00:00",
        )
        # Half-open
        repo.update_watch_circuit(
            "watch-1",
            circuit_state="half_open",
            circuit_failure_streak=5,
            circuit_opened_at="2026-09-01T12:00:00+00:00",
        )
        circuit = repo.get_watch_circuit("watch-1")
        assert circuit["circuit_state"] == "half_open"

        # Close (success after half-open)
        repo.update_watch_circuit(
            "watch-1",
            circuit_state="closed",
            circuit_failure_streak=0,
            circuit_opened_at=None,
        )
        circuit = repo.get_watch_circuit("watch-1")
        assert circuit["circuit_state"] == "closed"
        assert circuit["circuit_failure_streak"] == 0
        assert circuit["circuit_opened_at"] is None
        conn.close()

    def test_nonexistent_watch_returns_none(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        repo = _make_automation_repo(conn)
        assert repo.get_watch_circuit("no-such-watch") is None
        conn.close()

    def test_update_nonexistent_watch_returns_false(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        repo = _make_automation_repo(conn)
        ok = repo.update_watch_circuit(
            "no-such-watch",
            circuit_state="open",
            circuit_failure_streak=1,
        )
        assert ok is False
        conn.close()

    def test_in_transaction_variant(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        repo = _make_automation_repo(conn)
        ok = repo.update_watch_circuit_in_transaction(
            conn, "watch-1",
            circuit_state="open",
            circuit_failure_streak=2,
            circuit_opened_at="2026-09-01T14:00:00+00:00",
        )
        assert ok is True
        circuit = repo.get_watch_circuit_in_transaction(conn, "watch-1")
        assert circuit["circuit_state"] == "open"
        conn.close()


# -- TST-004: evaluation_cadence_minutes -----------------------------------

class TestCadence:
    """evaluation_cadence_minutes round-trips via update_watch_spec."""

    def test_default_cadence(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        row = conn.execute(
            "SELECT evaluation_cadence_minutes FROM connector_watches WHERE id='watch-1'"
        ).fetchone()
        assert row["evaluation_cadence_minutes"] == 60
        conn.close()

    def test_update_cadence(self, tmp_path: Path) -> None:
        conn = _make_conn(tmp_path)
        _seed_watch(conn)
        repo = _make_automation_repo(conn)
        ok = repo.update_watch_spec("watch-1", evaluation_cadence_minutes=15)
        assert ok is True
        row = conn.execute(
            "SELECT evaluation_cadence_minutes FROM connector_watches WHERE id='watch-1'"
        ).fetchone()
        assert row["evaluation_cadence_minutes"] == 15
        conn.close()


# -- TST-005: reconcile-from-v71 ------------------------------------------

class TestReconcile:
    """Reconcile adds HS-164-01 columns to a pre-164 (v71) DB."""

    def test_reconcile_adds_164_columns(self, tmp_path: Path) -> None:
        pre164 = _build_pre164_schema()
        db_path = tmp_path / "v71.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre164)
        conn.commit()

        # Verify 164 columns do NOT exist yet
        cw_cols = _get_columns(conn, "connector_watches")
        assert "evaluation_cadence_minutes" not in cw_cols
        assert "circuit_state" not in cw_cols

        sp_cols = _get_columns(conn, "steward_policies")
        assert "unattended_enabled" not in sp_cols

        # Reconcile
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        # Now columns exist
        cw_cols = _get_columns(conn, "connector_watches")
        assert "evaluation_cadence_minutes" in cw_cols
        assert "circuit_state" in cw_cols
        assert "circuit_failure_streak" in cw_cols
        assert "circuit_opened_at" in cw_cols

        sp_cols = _get_columns(conn, "steward_policies")
        assert "unattended_enabled" in sp_cols

        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        pre164 = _build_pre164_schema()
        db_path = tmp_path / "v71-idem.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre164)
        conn.commit()

        changed1 = reconcile_schema(conn, db_path=db_path)
        assert changed1 is True
        changed2 = reconcile_schema(conn, db_path=db_path)
        assert changed2 is False
        conn.close()


# -- TST-006: reconciled DB supports repo layer ----------------------------

class TestReconciledOperations:
    """After reconcile, the repo layer works on the reconciled DB."""

    def test_opt_in_on_reconciled_db(self, tmp_path: Path) -> None:
        pre164 = _build_pre164_schema()
        db_path = tmp_path / "v71-ops-policy.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre164)
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        _seed_project(conn)

        repo = _make_policy_repo(conn)
        pid = generate_pstpol_id()
        repo.insert_policy(policy_id=pid, project_id="proj-1", unattended_enabled=1)
        row = repo.get_policy(pid)
        assert row["unattended_enabled"] == 1

        repo.update_policy(pid, unattended_enabled=0)
        row = repo.get_policy(pid)
        assert row["unattended_enabled"] == 0
        conn.close()

    def test_circuit_on_reconciled_db(self, tmp_path: Path) -> None:
        pre164 = _build_pre164_schema()
        db_path = tmp_path / "v71-ops-circuit.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre164)
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        _seed_watch(conn)

        repo = _make_automation_repo(conn)
        ok = repo.update_watch_circuit(
            "watch-1",
            circuit_state="open",
            circuit_failure_streak=3,
            circuit_opened_at="2026-09-01T12:00:00+00:00",
        )
        assert ok is True
        circuit = repo.get_watch_circuit("watch-1")
        assert circuit["circuit_state"] == "open"
        assert circuit["circuit_failure_streak"] == 3
        conn.close()

    def test_cadence_on_reconciled_db(self, tmp_path: Path) -> None:
        pre164 = _build_pre164_schema()
        db_path = tmp_path / "v71-ops-cadence.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre164)
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        _seed_watch(conn)

        repo = _make_automation_repo(conn)
        ok = repo.update_watch_spec("watch-1", evaluation_cadence_minutes=30)
        assert ok is True
        row = conn.execute(
            "SELECT evaluation_cadence_minutes FROM connector_watches WHERE id='watch-1'"
        ).fetchone()
        assert row["evaluation_cadence_minutes"] == 30
        conn.close()
