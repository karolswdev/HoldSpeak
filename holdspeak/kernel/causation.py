"""Causal-chain authority resolution for brokered operations."""
from __future__ import annotations

from typing import Any, Mapping

from ..principals import PrincipalKind
from .model import KernelRefused, OperationRequest


def causality(
    store: Any, clock: Any, request: OperationRequest, principal: Any, operation_id: str,
) -> tuple[str, str]:
    parent_id = request.parent_operation_id
    if not parent_id:
        return "", operation_id
    parent = store.operation(parent_id)
    if parent is None:
        raise KernelRefused("parent_operation_unknown")
    if parent["state"] != "claimed":
        raise KernelRefused("parent_operation_not_running")
    warrant = parent["warrant"]
    if (
        not store.valid_warrant(warrant)
        or bool(parent["warrant_revoked"])
        or float(warrant.get("execution_expires_at") or 0) <= clock()
    ):
        raise KernelRefused("parent_operation_not_live")
    if (
        parent["principal_kind"] != "owner"
        and parent["principal_identity"] != principal.identity
    ):
        raise KernelRefused("parent_operation_scope_required")
    if principal.kind is PrincipalKind.AGENT and not live_owner_parent(
        store, clock, {"parent_operation_id": parent_id}, principal
    ):
        raise KernelRefused("parent_continuation_identity_required")
    return parent_id, str(parent["correlation_id"] or parent_id)


def live_owner_parent(
    store: Any, clock: Any, operation: Mapping[str, Any], principal: Any,
) -> bool:
    parent_id = str(operation.get("parent_operation_id") or "")
    if principal.kind is not PrincipalKind.AGENT or not parent_id:
        return False
    # Egress is a child of the invocation child. Walk that short causal chain
    # back to the live owner operation without manufacturing an owner actor.
    while parent_id:
        parent = store.operation(parent_id)
        if parent is None or parent["state"] != "claimed":
            return False
        warrant = parent["warrant"]
        if (
            not store.valid_warrant(warrant)
            or bool(parent["warrant_revoked"])
            or float(warrant.get("execution_expires_at") or 0) <= clock()
        ):
            return False
        if parent["principal_kind"] == "owner":
            return principal.identity in set(warrant.get("continuation_identities") or ())
        if parent["principal_identity"] != principal.identity:
            return False
        parent_id = str(parent.get("parent_operation_id") or "")
    return False
