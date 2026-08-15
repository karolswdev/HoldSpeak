"""Durable, receipt-gated materialization of runner-produced projections.

A projection is deliberately staged before the runner closes its terminal
receipt.  Domain writes happen only later, after that receipt is durable.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from .model import KernelRefused
from .projection_publisher import StagePublisher, retarget_publisher

__all__ = ["ProjectionStage", "ProjectionStager", "StagePublisher", "retarget_publisher"]

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
        self._parent_cancel_discards: set[str] = set()
        self._health_faults: list[dict[str, str]] = []

    def register(self, kind: str, materializer: Materializer, *, discard_on_parent_cancel: bool = False) -> None:
        if not kind or kind in self._materializers:
            raise ValueError(f"projection materializer already registered: {kind!r}")
        self._materializers[kind] = materializer
        if discard_on_parent_cancel:
            self._parent_cancel_discards.add(kind)

    def publisher(self, invocation_id: str, kind: str, encoder: Callable[[Any], Mapping[str, Any]]) -> StagePublisher:
        """Return the sole callback shape that a migrated service may give runner.

        A rebindable :class:`~.projection_publisher.StagePublisher`, so a dialect
        retry stages against the child that actually ran it (HS-131-10 round 2).
        """
        if not callable(encoder):
            raise TypeError("projection encoder must be callable")
        return StagePublisher(self, invocation_id, kind, encoder)

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

    def _scheduler_delegation_drift(self, conn: sqlite3.Connection, stage: ProjectionStage) -> tuple[str, str]:
        """Re-derive frozen scheduler terms immediately before publication."""
        row = conn.execute("""SELECT p.input_json,o.principal_kind FROM kernel_operations child
            JOIN kernel_parent_runs p ON p.operation_id=child.parent_operation_id
            JOIN kernel_operations o ON o.operation_id=p.operation_id
            WHERE child.operation_id=?""", (stage.operation_id,)).fetchone()
        if row is None or str(row["principal_kind"]) != "scheduler":
            return "", ""
        parent_input = json.loads(str(row["input_json"] or "{}"))
        delegation = conn.execute("SELECT * FROM kernel_schedule_delegations WHERE id=?", (str(parent_input.get("delegation_id") or ""),)).fetchone()
        if delegation is None or str(delegation["state"]) != "LIVE" or str(delegation["terms_sha256"]) != str(parent_input.get("terms_sha256") or ""):
            return "delegation_revoked", str(parent_input.get("workbench_id") or "")
        recipe = conn.execute("SELECT last_modified FROM recipes WHERE id=? AND deleted=0", (str(delegation["recipe_id"]),)).fetchone()
        if recipe is None or str(recipe["last_modified"]) != str(delegation["recipe_revision"]):
            return "delegation_stale_work", str(delegation["workbench_id"])
        from ..deployment_revisions import resolve_workbench_deployment_revision
        current = resolve_workbench_deployment_revision(conn, str(delegation["workbench_id"]))
        if current is None or current.id != str(delegation["deployment_revision_id"]):
            return "delegation_target_changed", str(delegation["workbench_id"])
        return "", ""

    @staticmethod
    def _retry_stage(conn: sqlite3.Connection, invocation_id: str) -> Any:
        """The stage a dialect RETRY of this logical invocation left, if any.

        A caller holds the invocation id it asked for. HS-131-10 admits a dialect
        retry as a second child under a derived id (``<iid>_r2``,
        :func:`~.provider_signals.retry_invocation_id`) which stages against
        itself — correctly, since it is the child that ran. Without this lookup
        every existing service would finalize the id it remembers, find no row,
        and silently drop the output the retry earned.

        Deliberately narrow: only ``<invocation_id>_r<digits>``, only when the
        asked-for id staged NOTHING (the first attempt raised its dialect signal
        before ever publishing), and the ordinary receipt/parent/drift gates below
        still decide whether the row may publish. The LIKE only narrows the scan;
        the regex is what decides membership.
        """
        rows = conn.execute(
            "SELECT * FROM kernel_projection_stages WHERE invocation_id LIKE ?"
            " ORDER BY created_at DESC",
            (f"{invocation_id}_r%",),
        ).fetchall()
        pattern = re.compile(rf"^{re.escape(invocation_id)}_r\d+$")
        for row in rows:
            if pattern.match(str(row["invocation_id"])):
                return row
        return None

    def finalize(self, invocation_id: str) -> Mapping[str, Any] | None:
        """Materialize exactly once, only when a matching receipt permits it."""
        published: Mapping[str, Any] | None = None
        revocation: tuple[str, str] | None = None
        with self._database._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM kernel_projection_stages WHERE invocation_id=?", (invocation_id,)).fetchone()
            if row is None:
                row = self._retry_stage(conn, invocation_id)
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
            # Kinds registered with discard_on_parent_cancel have no checkpoint
            # CAS of their own; the parent election is their only publication
            # fence.  Checkpointed kinds (sequence/workflow/workbench) keep the
            # HS-131-04 contract: the earned child receipt survives and the
            # stale checkpoint (advanced=0) blocks late output instead.
            if stage.kind in self._parent_cancel_discards:
                parent = conn.execute(
                    "SELECT p.state FROM kernel_operations child JOIN kernel_parent_runs p ON p.operation_id=child.parent_operation_id WHERE child.operation_id=?",
                    (stage.operation_id,),
                ).fetchone()
                if parent is not None and str(parent["state"]) in {"CANCELLING", "CANCELLED", "INDETERMINATE"}:
                    conn.execute("UPDATE kernel_projection_stages SET state='DISCARDED',updated_at=? WHERE stage_id=? AND state != 'PUBLISHED'", (self._clock(), stage.stage_id))
                    return None
            if stage.state == "PUBLISHED":
                return self._published(stage, conn)
            if stage.state == "DISCARDED":
                return None
            if stage.state != "STAGED":
                raise KernelRefused("projection_stage_state_invalid")
            drift, workbench_id = self._scheduler_delegation_drift(conn, stage)
            if drift:
                # The provider returned, and the schedule's terms changed while it
                # was doing so. The output never crosses the publication boundary
                # — but the CHILD's terminal receipt is not the place to say so.
                #
                # Round 2: this used to UPDATE an already-`succeeded` invocation
                # operation and its receipt to `refused`/<drift> — exactly the
                # mutation this story's acceptance criterion (and
                # `ExecutorPlane.receipt`'s `receipt_immutable`) forbids. The child
                # receipt is the honest record of what the PROVIDER did; the
                # schedule going stale is a fact about the DELEGATION. So the fence
                # moves entirely to the projection: the stage is DISCARDED with the
                # reason, the delegation is revoked below, no domain state is
                # written, and late publication is prevented by the same
                # transaction as before — nothing is rewritten.
                conn.execute(
                    "UPDATE kernel_projection_stages SET state='DISCARDED',final_result_json=?,updated_at=? WHERE stage_id=?",
                    (_canonical({"discarded": drift}), self._clock(), stage.stage_id),
                )
                revocation = (workbench_id, drift)
            else:
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
                published = dict(projection)
        if revocation is not None:
            from ..services.schedule_delegation import ScheduleDelegationService
            ScheduleDelegationService(self._database).revoke(*revocation)
            return None
        return published

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
