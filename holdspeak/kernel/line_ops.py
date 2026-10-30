"""The Line's kernel operation ``calls.line.buy_number`` (LINE-3b, LINE design §8).

Buying a Telnyx number spends his money and leaves the device: it waits for
his press (Calls design §5) and it is one kernel operation with one terminal
receipt. The admitted payload names the number and its cost as Telnyx
quoted them (``monthly_cost``, ``upfront_cost``, ``currency``); the journal
keeps only the payload's hash, so the target and the receipt's ``result_ref``
name both: ``phone_number:12125550100/monthly-1.00-USD/upfront-1.00-USD``. The shape is
``phone_ops.py``'s: one ``OperationSpec`` run through the desk's complete
kernel path (``services/desk_kernel.run``); only an OWNER principal is
admitted, so an agent's credential is refused with a receipt.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any, Mapping

from ..principals import PrincipalKind
from .desk import _DESK_PATH
from .model import Admission, KernelRefused, OperationRequest, valid_ref

NAME = "calls.line.buy_number"


class BuyNumberCodec:
    """Admission for ``calls.line.buy_number``: only an OWNER principal (his
    press); any other principal is refused with a receipt."""

    name = NAME
    version = 1

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        native_id = str(args.get("native_id") or "")
        try:
            uuid.UUID(native_id)
        except (TypeError, ValueError) as exc:
            raise KernelRefused("desk_native_id_invalid") from exc
        payload = args.get("payload")
        if not isinstance(payload, Mapping) or set(args) - {"native_id", "payload"}:
            raise KernelRefused("invalid_arguments")
        if not request.target_ref or not valid_ref(request.target_ref):
            raise KernelRefused("desk_target_invalid")
        material = {"name": request.name, "version": request.version, "target_ref": request.target_ref,
                    "placement": request.placement, "arguments": {"native_id": native_id, "payload": dict(payload)}}
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True, default=str)
        return Admission(
            target_ref=request.target_ref, placement=request.placement,
            payload_hash="sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            refs=(request.target_ref,), head=self.name, ttl_seconds=60.0, native_id=native_id,
        )

    def authorize(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> Admission:
        if not _DESK_PATH.get():
            raise KernelRefused("desk_operation_service_required", provenance={"target_ref": admission.target_ref})
        if principal.kind is not PrincipalKind.OWNER:
            raise KernelRefused("owner_principal_required", provenance={"target_ref": admission.target_ref})
        return admission

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    def validate_claim(self, operation: Mapping[str, Any]) -> None:
        return None

    def read_native(self, native_id: str) -> None:
        return None

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "process_id": f"process:{operation['operation_id']}", "kind": self.name,
            "principal": operation["principal_identity"], "generic_state": str(operation["state"]),
            "domain_state": str(operation["state"]), "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }


def specs() -> tuple[Any, ...]:
    """The one ``OperationSpec`` (``kernel/runtime.py`` composes it)."""
    from .model import OperationSpec

    return (OperationSpec(NAME, 1, BuyNumberCodec(), "agent.submit", "propose"),)


__all__ = ["BuyNumberCodec", "NAME", "specs"]
