"""Fence: no positional INSERT INTO <table> VALUES in holdspeak/.

Every INSERT must name its columns so that the reconcile engine's
column-appending strategy (ADD COLUMN at end of table) cannot cause
value/column misalignment on long-lived databases.

See: the positional-inserts-vs-reconcile-order systemic defect.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

# Tables where positional INSERT is known-safe (e.g. test-only temp tables).
# Add entries as ("filename_stem", "table_name") tuples.
ALLOW_LIST: set[tuple[str, str]] = set()

_POSITIONAL_RE = re.compile(
    r"""(?ix)
    INSERT \s+
    (?:OR \s+ [A-Z]+ \s+)?
    INTO \s+
    ([a-zA-Z_][a-zA-Z0-9_]*) \s+
    VALUES
    """,
)

_NAMED_COL_RE = re.compile(
    r"""(?ix)
    INSERT \s+
    (?:OR \s+ [A-Z]+ \s+)?
    INTO \s+
    [a-zA-Z_][a-zA-Z0-9_]* \s*
    \(                          # opening paren of column list
    """,
)


def _scan_holdspeak_source() -> list[str]:
    """Return file:line entries for every positional INSERT in holdspeak/."""
    root = Path(__file__).resolve().parents[2] / "holdspeak"
    violations: list[str] = []
    for py in sorted(root.rglob("*.py")):
        rel = py.relative_to(root.parent)
        for lineno, line in enumerate(py.read_text().splitlines(), 1):
            stripped = line.strip()
            # Skip comments and blank lines
            if stripped.startswith("#") or not stripped:
                continue
            if _POSITIONAL_RE.search(stripped):
                # It is positional -- no column list between table and VALUES.
                # But check it's not actually a named-column INSERT by looking
                # for a paren after the table name (before VALUES).
                if _NAMED_COL_RE.search(stripped):
                    continue  # has column list -- safe
                table_match = _POSITIONAL_RE.search(stripped)
                if table_match:
                    table = table_match.group(1)
                    stem = py.stem
                    if (stem, table) in ALLOW_LIST:
                        continue
                    violations.append(f"{rel}:{lineno} -> {table}")
    return violations


def test_no_positional_inserts_in_holdspeak():
    """Every INSERT in holdspeak/ must name its columns explicitly."""
    violations = _scan_holdspeak_source()
    if violations:
        msg = (
            "Positional INSERT statements found in holdspeak/ source.\n"
            "These are unsafe when the reconcile engine appends columns,\n"
            "causing column-order divergence on long-lived databases.\n\n"
            "Fix each INSERT to name its columns explicitly:\n"
            "  INSERT INTO table (col1, col2) VALUES (?, ?)\n\n"
            "Violations:\n"
        )
        for v in violations:
            msg += f"  {v}\n"
        pytest.fail(msg)


# ---------------------------------------------------------------------------
# Regression: column-order divergence on inference_assignment_migrations
# ---------------------------------------------------------------------------
# The real defect: a long-lived DB created the table without result_sha256.
# The reconcile added it at the END (after committed_at).  A positional
# INSERT wrote the sha256 into committed_at and the timestamp into
# result_sha256, breaking migration_marker integrity.  The fix: named
# columns.  This test recreates the scenario and proves the fix holds.
# ---------------------------------------------------------------------------


def test_marker_integrity_survives_reconciled_column_order(tmp_path: Path) -> None:
    """Marker INSERT works even when column order diverges from canonical."""
    import hashlib
    import json
    import re as _re
    import sqlite3

    from holdspeak.db.schema import SCHEMA_SQL
    from holdspeak.db.reconcile import reconcile_schema

    # Step 1: Build an "old" DDL that lacks result_sha256.
    # Replace the canonical definition with one missing result_sha256.
    old_table = (
        "CREATE TABLE IF NOT EXISTS inference_assignment_migrations (\n"
        "    family TEXT PRIMARY KEY,\n"
        "    marker_revision INTEGER NOT NULL,\n"
        "    source_sha256 TEXT NOT NULL,\n"
        "    result_json TEXT NOT NULL,\n"
        "    committed_at TEXT NOT NULL\n"
        ");"
    )
    old_schema = _re.sub(
        r"CREATE TABLE IF NOT EXISTS inference_assignment_migrations\s*\(.*?\);",
        old_table,
        SCHEMA_SQL,
        count=1,
        flags=_re.DOTALL,
    )
    assert "result_sha256" not in old_schema.split("inference_assignment_migrations")[1].split(";")[0], \
        "old_schema should not have result_sha256 in inference_assignment_migrations"

    db_path = tmp_path / "old-marker.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(old_schema)
        conn.commit()

        # Verify the old column order: family, marker_revision, source_sha256, result_json, committed_at
        cols_before = [
            row[1] for row in conn.execute("PRAGMA table_info(inference_assignment_migrations)").fetchall()
        ]
        assert cols_before == [
            "family", "marker_revision", "source_sha256", "result_json", "committed_at"
        ]

        # Step 2: Reconcile -- adds result_sha256 at the END
        changed = reconcile_schema(conn, db_path=db_path)
        assert changed is True

        cols_after = [
            row[1] for row in conn.execute("PRAGMA table_info(inference_assignment_migrations)").fetchall()
        ]
        # result_sha256 should now exist but be LAST (not in canonical position)
        assert "result_sha256" in cols_after
        assert cols_after[-1] == "result_sha256", (
            f"reconcile should append result_sha256 at end, got: {cols_after}"
        )
        # Column order now diverges from canonical
        assert cols_after != [
            "family", "marker_revision", "source_sha256", "result_json", "result_sha256", "committed_at"
        ]

        # Step 3: Insert a marker row using the FIXED named-column INSERT
        # (mirroring what the service does)
        def _canonical(value):
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

        def _sha(value):
            return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()

        result = {
            "schema": "InferenceAssignmentMigrationMarker@1",
            "family": "test-family",
            "marker_revision": 1,
            "source_sha256": "sha256:" + "a" * 64,
            "assignments": [],
        }
        committed_at = "2026-08-30T12:00:00.000000Z"

        conn.execute(
            "INSERT INTO inference_assignment_migrations "
            "(family, marker_revision, source_sha256, result_json, result_sha256, committed_at) "
            "VALUES (?,?,?,?,?,?)",
            ("test-family", 1, "sha256:" + "a" * 64, _canonical(result), _sha(result), committed_at),
        )
        conn.commit()

        # Step 4: Read it back and verify integrity (like migration_marker does)
        row = conn.execute(
            "SELECT * FROM inference_assignment_migrations WHERE family=?",
            ("test-family",),
        ).fetchone()
        assert row is not None

        stored_result = json.loads(str(row["result_json"]))
        stored_sha = str(row["result_sha256"])
        stored_committed = str(row["committed_at"])

        # The sha should match the result_json, NOT be a timestamp
        assert stored_sha == _sha(stored_result), (
            f"Integrity violation: result_sha256={stored_sha!r}, "
            f"expected={_sha(stored_result)!r}, "
            f"committed_at={stored_committed!r}"
        )
        # committed_at should be a timestamp, not a sha
        assert stored_committed == committed_at, (
            f"committed_at should be the timestamp, got: {stored_committed!r}"
        )
        assert stored_sha.startswith("sha256:"), (
            f"result_sha256 should start with 'sha256:', got: {stored_sha!r}"
        )
    finally:
        conn.close()


def test_positional_insert_would_corrupt_on_divergent_order(tmp_path: Path) -> None:
    """Prove that a POSITIONAL insert on a reconciled table writes wrong values.

    This is the negative test: without named columns, the sha goes into
    committed_at and the timestamp goes into result_sha256.
    """
    import hashlib
    import json
    import re as _re
    import sqlite3

    from holdspeak.db.schema import SCHEMA_SQL
    from holdspeak.db.reconcile import reconcile_schema

    old_table = (
        "CREATE TABLE IF NOT EXISTS inference_assignment_migrations (\n"
        "    family TEXT PRIMARY KEY,\n"
        "    marker_revision INTEGER NOT NULL,\n"
        "    source_sha256 TEXT NOT NULL,\n"
        "    result_json TEXT NOT NULL,\n"
        "    committed_at TEXT NOT NULL\n"
        ");"
    )
    old_schema = _re.sub(
        r"CREATE TABLE IF NOT EXISTS inference_assignment_migrations\s*\(.*?\);",
        old_table,
        SCHEMA_SQL,
        count=1,
        flags=_re.DOTALL,
    )

    db_path = tmp_path / "positional-corrupt.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(old_schema)
        conn.commit()
        reconcile_schema(conn, db_path=db_path)

        def _canonical(value):
            return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)

        def _sha(value):
            return "sha256:" + hashlib.sha256(_canonical(value).encode()).hexdigest()

        result = {
            "schema": "InferenceAssignmentMigrationMarker@1",
            "family": "corrupt-test",
            "marker_revision": 1,
            "source_sha256": "sha256:" + "b" * 64,
            "assignments": [],
        }
        committed_at = "2026-08-30T12:00:00.000000Z"
        result_sha = _sha(result)

        # Positional INSERT (the broken way) -- values go in canonical order:
        # family, marker_revision, source_sha256, result_json, result_sha256, committed_at
        # But the table's column order after reconcile is:
        # family, marker_revision, source_sha256, result_json, committed_at, result_sha256
        # So position 5 (result_sha256) goes into committed_at, and position 6
        # (committed_at) goes into result_sha256.
        conn.execute(
            "INSERT INTO inference_assignment_migrations VALUES (?,?,?,?,?,?)",
            ("corrupt-test", 1, "sha256:" + "b" * 64, _canonical(result), result_sha, committed_at),
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM inference_assignment_migrations WHERE family=?",
            ("corrupt-test",),
        ).fetchone()

        # The corruption: result_sha256 column has the timestamp, committed_at has the sha
        assert str(row["result_sha256"]) == committed_at, (
            "Without named columns, the timestamp leaks into result_sha256"
        )
        assert str(row["committed_at"]) == result_sha, (
            "Without named columns, the sha leaks into committed_at"
        )

        # And integrity verification fails
        stored_result = json.loads(str(row["result_json"]))
        assert str(row["result_sha256"]) != _sha(stored_result), (
            "Integrity check should fail on the corrupted row"
        )
    finally:
        conn.close()
