"""Durable, receipt-gated materialization of runner-produced projections.

A projection is deliberately staged before the runner closes its terminal
receipt.  Domain writes happen only later, after that receipt is durable.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .model import KernelRefused


_COMPLETED_STATES = frozenset({"succeeded", "failed", "refused", "cancelled", "indeterminate"})
_NON_SUCCESS = _COMPLETED_STATES - {"succeeded"}


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise KernelRefused("projection_not_canonicalizable") from exc


@dataclass(frozen=True)
class ProjectionStage:
    stage_id: str
    invocation_id: str
    operation_id: str
    kind: str
    projection: Mapping[str, Any]
    result_ref: str
    state: str
    created_at: float
    updated_at: float


class _PublicationPermit:
    """Private capability, valid for one materializer and one SQLite transaction."""
    __slots__ = ("_stager", "_connection", "_used")

    def __init__(self, stager: "ProjectionStager", connection: sqlite3.Connection) -> None:
        self._stager, self._connection, self._used = stager, connection, False

    def use(self, conn: sqlite3.Connection) -> None:
        self._stager.require_permit(self, conn)


Materializer = Callable[[sqlite3.Connection, ProjectionStage, _PublicationPermit], Mapping[str, Any]]


class ProjectionStager:
    """Kernel-owned stage store and atomic finalization registry."""

    def __init__(self, database: Any, broker: Any, *, clock: Callable[[], float] = time.time) -> None:
        self._database, self._broker, self._clock = database, broker, clock
        self._materializers: dict[str, Materializer] = {}
        self._health_faults: list[dict[str, str]] = []

    def register(self, kind: str, materializer: Materializer) -> None:
        if not kind or kind in self._materializers:
            raise ValueError(f"projection materializer already registered: {kind!r}")
        self._materializers[kind] = materializer

    def publisher(self, invocation_id: str, kind: str, encoder: Callable[[Any], Mapping[str, Any]]) -> Callable[[Any], str]:
        """Return the sole callback shape that a migrated service may give runner."""
        if not callable(encoder):
            raise TypeError("projection encoder must be callable")
        def publish(result: Any) -> str:
            projection = encoder(result)
            if not isinstance(projection, Mapping):
                raise KernelRefused("projection_encoder_not_mapping")
            return self.stage(invocation_id, kind, projection).result_ref
        return publish

    def stage(self, invocation_id: str, kind: str, projection: Mapping[str, Any]) -> ProjectionStage:
        material = _canonical(dict(projection))
        digest = "sha256:" + hashlib.sha256(material.encode()).hexdigest()
        now = self._clock()
        with self._database._connection() as conn:
            operation = conn.execute(
                "SELECT operation_id FROM kernel_operations WHERE native_id=? ORDER BY created_at DESC LIMIT 1",
                (invocation_id,),
            ).fetchone()
            if operation is None:
                raise KernelRefused("projection_invocation_unknown")
            existing = conn.execute(
                "SELECT * FROM kernel_projection_stages WHERE invocation_id=? AND kind=?",
                (invocation_id, kind),
            ).fetchone()
            if existing is not None:
                if str(existing["projection_sha256"]) != digest:
                    raise KernelRefused("projection_stage_payload_conflict")
                return self._row(existing)
            stage_id = "pstg_" + uuid.uuid4().hex
            conn.execute(
                """INSERT INTO kernel_projection_stages(
                    stage_id,invocation_id,operation_id,kind,projection_json,projection_sha256,
                    result_ref,state,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (stage_id, invocation_id, operation["operation_id"], kind, material, digest,
                 f"projection-stage:{stage_id}", "STAGED", now, now),
            )
            row = conn.execute("SELECT * FROM kernel_projection_stages WHERE stage_id=?", (stage_id,)).fetchone()
        return self._row(row)

    def finalize(self, invocation_id: str) -> Mapping[str, Any] | None:
        """Materialize exactly once, only when a matching receipt permits it."""
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM kernel_projection_stages WHERE invocation_id=?", (invocation_id,)).fetchone()
            if row is None:
                return None
            stage = self._row(row)
            receipt = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (stage.operation_id,)).fetchone()
            if receipt is None:
                return None
            operation = conn.execute("SELECT * FROM kernel_operations WHERE operation_id=?", (stage.operation_id,)).fetchone()
            if operation is None or str(operation["native_id"]) != stage.invocation_id:
                raise KernelRefused("projection_receipt_invocation_mismatch")
            outcome = str(receipt["outcome"])
            if outcome in _NON_SUCCESS:
                conn.execute("UPDATE kernel_projection_stages SET state='DISCARDED',updated_at=? WHERE stage_id=? AND state != 'PUBLISHED'", (self._clock(), stage.stage_id))
                return None
            if outcome != "succeeded" or str(receipt["result_ref"]) != stage.result_ref:
                raise KernelRefused("projection_receipt_result_ref_mismatch")
            if stage.state == "PUBLISHED":
                return self._published(stage, conn)
            if stage.state == "DISCARDED":
                return None
            if stage.state != "STAGED":
                raise KernelRefused("projection_stage_state_invalid")
            result = conn.execute("UPDATE kernel_projection_stages SET state='FINALIZING',updated_at=? WHERE stage_id=? AND state='STAGED'", (self._clock(), stage.stage_id)).rowcount
            if result != 1:
                raise KernelRefused("projection_stage_claim_conflict")
            materializer = self._materializers.get(stage.kind)
            if materializer is None:
                raise KernelRefused("projection_materializer_unknown")
            permit = _PublicationPermit(self, conn)
            projection = materializer(conn, stage, permit)
            if not permit._used:
                raise KernelRefused("projection_permit_not_used")
            final_json = _canonical(dict(projection))
            conn.execute("UPDATE kernel_projection_stages SET state='PUBLISHED',final_result_json=?,updated_at=? WHERE stage_id=? AND state='FINALIZING'", (final_json, self._clock(), stage.stage_id))
            return dict(projection)

    def require_permit(self, permit: object, conn: sqlite3.Connection) -> None:
        if not isinstance(permit, _PublicationPermit) or permit._stager is not self or permit._connection is not conn or permit._used:
            raise KernelRefused("projection_publication_permit_invalid")
        permit._used = True

    def recover(self) -> Mapping[str, Any]:
        """Reap first, then reconcile durable stages without inventing truth."""
        reaped = self._broker.reap_expired()
        finalized = discarded = 0
        faults: list[dict[str, str]] = []
        with self._database._connection() as conn:
            rows = conn.execute("SELECT * FROM kernel_projection_stages WHERE state IN ('STAGED','FINALIZING')").fetchall()
        for row in rows:
            stage = self._row(row)
            receipt = self._broker.store.receipt(stage.operation_id)
            if receipt is not None:
                if str(receipt["outcome"]) == "succeeded":
                    if self.finalize(stage.invocation_id) is not None:
                        finalized += 1
                else:
                    self.finalize(stage.invocation_id)
                    discarded += 1
                continue
            operation = self._broker.store.operation(stage.operation_id)
            if operation is not None and str(operation.get("state")) in _COMPLETED_STATES:
                fault = {"code": "terminal_operation_without_receipt", "operation_id": stage.operation_id, "stage_id": stage.stage_id}
                faults.append(fault)
        self._health_faults = faults
        return {"reaped": reaped, "finalized": finalized, "discarded": discarded, "healthy": not faults, "faults": faults}

    @property
    def health_faults(self) -> tuple[Mapping[str, str], ...]:
        return tuple(self._health_faults)

    def get(self, invocation_id: str) -> ProjectionStage | None:
        with self._database._connection() as conn:
            row = conn.execute("SELECT * FROM kernel_projection_stages WHERE invocation_id=?", (invocation_id,)).fetchone()
        return self._row(row) if row else None

    def _published(self, stage: ProjectionStage, conn: sqlite3.Connection) -> Mapping[str, Any]:
        row = conn.execute("SELECT final_result_json FROM kernel_projection_stages WHERE stage_id=?", (stage.stage_id,)).fetchone()
        if row is None or not str(row["final_result_json"]):
            raise KernelRefused("projection_published_result_missing")
        return json.loads(str(row["final_result_json"]))

    @staticmethod
    def _row(row: Any) -> ProjectionStage:
        return ProjectionStage(str(row["stage_id"]), str(row["invocation_id"]), str(row["operation_id"]), str(row["kind"]), json.loads(str(row["projection_json"])), str(row["result_ref"]), str(row["state"]), float(row["created_at"]), float(row["updated_at"]))


__all__ = ["ProjectionStage", "ProjectionStager"]
