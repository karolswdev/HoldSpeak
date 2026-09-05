"""Typed codec adapting the Phase-104 gate as ``decide``'s native record."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from ..db.gate import APPROVED, DENIED
from ..operation_policy import describe_operation, resolve_policy
from .model import Admission, KernelRefused, OperationRequest, forbidden_content

_HASH = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED = frozenset({"proposal_id", "tool", "args_sha256", "args_head", "cwd", "ttl_seconds"})


@dataclass(frozen=True)
class ToolCallAdmission(Admission):
    operation: Mapping[str, Any]
    policy: Mapping[str, Any]


class ToolCallCodec:
    """The one reference type: a redacted tool-call hold in the existing gate."""

    name = "tool.call"
    version = 1
    # Permit the controller's atomic child reservation. The opaque ParentRun
    # context and authenticated parent scope are validated by the broker.
    trusted_child = True

    def __init__(self, gate: Any, mode_loader: Any) -> None:
        self._gate = gate
        self._mode_loader = mode_loader

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        unknown = set(args) - _ALLOWED
        if unknown:
            raise KernelRefused("operation_field_not_allowed", sorted(unknown)[0])
        proposal_id = str(args.get("proposal_id") or request.request_id).strip()
        tool = str(args.get("tool") or "").strip()
        args_hash = str(args.get("args_sha256") or "").lower()
        if not proposal_id or not tool or not _HASH.fullmatch(args_hash):
            raise KernelRefused("tool_call_prerequisite_failed")
        try:
            ttl = float(args.get("ttl_seconds") or 30.0)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("tool_call_ttl_invalid") from exc
        if ttl <= 0:
            raise KernelRefused("tool_call_ttl_invalid")
        material = {
            "name": request.name,
            "version": request.version,
            "target_ref": request.target_ref,
            "placement": request.placement,
            "proposal_id": proposal_id,
            "tool": tool,
            "args_sha256": args_hash,
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        payload_hash = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
        refs = tuple(dict.fromkeys((*request.subject_refs, f"gate:{proposal_id}")))
        return Admission(
            target_ref=request.target_ref or f"gate:{proposal_id}",
            placement=request.placement or "hub:local",
            payload_hash=payload_hash,
            refs=refs,
            head=f"{tool} {str(args.get('args_head') or '')}"[:120],
            ttl_seconds=ttl,
            native_id=proposal_id,
        )

    def authorize(
        self, request: OperationRequest, admission: Admission,
        principal: Any, operation_id: str,
    ) -> ToolCallAdmission:
        args = request.arguments
        descriptor = describe_operation(
            operation_id=operation_id,
            family="tool_gate",
            effect_class="agent/tool_call_hold",
            actor=principal.name,
            destination=str(args.get("cwd") or "unknown_cwd"),
            data_classes=("tool_arguments_redacted",),
            resource_scope=str(args.get("tool") or ""),
            fixed_destination=bool(args.get("cwd")),
            consequence="execute_on_approval",
        )
        operation = descriptor.to_dict()
        operation["kernel_operation_id"] = operation_id
        operation["admitted_envelope_sha256"] = admission.payload_hash
        return ToolCallAdmission(
            **admission.__dict__,
            operation=operation,
            policy=resolve_policy(
                descriptor, mode=self._mode_loader(), source="config"
            ).to_dict(),
        )

    def admit(
        self, request: OperationRequest, admission: ToolCallAdmission,
        principal: Any, operation_id: str,
    ) -> Any:
        args = request.arguments
        return self._gate.propose(
            proposal_id=admission.native_id,
            session_key=principal.identity,
            agent=principal.name,
            tool=str(args.get("tool") or ""),
            args_sha256=str(args.get("args_sha256") or ""),
            args_head=str(args.get("args_head") or ""),
            cwd=str(args.get("cwd") or ""),
            ttl_seconds=admission.ttl_seconds,
            operation=dict(admission.operation),
            policy_snapshot=dict(admission.policy),
        )

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> Any:
        native = APPROVED if decision == "approve" else DENIED
        return self._gate.decide(
            native_id, decision=native, decided_by=principal.identity, reason=reason or None
        )

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        value = self._gate.get(native_id)
        return value.to_dict() if value is not None else None

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        value = self._gate.get(native_id)
        domain_state = value.state if value is not None else "unknown"
        generic = {
            "held": "waiting", "approved": "ended", "denied": "ended",
            "expired": "failed", "invalidated": "failed",
        }.get(domain_state, "unknown")
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": "tool_call_hold",
            "principal": operation["principal_identity"],
            "generic_state": generic,
            "domain_state": domain_state,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }
