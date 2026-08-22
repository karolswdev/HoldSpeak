"""Durable operation metadata and its per-stream SHA-256 chain."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
import uuid
from collections.abc import Mapping
from typing import Any

from .journal_txn import append_record
from .journal_txn import json_encode as _json
from .journal_txn import record_hash as _hash
from .model import KernelRefused
from .runner_receipt_evidence import consume_runner_receipt_evidence

# Receipt readers must see the executing scheduler separately from the owner
# who delegated it; every receipt read path returns this same joined shape.
_RECEIPT_SQL = (
    "SELECT r.*, o.principal_kind AS actor_kind, o.principal_identity AS actor_identity,"
    " o.delegator_kind, o.delegator_identity, o.authority_basis, o.target_ref"
    " FROM kernel_receipts r JOIN kernel_operations o ON o.operation_id=r.operation_id"
    " WHERE r.operation_id=?"
)


class JournalStore:
    _publication_wait_seconds = 5.0
    _publication_poll_seconds = 0.01

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
            raise KernelRefused("event_filter_not_allowed", min(unknown))
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

    def reconstruct_claimed_inference_child(self, operation_id: str) -> dict[str, Any] | None:
        """Return a claimed inference child only when its signed identity is intact.

        The operation row is scheduler state, not proof.  Approval's signed
        warrant is the immutable admission fact, so every dispatch-relevant row
        field is cross-bound to it before a controller may adopt the child.
        """
        operation = self.operation(operation_id)
        if operation is None:
            return None
        warrant = operation.get("warrant") or {}
        placement = str(operation.get("placement") or "")
        claimant = str(operation.get("claimed_by") or "")
        if (
            operation["name"] != "inference.invoke"
            or int(operation["version"]) != 1
            or operation["state"] != "claimed"
            or not claimant
            or not warrant
            or bool(operation.get("warrant_revoked"))
            or not self.valid_warrant(warrant)
            or float(warrant.get("execution_expires_at") or 0) <= self._clock()
            or warrant.get("operation_id") != operation["operation_id"]
            or warrant.get("envelope_sha256") != operation["envelope_sha256"]
            or warrant.get("target_ref") != operation["target_ref"]
            or warrant.get("target_binding") != operation["target_ref"]
            or warrant.get("placement") != operation["placement"]
            or warrant.get("policy_version") != operation["policy_version"]
            or warrant.get("native_id") != operation["native_id"]
            or warrant.get("principal_kind") != operation["principal_kind"]
            or warrant.get("principal_identity") != operation["principal_identity"]
            or warrant.get("parent_operation_id") != (operation.get("parent_operation_id") or "")
            or not str(operation.get("target_ref") or "").startswith("deployment-revision:")
            or not str(operation.get("native_id") or "")
            or not placement.startswith("node:")
            or claimant != placement.removeprefix("node:")
        ):
            return None
        return operation

    def reconstruct_inference_child_receipt(self, operation_id: str) -> dict[str, Any] | None:
        """Reconstruct a terminal child receipt from signed admission + kernel rows."""
        operation = self.operation(operation_id)
        receipt = self.receipt(operation_id)
        if operation is None or receipt is None:
            return None
        with self._connection() as conn:
            attestation = conn.execute(
                "SELECT * FROM kernel_inference_receipt_attestations WHERE operation_id=?",
                (operation_id,),
            ).fetchone()
        if attestation is None:
            return None
        try:
            attested_material = json.loads(str(attestation["material_json"]))
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
        warrant = operation.get("warrant") or {}
        placement = str(operation.get("placement") or "")
        claimant = str(operation.get("claimed_by") or "")
        if (
            operation["name"] != "inference.invoke"
            or int(operation["version"]) != 1
            or operation["state"] not in {"succeeded", "failed", "refused", "cancelled", "indeterminate"}
            or receipt["state"] != operation["state"]
        ):
            return None
        material = {
            "schema": "KernelInferenceReceiptAttestation@1",
            "operation_id": str(operation["operation_id"]),
            "receipt_id": str(receipt["receipt_id"]),
            "state": str(receipt["state"]),
            "outcome": str(receipt["outcome"]),
            "result_ref": str(receipt["result_ref"]),
            "name": str(operation["name"]),
            "version": int(operation["version"]),
            "native_id": str(operation["native_id"]),
            "envelope_sha256": str(operation["envelope_sha256"]),
            "target_ref": str(operation["target_ref"]),
            "placement": str(operation["placement"]),
            "policy_version": str(operation["policy_version"]),
            "principal_kind": str(operation["principal_kind"]),
            "principal_identity": str(operation["principal_identity"]),
            "parent_operation_id": str(operation.get("parent_operation_id") or ""),
            "warrant_basis": str(warrant.get("signature") or ""),
            "runner_signal": str(attested_material.get("runner_signal") or ""),
            "send_phase": str(attested_material.get("send_phase") or ""),
        }
        expected = hmac.new(
            self._secret().encode(), _json(material).encode(), hashlib.sha256
        ).hexdigest()
        if (
            str(attestation["receipt_id"]) != str(receipt["receipt_id"])
            or attested_material != material
            or not hmac.compare_digest(str(attestation["signature"]), expected)
        ):
            return None
        # A refusal can terminalize before approval/claim and therefore has no
        # warrant.  Its kernel HMAC attestation still proves the full admitted
        # operation and receipt.  Any provider-reaching child must additionally
        # satisfy the signed-warrant execution identity below.
        if warrant:
            warrant_identity_invalid = bool(
                not self.valid_warrant(warrant)
                or warrant.get("operation_id") != operation["operation_id"]
                or warrant.get("envelope_sha256") != operation["envelope_sha256"]
                or warrant.get("target_ref") != operation["target_ref"]
                or warrant.get("target_binding") != operation["target_ref"]
                or warrant.get("placement") != operation["placement"]
                or warrant.get("policy_version") != operation["policy_version"]
                or warrant.get("native_id") != operation["native_id"]
                or warrant.get("principal_kind") != operation["principal_kind"]
                or warrant.get("principal_identity") != operation["principal_identity"]
                or warrant.get("parent_operation_id") != (operation.get("parent_operation_id") or "")
                or float(receipt["created_at"]) > float(warrant.get("execution_expires_at") or 0)
            )
            unclaimed_pre_send_refusal = bool(
                operation["state"] == "refused"
                and str(attested_material.get("send_phase")) == "pre_send"
                and not claimant
            )
            if warrant_identity_invalid or (
                not unclaimed_pre_send_refusal
                and (
                    not placement.startswith("node:")
                    or claimant != placement.removeprefix("node:")
                )
            ):
                return None
        elif operation["state"] != "refused" or str(attested_material.get("send_phase")) != "pre_send":
            return None
        return {
            "operation": operation,
            "receipt": receipt,
            "terminal_attestation": {
                **material,
                "signature": str(attestation["signature"]),
            },
        }
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
        from .publication_transition import transition

        return transition(self, operation_id, expected_revision, state, **changes)
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
        wait_until = time.monotonic() + 5.0
        while True:
            with self._connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                parent = conn.execute(
                    "SELECT publication_claim_id FROM kernel_parent_runs "
                    "WHERE operation_id=?",
                    (operation_id,),
                ).fetchone()
                if parent is None or not str(parent["publication_claim_id"] or ""):
                    conn.execute(
                        "UPDATE kernel_operations SET warrant_revoked=1,"
                        "revision=revision+1,updated_at=? WHERE operation_id=?",
                        (self._clock(), operation_id),
                    )
                    break
            if time.monotonic() >= wait_until:
                raise KernelRefused(
                    "parent_publication_in_progress", operation_id=operation_id
                )
            time.sleep(0.01)
        return self.operation(operation_id) or {}

    def transition_and_receipt(
        self, operation_id: str, expected_revision: int, state: str, outcome: str,
        result_ref: str = "", *, runner_evidence: Any = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Durably couple a claimed operation's terminal state and receipt."""
        receipt_id = "rcpt_" + uuid.uuid4().hex
        secret = self._secret()
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
            runner_signal, send_phase = (
                ("kernel_refused", "pre_send")
                if str(operation["name"]) == "inference.invoke"
                and int(operation["version"]) == 1
                and outcome == "refused"
                else ("none", "pre_send")
            )
            if (
                str(operation["name"]) == "inference.invoke"
                and int(operation["version"]) == 1
                and runner_evidence is not None
            ):
                evidence = consume_runner_receipt_evidence(
                    runner_evidence, operation_id=operation_id,
                    outcome=outcome, result_ref=result_ref,
                )
                runner_signal, send_phase = evidence.runner_signal, evidence.send_phase
            self._attest_inference_receipt(
                conn, operation, receipt, secret,
                runner_signal=runner_signal, send_phase=send_phase,
            )
        return self._operation(operation), dict(receipt)

    def add_receipt(
        self, operation_id: str, state: str, outcome: str, result_ref: str = "",
        *, runner_evidence: Any = None,
    ) -> dict[str, Any]:
        receipt_id = "rcpt_" + uuid.uuid4().hex
        secret = self._secret()
        with self._connection() as conn:
            existing = conn.execute(_RECEIPT_SQL, (operation_id,)).fetchone()
            if existing is not None:
                return dict(existing)
            conn.execute(
                "INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)",
                (receipt_id, operation_id, state, outcome, result_ref, self._clock()),
            )
            operation = conn.execute(
                "SELECT * FROM kernel_operations WHERE operation_id=?", (operation_id,)
            ).fetchone()
            receipt = conn.execute(_RECEIPT_SQL, (operation_id,)).fetchone()
            runner_signal, send_phase = (
                ("kernel_refused", "pre_send")
                if str(operation["name"]) == "inference.invoke"
                and int(operation["version"]) == 1
                and outcome == "refused"
                else ("none", "pre_send")
            )
            if (
                str(operation["name"]) == "inference.invoke"
                and int(operation["version"]) == 1
                and runner_evidence is not None
            ):
                evidence = consume_runner_receipt_evidence(
                    runner_evidence, operation_id=operation_id,
                    outcome=outcome, result_ref=result_ref,
                )
                runner_signal, send_phase = evidence.runner_signal, evidence.send_phase
            self._attest_inference_receipt(
                conn, operation, receipt, secret,
                runner_signal=runner_signal, send_phase=send_phase,
            )
        return self.receipt(operation_id) or {}

    @staticmethod
    def _attest_inference_receipt(conn: Any, operation: Any, receipt: Any, secret: str, *, runner_signal: str, send_phase: str) -> None:
        if operation is None or receipt is None or str(operation["name"]) != "inference.invoke" or int(operation["version"]) != 1:
            return
        warrant = json.loads(str(operation["warrant_json"] or "{}"))
        material = {
            "schema": "KernelInferenceReceiptAttestation@1",
            "operation_id": str(operation["operation_id"]),
            "receipt_id": str(receipt["receipt_id"]),
            "state": str(receipt["state"]),
            "outcome": str(receipt["outcome"]),
            "result_ref": str(receipt["result_ref"]),
            "name": str(operation["name"]),
            "version": int(operation["version"]),
            "native_id": str(operation["native_id"]),
            "envelope_sha256": str(operation["envelope_sha256"]),
            "target_ref": str(operation["target_ref"]),
            "placement": str(operation["placement"]),
            "policy_version": str(operation["policy_version"]),
            "principal_kind": str(operation["principal_kind"]),
            "principal_identity": str(operation["principal_identity"]),
            "parent_operation_id": str(operation["parent_operation_id"] or ""),
            "warrant_basis": str(warrant.get("signature") or ""),
            "runner_signal": runner_signal,
            "send_phase": send_phase,
        }
        signature = hmac.new(secret.encode(), _json(material).encode(), hashlib.sha256).hexdigest()
        conn.execute(
            "INSERT INTO kernel_inference_receipt_attestations VALUES(?,?,?,?,?)",
            (receipt["receipt_id"], operation["operation_id"], _json(material), signature, receipt["created_at"]),
        )
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
