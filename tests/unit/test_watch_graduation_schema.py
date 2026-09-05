"""HS-159-01: WatchSpec@1 graduation schema — reconcile, backfill, new tables.

Tests:
- TST-001: a fresh DB has all new columns/tables with correct defaults.
- TST-002: a legacy (pre-159) DB reconciles: existing connector_watches rows
  backfilled to WatchSpec@1 with IDs, query_json, snapshot_json, and attached
  connector_reactions intact; repeated reconcile idempotent.
- TST-003: real-DB proof — copy the owner's DB, reconcile the copy, verify
  watch row counts, reactions intact, backfill truth, and idempotency.
- TST-004: project_sources enforces DOM-013 by shape (no query/cadence/baseline
  columns exist).
- TST-005: backfill truth table — enabled/disabled, custom/default cadence,
  existing query_json preserved.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
from pathlib import Path
from typing import Optional

import pytest

from holdspeak.db.schema import SCHEMA_SQL, SCHEMA_VERSION
from holdspeak.db.reconcile import reconcile_schema


# ── Helpers ──────────────────────────────────────────────────────────────

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


def _build_pre159_schema() -> str:
    """Return SCHEMA_SQL with HS-159-01 additions stripped out.

    This produces a schema matching the shape before this story: the
    connector_watches table without graduation columns and none of the
    eight new tables.
    """
    sql = SCHEMA_SQL

    # Strip graduation columns from connector_watches.
    sql = re.sub(
        r",\n    -- HS-159-01: WatchSpec@1 graduation columns \(§9\.3\)\.\n"
        r"    schema_version TEXT NOT NULL DEFAULT '',\n"
        r"    project_id TEXT,\n"
        r"    intent TEXT NOT NULL DEFAULT '',\n"
        r"    provider_connection_id TEXT,\n"
        r"    subject_kind TEXT NOT NULL DEFAULT '',\n"
        r"    trigger_kind TEXT NOT NULL DEFAULT '',\n"
        r"    trigger_json TEXT NOT NULL DEFAULT '\{\}',\n"
        r"    mode TEXT NOT NULL DEFAULT '',\n"
        r"    state TEXT NOT NULL DEFAULT '',\n"
        r"    revision INTEGER NOT NULL DEFAULT 0,\n"
        r"    baseline_state TEXT NOT NULL DEFAULT '',\n"
        r"    test_state TEXT NOT NULL DEFAULT '',\n"
        r"    test_result_json TEXT,\n"
        r"    last_test_at TEXT,\n"
        r"    next_evaluation_at TEXT,\n"
        r"    last_evaluated_at TEXT",
        "",
        sql,
        count=1,
    )

    # Strip the eight new tables and their indexes by truncating at the marker.
    marker = "\n-- HS-159-01: Project setup interview"
    idx = sql.find(marker)
    if idx >= 0:
        sql = sql[:idx] + "\n"

    return sql


def _find_real_db() -> Optional[Path]:
    real_home = os.environ.get("HOLDSPEAK_REAL_HOME") or str(Path.home())
    candidate = Path(real_home) / ".local" / "share" / "holdspeak" / "holdspeak.db"
    if candidate.exists():
        return candidate
    return None


# ── TST-001: fresh DB has all new shapes ─────────────────────────────────

class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has every HS-159-01 shape."""

    def test_schema_version_is_73(self) -> None:
        assert SCHEMA_VERSION == 73

    def test_connector_watches_has_graduation_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "connector_watches")
        grad_cols = [
            "schema_version", "project_id", "intent",
            "provider_connection_id", "subject_kind", "trigger_kind",
            "trigger_json", "mode", "state", "revision",
            "baseline_state", "test_state", "test_result_json",
            "last_test_at", "next_evaluation_at", "last_evaluated_at",
        ]
        for col in grad_cols:
            assert col in cols, f"connector_watches missing column {col}"
        conn.close()

    def test_connector_watches_graduation_defaults(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh-defaults.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "connector_watches")
        assert cols["schema_version"]["dflt_value"] == "''"
        assert cols["schema_version"]["notnull"] == 1
        assert cols["project_id"]["notnull"] == 0  # nullable
        assert cols["revision"]["dflt_value"] == "0"
        assert cols["trigger_json"]["dflt_value"] == "'{}'"
        conn.close()

    @pytest.mark.parametrize("table_name", [
        "project_setup_sessions",
        "project_setup_answers",
        "watch_setup_proposals",
        "watch_provider_connections",
        "watch_rules",
        "watch_evaluations",
        "watch_effects",
        "project_sources",
    ])
    def test_new_table_exists(self, tmp_path: Path, table_name: str) -> None:
        conn = sqlite3.connect(str(tmp_path / f"fresh-{table_name}.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, table_name), f"Table {table_name} missing"
        conn.close()

    def test_setup_answers_unique_constraint(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "unique-answers.db"))
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO project_setup_sessions (id) VALUES ('s1')"
        )
        conn.execute(
            "INSERT INTO project_setup_answers "
            "(id,session_id,question_id,revision) VALUES ('a1','s1','q1',1)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO project_setup_answers "
                "(id,session_id,question_id,revision) VALUES ('a2','s1','q1',1)"
            )
        conn.close()

    def test_watch_rules_unique_constraint(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "unique-rules.db"))
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO connector_watches (id,connector_id,query_kind) "
            "VALUES ('w1','gh','pull_requests')"
        )
        conn.execute(
            "INSERT INTO watch_rules (id,watch_id,ordinal) VALUES ('r1','w1',0)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO watch_rules (id,watch_id,ordinal) VALUES ('r2','w1',0)"
            )
        conn.close()

    def test_watch_evaluations_unique_constraint(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "unique-evals.db"))
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO connector_watches (id,connector_id,query_kind) "
            "VALUES ('w1','gh','pull_requests')"
        )
        conn.execute(
            "INSERT INTO watch_evaluations (id,watch_id,watch_revision,source_revision) "
            "VALUES ('e1','w1',1,'rev-a')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO watch_evaluations (id,watch_id,watch_revision,source_revision) "
                "VALUES ('e2','w1',1,'rev-a')"
            )
        conn.close()

    def test_watch_effects_idempotency_key_unique(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "unique-effects.db"))
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT INTO connector_watches (id,connector_id,query_kind) "
            "VALUES ('w1','gh','pull_requests')"
        )
        conn.execute(
            "INSERT INTO watch_rules (id,watch_id,ordinal) VALUES ('r1','w1',0)"
        )
        conn.execute(
            "INSERT INTO watch_evaluations (id,watch_id,watch_revision,source_revision) "
            "VALUES ('ev1','w1',1,'rev-a')"
        )
        conn.execute(
            "INSERT INTO watch_effects (id,evaluation_id,rule_id,idempotency_key) "
            "VALUES ('fx1','ev1','r1','key-1')"
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO watch_effects (id,evaluation_id,rule_id,idempotency_key) "
                "VALUES ('fx2','ev1','r1','key-1')"
            )
        conn.close()

    def test_project_sources_dom013_by_shape(self, tmp_path: Path) -> None:
        """DOM-013: project_sources must NOT have query, cadence, or baseline columns."""
        conn = sqlite3.connect(str(tmp_path / "dom013.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_sources")
        forbidden = {"query", "query_json", "cadence", "cadence_json",
                      "baseline", "baseline_json", "snapshot_json",
                      "refresh_interval_minutes"}
        present_forbidden = forbidden & set(cols.keys())
        assert present_forbidden == set(), (
            f"project_sources has forbidden columns: {present_forbidden}"
        )
        # Required columns are present.
        for col in ["id", "project_id", "source_ref", "label",
                     "semantic_role", "materiality_policy_json",
                     "enabled", "freshness_state", "last_observed_at",
                     "revision", "created_at", "updated_at"]:
            assert col in cols, f"project_sources missing column {col}"
        conn.close()

    def test_new_indexes_exist(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "indexes.db"))
        conn.executescript(SCHEMA_SQL)
        expected_indexes = [
            "idx_project_setup_answers_session",
            "idx_watch_setup_proposals_session",
            "idx_watch_provider_connections_provider",
            "idx_watch_rules_watch",
            "idx_watch_evaluations_watch",
            "idx_watch_effects_evaluation",
            "idx_watch_effects_idempotency",
            "idx_project_sources_project",
            "idx_project_sources_ref",
        ]
        for idx_name in expected_indexes:
            assert _index_exists(conn, idx_name), f"Index {idx_name} missing"
        conn.close()


