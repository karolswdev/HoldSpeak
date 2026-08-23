"""Stored-route C1 deferred queue owner reconstruction."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind
from .intel_child import sha
from .intel_plan import (
    CAPABILITY_DEFERRED_ANALYSIS,
    MeetingIntelRefused,
    SESSION_NOT_ADMITTED,
)

log = get_logger("intel_queue")

PARENT_KIND = "meeting.deferred-intel-job"
QUEUE_SERVICE_IDENTITY = "meeting-intel-queue"
QUEUE_AUTHORITY_BASIS = "meeting-intel-queue:deferred"


def bound_bookmark_label_dispatch() -> Callable[[Any, Mapping[str, Any], Any], Any]:
    """Return the reviewed `.call` leaf for one immutable bookmark operation."""
    def call(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Any:
        if cancellation.is_set():
            return None
        return engine.generate_bookmark_label_with_context(
            local_context=payload["context_material"],
            meeting_summary=payload["summary_material"],
        )
    return call


def bound_auto_title_dispatch() -> Callable[[Any, Mapping[str, Any], Any], Any]:
    """Return the reviewed `.call` leaf for the displaced auto-title member."""
    def call(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Any:
        if cancellation.is_set():
            return None
        return engine.generate_title(payload["transcript_material"])
    return call


def bound_analysis_dispatch() -> Callable[[Any, Mapping[str, Any], Any], Any]:
    """Return the reviewed `.call` leaf for deferred analysis."""
    def call(engine: Any, payload: Mapping[str, Any], cancellation: Any) -> Any:
        if cancellation.is_set():
            return None
        return engine.analyze(payload["transcript_material"], stream=False)
    return call


def queue_service_principal() -> Principal:
    """Return the narrow service identity for one bound queue owner."""
    return Principal(
        PrincipalKind.SERVICE,
        QUEUE_SERVICE_IDENTITY,
        frozenset({(PARENT_KIND, 1), ("inference.invoke", 1), ("inference.cancel", 1)}),
        QUEUE_AUTHORITY_BASIS,
    )


class BoundDeferredIntelJob:
    """Exact stored-route executor for a C1b-bound queue claim.

    This is intentionally separate from :class:`DeferredIntelJob`: constructing
    it only reconstructs the persisted parent and bundle members.  It has no
    Config, planner, host, or legacy-plan entrance, so restart cannot retarget a
    claimed descriptor.
    """

    def __init__(
        self,
        broker: Any,
        *,
        job: Any,
        parent: Any,
        members: Mapping[str, Mapping[str, Any]],
    ) -> None:
        self._broker = broker
        self._job = job
        self._parent = parent
        self._members = {str(key): dict(value) for key, value in members.items()}
        self._principal = queue_service_principal()
        self._closed = False

    @classmethod
    def reconstruct(cls, db: Any, job: Any, *, broker: Any = None) -> "BoundDeferredIntelJob":
        """Rebuild a claimed job from its stored IDs only."""
        from ..kernel.parent_run import ParentRun
        from ..kernel.runtime import _service

        if not all(
            str(getattr(job, field, "") or "").strip()
            for field in ("job_id", "parent_operation_id", "bundle_id", "bundle_sha256")
        ):
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, CAPABILITY_DEFERRED_ANALYSIS)
        broker = broker if broker is not None else _service()
        with db._connection() as conn:
            parent_row = conn.execute(
                """SELECT p.*,o.principal_kind,o.principal_identity
                   FROM kernel_parent_runs p JOIN kernel_operations o ON o.operation_id=p.operation_id
                  WHERE p.operation_id=? AND p.kind=? AND p.state='OPEN'
                    AND o.principal_kind='service' AND o.principal_identity=?""",
                (str(job.parent_operation_id), PARENT_KIND, QUEUE_SERVICE_IDENTITY),
            ).fetchone()
            bundle = conn.execute(
                """SELECT * FROM inference_parent_route_bundles
                   WHERE id=? AND parent_operation_id=? AND sha256=?""",
                (str(job.bundle_id), str(job.parent_operation_id), str(job.bundle_sha256)),
            ).fetchone()
            members = conn.execute(
                """SELECT * FROM inference_parent_route_bundle_members
                   WHERE bundle_id=? ORDER BY ordinal""",
                (str(job.bundle_id),),
            ).fetchall()
        if parent_row is None or bundle is None or not members:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, CAPABILITY_DEFERRED_ANALYSIS)
        parent = ParentRun(
            str(parent_row["operation_id"]),
            str(parent_row["native_id"]),
            broker.parent_run_controller._context(parent_row),
            replayed=True,
        )
        return cls(
            broker,
            job=job,
            parent=parent,
            members={str(row["capability_id"]): dict(row) for row in members},
        )

    @property
    def parent_operation_id(self) -> str:
        return str(self._parent.operation_id)

    def execute(
        self,
        *,
        capability: str,
        operation_suffix: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], Any], Any],
        projection_kind: str,
        projection: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any]]:
        """Stage private material and execute one exact frozen bundle member."""
        if self._closed:
            raise MeetingIntelRefused(SESSION_CLOSED, capability)
        member = self._members.get(capability)
        if member is None:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)
        from ..services.inference_semantic_adapters import adapter_for_frozen_definition

        operation_id = "meeting:deferred:" + sha(
            (str(self._job.job_id), capability, operation_suffix)
        ).split(":", 1)[1]
        command_id = "meeting-bound-route:" + operation_id
        adoption = self._broker.inference_adoption_service
        admitted = adoption.admit_on_frozen_route(
            self._principal,
            command_id=command_id,
            route_plan_id=str(member["route_plan_id"]),
            capability_id=capability,
            operation_id=operation_id,
            payload=dict(material),
            reserved_output_tokens=512,
            parent_operation_id=self.parent_operation_id,
        )
        definition = adoption._frozen_capability_definition(str(member["route_plan_id"]))
        adapter = adapter_for_frozen_definition(definition, call)

        def publish(value: Any, winning: Mapping[str, Any]) -> str:
            # The controller has already elected this child and retained its exact
            # private result reference. Stage against that reference rather than a
            # fresh projection-stage ref, so finalization can verify the receipt.
            from ..services.inference_adoption_service import _sha256

            invocation_id = str(winning["child_invocation_id"])
            stage = self._broker.projection_stager.stage(
                invocation_id,
                projection_kind,
                dict(projection(dict(value))),
                result_sha256=_sha256(value),
                receipt_result_ref=str(winning["result_ref"]),
            )
            return stage.result_ref

        routed = adoption.execute(
            self._principal,
            execution_id=str(admitted["execution"]["id"]),
            adapter=adapter,
            publish=publish,
            parent_context=self._parent.context,
        )
        result = routed.get("result")
        if str(routed.get("outcome")) != "succeeded" or not isinstance(result, Mapping):
            return None, routed
        winning = routed.get("winning_reservation") or {}
        invocation_id = str(winning.get("child_invocation_id") or "")
        published = self._broker.projection_stager.finalize(invocation_id) if invocation_id else None
        return (dict(published) if isinstance(published, Mapping) else None), routed

    def close(self, outcome: str) -> bool:
        """Close the old owner before any reserved successor can be promoted."""
        if self._closed:
            return self._broker.store.receipt(self.parent_operation_id) is not None
        self._closed = True
        try:
            if self._broker.store.receipt(self.parent_operation_id) is None:
                self._broker.parent_run_controller.close(
                    self._parent.context, outcome, principal=self._principal
                )
            return self._broker.store.receipt(self.parent_operation_id) is not None
        except Exception as exc:
            # The queue row remains a durable terminal-pending owner.  Its
            # successor is deliberately still reserved; recovery can retry close
            # but may never bind a second parent in this window.
            log.error("bound deferred intel close failed: %s", type(exc).__name__)
            return False


