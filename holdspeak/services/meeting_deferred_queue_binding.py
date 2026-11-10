"""The deferred Meeting queue's claim: one parent run per job, no frozen plan.

A claim records the job, its parent run and the assignment the engine door
reads for the summary (``engine_door.chain``). Every model call of the job
goes through the door, which picks the engine from the owner's live
assignment itself; nothing here plans or freezes a route.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

from ..db.models import IntelJob
from ..meeting_session.deferred_bound import (
    PARENT_KIND,
    job_capabilities,
    queue_service_principal,
)
from .errors import ConflictError, ValidationError

# The lawful bound queue owner is the only remaining consumer of this envelope.
JOB_DEADLINE_SECONDS = 30 * 60
#: Children one model call may spend: the door's first engine, its runner
#: dialect retry, the next engine and its dialect retry.
CHILDREN_PER_CALL = 4


@dataclass(frozen=True)
class _PendingQueueParent:
    """The kernel shell admitted before the claim writer epoch starts."""

    parent: Any
    deadline_at: float
    child_budget: int
    input_snapshot: dict[str, Any]
    assignment: str
    selection: str


def _input_snapshot(job: IntelJob) -> dict[str, Any]:
    return {
        "schema": "MeetingDeferredIntelQueueParent@1",
        "job_id": str(job.job_id),
        "meeting_id": str(job.meeting_id),
        "work_descriptor_sha256": str(job.work_descriptor_sha256 or ""),
        "transcript_hash": str(job.transcript_hash),
        "displaced_work": list(job.displaced_work or ()),
        "frozen_bookmark_timestamps": list(job.frozen_bookmark_timestamps or ()),
        "frozen_bookmark_operations": [
            {"id": bookmark_id, "timestamp": timestamp}
            for bookmark_id, timestamp in tuple(job.frozen_bookmark_operations or ())
        ],
        "frozen_plugin_members": [dict(member) for member in tuple(job.frozen_plugin_members or ())],
    }


class MeetingDeferredQueueBinder:
    """Bind one queue job to one parent run.

    ``prepare`` checks the disclosed engine chain and admits the kernel shell
    before the claim writer lock (the shell has its own journal transaction);
    ``__call__`` writes the parent-run row in the claim transaction and gives
    back the references the claim records.
    """

    def __init__(self, broker: Any, *, clock: Any = time.time) -> None:
        self._broker = broker
        self._clock = clock
        self._pending: dict[str, _PendingQueueParent] = {}

    def prepare(self, job: IntelJob, command_ids: Mapping[str, str]) -> None:
        """Refuse a job with no engine or a changed chain; admit its shell."""
        from .meeting_route_projection import chain_legs, project_route, route_is_off, selection_hash

        job_id = str(job.job_id or "")
        if not job_id:
            raise ValueError("bound queue job has no job_id")
        if job_id in self._pending:
            return
        db = self._broker.database
        current = project_route(db, invocation_id=f"meeting:{job.meeting_id}")
        if route_is_off(current):
            # PHILO-15 01 ruling: OFF wins. The queue settles the job as skipped.
            raise ValidationError(
                "The owner turned this off.",
                code="no_assignment",
                context={"capability_id": "meeting.deferred_analysis", "off": True},
            )
        if current.get("status") != "ready":
            raise ValidationError("No model assignment can be frozen.", code="no_assignment")
        self._refuse_drift(job, current)
        assignment, legs = chain_legs(db)
        calls = sum(
            len(tuple(job.frozen_bookmark_operations or ())) if capability == "meeting.bookmark_label" else 1
            for capability in job_capabilities(job)
        )
        deadline = float(self._clock()) + JOB_DEADLINE_SECONDS
        snapshot = _input_snapshot(job)
        child_budget = CHILDREN_PER_CALL * max(1, calls)
        parent = self._broker.parent_run_controller.start(
            queue_service_principal(),
            kind=PARENT_KIND,
            definition_ref=f"meeting:{job.meeting_id}:deferred:{job_id}",
            definition_revision=str(job.work_descriptor_sha256 or ""),
            input_snapshot=snapshot,
            deadline_at=deadline,
            child_budget=child_budget,
            idempotency_key=str(command_ids["parent_command_id"]),
            _defer_persist=True,
        )
        self._pending[job_id] = _PendingQueueParent(
            parent=parent, deadline_at=deadline, child_budget=child_budget,
            input_snapshot=snapshot, assignment=assignment,
            selection=str(selection_hash(assignment, legs) or ""),
        )

    def _refuse_drift(self, job: IntelJob, current: Mapping[str, Any]) -> None:
        """The chain the run gesture disclosed (its hash and every leg) must be
        the chain the door reads now; else the job is refused before any
        model is contacted."""
        expected = getattr(job, "planned_route", None)
        if not isinstance(expected, Mapping):
            return
        if (
            current.get("selection_hash") == expected.get("selection_hash")
            and list(current.get("legs") or ()) == list(expected.get("legs") or ())
        ):
            return
        try:
            self._broker.database.intel.record_run_receipt(
                str(job.meeting_id), str(job.job_id), expected.get("selection_hash"), "refused", None,
            )
        finally:
            raise ConflictError(
                "The disclosed route changed before queue claim.", code="selection_drift",
            )

    def discard(self, job_id: str) -> None:
        """Terminalize an unbound pre-admitted shell after a lost claim race."""
        pending = self._pending.pop(str(job_id), None)
        if pending is None or pending.parent.context is not None:
            return
        try:
            self._broker.receipt(
                pending.parent.operation_id,
                "refused",
                "meeting-deferred-queue:claim-not-granted",
                self._broker.parent_run_controller._node,
            )
        except Exception:
            # The durable claim winner remains authoritative; this is only orphan
            # hygiene for a pre-admitted shell that never became a parent-run row.
            return

    def __call__(
        self, conn: Any, job: IntelJob, command_ids: Mapping[str, str]
    ) -> Mapping[str, str]:
        """Write the parent-run row in the claim transaction. The claim keeps
        ``bundle_id`` = the assignment id and ``bundle_sha256`` = the selection
        hash of its chain (the column names stay; nothing is frozen)."""
        del command_ids
        job_id = str(job.job_id or "")
        pending = self._pending.pop(job_id, None)
        if pending is None:
            raise ValueError("bound queue parent was not prepared")
        controller = self._broker.parent_run_controller
        try:
            # The assignment may change between ``prepare`` and this claim.
            from .meeting_route_projection import project_route

            current = project_route(self._broker.database, invocation_id=f"meeting:{job.meeting_id}")
            if current.get("selection_hash") != (pending.selection or None):
                raise ConflictError(
                    "The disclosed route changed before queue claim.", code="selection_drift",
                )
            self._refuse_drift(job, current)
            row = controller._persist_parent(
                conn,
                operation_id=pending.parent.operation_id,
                native_id=pending.parent.native_id,
                kind=PARENT_KIND,
                definition_ref=f"meeting:{job.meeting_id}:deferred:{job_id}",
                definition_revision=str(job.work_descriptor_sha256 or ""),
                input_snapshot=pending.input_snapshot,
                deadline_at=pending.deadline_at,
                child_budget=pending.child_budget,
                now=controller._clock(),
            )
            if row is None:
                raise ValueError("bound queue parent row was not written")
        except Exception:
            # The repository rolls back its writer before calling discard(), which
            # then has the pending shell available for a durable refusal receipt.
            self._pending[job_id] = pending
            raise
        return {
            "parent_operation_id": str(pending.parent.operation_id),
            "bundle_id": pending.assignment,
            "bundle_sha256": pending.selection,
        }


__all__ = ["MeetingDeferredQueueBinder"]