# ── TST-002: legacy fixture reconciles with zero data loss ───────────────

class TestLegacyReconcile:
    """A pre-159 DB reconciles cleanly; backfill produces WatchSpec@1 truth."""

    def test_reconcile_adds_graduation_columns(self, tmp_path: Path) -> None:
        pre159 = _build_pre159_schema()
        db_path = tmp_path / "legacy.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre159)

        # Seed a legacy watch with attached reaction.
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,name,query_json,enabled) "
            "VALUES (?,?,?,?,?,?)",
            ("watch-legacy", "gh", "pull_requests", "Legacy GH",
             json.dumps({"repository": "acme/app", "refresh_interval_minutes": 20}),
             1),
        )
        # Need a workbench for the reaction FK.
        conn.execute(
            "INSERT INTO workbenches (id,name) VALUES ('wb-1','Test WB')"
        )
        conn.execute(
            "INSERT INTO connector_reactions "
            "(id,watch_id,event_pattern,workbench_id,enabled) "
            "VALUES (?,?,?,?,?)",
            ("reaction-1", "watch-legacy", "github.pr.*", "wb-1", 1),
        )
        conn.commit()

        # Verify pre-reconcile: graduation columns missing.
        old_cols = _get_columns(conn, "connector_watches")
        assert "schema_version" not in old_cols
        assert "trigger_kind" not in old_cols

        # Reconcile.
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        # New columns present.
        new_cols = _get_columns(conn, "connector_watches")
        assert "schema_version" in new_cols
        assert "project_id" in new_cols
        assert "trigger_kind" in new_cols
        assert "state" in new_cols

        # New tables present.
        for table in [
            "project_setup_sessions", "project_setup_answers",
            "watch_setup_proposals", "watch_provider_connections",
            "watch_rules", "watch_evaluations", "watch_effects",
            "project_sources",
        ]:
            assert _table_exists(conn, table), f"Table {table} not created"

        # Existing watch data intact.
        watch = conn.execute(
            "SELECT * FROM connector_watches WHERE id='watch-legacy'"
        ).fetchone()
        assert watch is not None
        w = dict(watch)
        assert w["id"] == "watch-legacy"
        assert w["connector_id"] == "gh"
        assert w["query_kind"] == "pull_requests"
        assert w["name"] == "Legacy GH"
        assert w["enabled"] == 1

        # query_json UNTOUCHED.
        q = json.loads(w["query_json"])
        assert q == {"repository": "acme/app", "refresh_interval_minutes": 20}

        # Backfill truth: WatchSpec@1 values.
        assert w["schema_version"] == "WatchSpec@1"
        assert w["intent"] == "Legacy automation watch"
        assert w["project_id"] is None
        assert w["trigger_kind"] == "poll"
        trigger = json.loads(w["trigger_json"])
        assert trigger == {"every_minutes": 20}
        assert w["state"] == "active"
        assert w["mode"] == "yolo"
        assert w["revision"] == 1

        # Attached reaction intact.
        reaction = conn.execute(
            "SELECT * FROM connector_reactions WHERE id='reaction-1'"
        ).fetchone()
        assert reaction is not None
        r = dict(reaction)
        assert r["watch_id"] == "watch-legacy"
        assert r["event_pattern"] == "github.pr.*"
        assert r["enabled"] == 1

        conn.close()

    def test_disabled_watch_backfills_to_paused(self, tmp_path: Path) -> None:
        pre159 = _build_pre159_schema()
        db_path = tmp_path / "disabled.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre159)
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,enabled) "
            "VALUES ('watch-off','jira','issues',0)"
        )
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        watch = conn.execute(
            "SELECT state FROM connector_watches WHERE id='watch-off'"
        ).fetchone()
        assert dict(watch)["state"] == "paused"
        conn.close()

    def test_default_cadence_backfill(self, tmp_path: Path) -> None:
        """Watch with no explicit refresh_interval_minutes gets default 35."""
        pre159 = _build_pre159_schema()
        db_path = tmp_path / "default-cad.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre159)
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,query_json) "
            "VALUES ('watch-default','gh','pull_requests',?)",
            (json.dumps({"repository": "acme/app"}),),
        )
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        watch = conn.execute(
            "SELECT trigger_json FROM connector_watches WHERE id='watch-default'"
        ).fetchone()
        trigger = json.loads(dict(watch)["trigger_json"])
        assert trigger == {"every_minutes": 35}
        conn.close()

    def test_reconcile_is_idempotent(self, tmp_path: Path) -> None:
        pre159 = _build_pre159_schema()
        db_path = tmp_path / "idem.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre159)
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,enabled) "
            "VALUES ('watch-idem','gh','pull_requests',1)"
        )
        conn.commit()

        first = reconcile_schema(conn, db_path=db_path)
        assert first is True

        # Snapshot the watch after first reconcile.
        w1 = dict(conn.execute(
            "SELECT * FROM connector_watches WHERE id='watch-idem'"
        ).fetchone())

        second = reconcile_schema(conn, db_path=db_path)
        assert second is False  # no changes on second run

        # Watch unchanged.
        w2 = dict(conn.execute(
            "SELECT * FROM connector_watches WHERE id='watch-idem'"
        ).fetchone())
        assert w1["schema_version"] == w2["schema_version"]
        assert w1["trigger_json"] == w2["trigger_json"]
        assert w1["state"] == w2["state"]
        assert w1["revision"] == w2["revision"]

        conn.close()

    def test_backfill_does_not_touch_query_json(self, tmp_path: Path) -> None:
        """query_json must remain UNTOUCHED by the backfill."""
        pre159 = _build_pre159_schema()
        db_path = tmp_path / "query-untouched.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre159)
        original_query = json.dumps({
            "repository": "acme/widget",
            "refresh_interval_minutes": 10,
            "labels": ["bug", "urgent"],
        })
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,query_json) "
            "VALUES ('watch-q','gh','pull_requests',?)",
            (original_query,),
        )
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        watch = conn.execute(
            "SELECT query_json FROM connector_watches WHERE id='watch-q'"
        ).fetchone()
        assert dict(watch)["query_json"] == original_query
        conn.close()


