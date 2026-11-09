# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_watch_graduation_schema.py to restore.

# ruff: noqa


# --- TestFreshSchema: P3/P8: asserts columns, tables, indexes and SQLite UNIQUE constraints exist, and a forbidden-columns rule; the reconcile and backfill tests cover the behaviour
class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has every HS-159-01 shape."""

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
