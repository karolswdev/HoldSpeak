"""Generic operation liveness terminalization."""
from __future__ import annotations

from typing import Any

from . import desk_broker
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
        if desk_broker.is_desk(operation["name"]):
            # PHILO-7-02 T7: the state, the revoked warrant and the receipt atomically.
            closed = desk_broker.reap(broker.store, operation, terminal_state, reason)
            if not closed:
                continue
        else:
            try:
                terminal = broker.store.transition(
                    operation["operation_id"],
                    int(operation["revision"]),
                    terminal_state,
                    warrant_revoked=1,
                )
            except KernelRefused as exc:
                if exc.reason in {
                    "operation_revision_conflict",
                    "parent_publication_in_progress",
                }:
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


def reap_and_recover_projections(broker: Any) -> dict[str, Any]:
    """The required liveness-before-projection-recovery ordering (carved from ``broker.py``)."""
    parent_recovered = getattr(getattr(broker, "parent_run_controller", None), "reconcile_abandoned", lambda: 0)()
    reaped = broker.reap_expired()
    stager = getattr(broker, "projection_stager", None)
    if stager is None:
        return {"parents": parent_recovered, "reaped": reaped, "projections": None}
    # recover() runs a second, harmless reap immediately before its scan so
    # callers cannot accidentally reverse the durable ordering.
    return {"parents": parent_recovered, "reaped": reaped, "projections": stager.recover()}


__all__ = ["reap_and_recover_projections", "reap_expired"]
