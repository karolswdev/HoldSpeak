"""Queue-owned binding of deferred Meeting jobs to frozen route bundles.

The queue derives every durable command identity from ``intel_jobs.job_id``.
It owns no planner, controller, or provider path: it composes the existing
SERVICE policy, parent/bundle service, and later frozen-route execution.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Mapping

from ..db.models import IntelJob
from ..meeting_session.deferred_admission import (
    JOB_DEADLINE_SECONDS,
    PARENT_KIND,
    queue_service_principal,
)
from ..meeting_session.intel_plan import DISPLACED_AUTO_TITLE, DISPLACED_BOOKMARK_LABELS
from .inference_parent_route_bundle_service import InferenceParentRouteBundleService
from .inference_route_plan_service import ROUTE_PLANNING_AUTHORITY


@dataclass(frozen=True)
class _PendingQueueParent:
    """The kernel shell admitted before the claim writer epoch starts."""

    parent: Any
    deadline_at: float
    routes: tuple[dict[str, str], ...]
    lifecycle_child_budget: int
    admitted_child_budget: int
    admitted_policy_fingerprints: tuple[dict[str, Any], ...]


class MeetingDeferredQueueBinder:
    """Bind one immutable queue job to one SERVICE route bundle.

    ``prepare`` deliberately performs only pre-claim routing election and kernel
    shell admission.  The queue calls it before taking SQLite's claim writer
    lock, because the kernel shell has its own journal transaction.  The actual
    parent-run row, frozen routes, manifest, member rows, claim references, and
    ledger event commit together through the connection passed to ``__call__``.
    """

    def __init__(
        self,
        broker: Any,
        *,
        bundles: InferenceParentRouteBundleService | None = None,
        clock: Any = time.time,
    ) -> None:
        self._broker = broker
        self._bundles = bundles or InferenceParentRouteBundleService(
            broker, broker.inference_adoption_service
        )
        self._clock = clock
        self._pending: dict[str, _PendingQueueParent] = {}

    @staticmethod
    def _routes(job: IntelJob) -> tuple[dict[str, str], ...]:
        routes = [
            {
                "key": "analysis",
                "capability_id": "meeting.deferred_analysis",
                "invocation_id": str(job.job_id),
            }
        ]
        seen = {"meeting.deferred_analysis"}
        displaced_capabilities = {
            DISPLACED_BOOKMARK_LABELS: "meeting.bookmark_label",
            DISPLACED_AUTO_TITLE: "meeting.auto_title",
        }
        for slug in tuple(job.displaced_work or ()):
            capability = displaced_capabilities.get(str(slug))
            # The V3 descriptor freezes concrete label operations. A historical
            # bookmark slug with zero surviving operations is no work at all;
            # declaring its route would make bundle budgeting disagree with the
            # parent declaration and wrongly block the base summary.
            if (
                capability == "meeting.bookmark_label"
                and not tuple(job.frozen_bookmark_operations or ())
            ):
                continue
            if capability is not None and capability not in seen:
                routes.append(
                    {
                        "key": capability.rsplit(".", 1)[-1],
                        "capability_id": capability,
                        "invocation_id": str(job.job_id),
                    }
                )
                seen.add(capability)
        # C2 membership is immutable descriptor evidence.  Never construct a
        # capability from a runtime plugin string: invalid descriptor entries are
        # refused before the bundle exists, and every valid entry is an exact
        # registry capability member with its own frozen route plan.
        for frozen in tuple(job.frozen_plugin_members or ()):
            capability = str(frozen.get("capability_id") or "").strip()
            plugin_id = str(frozen.get("plugin_id") or "").strip()
            if capability != f"meeting.plugin.{plugin_id}" or not plugin_id:
                raise ValueError("frozen plugin descriptor is not exact")
            if capability in seen:
                raise ValueError("duplicate frozen plugin capability")
            routes.append(
                {
                    "key": f"plugin:{plugin_id}",
                    "capability_id": capability,
                    "invocation_id": str(job.job_id),
                }
            )
            seen.add(capability)
        return tuple(routes)

    def prepare(self, job: IntelJob, command_ids: Mapping[str, str]) -> None:
        """Pre-admit the deterministic shell without material or provider egress.

        Missing exact SERVICE assignments fail before a shell exists.  The
        in-transaction bundle form repeats route election and rejects an
        assignment/policy race before it writes the binding.
        """
        job_id = str(job.job_id or "")
        if not job_id:
            raise ValueError("bound queue job has no job_id")
        if job_id in self._pending:
            return
        principal = queue_service_principal()
        deadline = float(self._clock()) + JOB_DEADLINE_SECONDS
        routes = self._routes(job)
        child_budget = 0
        lifecycle_child_budget = 0
        policy_fingerprints: list[dict[str, Any]] = []
        for route in routes:
            resolved = self._bundles._plans.resolve_route_plan_for_feature(
                ROUTE_PLANNING_AUTHORITY,
                feature_principal=principal,
                parent_kind=PARENT_KIND,
                capability_id=route["capability_id"],
                invocation_id=route["invocation_id"],
                deadline_at=deadline,
            )
            policy = resolved["retry_policy"]
            policy_fingerprints.append(
                {
                    "id": policy["id"],
                    "revision": policy["revision"],
                    "sha256": policy["sha256"],
                    "total_physical_attempts": policy["total_physical_attempts"],
                }
            )
            # One frozen route definition can legally serve many bookmark-label
            # operations.  Pay the route's governed physical-attempt allowance
            # once per immutable operation, not once per capability member.
            instances = (
                len(tuple(job.frozen_bookmark_operations or ()))
                if route["capability_id"] == "meeting.bookmark_label"
                else 1
            )
            allowance = int(policy["total_physical_attempts"])
            child_budget += allowance * instances
            # The bundle has one member per capability, so its normal declaration
            # accounts for the first operation.  Carry each additional frozen
            # bookmark operation as lifecycle budget; the bundle service includes
            # it in its independently recomputed parent total.
            lifecycle_child_budget += allowance * max(0, instances - 1)
        parent = self._broker.parent_run_controller.start(
            principal,
            kind=PARENT_KIND,
            definition_ref=f"meeting:{job.meeting_id}:deferred:{job_id}",
            definition_revision=str(job.work_descriptor_sha256 or ""),
            input_snapshot={
                "schema": "MeetingDeferredIntelQueueParent@1",
                "job_id": job_id,
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
            },
            deadline_at=deadline,
            child_budget=child_budget,
            idempotency_key=str(command_ids["parent_command_id"]),
            _defer_persist=True,
        )
        self._pending[job_id] = _PendingQueueParent(
            parent=parent,
            deadline_at=deadline,
            routes=routes,
            lifecycle_child_budget=lifecycle_child_budget,
            admitted_child_budget=child_budget,
            admitted_policy_fingerprints=tuple(policy_fingerprints),
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
        job_id = str(job.job_id or "")
        pending = self._pending.pop(job_id, None)
        if pending is None:
            raise ValueError("bound queue parent was not prepared")
        try:
            started = self._bundles.start_in_transaction(
                conn,
                queue_service_principal(),
                command_id=str(command_ids["bundle_command_id"]),
                parent_command_id=str(command_ids["parent_command_id"]),
                parent_kind=PARENT_KIND,
                definition_ref=f"meeting:{job.meeting_id}:deferred:{job_id}",
                definition_revision=str(job.work_descriptor_sha256 or ""),
                input_snapshot={
                    "schema": "MeetingDeferredIntelQueueParent@1",
                    "job_id": job_id,
                    "meeting_id": str(job.meeting_id),
                    "work_descriptor_sha256": str(job.work_descriptor_sha256 or ""),
                    "transcript_hash": str(job.transcript_hash),
                    "displaced_work": list(job.displaced_work or ()),
                    "frozen_plugin_members": [dict(member) for member in tuple(job.frozen_plugin_members or ())],
                },
                deadline_at=pending.deadline_at,
                routes=pending.routes,
                lifecycle_child_budget=pending.lifecycle_child_budget,
                parent=pending.parent,
                admitted_child_budget=pending.admitted_child_budget,
                admitted_policy_fingerprints=pending.admitted_policy_fingerprints,
            )
        except Exception:
            # The repository rolls back its writer before calling discard(), which
            # then has the pending shell available for a durable refusal receipt.
            self._pending[job_id] = pending
            raise
        bundle = started["bundle"]
        return {
            "parent_operation_id": str(started["parent"].operation_id),
            "bundle_id": str(bundle["id"]),
            "bundle_sha256": str(bundle["sha256"]),
        }


__all__ = ["MeetingDeferredQueueBinder"]
