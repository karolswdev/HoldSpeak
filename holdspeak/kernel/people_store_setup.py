"""Content-free, owner-approved creation of the encrypted People sidecar."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from ..principals import Principal, PrincipalKind
from .external_egress import LOCAL_NODE
from .model import Admission, KernelRefused, OperationRequest


class PeopleStoreSetupRefused(PermissionError):
    def __init__(self, reason: str, *, receipt: Mapping[str, Any] | None = None) -> None:
        self.reason = reason
        self.receipt = dict(receipt or {})
        super().__init__(reason)


@dataclass(frozen=True)
class PeopleStoreSetupPlan:
    native_id: str
    initialize: Callable[[], Any] = field(compare=False, repr=False)


class PeopleStoreSetupExecutions:
    """Process-local callable binding; persisted records see random ids only."""

    def __init__(self) -> None:
        self._plans: dict[str, PeopleStoreSetupPlan] = {}
        self._operation_ids: dict[str, str] = {}
        self._outcomes: dict[str, str] = {}

    def bind(self, initialize: Callable[[], Any]) -> PeopleStoreSetupPlan:
        plan = PeopleStoreSetupPlan("people_setup_" + uuid.uuid4().hex, initialize)
        self._plans[plan.native_id] = plan
        return plan

    def plan(self, native_id: str) -> PeopleStoreSetupPlan | None:
        return self._plans.get(native_id)

    def admit(self, native_id: str, operation_id: str) -> None:
        self._operation_ids[native_id] = operation_id

    def record(self, native_id: str, outcome: str) -> None:
        self._outcomes[native_id] = outcome
        self._plans.pop(native_id, None)

    def discard(self, native_id: str) -> None:
        self._plans.pop(native_id, None)

    def read(self, native_id: str) -> dict[str, str] | None:
        if native_id not in self._plans and native_id not in self._outcomes:
            return None
        return {
            "native_id": native_id,
            "operation_id": self._operation_ids.get(native_id, ""),
            "outcome": self._outcomes.get(native_id, "not_started"),
        }


PEOPLE_STORE_SETUP_EXECUTIONS = PeopleStoreSetupExecutions()


class PeopleStoreSetupCodec:
    name = "people.store-setup"
    version = 1

    def __init__(self, executions: PeopleStoreSetupExecutions = PEOPLE_STORE_SETUP_EXECUTIONS) -> None:
        self._executions = executions

    def validate(self, request: OperationRequest) -> Admission:
        if set(request.arguments) != {"setup_id"}:
            raise KernelRefused("people_store_setup_arguments_invalid")
        native_id = str(request.arguments.get("setup_id") or "")
        if self._executions.plan(native_id) is None:
            raise KernelRefused("people_store_setup_plan_unknown")
        if request.target_ref != "people-store:local" or request.placement != "node:local":
            raise KernelRefused("people_store_setup_target_invalid")
        material = {"name": self.name, "version": self.version, "target": "people-store:local", "placement": "node:local", "data_class": "key-custody"}
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        return Admission(
            target_ref="people-store:local", placement="node:local",
            payload_hash="sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
            refs=("people-store", "data-class:key-custody"),
            head="initialize encrypted people store", ttl_seconds=30.0, native_id=native_id,
        )

    def authorize(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> Admission:
        if principal.kind is not PrincipalKind.OWNER:
            raise KernelRefused("people_store_setup_owner_required")
        return admission

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        self._executions.admit(admission.native_id, operation_id)

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def read_native(self, native_id: str) -> dict[str, str] | None:
        return self._executions.read(native_id)

    def project_receipts(self, native_id: str) -> list[dict[str, str]]:
        result = self._executions.read(native_id)
        if result is None or result["outcome"] == "not_started":
            return []
        return [{"receipt_ref": f"people-store-setup:{native_id}", "native_id": native_id, "outcome": result["outcome"]}]

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, str]:
        result = self._executions.read(native_id) or {}
        outcome = str(result.get("outcome") or "unknown")
        return {"process_id": f"process:{operation['operation_id']}", "kind": self.name,
                "principal": operation["principal_identity"],
                "generic_state": "unknown" if outcome == "indeterminate" else str(operation["state"]),
                "domain_state": outcome, "target_ref": operation["target_ref"],
                "current_operation_id": operation["operation_id"]}


def run_people_store_setup(*, initialize: Callable[[], Any], principal: Principal, broker: Any = None) -> Any:
    if broker is None:
        from .runtime import _service
        broker = _service()
    plan = PEOPLE_STORE_SETUP_EXECUTIONS.bind(initialize)
    handle = broker.submit({
        "request_schema": 1, "request_id": str(uuid.uuid4()),
        "idempotency_key": f"people-store-setup:{plan.native_id}",
        "operation": {"name": "people.store-setup", "version": 1},
        "subject_refs": ["people-store"], "target": {"ref": "people-store:local"},
        "arguments": {"setup_id": plan.native_id}, "placement": "node:local",
    }, principal)
    if handle["state"] == "refused":
        PEOPLE_STORE_SETUP_EXECUTIONS.discard(plan.native_id)
        raise PeopleStoreSetupRefused(str((handle.get("receipt") or {}).get("outcome") or "kernel_refused"), receipt=handle.get("receipt"))
    approved = broker.decide(handle["operation_id"], "approve", handle["revision"], principal)
    if not (broker.claim(LOCAL_NODE, plan.native_id).get("operations") or []):
        PEOPLE_STORE_SETUP_EXECUTIONS.discard(plan.native_id)
        raise PeopleStoreSetupRefused("people_store_setup_warrant_refused")
    result_ref = f"people-store-setup:{plan.native_id}"
    try:
        result = plan.initialize()
    except BaseException:
        PEOPLE_STORE_SETUP_EXECUTIONS.record(plan.native_id, "indeterminate")
        broker.receipt(approved["operation_id"], "indeterminate", result_ref, LOCAL_NODE)
        raise
    PEOPLE_STORE_SETUP_EXECUTIONS.record(plan.native_id, "succeeded")
    broker.receipt(approved["operation_id"], "succeeded", result_ref, LOCAL_NODE)
    return result
