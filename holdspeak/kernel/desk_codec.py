"""The desk operations' kernel codec (PHILO-7-02).

One ``OperationSpec`` per desk kernel operation name (the fifteen admitted desk
writes and the two owner-only delegation operations), carved from ``desk.py``
(the kernel density guard). Admission reads the grant by identity
(``desk.by_identity``) and FREEZES it on the operation; the claim re-checks it
by the frozen basis (``desk.by_basis``): the execution cutoff.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import replace
from typing import Any, Mapping

from ..principals import PrincipalKind
from .desk import (
    DELEGATION_OPERATIONS, DESK_GRANT_OPERATIONS, DESK_KERNEL_OPERATIONS, EXPIRED, OWNER_REQUIRED,
    REVOCATION_REASONS, REVOKED, _DESK_PATH, basis, by_basis, by_identity, provenance,
)
from .model import Admission, KernelRefused, OperationRequest, valid_ref


class DeskCodec:
    """One kernel operation spec per desk operation name (and the two delegation operations).

    The payload is fixed at admission (XI.3): the request's ``arguments`` are
    ``{native_id, payload}``, where ``payload`` is the validated operation
    arguments. Only its hash reaches the journal.
    """

    version = 1

    def __init__(self, name: str, database: Any, *, clock: Any = time.time) -> None:
        if name not in DESK_KERNEL_OPERATIONS:
            raise ValueError(f"not a desk kernel operation: {name}")
        self.name = name
        self._database = database
        self._clock = clock

    # -- admission -------------------------------------------------------

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
        if self.name in DELEGATION_OPERATIONS:
            _validate_delegation(self.name, payload)
        if not request.target_ref or not valid_ref(request.target_ref):
            raise KernelRefused("desk_target_invalid")
        material = {"name": request.name, "version": request.version, "target_ref": request.target_ref,
                    "placement": request.placement, "arguments": {"native_id": native_id, "payload": dict(payload)}}
        canonical = json.dumps(material, separators=(",", ":"), sort_keys=True, default=str)
        return Admission(
            target_ref=request.target_ref, placement=request.placement,
            payload_hash="sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            refs=(request.target_ref,), head=self.name, ttl_seconds=30.0, native_id=native_id,
        )

    def authorize(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> Admission:
        if not _DESK_PATH.get():
            raise KernelRefused("desk_operation_service_required", provenance={"target_ref": admission.target_ref})
        if self.name in DELEGATION_OPERATIONS:
            # XI.4: only the owner delegates; an agent can never grant itself.
            if principal.kind is not PrincipalKind.OWNER:
                raise KernelRefused(OWNER_REQUIRED, provenance={"target_ref": admission.target_ref})
            return admission
        if principal.kind is PrincipalKind.OWNER:
            return admission  # the owner's own gesture
        if principal.kind is not PrincipalKind.AGENT:
            raise KernelRefused("declared_capability_required")
        now = self._clock()
        with self._database._connection() as conn:
            code, row = by_identity(conn, principal.identity, self.name, now)
        if code:
            refused = provenance(row, admission.target_ref) if code in {EXPIRED, REVOKED} else {"target_ref": admission.target_ref}
            raise KernelRefused(code, provenance=refused)
        # Frozen at admission (invariant 1): the grant id and its terms hash.
        return replace(admission, authority_basis=basis(str(row["id"]), str(row["terms_sha256"])),
                       delegator_kind=str(row["delegator_kind"]),
                       delegator_identity=str(row["delegator_identity"]))

    def admit(self, request: OperationRequest, admission: Admission, principal: Any, operation_id: str) -> None:
        return None

    def decide(self, native_id: str, decision: str, principal: Any, reason: str = "") -> None:
        return None

    # -- the execution cutoff (invariant 3) -------------------------------

    def validate_claim(self, operation: Mapping[str, Any]) -> None:
        """The grant must be LIVE and unexpired AT THE CLAIM, by the operation's own frozen basis."""
        if self.name not in DESK_GRANT_OPERATIONS or str(operation.get("principal_kind")) != "agent":
            return
        with self._database._connection() as conn:
            code = by_basis(conn, operation, self._clock(), authoritative=True)
        if code:
            raise KernelRefused(code)

    # -- reads -------------------------------------------------------------

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


def _validate_delegation(name: str, payload: Mapping[str, Any]) -> None:
    identity = payload.get("agent_identity")
    if not isinstance(identity, str) or not identity.strip():
        raise KernelRefused("invalid_arguments")
    if name == "delegation.grant":
        expires_at = payload.get("expires_at")
        if expires_at is not None and (isinstance(expires_at, bool) or not isinstance(expires_at, (int, float))):
            raise KernelRefused("invalid_arguments")
        if set(payload) - {"agent_identity", "expires_at", "grant_id"}:
            raise KernelRefused("invalid_arguments")
    else:
        if payload.get("reason") not in REVOCATION_REASONS or set(payload) - {"agent_identity", "reason"}:
            raise KernelRefused("invalid_arguments")


def specs(database: Any, *, clock: Any = None) -> tuple[Any, ...]:
    """One ``OperationSpec`` per desk kernel operation (``kernel/runtime.py`` composes them)."""
    from .model import OperationSpec

    kwargs = {"clock": clock} if clock else {}
    return tuple(
        OperationSpec(name, 1, DeskCodec(name, database, **kwargs), "agent.submit", "propose")
        for name in sorted(DESK_KERNEL_OPERATIONS)
    )
