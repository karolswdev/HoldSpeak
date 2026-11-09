"""The deferred Meeting queue's job owner: one parent per job, each model call through the engine door."""

from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any, Callable, Mapping

from ..logging_config import get_logger
from ..principals import Principal, PrincipalKind


def sha(value: Any) -> str:
    return "sha256:" + hashlib.sha256(str(value).encode("utf-8", "replace")).hexdigest()

from .intel_plan import (
    CAPABILITY_DEFERRED_ANALYSIS,
    MeetingIntelRefused,
    SESSION_CLOSED,
    SESSION_NOT_ADMITTED,
)

log = get_logger("intel_queue")


# A direct runner helper is retired, but the bound executor still owns the
# provider-content boundary.  Never allow a provider exception or a returned
# error result to become a journal error string.
PROVIDER_ERROR_RESULT = "provider_error_result"


class BoundMeetingProviderFailure(RuntimeError):
    """Content-free provider failure emitted only by the C1 bound executor."""

    def __init__(
        self, contract: str, exc: BaseException | None = None, *, reason: str = ""
    ) -> None:
        short = reason or (type(exc).__name__ if exc is not None else PROVIDER_ERROR_RESULT)
        super().__init__(f"{contract}:{short}")
        self.contract = contract
        self.reason = short


def _provider_error_of(result: Any) -> str:
    if result is None or isinstance(result, (str, bytes, Mapping)):
        return ""
    return str(getattr(result, "error", "") or "")


class BoundMeetingAdapter:
    """Sanitize one bound Meeting provider call without swallowing kernel control."""

    connector_id = "inference-provider"

    def __init__(
        self, contract: str, call: Callable[[Any, Mapping[str, Any], Any], Any]
    ) -> None:
        self._contract = contract
        self._call = call

    def dispatch(
        self, engine: Any, payload: Mapping[str, Any], cancellation: Any
    ) -> Any:
        from ..kernel.model import KernelRefused
        from ..kernel.provider_signals import CONTROL_SIGNALS

        try:
            result = self._call(engine, payload, cancellation)
        except CONTROL_SIGNALS:
            raise
        except (KernelRefused, MeetingIntelRefused):
            raise
        except BaseException as exc:
            raise BoundMeetingProviderFailure(self._contract, exc) from None
        if _provider_error_of(result):
            raise BoundMeetingProviderFailure(
                self._contract, reason=PROVIDER_ERROR_RESULT
            )
        return result

    def cancel(self) -> str:
        return "cancelled"


