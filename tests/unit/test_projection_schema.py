"""HS-131-03: v45 databases gain receipt-gated projection storage."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database
from holdspeak.db.core import read_schema_version


def test_v45_upgrades_to_projection_stage_schema(tmp_path: Path) -> None:
    path = tmp_path / "v45-projection.db"
    database = Database(path)
    with database._connection() as conn:
        conn.executescript("""
            DROP TABLE ask_results;
            DROP INDEX idx_kernel_projection_stages_recovery;
            DROP TABLE kernel_projection_stages;
            DELETE FROM schema_version;
            INSERT INTO schema_version(version) VALUES (45);
        """)
    Database(path)
    with Database(path)._connection() as conn:
        stages = {row[1] for row in conn.execute("PRAGMA table_info(kernel_projection_stages)")}
        ask = {row[1] for row in conn.execute("PRAGMA table_info(ask_results)")}
    assert read_schema_version(path) == 46
    assert {"stage_id", "invocation_id", "operation_id", "result_ref", "state", "final_result_json"} <= stages
    assert {"projection_stage_id", "invocation_id", "operation_id", "receipt_id", "payload_json"} <= ask
