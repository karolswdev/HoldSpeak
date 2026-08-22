"""The separate executor plane: atomic claim, immutable receipt, reconcile."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..principals import PrincipalKind
from .claim_witness import _install_claim_issuer
from .model import FINAL_STATES, KernelRefused, valid_ref
from .runner_receipt_evidence import (
    RUNNER_RECEIPT_EVIDENCE_REQUIRED,
    consume_runner_receipt_evidence,
)

# HS-131-10 round 2: the process's ONE witness issuer, taken here at import and
# unobtainable afterwards (`_install_claim_issuer` refuses every later call). It
# is a module local rather than an importable mint, so no product module can be
# handed authority by calling something with a string and a mapping.
_issue_claim_witness = _install_claim_issuer()


class ExecutorPlane:
    store: Any
    _clock: Any

    def claim(self, principal: Any, native_id: str = "") -> dict[str, Any]:
        if principal.kind is not PrincipalKind.NODE:
            raise KernelRefused("node_principal_required_to_claim")
        operation = self.store.claim_candidate(principal.identity, native_id)
        if operation is None:
            return {"operations": []}
        # HS-131-10: the CHILD's warrant, kept separate from the ancestor walk's.
        # The walk used to assign through this same name, so a claimed child was
        # handed back its last ANCESTOR's warrant — and everything downstream (the
        # engine's mesh envelope, the dispatch context's authenticated basis) was
        # then bound to the wrong operation.
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
        if not reason:
            parent_id = str(operation.get("parent_operation_id") or "")
            while parent_id:
                parent = self.store.operation(parent_id)
                ancestor = {} if parent is None else parent["warrant"]
                if (
                    parent is None or parent["state"] != "claimed" or bool(parent["warrant_revoked"])
                    or not self.store.valid_warrant(ancestor)
                    or float(ancestor.get("execution_expires_at") or 0) <= self._clock()
                ):
                    reason = "parent_operation_not_live"
                    break
                parent_id = str(parent.get("parent_operation_id") or "")
        if not reason:
            spec = getattr(self, "_specs", {}).get((operation["name"], operation["version"]))
            validate_claim = getattr(getattr(spec, "codec", None), "validate_claim", None)
            if callable(validate_claim):
                try:
                    validate_claim(operation)
                except KernelRefused as exc:
                    reason = exc.reason
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
        # HS-131-10: the ONE witness mint. Everything an adapter factory later
        # demands is proven HERE — the signature, the revocation state, the
        # expiry, the payload binding, and the whole ancestor chain have just been
        # verified for THIS operation — so the dispatch context is minted from an
        # event that happened rather than from arguments a caller can write down.
        claimed["claim_witness"] = _issue_claim_witness(
            operation_id=str(operation["operation_id"]), warrant=warrant
        )
        return {"operations": [claimed]}

    def receipt(
        self, operation_id: str, outcome: str, result_ref: str, principal: Any,
        *, runner_evidence: Any = None,
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
            if runner_evidence is not None and operation["name"] == "inference.invoke" and int(operation["version"]) == 1:
                consume_runner_receipt_evidence(
                    runner_evidence, operation_id=operation_id,
                    outcome=outcome, result_ref=result_ref,
                )
            return existing
        if (
            operation["name"] == "inference.invoke"
            and int(operation["version"]) == 1
            and runner_evidence is None
        ):
            raise KernelRefused(RUNNER_RECEIPT_EVIDENCE_REQUIRED)
        states = {
            "succeeded": "succeeded", "failed": "failed", "cancelled": "cancelled",
            "refused": "refused", "indeterminate": "indeterminate",
        }
        if outcome not in states:
            raise KernelRefused("receipt_outcome_unknown", operation_id=operation_id)
        operation, _ = self.store.transition_and_receipt(
            operation_id, operation["revision"], states[outcome], outcome, result_ref,
            runner_evidence=runner_evidence,
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