def _receipt(sent: Any) -> dict[str, Any]:
    """The door's attempts as the queue's route receipt: each attempt's
    number is its ``route_leg_ordinal`` (attempt 1 is the first engine of
    the chain, attempt 2 the next), so the public receipt maps it to the
    disclosed host."""
    return {"attempts": [
        {"route_leg_ordinal": number, "send_phase": phase, "outcome": outcome, "child_operation_id": operation_id}
        for number, (_revision, phase, operation_id, outcome) in enumerate(tuple(sent or ()), 1)
    ]}


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
        # The project's memory, when the job staged any (intel_queue.py).  An
        # engine is asked for the extra argument only when there is memory.
        memory = str(payload.get("memory_material") or "")
        extra = {"memory_context": memory} if memory else {}
        return engine.analyze(payload["transcript_material"], stream=False, **extra)
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

    Constructing it only reconstructs the persisted parent and bundle members.
    It has no
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
        deadline_at: float = 0.0,
    ) -> None:
        self._broker = broker
        #: The parent's deadline: no model call of this job runs past it.
        self._deadline_at = float(deadline_at or 0.0)
        self._job = job
        self._parent = parent
        self._members = {str(key): dict(value) for key, value in members.items()}
        self._principal = queue_service_principal()
        self._closed = False
        self.memory_sent: Any = None  # the memory staged on the last execute
        # The attempts of the last model call: the receipt a later
        # exception still writes (``durable_route_receipt``).
        self._last_receipt: Mapping[str, Any] | None = None

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
            deadline_at=float(parent_row["deadline_at"] or 0.0),
        )

    @property
    def parent_operation_id(self) -> str:
        return str(self._parent.operation_id)

    def egress_model_host(self, db: Any, capability: str) -> str:
        """The host this job's model call egresses to: the engine the door
        picks for ``capability`` (HS-200-42, Article III: the row states the
        host the call goes to, not the enqueue-time estimate). An adopted
        mesh node wins, else the endpoint's bare host, else the boundary."""
        from ..services import engine_door

        try:
            engine = engine_door.engine_for(self._broker, capability)
            row = db.deployment_revisions.get(engine.revision)
        except Exception:
            return ""
        if row is None:
            return ""
        from ..intel.providers import endpoint_host

        node = str(getattr(row, "node", "") or "").strip()
        if node:
            return node
        host = endpoint_host(getattr(row, "endpoint", ""))
        if host:
            return host
        return str(getattr(row, "boundary", "") or "").strip() or "local"

    def require_frozen_plugin_member(self, frozen: Mapping[str, Any]) -> Mapping[str, Any]:
        """Prove descriptor, bundle member and the registered capability say
        the same plugin, before any model call. A host or registry drift is a
        queue refusal, never a call under an almost-matching capability."""
        capability = str(frozen.get("capability_id") or "").strip()
        plugin_id = str(frozen.get("plugin_id") or "").strip()
        revision = str(frozen.get("plugin_definition_revision") or "").strip()
        if capability != f"meeting.plugin.{plugin_id}" or not plugin_id or not revision:
            raise MeetingIntelRefused("frozen_plugin_descriptor_invalid", capability)
        if capability not in self._members:
            raise MeetingIntelRefused("frozen_plugin_bundle_member_missing", capability)
        try:
            definition = self._registry().require(capability).canonical_dict()
        except Exception:
            raise MeetingIntelRefused("frozen_plugin_capability_drift", capability) from None
        if (
            int(definition.get("revision") or 0) != int(frozen.get("capability_revision") or 0)
            or str(definition.get("schema_sha256") or "") != str(frozen.get("schema_sha256") or "")
            or str(definition.get("plugin_id") or "") != plugin_id
            or str(definition.get("plugin_definition_revision") or "") != revision
            or dict(definition.get("output_schema") or {}) != dict(frozen.get("output_schema") or {})
        ):
            raise MeetingIntelRefused("frozen_plugin_capability_drift", capability)
        return definition

    def _registry(self) -> Any:
        from ..inference_capabilities import process_inference_capability_registry

        return getattr(self._broker, "inference_capability_registry", None) or process_inference_capability_registry()

    def durable_route_receipt(self) -> Mapping[str, Any] | None:
        """The attempts of the last model call, for a receipt written after
        an exception (``None`` when no call was sent)."""
        return self._last_receipt

    def execute(
        self,
        *,
        capability: str,
        operation_suffix: str,
        material: Mapping[str, Any],
        call: Callable[[Any, Mapping[str, Any], Any], Any],
        projection_kind: str,
        projection: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        executor_held: Callable[[], bool] | None = None,
        memory: Any = None,
        memory_heading: str = "MEMORY",
    ) -> tuple[Mapping[str, Any] | None, Mapping[str, Any]]:
        """Run one member of this job through the engine door, under the
        job's parent, and publish its projection.

        ``memory`` (a ``MemoryContext``) is staged as ``memory_material`` and
        ``memory_refs``, cut to what the engine leaves after the material:
        memory never makes a job that fit fail. Returns ``(published,
        routed)``; ``routed`` is ``{outcome, receipt}`` and the receipt's
        attempts carry the door's attempt number as ``route_leg_ordinal``.
        """
        if self._closed:
            raise MeetingIntelRefused(SESSION_CLOSED, capability)
        if capability not in self._members:
            raise MeetingIntelRefused(SESSION_NOT_ADMITTED, capability)
        from ..kernel.model import KernelRefused
        from ..services import engine_door
        from ..services.inference_semantic_adapters import adapter_for

        if executor_held is not None and not executor_held():
            return None, {"outcome": "lease_lost"}
        try:
            engine = engine_door.engine_for(self._broker, capability)
        except engine_door.EngineDoorError:
            return None, {"outcome": "refused", "receipt": {"attempts": []}}
        if memory:
            from ..services.memory_grounding import fit_memory

            def with_memory(candidate: Any) -> dict[str, Any]:
                staged = dict(material)
                if candidate:
                    staged["memory_material"] = candidate.prompt_block(memory_heading)
                    staged["memory_refs"] = candidate.refs
                return staged

            sent = fit_memory(memory, lambda candidate: engine_door.room(
                self._broker, engine, with_memory(candidate), reserved_output_tokens=512,
            ) >= 0)
            # What was staged, for the run receipt's "Looked at".
            self.memory_sent = sent
            material = with_memory(sent)

        def require_current_executor(_operation: str, _child: str, _attempt: int) -> None:
            if executor_held is not None and not executor_held():
                raise KernelRefused("bound_executor_lease_lost")

        run_id = "meetingdeferred_" + sha(
            (str(self._job.job_id), capability, operation_suffix, uuid.uuid4().hex)
        ).split(":", 1)[1][:40]
        adapter = adapter_for(capability, BoundMeetingAdapter(capability, call).dispatch, registry=self._registry())
        try:
            answer = engine_door.run(
                self._broker, self._principal, capability, dict(material), engine=engine,
                adapter=adapter, invocation_id=run_id,
                deadline=max(1.0, self._deadline_at - time.time()) if self._deadline_at else engine_door.DEFAULT_DEADLINE_SECONDS,
                stage=(projection_kind, lambda value: dict(projection(dict(value)))),
                parent_context=self._parent.context,
                before_physical_dispatch=require_current_executor,
            )
        except engine_door.EngineDoorError as exc:
            self._last_receipt = _receipt(exc.sent)
            return None, {"outcome": exc.outcome or "failed", "receipt": self._last_receipt}
        except Exception as exc:
            # A publication that failed after the call: the receipt still
            # names the engine that was contacted.
            self._last_receipt = _receipt(getattr(exc, "sent", ()))
            raise
        self._last_receipt = _receipt(answer.sent)
        published = answer.published
        return (dict(published) if isinstance(published, Mapping) else None), {
            "outcome": "succeeded", "receipt": self._last_receipt, "result": answer.result,
        }

    def close(self, outcome: str, *, executor_lease: Mapping[str, Any] | None = None) -> bool:
        """Close the old owner before any reserved successor can be promoted.

        A live queue worker supplies its opaque executor bearer.  Parent receipt
        election then verifies it in the same SQLite writer transaction; orphan
        recovery deliberately has no bearer because its job is already terminal.
        """
        if self._closed:
            return self._broker.store.receipt(self.parent_operation_id) is not None
        self._closed = True
        try:
            if self._broker.store.receipt(self.parent_operation_id) is None:
                self._broker.parent_run_controller.close(
                    self._parent.context, outcome, principal=self._principal,
                    executor_lease=executor_lease,
                )
            return self._broker.store.receipt(self.parent_operation_id) is not None
        except Exception as exc:
            # The queue row remains a durable terminal-pending owner.  Its
            # successor is deliberately still reserved; recovery can retry close
            # but may never bind a second parent in this window.
            log.error("bound deferred intel close failed: %s", type(exc).__name__)
            return False
