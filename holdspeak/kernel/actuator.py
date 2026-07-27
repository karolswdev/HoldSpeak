"""Typed ``actuator.egress`` codec over the existing proposal state machine."""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from ..operation_policy import operation_for_proposal, resolve_policy
from .model import Admission, KernelRefused, OperationRequest, forbidden_content, valid_ref

_ALLOWED = frozenset(
    {
        "proposal_id",
        "meeting_id",
        "origin",
        "window_id",
        "plugin_id",
        "plugin_version",
        "target",
        "action",
        "preview",
        "payload",
        "reversible",
        "required_capabilities",
    }
)
_DATA_CLASSES = ("proposed_content", "connector_metadata")
_PLACEMENT = "node:actuator-local"


@dataclass(frozen=True)
class ActuatorAdmission(Admission):
    values: Mapping[str, Any]
    control_mode: str = "neutral"


class ActuatorCodec:
    """Link one kernel operation to one durable actuator proposal."""

    name = "actuator.egress"
    version = 1

    def __init__(self, repository: Any, mode_loader: Any) -> None:
        self._repository = repository
        self._mode_loader = mode_loader

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        unknown = set(args) - _ALLOWED
        if unknown:
            raise KernelRefused("operation_field_not_allowed", sorted(unknown)[0])
        proposal_id = str(args.get("proposal_id") or "").strip()
        target = str(args.get("target") or "").strip().lower()
        action = str(args.get("action") or "").strip()
        preview = str(args.get("preview") or "").strip()
        plugin_id = str(args.get("plugin_id") or "").strip()
        window_id = str(args.get("window_id") or "").strip()
        origin = str(args.get("origin") or "desk").strip().lower()
        payload = args.get("payload")
        capabilities = args.get("required_capabilities") or []
        expected_ref = f"actuator:{proposal_id}"
        try:
            uuid.UUID(proposal_id)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("actuator_proposal_id_invalid") from exc
        if (
            not all((target, action, preview, plugin_id, window_id))
            or origin not in {"desk", "meeting"}
            or not isinstance(payload, Mapping)
            or not isinstance(args.get("reversible"), bool)
            or not isinstance(capabilities, list)
            or not all(isinstance(item, str) and item.strip() for item in capabilities)
            or request.target_ref != expected_ref
            or not valid_ref(request.target_ref)
            or request.placement != _PLACEMENT
        ):
            raise KernelRefused("actuator_egress_prerequisite_failed")
        meeting_id = args.get("meeting_id")
        if origin == "meeting" and not str(meeting_id or "").strip():
            raise KernelRefused("actuator_meeting_id_required")
        values = {
            "proposal_id": proposal_id,
            "meeting_id": str(meeting_id).strip() if meeting_id is not None else None,
            "origin": origin,
            "window_id": window_id,
            "plugin_id": plugin_id,
            "plugin_version": str(args.get("plugin_version") or "unknown").strip() or "unknown",
            "idempotency_key": request.idempotency_key,
            "target": target,
            "action": action,
            "preview": preview,
            "payload": dict(payload),
            "reversible": bool(args.get("reversible")),
            "required_capabilities": [str(item).strip() for item in capabilities],
        }
        material = {
            "name": request.name,
            "version": request.version,
            "target_ref": request.target_ref,
            "placement": request.placement,
            "values": values,
        }
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True)
        digest = "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
        refs = tuple(
            dict.fromkeys(
                (
                    *request.subject_refs,
                    expected_ref,
                    f"egress:{target}",
                    *(f"data-class:{item}" for item in _DATA_CLASSES),
                )
            )
        )
        return ActuatorAdmission(
            target_ref=expected_ref,
            placement=request.placement,
            payload_hash=digest,
            refs=refs,
            head=f"egress {target} {_DATA_CLASSES[0]}+{_DATA_CLASSES[1]}",
            ttl_seconds=30.0,
            native_id=proposal_id,
            values=values,
        )

    def authorize(
        self, request: OperationRequest, admission: ActuatorAdmission,
        principal: Any, operation_id: str,
    ) -> ActuatorAdmission:
        return ActuatorAdmission(
            **{**admission.__dict__, "control_mode": str(self._mode_loader())}
        )

    def admit(
        self, request: OperationRequest, admission: ActuatorAdmission,
        principal: Any, operation_id: str,
    ) -> Any:
        proposal = self._repository.record_proposal(
            **dict(admission.values),
            control_mode=admission.control_mode,
            policy_source="kernel",
        )
        if proposal.id != admission.native_id:
            raise KernelRefused("actuator_native_link_conflict")
        return proposal

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> Any:
        proposal = self._repository.get_proposal(native_id)
        if proposal is None:
            raise KernelRefused("actuator_proposal_missing")
        target = "approved" if decision == "approve" else "rejected"
        policy_snapshot = None
        if target == "approved":
            captured = dict(proposal.policy_snapshot or {})
            policy = resolve_policy(
                operation_for_proposal(proposal, actor=principal.identity),
                mode=str(captured.get("mode") or "neutral"),
                source=str(captured.get("source") or "kernel"),
                explicit_authorization=True,
            )
            if policy.outcome != "allowed":
                raise KernelRefused("actuator_policy_refused")
            policy_snapshot = policy.to_dict()
        return self._repository.transition_proposal(
            native_id,
            to_status=target,
            actor=principal.identity,
            detail=reason or None,
            policy_snapshot=policy_snapshot,
        )

    def read_native(self, native_id: str) -> dict[str, Any] | None:
        proposal = self._repository.get_proposal(native_id)
        if proposal is None:
            return None
        return {
            "id": proposal.id,
            "status": proposal.status,
            "target": proposal.target,
            "action": proposal.action,
            "preview": proposal.preview,
            "payload": dict(proposal.payload),
            "authority": {
                "payload_hash": proposal.approved_payload_hash,
                "destination": proposal.approved_destination,
                "preview_hash": proposal.approved_preview_hash,
                "renderer": proposal.preview_renderer_version,
                "effect_class": proposal.effect_class,
                "policy_version": proposal.policy_version,
            },
            "result": proposal.result,
            "error": proposal.error,
        }

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        proposal = self._repository.get_proposal(native_id)
        domain_state = proposal.status if proposal is not None else "unknown"
        generic = {
            "proposed": "waiting",
            "approved": "waiting",
            "executed": "ended",
            "rejected": "ended",
            "failed": "failed",
        }.get(domain_state, "unknown")
        return {
            "process_id": f"process:{operation['operation_id']}",
            "kind": self.name,
            "principal": operation["principal_identity"],
            "generic_state": generic,
            "domain_state": domain_state,
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
            "proposal_ref": f"actuator:{native_id}",
        }

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return [
            {
                "receipt_ref": f"actuator-audit:{entry.id}",
                "native_id": native_id,
                "outcome": entry.to_status,
                "actor": entry.actor,
                "from_state": entry.from_status,
                "created_at": entry.created_at,
            }
            for entry in self._repository.list_audit(native_id)
        ]
