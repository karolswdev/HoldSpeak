"""HS-125-03 schema migration coverage for decision commitments."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db.core import Database, reset_database
from holdspeak.db.schema import SCHEMA_VERSION


def test_migrates_v38_database_to_decision_commitments(tmp_path: Path) -> None:
    path = tmp_path / "v38.db"
    reset_database()
    database = Database(path)
    with database._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at) VALUES (?, ?)",
            ("existing-meeting", "2026-08-01T09:00:00"),
        )
        conn.executescript(
            """
            DROP TABLE decision_commitments;
            DELETE FROM schema_version;
            INSERT INTO schema_version(version) VALUES (38);
            """
        )

    reset_database()
    migrated = Database(path)
    with migrated._connection() as conn:
        columns = {
            row[1] for row in conn.execute("PRAGMA table_info(decision_commitments)")
        }
        meeting = conn.execute(
            "SELECT id FROM meetings WHERE id = 'existing-meeting'"
        ).fetchone()
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]

    assert {"id", "decision_id", "action_item_id", "owner", "due_at", "status"} <= columns
    assert meeting is not None
    assert version == SCHEMA_VERSION == 56
    reset_database()
