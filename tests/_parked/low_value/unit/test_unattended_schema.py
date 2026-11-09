# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_unattended_schema.py to restore.

# ruff: noqa


# --- TestFreshSchema: P3: asserts column types, NOT NULL and default text in SQLite pragma, and a schema version floor; the opt-in, circuit and cadence tests cover the behaviour
class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has the HS-164-01 columns."""

    def test_schema_version_is_at_least_the_phase_floor(self) -> None:
        """SCHEMA_VERSION is informational and additive-only (HS-137): this
        phase was built at 73; later additive phases bump it (74 the
        calendar_event_projects join, 75 calendar_event_link_suppressions).
        The honest assertion is the floor, read from the real constant."""
        assert SCHEMA_VERSION >= 73

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
