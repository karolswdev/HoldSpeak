"""Typed admitted cancellation codec for durable inference invocations."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .inference_shared import digest
from .model import Admission, KernelRefused, OperationRequest, forbidden_content

_CANCEL_FIELDS = frozenset({"invocation_id", "signal_id", "reason"})


class InferenceCancelCodec:
    """A cancellation signal is itself admitted and receipted as an operation."""

    name = "inference.cancel"
    version = 1

    def __init__(self, database: Any, store: Any) -> None:
        self._database = database
        self._store = store

    def validate(self, request: OperationRequest) -> Admission:
        args = request.arguments
        if forbidden_content(args):
            raise KernelRefused("journal_content_forbidden")
        if set(args) - _CANCEL_FIELDS:
            raise KernelRefused("operation_field_not_allowed")
        invocation_id = str(args.get("invocation_id") or "").strip()
        signal_id = str(args.get("signal_id") or "").strip()
        if request.target_ref or request.placement or not invocation_id or not signal_id:
            raise KernelRefused("inference_cancel_prerequisite_failed")
        return Admission(
            target_ref=f"invocation:{invocation_id}", placement="", payload_hash="",
            refs=(f"invocation:{invocation_id}",), head="cancel inference run",
            ttl_seconds=30.0, native_id=signal_id,
        )

    def authorize(
        self, request: OperationRequest, admission: Admission,
        principal: Any, operation_id: str,
    ) -> Admission:
        parent = self._store.operation(request.parent_operation_id)
        if parent is None or parent["native_id"] != request.arguments["invocation_id"]:
            raise KernelRefused("inference_cancel_parent_mismatch")
        return Admission(
            **{
                **admission.__dict__, "placement": parent["placement"],
                "payload_hash": digest(
                    {
                        "name": self.name, "invocation_id": parent["native_id"],
                        "signal_id": admission.native_id, "placement": parent["placement"],
                    }
                ),
            }
        )

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> Any:
        return {"signal_id": admission.native_id}

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> Any:
        return {"signal_id": native_id, "decision": decision}

    def read_native(self, native_id: str) -> dict[str, Any]:
        return {"signal_id": native_id}

    def project_process(self, native_id: str, operation: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "process_id": f"process:{operation['operation_id']}", "kind": self.name,
            "generic_state": operation["state"], "domain_state": operation["state"],
            "target_ref": operation["target_ref"],
            "current_operation_id": operation["operation_id"],
        }

    def project_receipts(self, native_id: str) -> list[dict[str, Any]]:
        return []
