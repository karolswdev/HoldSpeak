"""The separate executor plane: atomic claim, immutable receipt, reconcile."""
from __future__ import annotations

from typing import Any, Mapping

from ..principals import PrincipalKind
from .model import FINAL_STATES, KernelRefused, valid_ref


class ExecutorPlane:
    store: Any
    _clock: Any

    def claim(self, principal: Any) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.NODE:
            raise KernelRefused("node_principal_required_to_claim")
        operation = self.store.claim_candidate(principal.identity)
        if operation is None:
            return {"operations": []}
        warrant = operation["warrant"]
        reason = ""
        if not self.store.valid_warrant(warrant):
            reason = "warrant_signature_invalid"
        elif bool(operation["warrant_revoked"]):
            reason = "warrant_revoked"
        elif float(warrant.get("expires_at") or 0) <= self._clock():
            reason = "warrant_expired"
        elif warrant.get("envelope_sha256") != operation["envelope_sha256"]:
            reason = "warrant_payload_mismatch"
        if reason:
            operation = self.store.transition(
                operation["operation_id"], operation["revision"], "refused"
            )
            receipt = self._terminal(operation, "refused", reason)
            return {"operations": [], "refusal": receipt}
        self.store.append(
            "operation.claimed", operation["operation_id"], refs=(operation["target_ref"],)
        )
        claimed = self._handle(operation)
        claimed["warrant"] = warrant
        return {"operations": [claimed]}

    def receipt(
        self, operation_id: str, outcome: str, result_ref: str, principal: Any,
    ) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.NODE:
            raise KernelRefused("node_principal_required_to_receipt")
        if not valid_ref(result_ref):
            raise KernelRefused("result_ref_invalid", operation_id=operation_id)
        operation = self.store.operation(operation_id)
        if operation is None:
            raise KernelRefused("operation_unknown", operation_id=operation_id)
        if operation["claimed_by"] != principal.identity:
            raise KernelRefused("executor_claim_required", operation_id=operation_id)
        existing = self.store.receipt(operation_id)
        if existing is not None:
            if existing["outcome"] != outcome or existing["result_ref"] != result_ref:
                raise KernelRefused("receipt_immutable", operation_id=operation_id)
            return existing
        states = {
            "succeeded": "succeeded", "failed": "failed",
            "refused": "refused", "indeterminate": "indeterminate",
        }
        if outcome not in states:
            raise KernelRefused("receipt_outcome_unknown", operation_id=operation_id)
        operation = self.store.transition(
            operation_id, operation["revision"], states[outcome]
        )
        return self._terminal(operation, states[outcome], outcome, result_ref)

    def reconcile(self, operation_id: str, principal: Any) -> dict[str, Any]:
        if principal.kind is not PrincipalKind.NODE:
            raise KernelRefused("node_principal_required_to_reconcile")
        operation = self.store.operation(operation_id)
        if operation is None:
            raise KernelRefused("operation_unknown", operation_id=operation_id)
        reconciliation = "receipt_missing"
        if operation["state"] in FINAL_STATES:
            reconciliation = "terminal"
        return {
            "operation": operation,
            "receipt": self.store.receipt(operation_id),
            "reconcile": reconciliation,
        }

    def _terminal(
        self, operation: Mapping[str, Any], state: str, outcome: str,
        result_ref: str = "",
    ) -> dict[str, Any]:
        receipt = self.store.add_receipt(
            operation["operation_id"], state, outcome, result_ref
        )
        refs = tuple(filter(None, (operation["target_ref"], result_ref)))
        self.store.append(
            "operation.receipt", operation["operation_id"], refs=refs, head=outcome
        )
        return receipt

    @staticmethod
    def _handle(
        operation: Mapping[str, Any], receipt: Any = None,
    ) -> dict[str, Any]:
        result = {
            "operation_id": operation.get("operation_id"),
            "state": operation.get("state"),
            "revision": operation.get("revision"),
            "target_ref": operation.get("target_ref"),
        }
        if receipt is not None:
            result["receipt"] = receipt
        return result
