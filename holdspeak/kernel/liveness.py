"""Generic operation liveness terminalization."""
from __future__ import annotations

from typing import Any

from .model import KernelRefused


def reap_expired(broker: Any) -> dict[str, Any]:
    """Refuse unclaimed work; mark claimed, silent work indeterminate."""
    now = broker._clock()
    reaped: list[dict[str, str]] = []
    candidates = (
        *broker.store.operations_in_state("awaiting_execution"),
        *broker.store.operations_in_state("claimed"),
    )
    for operation in candidates:
        warrant = operation.get("warrant") or {}
        state = str(operation.get("state") or "")
        deadline_key = (
            "expires_at"
            if state == "awaiting_execution"
            else "execution_expires_at"
        )
        try:
            deadline = float(warrant.get(deadline_key) or 0)
        except (TypeError, ValueError):
            deadline = 0
        if deadline > now:
            continue
        terminal_state = (
            "refused" if state == "awaiting_execution" else "indeterminate"
        )
        reason = (
            "execution_claim_expired"
            if state == "awaiting_execution"
            else "execution_liveness_expired"
        )
        try:
            terminal = broker.store.transition(
                operation["operation_id"],
                int(operation["revision"]),
                terminal_state,
                warrant_revoked=1,
            )
        except KernelRefused as exc:
            if exc.reason == "operation_revision_conflict":
                continue
            raise
        broker._terminal(terminal, terminal_state, reason)
        reaped.append(
            {
                "operation_id": str(operation["operation_id"]),
                "state": terminal_state,
                "outcome": reason,
            }
        )
    return {"reaped": reaped, "count": len(reaped)}


__all__ = ["reap_expired"]
