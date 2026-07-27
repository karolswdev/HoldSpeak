"""Durable operation metadata and its per-stream SHA-256 chain."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from typing import Any, Mapping

from .model import KernelRefused, forbidden_content

_HEAD_LIMIT = 120
_EVENT_FIELDS = (
    "stream", "stream_sequence", "event_id", "operation_id", "process_id",
    "correlation_id", "causation_id", "event_type", "event_version", "refs",
    "privacy_class", "head", "timestamp", "previous_sha256",
)


def _json(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _hash(record: Mapping[str, Any]) -> str:
    material = {field: record[field] for field in _EVENT_FIELDS}
    return "sha256:" + hashlib.sha256(_json(material).encode()).hexdigest()


class JournalStore:
    def __init__(self, connection: Any, *, clock: Any = time.time) -> None:
        self._connection = connection
        self._clock = clock

    def _secret(self) -> str:
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM kernel_meta WHERE key='warrant_secret'").fetchone()
            if row is not None:
                return str(row[0])
            value = secrets.token_hex(32)
            conn.execute("INSERT INTO kernel_meta(key,value) VALUES('warrant_secret',?)", (value,))
            return value

    def append(
        self, event_type: str, operation_id: str, *, refs: tuple[str, ...] = (),
        head: str = "", privacy_class: str = "private", stream: str = "operations",
        process_id: str = "", correlation_id: str = "", causation_id: str = "",
    ) -> dict[str, Any]:
        metadata = {"refs": refs, "head": head}
        if forbidden_content(metadata):
            raise KernelRefused("journal_content_forbidden")
        with self._connection() as conn:
            previous = conn.execute(
                "SELECT stream_sequence, record_sha256 FROM kernel_journal WHERE stream=? ORDER BY stream_sequence DESC LIMIT 1",
                (stream,),
            ).fetchone()
            sequence = int(previous[0]) + 1 if previous is not None else 1
            record = {
                "stream": stream,
                "stream_sequence": sequence,
                "event_id": "evt_" + uuid.uuid4().hex,
                "operation_id": operation_id,
                "process_id": process_id,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "event_type": event_type,
                "event_version": 1,
                "refs": list(refs),
                "privacy_class": privacy_class,
                "head": str(head)[:_HEAD_LIMIT],
                "timestamp": self._clock(),
                "previous_sha256": str(previous[1]) if previous is not None else "sha256:genesis",
            }
            record_hash = _hash(record)
            cursor = conn.execute(
                """INSERT INTO kernel_journal(
                    stream,stream_sequence,event_id,operation_id,process_id,correlation_id,
                    causation_id,event_type,event_version,refs_json,privacy_class,head,
                    timestamp,previous_sha256,record_sha256
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    record["stream"], sequence, record["event_id"], operation_id,
                    process_id, correlation_id, causation_id, event_type, 1,
                    _json(record["refs"]), privacy_class, record["head"],
                    record["timestamp"], record["previous_sha256"], record_hash,
                ),
            )
            record["cursor"] = int(cursor.lastrowid)
            record["record_sha256"] = record_hash
            return record

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
                    authority_basis,state,revision,native_id,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    values["operation_id"], values["request_id"], values["idempotency_key"],
                    values["name"], values["version"], values["principal_kind"],
                    values["principal_identity"], values["target_ref"], values["placement"],
                    values["envelope_sha256"], values["policy_version"],
                    values["authority_basis"], values["state"], 1, values["native_id"],
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

    def claim_candidate(self, executor: str) -> dict[str, Any] | None:
        """Atomically acquire one approved operation; first claimant wins."""
        with self._connection() as conn:
            row = conn.execute(
                """SELECT operation_id,revision FROM kernel_operations
                   WHERE state='awaiting_execution' AND placement=?
                   ORDER BY created_at LIMIT 1""",
                (f"node:{executor}",),
            ).fetchone()
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

    def add_receipt(self, operation_id: str, state: str, outcome: str, result_ref: str = "") -> dict[str, Any]:
        receipt_id = "rcpt_" + uuid.uuid4().hex
        with self._connection() as conn:
            existing = conn.execute(
                "SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)
            ).fetchone()
            if existing is not None:
                return dict(existing)
            conn.execute(
                "INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)",
                (receipt_id, operation_id, state, outcome, result_ref, self._clock()),
            )
        return self.receipt(operation_id) or {}

    def receipt(self, operation_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM kernel_receipts WHERE operation_id=?", (operation_id,)
            ).fetchone()
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