# ── TST-003: real-DB proof ───────────────────────────────────────────────

@pytest.mark.skipif(
    _find_real_db() is None,
    reason="Owner's real DB not found (CI or isolated HOME)",
)
class TestRealDbReconcile:
    """Copy the owner's real DB, reconcile the copy, verify zero data loss.

    Proves: existing watch IDs/row counts, attached reactions, and
    backfill truth survive the additive schema graduation.
    """

    def test_real_db_reconcile_preserves_watches_and_reactions(self, tmp_path: Path) -> None:
        real_db = _find_real_db()
        assert real_db is not None

        copy_path = tmp_path / "real_copy.db"
        shutil.copy2(str(real_db), str(copy_path))

        conn = sqlite3.connect(str(copy_path))
        conn.row_factory = sqlite3.Row

        # Snapshot BEFORE.
        before_watch_count = conn.execute(
            "SELECT COUNT(*) FROM connector_watches"
        ).fetchone()[0]
        before_watch_ids = sorted(
            r[0] for r in conn.execute("SELECT id FROM connector_watches").fetchall()
        )
        before_reaction_count = conn.execute(
            "SELECT COUNT(*) FROM connector_reactions"
        ).fetchone()[0]
        before_reaction_watch_ids = sorted(
            r[0] for r in conn.execute(
                "SELECT watch_id FROM connector_reactions WHERE watch_id IS NOT NULL"
            ).fetchall()
        )

        # Reconcile.
        reconcile_schema(conn, db_path=copy_path)

        # Snapshot AFTER.
        after_watch_count = conn.execute(
            "SELECT COUNT(*) FROM connector_watches"
        ).fetchone()[0]
        after_watch_ids = sorted(
            r[0] for r in conn.execute("SELECT id FROM connector_watches").fetchall()
        )
        after_reaction_count = conn.execute(
            "SELECT COUNT(*) FROM connector_reactions"
        ).fetchone()[0]
        after_reaction_watch_ids = sorted(
            r[0] for r in conn.execute(
                "SELECT watch_id FROM connector_reactions WHERE watch_id IS NOT NULL"
            ).fetchall()
        )

        # Row counts unchanged.
        assert after_watch_count == before_watch_count, (
            f"watch row count changed: {before_watch_count} -> {after_watch_count}"
        )
        assert after_reaction_count == before_reaction_count, (
            f"reaction row count changed: {before_reaction_count} -> {after_reaction_count}"
        )

        # IDs unchanged.
        assert after_watch_ids == before_watch_ids
        assert after_reaction_watch_ids == before_reaction_watch_ids

        # All watches graduated.
        graduated = conn.execute(
            "SELECT COUNT(*) FROM connector_watches WHERE schema_version='WatchSpec@1'"
        ).fetchone()[0]
        assert graduated == after_watch_count, (
            f"Not all watches graduated: {graduated}/{after_watch_count}"
        )

        # New columns present.
        cols = _get_columns(conn, "connector_watches")
        assert "schema_version" in cols
        assert "trigger_kind" in cols

        # New tables present.
        for table in [
            "project_setup_sessions", "watch_rules",
            "watch_evaluations", "watch_effects", "project_sources",
        ]:
            assert _table_exists(conn, table)

        # Second reconcile is a no-op.
        changed = reconcile_schema(conn, db_path=copy_path)
        assert changed is False, "second reconcile should be a no-op"

        conn.close()


