# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_delta_schema.py to restore.

# ruff: noqa


# --- TestFreshSchema: P3: table, column, default, foreign key and index exist in the schema SQL; SQLite behaviour, no user outcome
class TestFreshSchema:
    """A fresh DB built from SCHEMA_SQL has every HS-160-01 shape."""

    def test_schema_version_is_at_least_the_phase_floor(self) -> None:
        """SCHEMA_VERSION is informational and additive-only (HS-137): this
        phase was built at 73; later additive phases bump it (74 the
        calendar_event_projects join, 75 calendar_event_link_suppressions).
        The honest assertion is the floor, read from the real constant."""
        assert SCHEMA_VERSION >= 73

    # -- project_observations (SS5.5) --

    def test_observations_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_observations")
        conn.close()

    def test_observations_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_observations")
        expected = [
            "id", "project_id", "source_id", "observation_kind",
            "subject_ref", "source_version", "observed_at", "captured_at",
            "fact_json", "content_hash", "supersedes_observation_id",
            "coverage_state",
        ]
        for col in expected:
            assert col in cols, f"project_observations missing column {col}"
        conn.close()

    def test_observations_defaults(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_observations")
        assert cols["source_id"]["notnull"] == 1
        assert cols["source_id"]["dflt_value"] == "''"
        assert cols["fact_json"]["dflt_value"] == "'{}'"
        assert cols["content_hash"]["dflt_value"] == "''"
        assert cols["coverage_state"]["dflt_value"] == "''"
        conn.close()

    def test_observations_fk_to_projects(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "projects" in _fk_tables(conn, "project_observations")
        assert _fk_on_delete(conn, "project_observations")["projects"] == "CASCADE"
        conn.close()

    def test_observations_index(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _index_exists(conn, "idx_project_observations_source")
        conn.close()

    # -- project_evidence_links (SS5.6) --

    def test_evidence_links_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_evidence_links")
        conn.close()

    def test_evidence_links_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_evidence_links")
        expected = [
            "id", "project_id", "target_ref", "evidence_ref",
            "relation", "observation_id", "excerpt_locator_json",
            "created_at",
        ]
        for col in expected:
            assert col in cols, f"project_evidence_links missing column {col}"
        conn.close()

    def test_evidence_links_fk_cascade(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "projects" in _fk_tables(conn, "project_evidence_links")
        assert _fk_on_delete(conn, "project_evidence_links")["projects"] == "CASCADE"
        conn.close()

    def test_evidence_links_index(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _index_exists(conn, "idx_project_evidence_links_target")
        conn.close()

    # -- project_proposals (SS5.7) --

    def test_proposals_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_proposals")
        conn.close()

    def test_proposals_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_proposals")
        expected = [
            "id", "project_id", "review_window_key", "proposal_kind",
            "target_ref", "title", "rationale", "patch_json",
            "materiality", "confidence", "producer_kind",
            "model_receipt_ref", "lifecycle", "deferred_until",
            "dismissal_basis_hash", "created_at", "decided_at",
            "decided_by_ref",
        ]
        for col in expected:
            assert col in cols, f"project_proposals missing column {col}"
        conn.close()

    def test_proposals_defaults(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_proposals")
        assert cols["lifecycle"]["dflt_value"] == "'open'"
        assert cols["patch_json"]["dflt_value"] == "'{}'"
        assert cols["review_window_key"]["dflt_value"] == "''"
        conn.close()

    def test_proposals_fk_cascade(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "projects" in _fk_tables(conn, "project_proposals")
        assert _fk_on_delete(conn, "project_proposals")["projects"] == "CASCADE"
        conn.close()

    def test_proposals_index(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _index_exists(conn, "idx_project_proposals_window")
        conn.close()

    # -- project_reviews (SS5.8) --

    def test_reviews_table_exists(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _table_exists(conn, "project_reviews")
        conn.close()

    def test_reviews_columns(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_reviews")
        expected = [
            "id", "project_id", "status", "from_sequence",
            "through_sequence", "source_manifest_json",
            "project_revision_opened", "project_revision_accepted",
            "opened_at", "accepted_at", "accepted_by_ref", "summary_json",
        ]
        for col in expected:
            assert col in cols, f"project_reviews missing column {col}"
        conn.close()

    def test_reviews_defaults(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        cols = _get_columns(conn, "project_reviews")
        assert cols["status"]["dflt_value"] == "'open'"
        assert cols["source_manifest_json"]["dflt_value"] == "'{}'"
        conn.close()

    def test_reviews_fk_cascade(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert "projects" in _fk_tables(conn, "project_reviews")
        assert _fk_on_delete(conn, "project_reviews")["projects"] == "CASCADE"
        conn.close()

    def test_reviews_index(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "fresh.db"))
        conn.executescript(SCHEMA_SQL)
        assert _index_exists(conn, "idx_project_reviews_status")
        conn.close()


# --- TestProposalLifecycle: P3: writes a row with raw SQL and reads the same literal back; tests SQLite
class TestProposalLifecycle:
    """Every SS5.7 lifecycle value can be stored and retrieved."""

    LIFECYCLES = ["open", "accepted", "deferred", "dismissed", "superseded", "failed"]

    def test_all_lifecycle_values_storable(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "prop-lc.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        for i, lc in enumerate(self.LIFECYCLES):
            pid = f"pprop_{'0' * 27}{i:05d}"
            conn.execute(
                "INSERT INTO project_proposals "
                "(id, project_id, lifecycle) VALUES (?, ?, ?)",
                (pid, "proj-1", lc),
            )

        rows = conn.execute(
            "SELECT lifecycle FROM project_proposals ORDER BY id"
        ).fetchall()
        stored = [dict(r)["lifecycle"] for r in rows]
        assert stored == self.LIFECYCLES

        conn.close()

    def test_proposal_dismissal_basis_hash_storable(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "prop-dbh.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        conn.execute(
            "INSERT INTO project_proposals "
            "(id, project_id, lifecycle, dismissal_basis_hash) "
            "VALUES (?, ?, ?, ?)",
            ("pprop_" + "a" * 32, "proj-1", "dismissed", "sha256:abc123"),
        )
        row = conn.execute(
            "SELECT dismissal_basis_hash FROM project_proposals "
            "WHERE id = ?", ("pprop_" + "a" * 32,)
        ).fetchone()
        assert dict(row)["dismissal_basis_hash"] == "sha256:abc123"

        conn.close()

    def test_proposal_deferred_until_storable(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "prop-def.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        conn.execute(
            "INSERT INTO project_proposals "
            "(id, project_id, lifecycle, deferred_until) "
            "VALUES (?, ?, ?, ?)",
            ("pprop_" + "b" * 32, "proj-1", "deferred", "2025-09-01T00:00:00"),
        )
        row = conn.execute(
            "SELECT deferred_until FROM project_proposals "
            "WHERE id = ?", ("pprop_" + "b" * 32,)
        ).fetchone()
        assert dict(row)["deferred_until"] == "2025-09-01T00:00:00"

        conn.close()


# --- TestReviewShape: P3: writes a row with raw SQL and reads the same literal back; tests SQLite
class TestReviewShape:
    """Every SS5.8 column present and usable."""

    def test_review_round_trip(self, tmp_path: Path) -> None:
        conn = sqlite3.connect(str(tmp_path / "rev-rt.db"))
        conn.row_factory = sqlite3.Row
        conn.executescript(SCHEMA_SQL)
        _seed_project(conn)

        conn.execute(
            "INSERT INTO project_reviews "
            "(id, project_id, status, from_sequence, through_sequence, "
            "source_manifest_json, project_revision_opened, "
            "project_revision_accepted, opened_at, accepted_at, "
            "accepted_by_ref, summary_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "prev_" + "c" * 32, "proj-1", "accepted", 1, 5,
                '{"github":{"cursor":"sha-99"}}', 3, 7,
                "2025-08-01T00:00:00", "2025-08-01T01:00:00",
                "person:owner", '{"items_accepted":3}',
            ),
        )

        row = conn.execute(
            "SELECT * FROM project_reviews WHERE id = ?",
            ("prev_" + "c" * 32,),
        ).fetchone()
        d = dict(row)
        assert d["status"] == "accepted"
        assert d["from_sequence"] == 1
        assert d["through_sequence"] == 5
        assert d["project_revision_opened"] == 3
        assert d["project_revision_accepted"] == 7
        assert d["accepted_by_ref"] == "person:owner"

        conn.close()
