"""HS-131-02: v44 kernel evidence survives the cancelled-state upgrade."""
from __future__ import annotations

from pathlib import Path

from holdspeak.db import Database


def test_v44_kernel_rows_upgrade_byte_for_byte_and_accept_cancelled(tmp_path: Path) -> None:
    path = tmp_path / "v44-kernel.db"
    database = Database(path)
    operation = (
        "op-v44", "request-v44", "key-v44", "inference.invoke", 1, "owner", "owner",
        "invocation:one", "node:one", "sha256:" + "a" * 64, "policy", "basis", "succeeded",
        7, "invoke-one", "", "op-v44", "approve", "{}", 0, "node-one", 1.0, 2.0,
    )
    receipt = ("receipt-v44", "op-v44", "succeeded", "succeeded", "result:one", 3.0)
    with database._connection() as conn:
        conn.execute(
            "INSERT INTO kernel_operations(operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,decision,warrant_json,warrant_revoked,claimed_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", operation
        )
        conn.execute("INSERT INTO kernel_receipts VALUES(?,?,?,?,?,?)", receipt)
        # Recreate the actual v44 constraints, rather than faking only its version pin.
        conn.executescript(
            """
            PRAGMA foreign_keys = OFF;
            DROP INDEX idx_kernel_operations_state;
            CREATE TABLE kernel_operations_v44 AS SELECT operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,decision,warrant_json,warrant_revoked,claimed_by,created_at,updated_at FROM kernel_operations;
            DROP TABLE kernel_operations;
            CREATE TABLE kernel_operations (
                operation_id TEXT PRIMARY KEY, request_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
                name TEXT NOT NULL, version INTEGER NOT NULL, principal_kind TEXT NOT NULL,
                principal_identity TEXT NOT NULL, target_ref TEXT NOT NULL, placement TEXT NOT NULL,
                envelope_sha256 TEXT NOT NULL, policy_version TEXT NOT NULL, authority_basis TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('admitting','awaiting_decision','awaiting_execution','claimed','succeeded','failed','refused','indeterminate')),
                revision INTEGER NOT NULL DEFAULT 1, native_id TEXT NOT NULL,
                parent_operation_id TEXT NOT NULL DEFAULT '', correlation_id TEXT NOT NULL DEFAULT '', decision TEXT,
                warrant_json TEXT NOT NULL DEFAULT '{}', warrant_revoked INTEGER NOT NULL DEFAULT 0,
                claimed_by TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL,
                UNIQUE(principal_identity,idempotency_key)
            );
            INSERT INTO kernel_operations SELECT * FROM kernel_operations_v44;
            DROP TABLE kernel_operations_v44;
            CREATE INDEX idx_kernel_operations_state ON kernel_operations(state, created_at);
            CREATE TABLE kernel_receipts_v44 AS SELECT * FROM kernel_receipts;
            DROP TABLE kernel_receipts;
            CREATE TABLE kernel_receipts (
                receipt_id TEXT PRIMARY KEY, operation_id TEXT NOT NULL UNIQUE REFERENCES kernel_operations(operation_id),
                state TEXT NOT NULL CHECK(state IN ('succeeded','failed','refused','indeterminate')),
                outcome TEXT NOT NULL, result_ref TEXT NOT NULL DEFAULT '', created_at REAL NOT NULL
            );
            INSERT INTO kernel_receipts SELECT * FROM kernel_receipts_v44;
            DROP TABLE kernel_receipts_v44;
            DELETE FROM schema_version;
            INSERT INTO schema_version(version) VALUES (44);
            PRAGMA foreign_keys = ON;
            """
        )

    upgraded = Database(path)
    with upgraded._connection() as conn:
        carried_operation = tuple(conn.execute("SELECT operation_id,request_id,idempotency_key,name,version,principal_kind,principal_identity,target_ref,placement,envelope_sha256,policy_version,authority_basis,state,revision,native_id,parent_operation_id,correlation_id,decision,warrant_json,warrant_revoked,claimed_by,created_at,updated_at FROM kernel_operations WHERE operation_id='op-v44'").fetchone())
        carried_receipt = tuple(conn.execute("SELECT * FROM kernel_receipts WHERE operation_id='op-v44'").fetchone())
        conn.execute("UPDATE kernel_operations SET state='cancelled' WHERE operation_id='op-v44'")
        conn.execute("UPDATE kernel_receipts SET state='cancelled', outcome='cancelled' WHERE operation_id='op-v44'")
        indexes = {row[1] for row in conn.execute("PRAGMA index_list(kernel_operations)")}
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()

    assert carried_operation == operation
    assert carried_receipt == receipt
    assert "idx_kernel_operations_state" in indexes
    assert version == 53
    assert foreign_keys == []
