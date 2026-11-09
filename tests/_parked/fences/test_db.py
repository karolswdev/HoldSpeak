# PARKED 2026-11-09 (fences diet, pipe/fences-diet): a committed SNAPSHOT of the whole schema, re-recorded by hand on every schema change.
# Replaced by: the schema's own migration and reconcile tests, and test_static_sql_matches_schema.py (every static statement prepares).
"""Parked from tests/unit/test_db.py (TestDatabaseShape)."""
from pathlib import Path

import pytest


class TestDatabaseShape:
    @pytest.mark.real_schema  # a fresh build, never the template copy
    def test_fresh_schema_matches_canonical_snapshot(self, tmp_path, project_root: Path):
        """HS-31-04: the migration ladder was squashed to one canonical schema.
        A fresh build must match the committed snapshot exactly — any intended
        schema change must update tests/fixtures/db_schema_canonical.txt in the
        same commit, keeping the schema honest without a version ladder."""
        import re
        import sqlite3
        from holdspeak.db import Database

        Database(tmp_path / "schema_check.db")
        conn = sqlite3.connect(str(tmp_path / "schema_check.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        actual = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows
        ) + "\n"
        conn.close()

        snapshot = project_root / "tests" / "_parked" / "fences" / "fixtures" / "db_schema_canonical.txt"
        expected = snapshot.read_text()
        assert actual == expected, (
            "Fresh DB schema diverged from the canonical snapshot. If this change is "
            f"intended, regenerate {snapshot.relative_to(project_root)}."
        )


