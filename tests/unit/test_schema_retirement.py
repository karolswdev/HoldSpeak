"""Retirement omits new history without changing the owner's existing history."""
from __future__ import annotations

import ast
import sqlite3

import pytest

from holdspeak.db import Database
from holdspeak.db.schema import PARTS, RETIRED_TABLES, SCHEMA_SQL
from holdspeak.db.schema._parked import inference_routing, inference_turns, reactions
from tests._tree import ast_of, python_files
from tests.unit.test_static_sql_matches_schema import sweep_package
from tests.unit.test_unwritten_tables import _references

pytestmark = pytest.mark.real_schema

# Only tests import parked DDL: it is the original producer of the old shape.
HISTORICAL_SQL = inference_routing.SQL + inference_turns.SQL + reactions.SQL


def _history(conn: sqlite3.Connection) -> tuple[list[tuple], dict[str, list[tuple]]]:
    objects = [tuple(row) for row in conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ) if row[2] in RETIRED_TABLES]
    rows = {table: [tuple(row) for row in conn.execute(f'SELECT * FROM "{table}"')]
            for table in sorted(RETIRED_TABLES)}
    return objects, rows


def test_live_ddl_does_not_name_retired_history() -> None:
    for part in PARTS:
        assert not _references(part.SQL, RETIRED_TABLES), part.__name__
    # The archive and declaration agree without a second hand-kept table list.
    with sqlite3.connect(":memory:") as conn:
        conn.executescript(HISTORICAL_SQL)
        assert {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )} == RETIRED_TABLES


def test_live_schema_does_not_import_parked_ddl() -> None:
    for path in python_files("holdspeak", exclude=("_parked",)):
        for node in ast.walk(ast_of(path)):
            if isinstance(node, ast.ImportFrom):
                assert "_parked" not in (node.module or "").split("."), path
                assert all("_parked" not in alias.name.split(".") for alias in node.names), path
            elif isinstance(node, ast.Import):
                assert all("_parked" not in alias.name.split(".") for alias in node.names), path


def test_fresh_install_omits_retired_tables_indexes_triggers_and_foreign_keys(tmp_path) -> None:
    db = Database(tmp_path / "fresh.db")
    with db._connection() as conn:
        objects = conn.execute("SELECT type,name,tbl_name FROM sqlite_master").fetchall()
        assert not RETIRED_TABLES.intersection(row[2] for row in objects)
        for kind, table, _ in objects:
            if kind != "table":
                continue
            for fk in conn.execute(f'PRAGMA foreign_key_list("{table}")'):
                assert fk[2] not in RETIRED_TABLES, (table, tuple(fk))
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        result = sweep_package(conn)
        assert not result.offenders, result.offenders
    db.close()


def test_old_database_opens_with_history_rows_and_constraints_unchanged(tmp_path) -> None:
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA_SQL + HISTORICAL_SQL)
        conn.execute("PRAGMA foreign_keys=ON")
        # Valid original routing evidence and ToolTurn authority, including
        # opaque owner bytes and an old zoneless stamp, must survive unchanged.
        conn.execute(
            """INSERT INTO inference_route_plans
               (id,sha256,capability_id,capability_revision,capability_schema_sha256,
                assignment_id,assignment_revision,assignment_sha256,inherited_from,
                retry_policy_id,retry_policy_revision,operation_policy_revision,
                payload_json,deadline_at,created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            ("old-plan", "plan-hash", "ask.answer", 1, "schema-hash", "assignment", 1,
             "assignment-hash", "global", "retry", 1, "policy", '{"owner":"évidence"}',
             "2026-11-09T12:00:00+00:00", "2026-11-09T11:00:00"),
        )
        conn.execute(
            """INSERT INTO turn_capability_leases
               (lease_id,turn_id,terms_json,terms_sha256,nonce_sha256,epoch,
                created_at,expires_at,state)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            ("old-lease", "old-turn", '{"owner":"keep me"}', "terms-hash", "nonce", 1,
             1.0, 2.0, "expired"),
        )
        conn.execute(
            "INSERT INTO inference_route_plan_commands(command_id,request_sha256,plan_id,plan_sha256,created_at) VALUES (?,?,?,?,?)",
            ("old-command", "request-hash", "old-plan", "plan-hash", "2026-11-09T11:00:00+00:00"),
        )
        # This projection was still created after its repository was parked.
        # Keep a populated example with valid live parent rows as well.
        conn.execute("INSERT INTO workbenches(id) VALUES ('old-workbench')")
        conn.execute("INSERT INTO workbench_items(id,workbench_id) VALUES ('old-item','old-workbench')")
        conn.execute(
            "INSERT INTO connector_reactions(id,event_pattern,workbench_id) VALUES (?,?,?)",
            ("old-reaction", "meeting.saved", "old-workbench"),
        )
        conn.execute(
            "INSERT INTO service_events(id,event_type,producer,subject_ref,principal_kind) VALUES (?,?,?,?,?)",
            ("old-event", "meeting.saved", "meeting", "meeting:old", "owner"),
        )
        conn.execute(
            "INSERT INTO reaction_event_projections(reaction_id,event_id,item_id) VALUES (?,?,?)",
            ("old-reaction", "old-event", "old-item"),
        )
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        before = _history(conn)

    for _ in range(2):
        db = Database(path)
        with db._connection() as conn:
            assert _history(conn) == before
            with pytest.raises(sqlite3.IntegrityError, match="immutable inference route command"):
                conn.execute("DELETE FROM inference_route_plan_commands WHERE command_id='old-command'")
            result = sweep_package(conn)
            assert not result.offenders, result.offenders
            assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        # A live repository can still write and read alongside the history.
        db.profiles.upsert(profile_id="live", name="Live", kind="openAICompatible",
                           base_url="http://example.test/v1", model="test")
        assert db.profiles.get("live").name == "Live"
        db.close()
