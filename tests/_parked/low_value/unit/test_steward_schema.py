# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_steward_schema.py to restore.

# ruff: noqa


# --- TestFreshSchema: P3/P1: asserts tables, columns, foreign keys, indexes and column defaults exist in SQLite; the behaviour tests cover them
class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has the HS-163-01 shape."""

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


# --- TestRunLifecycle::test_insert_run_defaults: P3/P1: asserts tables, columns, foreign keys, indexes and column defaults exist in SQLite; the behaviour tests cover them
# (was a method of class TestRunLifecycle)
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
