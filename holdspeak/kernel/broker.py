"""The small operation broker: admission once, decision once, receipt always."""
from __future__ import annotations

import time
import uuid
from typing import Any, Mapping, Sequence

from ..operation_policy import POLICY_VERSION
from ..principals import PrincipalKind, PrincipalRight
from .admission import parse_request, refusal_values
from .executor import ExecutorPlane
from .journal import JournalStore
from .model import KernelRefused, OperationRequest, OperationSpec


class Broker(ExecutorPlane):
    def __init__(self, store: JournalStore, specs: Sequence[OperationSpec], *, clock: Any = time.time) -> None:
        self.store = store
        self._specs = {(item.name, item.version): item for item in specs}
        self._clock = clock
        self.last_authority_layers: tuple[str, ...] = ()

    def recover_invalidated(self, native_ids: Sequence[str]) -> int:
        recovered = 0
        for native_id in native_ids:
            operation = self.store.operation_for_native(native_id)
            if operation is None or operation["state"] not in {"admitting", "awaiting_decision"}:
                continue
            operation = self.store.transition(
                operation["operation_id"], operation["revision"], "indeterminate"
            )
            self._terminal(operation, "indeterminate", "hub_restart_during_decision")
            recovered += 1
        return recovered

    def read(self, refs: Sequence[str], view: str, consistency: str, principal: Any) -> dict[str, Any]:
        if principal.kind is PrincipalKind.NONE:
            raise KernelRefused("principal_authentication_required")
        if consistency not in {"committed", "eventual"}:
            raise KernelRefused("read_consistency_unknown")
        if view not in {"state", "canonical", "process", "receipt", "full"}:
            raise KernelRefused("read_view_unknown")
        objects: list[dict[str, Any]] = []
        for ref in refs:
            value = str(ref)
            operation = self.store.operation(value.removeprefix("operation:"))
            if operation is None:
                operation = self.store.operation_for_ref(value)
            if operation is None:
                continue
            if principal.kind is PrincipalKind.AGENT and operation["principal_identity"] != principal.identity:
                raise KernelRefused("principal_read_scope_required")
            item = {"ref": f"operation:{operation['operation_id']}", "operation": operation}
            spec = self._specs.get((operation["name"], operation["version"]))
            if spec is not None and view in {"canonical", "full"}:
                item["canonical"] = spec.codec.read_native(operation["native_id"])
            if spec is not None and view in {"process", "full"}:
                item["process"] = spec.codec.project_process(operation["native_id"], operation)
            if view in {"receipt", "full"}:
                item["receipt"] = self.store.receipt(operation["operation_id"])
                if spec is not None:
                    item["native_receipts"] = spec.codec.project_receipts(
                        operation["native_id"]
                    )
            objects.append(item)
        return {"view": view, "consistency": consistency, "objects": objects}

    def submit(self, raw: Any, principal: Any) -> dict[str, Any]:
        operation_id = "op_" + uuid.uuid4().hex
        try:
            request = parse_request(raw)
            spec = self._specs.get((request.name, request.version))
            if spec is None:
                raise KernelRefused("operation_type_unregistered")
            admission, layers = self._admit_authority(request, spec, principal, operation_id)
            parent_id, correlation_id = self._causality(request, principal, operation_id)
            self.last_authority_layers = tuple(layers)
        except KernelRefused as exc:
            return self._refuse_attempt(raw, principal, operation_id, exc.reason)
        except Exception:
            return self._refuse_attempt(
                raw, principal, operation_id, "authority_resolution_failed"
            )

        values = {
            "operation_id": operation_id,
            "request_id": request.request_id,
            "idempotency_key": request.idempotency_key,
            "name": request.name,
            "version": request.version,
            "principal_kind": principal.name,
            "principal_identity": principal.identity,
            "target_ref": admission.target_ref,
            "placement": admission.placement,
            "envelope_sha256": admission.payload_hash,
            "policy_version": POLICY_VERSION,
            "authority_basis": "authenticated_principal+declared_capability+hard_prerequisites+interruption_policy",
            "state": "admitting",
            "native_id": admission.native_id,
            "parent_operation_id": parent_id,
            "correlation_id": correlation_id,
        }
        try:
            operation = self.store.create_operation(values)
        except KernelRefused as exc:
            refused = self._refuse_attempt(
                raw, principal, operation_id, exc.reason, unique=True
            )
            try:
                spec.codec.admit(request, admission, principal, operation_id)
            except Exception:
                pass
            return refused
        if operation["state"] != "admitting":
            spec.codec.admit(request, admission, principal, operation["operation_id"])
            return self._handle(operation)
        self.store.append(
            "operation.admitted", operation["operation_id"], refs=admission.refs,
            head=admission.head, causation_id=parent_id or request.request_id,
        )
        try:
            spec.codec.admit(request, admission, principal, operation["operation_id"])
            operation = self.store.transition(
                operation["operation_id"], operation["revision"], "awaiting_decision"
            )
            self.store.append(
                "operation.awaiting_decision", operation["operation_id"], refs=admission.refs
            )
            return self._handle(operation)
        except Exception as exc:
            reason = getattr(exc, "reason", "native_admission_failed")
            operation = self.store.transition(
                operation["operation_id"], operation["revision"], "refused"
            )
            receipt = self._terminal(operation, "refused", str(reason))
            return self._handle(operation, receipt)

    def decide(
        self, operation_id: str, decision: str, expected_revision: int,
        principal: Any, *, reason: str = "",
    ) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.OWNER or not principal.permits(PrincipalRight.DECIDE):
            raise KernelRefused("owner_principal_required_to_decide", operation_id=operation_id)
        if decision not in {"approve", "reject"}:
            raise KernelRefused("decision_unknown", operation_id=operation_id)
        operation = self.store.operation(operation_id)
        if operation is None:
            raise KernelRefused("operation_unknown", operation_id=operation_id)
        if operation["state"] != "awaiting_decision":
            raise KernelRefused("operation_already_decided", operation_id=operation_id)
        if operation["revision"] != expected_revision:
            raise KernelRefused("operation_revision_conflict", operation_id=operation_id)
        spec = self._specs.get((operation["name"], operation["version"]))
        if spec is None:
            raise KernelRefused("operation_type_unregistered", operation_id=operation_id)
        try:
            spec.codec.decide(operation["native_id"], decision, principal, reason)
        except Exception as exc:
            raise KernelRefused(
                "operation_already_decided", operation_id=operation_id
            ) from exc
        if decision == "reject":
            operation = self.store.transition(
                operation_id, expected_revision, "refused", decision="reject"
            )
            receipt = self._terminal(operation, "refused", "owner_rejected")
            return self._handle(operation, receipt)
        now = self._clock()
        warrant = self.store.sign_warrant(
            {
                "warrant_id": "war_" + uuid.uuid4().hex,
                "operation_id": operation_id,
                "envelope_sha256": operation["envelope_sha256"],
                "target_ref": operation["target_ref"],
                "placement": operation["placement"],
                "policy_version": operation["policy_version"],
                "issued_at": now,
                "expires_at": now + 30.0,
                "uses": 1,
            }
        )
        operation = self.store.transition(
            operation_id, expected_revision, "awaiting_execution",
            decision="approve", warrant_json=warrant,
        )
        self.store.append("operation.approved", operation_id, refs=(operation["target_ref"],))
        return self._handle(operation)

    def events(self, after_cursor: int, filters: Mapping[str, Any], principal: Any) -> dict[str, Any]:
        if principal.kind is PrincipalKind.NONE:
            raise KernelRefused("principal_authentication_required")
        if principal.kind is PrincipalKind.AGENT:
            operation = self.store.operation(str(filters.get("operation_id") or ""))
            if operation is None or operation["principal_identity"] != principal.identity:
                raise KernelRefused("principal_event_scope_required")
        return self.store.events(after_cursor, filters)

    def _admit_authority(
        self, request: OperationRequest, spec: OperationSpec,
        principal: Any, operation_id: str,
    ) -> tuple[Any, list[str]]:
        layers: list[str] = []
        if principal.kind is PrincipalKind.NONE:
            raise KernelRefused("principal_authentication_required")
        layers.append("authenticated_principal")
        required = PrincipalRight(spec.required_capability)
        if principal.kind is PrincipalKind.AGENT and not principal.permits(required):
            raise KernelRefused("declared_capability_required")
        if principal.kind not in {PrincipalKind.OWNER, PrincipalKind.AGENT}:
            raise KernelRefused("declared_capability_required")
        layers.append("declared_capability")
        admission = spec.codec.validate(request)
        layers.append("hard_prerequisites")
        if spec.interruption not in {"allow", "propose", "refuse"}:
            raise KernelRefused("interruption_policy_invalid")
        if spec.interruption == "refuse":
            raise KernelRefused("interruption_policy_refused")
        admission = spec.codec.authorize(request, admission, principal, operation_id)
        layers.append("interruption_policy")
        return admission, layers

    def _causality(
        self, request: OperationRequest, principal: Any, operation_id: str,
    ) -> tuple[str, str]:
        parent_id = request.parent_operation_id
        if not parent_id:
            return "", operation_id
        parent = self.store.operation(parent_id)
        if parent is None:
            raise KernelRefused("parent_operation_unknown")
        if parent["state"] != "claimed":
            raise KernelRefused("parent_operation_not_running")
        if (
            parent["principal_kind"] != "owner"
            and parent["principal_identity"] != principal.identity
        ):
            raise KernelRefused("parent_operation_scope_required")
        return parent_id, str(parent["correlation_id"] or parent_id)

    def _refuse_attempt(
        self, raw: Any, principal: Any, operation_id: str, reason: str, *, unique: bool = False,
    ) -> dict[str, Any]:
        values = refusal_values(raw, principal, operation_id, reason)
        if unique:
            values["idempotency_key"] = operation_id
        operation = self.store.create_operation(values)
        self.store.append("operation.refused", operation["operation_id"], head=reason)
        receipt = self._terminal(operation, "refused", reason)
        return self._handle(operation, receipt)