# ── TST-005: backfill truth table ────────────────────────────────────────

class TestBackfillTruthTable:
    """Systematic backfill assertions per input state."""

    @pytest.fixture
    def legacy_db(self, tmp_path: Path):
        """Build a pre-159 DB with multiple watch variants and reconcile."""
        pre159 = _build_pre159_schema()
        db_path = tmp_path / "truth.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        conn.executescript(pre159)

        # Watch A: enabled, custom cadence 10.
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,query_json,enabled) "
            "VALUES ('watch-a','gh','pull_requests',?,1)",
            (json.dumps({"repository": "x/y", "refresh_interval_minutes": 10}),),
        )
        # Watch B: disabled, no explicit cadence.
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,query_json,enabled) "
            "VALUES ('watch-b','jira','issues',?,0)",
            (json.dumps({"jql": "assignee=me"}),),
        )
        # Watch C: enabled, malformed query_json.
        conn.execute(
            "INSERT INTO connector_watches "
            "(id,connector_id,query_kind,query_json,enabled) "
            "VALUES ('watch-c','gh','pull_requests','not-json',1)"
        )
        conn.commit()
        reconcile_schema(conn, db_path=db_path)
        return conn

    def test_enabled_custom_cadence(self, legacy_db) -> None:
        w = dict(legacy_db.execute(
            "SELECT * FROM connector_watches WHERE id='watch-a'"
        ).fetchone())
        assert w["schema_version"] == "WatchSpec@1"
        assert w["intent"] == "Legacy automation watch"
        assert w["project_id"] is None
        assert w["trigger_kind"] == "poll"
        assert json.loads(w["trigger_json"]) == {"every_minutes": 10}
        assert w["state"] == "active"
        assert w["mode"] == "yolo"
        assert w["revision"] == 1

    def test_disabled_default_cadence(self, legacy_db) -> None:
        w = dict(legacy_db.execute(
            "SELECT * FROM connector_watches WHERE id='watch-b'"
        ).fetchone())
        assert w["state"] == "paused"
        assert json.loads(w["trigger_json"]) == {"every_minutes": 35}

    def test_malformed_query_json(self, legacy_db) -> None:
        w = dict(legacy_db.execute(
            "SELECT * FROM connector_watches WHERE id='watch-c'"
        ).fetchone())
        assert w["schema_version"] == "WatchSpec@1"
        assert w["state"] == "active"
        assert json.loads(w["trigger_json"]) == {"every_minutes": 35}
        # query_json itself stays as-is (malformed).
        assert w["query_json"] == "not-json"
