"""Typed ``external.egress`` operation and the HS-107-04 triage.

N01 is a real connector socket boundary and migrates here; its manifest permission
and destination allow-list are admission prerequisites, so ``PermissionGate`` is
no longer a second policy decision. N02 was a dormant default-socket branch: every
production outbound connector injects an HTTP opener, so the ambient branch is
removed rather than called covered. N05 is not a model call despite the old triage
label: it is a scheduler failure-alert webhook and migrates here.

N06/N07 are the initial and compatibility-retry non-streaming calls to a remote
OpenAI-compatible meeting-intel endpoint; N08/N09 are their streaming twins. All
four cross a configured egress boundary and migrate here. Their local llama.cpp
siblings cross no egress boundary; model-invocation treatment is a separate family.
N10/N11 are dictation classification and its compatibility retry; N12 is dictation
rewrite. Their output returns to the hold-key caller, and RFC section 12 permanently
keeps these latency-sensitive computation calls outside kernel ceremony, even when
the selected compute endpoint is remote. N13 sends Cadence data to a Telegram chat
and migrates here with that chat/method as its admitted destination.

Callables and payloads stay in a process-local execution plan. The journal receives
only destination, data-class references, and a payload digest. Admission freezes
those values before the callable can run; every dispatch ends in a terminal receipt.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Mapping, Sequence

from ..principals import Principal, PrincipalKind
from .model import Admission, KernelRefused, OperationRequest, valid_ref

LOCAL_OWNER = Principal(PrincipalKind.OWNER, "local-owner")
LOCAL_NODE = Principal(PrincipalKind.NODE, "local")


class EgressOperationRefused(PermissionError):
    def __init__(self, destination: str, reason: str, *, receipt: Mapping[str, Any] | None = None) -> None:
        self.destination = destination
        self.reason = reason
        self.receipt = dict(receipt or {})
        super().__init__(f"egress to {destination!r} refused: {reason}")


@dataclass(frozen=True)
class EgressPlan:
    native_id: str
    connector_id: str
    destination: str
    data_classes: tuple[str, ...]
    payload_digest: str
    declared_permissions: tuple[str, ...]
    allowed_destinations: tuple[str, ...]
    destination_scope_required: bool
    sender: Callable[..., Any] = field(compare=False, repr=False)
    args: tuple[Any, ...] = field(compare=False, repr=False)
    kwargs: Mapping[str, Any] = field(compare=False, repr=False)


class EgressExecutionStore:
    def __init__(self) -> None:
        self._plans: dict[str, EgressPlan] = {}
        self._operation_ids: dict[str, str] = {}
        self._results: dict[str, dict[str, Any]] = {}

    def bind(
        self,
        *,
        connector_id: str,
        destination: str,
        data_classes: Sequence[str],
        payload_material: Any,
        declared_permissions: Sequence[str],
        allowed_destinations: Sequence[str] | None,
        sender: Callable[..., Any],
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
    ) -> EgressPlan:
        native_id = "egress_" + uuid.uuid4().hex
        try:
            encoded = json.dumps(payload_material, separators=(",", ":"), sort_keys=True, default=str)
        except (TypeError, ValueError):
            encoded = repr(payload_material)
        plan = EgressPlan(
            native_id=native_id,
            connector_id=str(connector_id or "external"),
            destination=str(destination or "").strip().lower(),
            data_classes=tuple(str(item).strip().lower() for item in data_classes),
            payload_digest="sha256:" + hashlib.sha256(encoded.encode()).hexdigest(),
            declared_permissions=tuple(str(item) for item in declared_permissions),
            allowed_destinations=tuple(
                str(item).strip().lower() for item in (allowed_destinations or ())
            ),
            destination_scope_required=allowed_destinations is not None,
            sender=sender,
            args=tuple(args),
            kwargs=MappingProxyType(dict(kwargs)),
        )
        self._plans[native_id] = plan
        return plan

    def plan(self, native_id: str) -> EgressPlan | None:
        return self._plans.get(native_id)

    def admit(self, native_id: str, operation_id: str) -> None:
        self._operation_ids[native_id] = operation_id

    def record(self, native_id: str, **result: Any) -> None:
        plan = self._plans[native_id]
        self._results[native_id] = {
            "native_id": native_id,
            "operation_id": self._operation_ids.get(native_id, ""),
            "connector_id": plan.connector_id,
            "destination": plan.destination,
            "data_classes": list(plan.data_classes),
            **result,
        }
        # Payload-bearing args and the callable never outlive terminal dispatch.
        self._plans.pop(native_id, None)

    def discard(self, native_id: str) -> None:
        self._plans.pop(native_id, None)

    def read(self, native_id: str) -> dict[str, Any] | None:
        result = self._results.get(native_id)
        if result is not None:
            return dict(result)
        plan = self._plans.get(native_id)
        if plan is None:
            return None
        return {
            "native_id": native_id,
            "operation_id": self._operation_ids.get(native_id, ""),
            "connector_id": plan.connector_id,
            "destination": plan.destination,
            "data_classes": list(plan.data_classes),
            "egress_outcome": "not_started",
        }


EGRESS_EXECUTIONS = EgressExecutionStore()


class ExternalEgressCodec:
    name = "external.egress"
    version = 1

    def __init__(self, executions: EgressExecutionStore = EGRESS_EXECUTIONS) -> None:
        self._executions = executions

    def validate(self, request: OperationRequest) -> Admission:
        if set(request.arguments) != {"egress_id"}:
            raise KernelRefused("external_egress_arguments_invalid")
        native_id = str(request.arguments.get("egress_id") or "")
        plan = self._executions.plan(native_id)
        target_ref = f"egress-operation:{native_id}"
        if plan is None or request.target_ref != target_ref or not valid_ref(target_ref):
            raise KernelRefused("external_egress_plan_unknown")
        if request.placement != "node:local" or not plan.destination or not plan.data_classes:
            raise KernelRefused("external_egress_prerequisite_failed")
        if any(not item or ":" in item for item in plan.data_classes):
            raise KernelRefused("external_egress_data_class_invalid")
        if "network:outbound" not in plan.declared_permissions:
            raise KernelRefused(f"external_egress_permission_required:{plan.destination}")
        if plan.destination_scope_required and plan.destination not in plan.allowed_destinations:
            raise KernelRefused(f"external_egress_destination_not_allowed:{plan.destination}")
        material = {
            "name": self.name,
            "version": self.version,
            "connector_id": plan.connector_id,
            "destination": plan.destination,
            "data_classes": plan.data_classes,
            "payload_digest": plan.payload_digest,
            "placement": request.placement,
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        return Admission(
            target_ref=target_ref,
            placement=request.placement,
            payload_hash="sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
            refs=tuple(
                dict.fromkeys(
                    (*request.subject_refs, f"egress:{plan.destination}", *(f"data-class:{item}" for item in plan.data_classes))
                )
            ),
            head=f"egress {plan.destination} {'+'.join(plan.data_classes)}",
            ttl_seconds=30.0,
            native_id=native_id,
        )

    def authorize(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> Admission:
        if principal.kind is not PrincipalKind.OWNER:
            raise KernelRefused("external_egress_owner_authority_required")
        return admission

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        self._executions.admit(admission.native_id, operation_id)

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        return self._executions.read(native_id)

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        result = self._executions.read(native_id)
        if result is None or result.get("egress_outcome") == "not_started":
            return []
        return [{
            "receipt_ref": f"egress-result:{native_id}",
            "native_id": native_id,
            "destination": result["destination"],
            "data_classes": result["data_classes"],
            "outcome": result["egress_outcome"],
        }]

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        result = self._executions.read(native_id) or {}
        outcome = str(result.get("egress_outcome") or "unknown")
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": "unknown" if outcome == "indeterminate" else operation["state"],
            "domain_state": outcome,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }


def run_external_egress(
    *,
    connector_id: str,
    destination: str,
    data_classes: Sequence[str],
    payload_material: Any,
    sender: Callable[..., Any],
    args: Sequence[Any] = (),
    kwargs: Mapping[str, Any] | None = None,
    declared_permissions: Sequence[str] = ("network:outbound",),
    allowed_destinations: Sequence[str] | None = None,
    principal: Principal = LOCAL_OWNER,
    broker: Any = None,
) -> Any:
    if broker is None:
        from .runtime import _service

        broker = _service()
    plan = EGRESS_EXECUTIONS.bind(
        connector_id=connector_id,
        destination=destination,
        data_classes=data_classes,
        payload_material=payload_material,
        declared_permissions=declared_permissions,
        allowed_destinations=allowed_destinations,
        sender=sender,
        args=args,
        kwargs=kwargs or {},
    )
    handle = broker.submit(
        {
            "request_schema": 1,
            "request_id": str(uuid.uuid4()),
            "idempotency_key": f"egress:{plan.native_id}",
            "operation": {"name": "external.egress", "version": 1},
            "subject_refs": [f"connector:{plan.connector_id}"],
            "target": {"ref": f"egress-operation:{plan.native_id}"},
            "arguments": {"egress_id": plan.native_id},
            "placement": "node:local",
        },
        principal,
    )
    if handle["state"] == "refused":
        receipt = handle.get("receipt") or {}
        EGRESS_EXECUTIONS.discard(plan.native_id)
        raise EgressOperationRefused(plan.destination, str(receipt.get("outcome") or "kernel_refused"), receipt=receipt)
    approved = broker.decide(handle["operation_id"], "approve", handle["revision"], principal)
    if not (broker.claim(LOCAL_NODE, plan.native_id).get("operations") or []):
        EGRESS_EXECUTIONS.discard(plan.native_id)
        raise EgressOperationRefused(plan.destination, "external_egress_warrant_refused")
    result_ref = f"egress-result:{plan.native_id}"
    try:
        result = plan.sender(*plan.args, **dict(plan.kwargs))
    except BaseException as exc:
        EGRESS_EXECUTIONS.record(plan.native_id, egress_outcome="indeterminate", error=f"{type(exc).__name__}: {exc}")
        broker.receipt(approved["operation_id"], "indeterminate", result_ref, LOCAL_NODE)
        raise
    EGRESS_EXECUTIONS.record(plan.native_id, egress_outcome="succeeded")
    broker.receipt(approved["operation_id"], "succeeded", result_ref, LOCAL_NODE)
    return result
