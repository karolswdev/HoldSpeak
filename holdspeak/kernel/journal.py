"""Durable operation metadata and its per-stream SHA-256 chain."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
import threading
from typing import Any, Mapping

from .journal_txn import append_record, json_encode as _json, record_hash as _hash
from .model import KernelRefused

# Receipt readers must see the executing scheduler separately from the owner
# who delegated it; every receipt read path returns this same joined shape.
_RECEIPT_SQL = (
    "SELECT r.*, o.principal_kind AS actor_kind, o.principal_identity AS actor_identity,"
    " o.delegator_kind, o.delegator_identity, o.authority_basis, o.target_ref"
    " FROM kernel_receipts r JOIN kernel_operations o ON o.operation_id=r.operation_id"
    " WHERE r.operation_id=?"
)


class JournalStore:
    def __init__(self, connection: Any, *, clock: Any = time.time) -> None:
        self._connection = connection
        self._clock = clock
        self._append_lock = threading.Lock()
    def _secret(self) -> str:
        """Read the warrant secret, minting it exactly once per database.

        Two callers can reach a fresh database at the same moment (a route thread
        and a background worker both building the broker). The mint is therefore
        idempotent and the value is re-read afterwards, so the loser of the race
        adopts the winner's secret instead of raising on the UNIQUE constraint or
        returning a secret the database does not hold.
        """
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM kernel_meta WHERE key='warrant_secret'").fetchone()
            if row is not None:
                return str(row[0])
            conn.execute(
                "INSERT OR IGNORE INTO kernel_meta(key,value) VALUES('warrant_secret',?)",
                (secrets.token_hex(32),),
            )
            stored = conn.execute(
                "SELECT value FROM kernel_meta WHERE key='warrant_secret'"
            ).fetchone()
            return str(stored[0])

    def append(
        self, event_type: str, operation_id: str, *, refs: tuple[str, ...] = (),
        head: str = "", privacy_class: str = "private", stream: str = "operations",
        process_id: str = "", correlation_id: str = "", causation_id: str = "",
    ) -> dict[str, Any]:
        return append_record(
            self._connection, self._append_lock, self._clock, event_type, operation_id,
            refs=refs, head=head, privacy_class=privacy_class, stream=stream,
            process_id=process_id, correlation_id=correlation_id, causation_id=causation_id,
        )

    def verify(self, stream: str = "operations") -> dict[str, Any]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM kernel_journal WHERE stream=? ORDER BY stream_sequence", (stream,)
            ).fetchall()
        previous = "sha256:genesis"
        for row in rows:
            record = self._event(row)
            if record["previous_sha256"] != previous:
                raise KernelRefused("journal_previous_hash_mismatch")
            if record["record_sha256"] != _hash(record):
                raise KernelRefused("journal_record_hash_mismatch")
            previous = record["record_sha256"]
        return {"ok": True, "stream": stream, "records": len(rows), "head": previous}

    def events(self, after_cursor: int, filters: Mapping[str, Any], limit: int = 100) -> dict[str, Any]:
        clauses, values = ["hub_sequence > ?"], [max(0, int(after_cursor))]
        allowed = {"operation_id", "event_type", "privacy_class", "stream"}
        unknown = set(filters) - allowed
        if unknown:
            raise KernelRefused("event_filter_not_allowed", sorted(unknown)[0])
        for key, value in filters.items():
            clauses.append(f"{key} = ?")
            values.append(str(value))
        values.append(max(1, min(int(limit), 500)))
        with self._connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM kernel_journal WHERE {' AND '.join(clauses)} ORDER BY hub_sequence LIMIT ?",
                values,
            ).fetchall()
        batch = [self._event(row) for row in rows]
        cursor = batch[-1]["cursor"] if batch else max(0, int(after_cursor))
        return {"after_cursor": after_cursor, "cursor": cursor, "events": batch}
    def last_receipt_for_ref(self, ref: str) -> str | None:
        """Return the latest journal receipt time for an admitted effect ref."""
        with self._connection() as conn:
            admitted = conn.execute(
                "SELECT operation_id,refs_json FROM kernel_journal "
                "WHERE event_type='operation.admitted' ORDER BY hub_sequence DESC"
            ).fetchall()
            operation_ids = [
                str(row["operation_id"])
                for row in admitted
                if str(ref) in json.loads(row["refs_json"])
            ]
            for operation_id in operation_ids:
                receipt = conn.execute(
                    "SELECT timestamp FROM kernel_journal "
                    "WHERE operation_id=? AND event_type='operation.receipt' "
                    "ORDER BY hub_sequence DESC LIMIT 1",
                    (operation_id,),
                ).fetchone()
                if receipt is not None:
                    return str(receipt["timestamp"])
        return None

    def create_operation(self, values: Mapping[str, Any]) -> dict[str, Any]:
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT * FROM kernel_operations WHERE principal_identity=? AND idempotency_key=?",
                (values["principal_identity"], values["idempotency_key"]),
            ).fetchone()
            if existing is not None:
                if str(existing["envelope_sha256"]) != values["envelope_sha256"]:
                    raise KernelRefused("idempotency_payload_mismatch", operation_id=str(existing["operation_id"]))
                return self._operation(existing)
            conn.execute(
                """INSERT INTO kernel_operations(
                    operation_id,request_id,idempotency_key,name,version,principal_kind,
                    principal_identity,target_ref,placement,envelope_sha256,policy_version,
                    authority_basis,state,revision,native_id,parent_operation_id,
                    correlation_id,delegator_kind,delegator_identity,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    values["operation_id"], values["request_id"], values["idempotency_key"],
                    values["name"], values["version"], values["principal_kind"],
                    values["principal_identity"], values["target_ref"], values["placement"],
                    values["envelope_sha256"], values["policy_version"],
                    values["authority_basis"], values["state"], 1, values["native_id"],
                    values.get("parent_operation_id", ""), values.get("correlation_id", ""),
                    values.get("delegator_kind", ""), values.get("delegator_identity", ""),
                    self._clock(), self._clock(),
                ),
            )
        return self.operation(str(values["operation_id"]))
    def operation(self, operation_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM kernel_operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
        return self._operation(row) if row is not None else None
    def operation_for_ref(self, ref: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM kernel_operations WHERE target_ref=? ORDER BY created_at DESC LIMIT 1", (ref,)
            ).fetchone()
        return self._operation(row) if row is not None else None
    def operation_for_native(self, native_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM kernel_operations WHERE native_id=? ORDER BY created_at DESC LIMIT 1", (native_id,)
            ).fetchone()
        return self._operation(row) if row is not None else None
    def operations_in_state(self, state: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM kernel_operations WHERE state=? ORDER BY created_at", (state,)
            ).fetchall()
        return [self._operation(row) for row in rows]

    def transition(self, operation_id: str, expected_revision: int, state: str, **changes: Any) -> dict[str, Any]:
        assignments = ["state=?", "revision=revision+1", "updated_at=?"]
        values: list[Any] = [state, self._clock()]
        allowed = {"decision", "warrant_json", "warrant_revoked", "claimed_by"}
        for key, value in changes.items():
            if key not in allowed:
                raise KernelRefused("operation_mutation_not_allowed", key)
            assignments.append(f"{key}=?")
            values.append(_json(value) if key == "warrant_json" else value)
        values.extend((operation_id, expected_revision))
        with self._connection() as conn:
            result = conn.execute(
                f"UPDATE kernel_operations SET {','.join(assignments)} WHERE operation_id=? AND revision=?",
                values,
            )
            if result.rowcount != 1:
                raise KernelRefused("operation_revision_conflict", operation_id=operation_id)
        return self.operation(operation_id) or {}
    def claim_candidate(
        self, executor: str, native_id: str = ""
    ) -> dict[str, Any] | None:
        """Atomically acquire one approved operation; first claimant wins."""
        query = """SELECT operation_id,revision FROM kernel_operations
                   WHERE state='awaiting_execution' AND placement=?"""
        values: tuple[Any, ...] = (f"node:{executor}",)
        if native_id:
            query += " AND native_id=?"
            values += (native_id,)
        query += " ORDER BY created_at LIMIT 1"
        with self._connection() as conn:
            row = conn.execute(query, values).fetchone()
            if row is None:
                return None
            result = conn.execute(
                """UPDATE kernel_operations SET state='claimed',claimed_by=?,revision=revision+1,updated_at=?
                   WHERE operation_id=? AND revision=? AND state='awaiting_execution'""",
                (executor, self._clock(), row["operation_id"], row["revision"]),
            )
            if result.rowcount != 1:
                return None
        return self.operation(str(row["operation_id"]))
    def revoke_warrant(self, operation_id: str) -> dict[str, Any]:
        with self._connection() as conn:
            conn.execute(
                "UPDATE kernel_operations SET warrant_revoked=1,revision=revision+1,updated_at=? WHERE operation_id=?",
                (self._clock(), operation_id),
            )
        return self.operation(operation_id) or {}

    def transition_and_receipt(
        self, operation_id: str, expected_revision: int, state: str, outcome: str,
        result_ref: str = "",
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Durably couple a claimed operation's terminal state and receipt."""
        receipt_id = "rcpt_" + uuid.uuid4().hex
        with self._connection() as conn:
            existing = conn.execute(_RECEIPT_SQL, (operation_id,)).fetchone()
            if existing is not None:
                return self._operation(conn.execute(
                    "SELECT * FROM kernel_operations WHERE operation_id=?", (operation_id,)
                ).fetchone()), dict(existing)
            result = conn.execute(
                "UPDATE kernel_operations SET state=?,revision=revision+1,updated_at=? "
                "WHERE operation_id=? AND revision=?",
                (state, self._clock(), operation_id, expected_revision),
            )
            if result.rowcount != 1:
                raise KernelRefused("operation_revision_conflict", operation_id=operation_id)
            conn.execute(
                "INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)",
                (receipt_id, operation_id, state, outcome, result_ref, self._clock()),
            )
            operation = conn.execute(
                "SELECT * FROM kernel_operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            receipt = conn.execute(_RECEIPT_SQL, (operation_id,)).fetchone()
        return self._operation(operation), dict(receipt)

    def add_receipt(self, operation_id: str, state: str, outcome: str, result_ref: str = "") -> dict[str, Any]:
        receipt_id = "rcpt_" + uuid.uuid4().hex
        with self._connection() as conn:
            existing = conn.execute(_RECEIPT_SQL, (operation_id,)).fetchone()
            if existing is not None:
                return dict(existing)
            conn.execute(
                "INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)",
                (receipt_id, operation_id, state, outcome, result_ref, self._clock()),
            )
        return self.receipt(operation_id) or {}
    def receipt(self, operation_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(_RECEIPT_SQL, (operation_id,)).fetchone()
        return dict(row) if row is not None else None
    def sign_warrant(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        warrant = dict(payload)
        warrant["signature"] = hmac.new(
            self._secret().encode(), _json(warrant).encode(), hashlib.sha256
        ).hexdigest()
        return warrant
    def valid_warrant(self, warrant: Mapping[str, Any]) -> bool:
        unsigned = {key: value for key, value in warrant.items() if key != "signature"}
        expected = hmac.new(self._secret().encode(), _json(unsigned).encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(str(warrant.get("signature") or ""), expected)

    @staticmethod
    def _operation(row: Any) -> dict[str, Any]:
        value = dict(row)
        value["warrant"] = json.loads(value.pop("warrant_json") or "{}")
        return value

    @staticmethod
    def _event(row: Any) -> dict[str, Any]:
        value = dict(row)
        value["cursor"] = value.pop("hub_sequence")
        value["refs"] = json.loads(value.pop("refs_json"))
        return value
