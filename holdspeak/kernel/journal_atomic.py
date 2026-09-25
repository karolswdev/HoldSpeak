"""One-connection atomic operation writes (PHILO-7-02, the lifecycle beat's invariant 4).

A typed concern carved from ``journal.py`` (the kernel density guard): the
terminal state and its receipt commit in ONE SQLite transaction, in an explicit
order, on ONE connection:

1. ``BEGIN IMMEDIATE`` (the write lock is held from here to the commit);
2. read the existing receipt and the operation's revision -- default: an
   existing receipt is returned and nothing runs again; ``strict``: an existing
   receipt raises ``operation_already_terminal`` and a moved revision
   ``operation_revision_conflict``, before anything is written;
3. ``effect(conn)`` when given (local SQL on THIS connection only);
4. UPDATE the state, ``revision+1`` (and ``decision`` / ``warrant_revoked``);
5. INSERT the receipt (and the caller's in-transaction attestation);
6. commit. Any exception in 3-5 rolls all of it back.
"""
from __future__ import annotations

import uuid
from typing import Any, Callable, Mapping

from .model import KernelRefused

RECEIPT_SQL = (
    "SELECT r.*, o.principal_kind AS actor_kind, o.principal_identity AS actor_identity,"
    " o.delegator_kind, o.delegator_identity, o.authority_basis, o.target_ref"
    " FROM kernel_receipts r JOIN kernel_operations o ON o.operation_id=r.operation_id"
    " WHERE r.operation_id=?"
)
_OPERATION_SQL = "SELECT * FROM kernel_operations WHERE operation_id=?"
_INSERT_RECEIPT = (
    "INSERT INTO kernel_receipts(receipt_id,operation_id,state,outcome,result_ref,created_at) VALUES(?,?,?,?,?,?)"
)


def insert_operation(conn: Any, values: Mapping[str, Any], now: float) -> None:
    """``create_operation``'s INSERT: the same columns and defaults."""
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
            now, now,
        ),
    )


def create_refused_with_receipt(store: Any, values: Mapping[str, Any], outcome: str) -> tuple[Any, Any]:
    """T1: the refused row and its receipt in ONE transaction.

    ``create_operation``'s logic exactly (the ``(principal_identity,
    idempotency_key)`` lookup: an existing row comes back with its existing
    receipt and nothing is written; ``idempotency_payload_mismatch`` as today).
    """
    with store._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT * FROM kernel_operations WHERE principal_identity=? AND idempotency_key=?",
            (values["principal_identity"], values["idempotency_key"]),
        ).fetchone()
        if existing is not None:
            if str(existing["envelope_sha256"]) != values["envelope_sha256"]:
                raise KernelRefused("idempotency_payload_mismatch", operation_id=str(existing["operation_id"]))
            receipt = conn.execute(RECEIPT_SQL, (existing["operation_id"],)).fetchone()
            return existing, receipt
        insert_operation(conn, values, store._clock())
        conn.execute(_INSERT_RECEIPT, ("rcpt_" + uuid.uuid4().hex, values["operation_id"],
                                       values["state"], outcome, "", store._clock()))
        return (conn.execute(_OPERATION_SQL, (values["operation_id"],)).fetchone(),
                conn.execute(RECEIPT_SQL, (values["operation_id"],)).fetchone())


def transition_and_receipt(
    store: Any, operation_id: str, expected_revision: int, state: str, outcome: str,
    result_ref: str = "", *, strict: bool = False, decision: str | None = None,
    warrant_revoked: int | None = None, effect: Callable[[Any], None] | None = None,
    attest: Callable[[Any, Any, Any], None] | None = None,
) -> tuple[Any, Any]:
    """Steps 1-6 above; returns the operation row and the receipt row."""
    with store._connection() as conn:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(RECEIPT_SQL, (operation_id,)).fetchone()
        if existing is not None:
            if strict:
                raise KernelRefused("operation_already_terminal", operation_id=operation_id)
            return conn.execute(_OPERATION_SQL, (operation_id,)).fetchone(), existing
        if strict:
            current = conn.execute("SELECT revision FROM kernel_operations WHERE operation_id=?", (operation_id,)).fetchone()
            if current is None or int(current["revision"]) != int(expected_revision):
                raise KernelRefused("operation_revision_conflict", operation_id=operation_id)
        if effect is not None:
            effect(conn)
        assignments, values = ["state=?", "revision=revision+1", "updated_at=?"], [state, store._clock()]
        for column, value in (("decision", decision), ("warrant_revoked", warrant_revoked)):
            if value is not None:
                assignments.append(f"{column}=?")
                values.append(value)
        changed = conn.execute(
            f"UPDATE kernel_operations SET {','.join(assignments)} WHERE operation_id=? AND revision=?",
            (*values, operation_id, expected_revision),
        ).rowcount
        if changed != 1:
            raise KernelRefused("operation_revision_conflict", operation_id=operation_id)
        conn.execute(_INSERT_RECEIPT, ("rcpt_" + uuid.uuid4().hex, operation_id, state, outcome,
                                       result_ref, store._clock()))
        operation = conn.execute(_OPERATION_SQL, (operation_id,)).fetchone()
        receipt = conn.execute(RECEIPT_SQL, (operation_id,)).fetchone()
        if attest is not None:
            attest(conn, operation, receipt)
        return operation, receipt
