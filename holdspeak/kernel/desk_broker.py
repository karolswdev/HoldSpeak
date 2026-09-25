"""The desk operations' atomic closures at the broker's seams (PHILO-7-02, the lifecycle beat).

A typed concern carved beside ``broker.py`` (the kernel density guard): the
broker keeps one call per seam; the desk behaviour is here. Every closure of an
operation named in ``DESK_KERNEL_OPERATIONS`` couples the end state and its
receipt in ONE transaction (``journal_atomic``), then appends the journal
event (the T-numbers are the beat's inventory):

* T1 ``refuse_attempt`` -- a refusal at admission: the refused row + receipt;
* T2 ``native_failure`` -- a native-admission failure;
* T3 ``approval`` -- the desk delegation recognised at approval, or the
  agent's own operation refused there with a receipt;
* T4 ``reject`` -- an explicit rejection (``decision='reject'`` in the same UPDATE);
* T5 ``claim_refusal`` -- the claim's refusal (the execution cutoff);
* T6 ``recover_on_startup`` -- a dead process's admitting/awaiting operation;
* T7 ``reap`` -- the liveness reaper (``warrant_revoked=1``).
"""
from __future__ import annotations

from typing import Any, Mapping

from ..principals import PrincipalKind
from .desk import DESK_GRANT_OPERATIONS, DESK_KERNEL_OPERATIONS, REQUIRED, by_basis
from .model import KernelRefused

#: The strict seam's two conflict codes: a winner already ended it, or moved it.
STRICT_CONFLICTS = frozenset({"operation_already_terminal", "operation_revision_conflict"})


def is_desk(name: Any) -> bool:
    return str(name) in DESK_KERNEL_OPERATIONS


def journal_receipt(store: Any, operation: Mapping[str, Any], outcome: str, result_ref: str = "") -> None:
    """The receipt's journal event after an atomic write (``_terminal``'s second half)."""
    refs = tuple(filter(None, (operation["target_ref"], result_ref)))
    store.append("operation.receipt", operation["operation_id"], refs=refs, head=outcome)


def refuse_attempt(broker: Any, values: Mapping[str, Any], reason: str) -> dict[str, Any]:
    """T1."""
    operation, receipt = broker.store.create_refused_with_receipt(values, reason)
    broker.store.append("operation.refused", operation["operation_id"], head=reason)
    journal_receipt(broker.store, operation, reason)
    return broker._handle(operation, receipt)


def native_failure(broker: Any, operation: Mapping[str, Any], reason: str) -> dict[str, Any]:
    """T2."""
    ended, receipt = broker.store.transition_and_receipt(
        operation["operation_id"], operation["revision"], "refused", reason, strict=True,
    )
    journal_receipt(broker.store, ended, reason)
    return broker._handle(ended, receipt)


def approval(broker: Any, operation: Mapping[str, Any], principal: Any, expected_revision: int) -> bool:
    """T3: True when the kernel approves under the frozen desk delegation.

    The delegation holds only when the caller IS the operation's own agent
    actor (an explicit bind), the operation is a desk grant operation, and the
    grant its frozen basis names is LIVE and unexpired now (authoritative).
    When that actor's authority fails, its awaiting operation is ended
    ``refused`` with a receipt -- state- and revision-scoped BEFORE anything is
    written; the strict seam decides a race (a winner makes it raise that
    conflict, with no receipt and no event). Any other caller: False, and the
    broker refuses as today, writing nothing.
    """
    if not (
        principal.kind is PrincipalKind.AGENT
        and operation["name"] in DESK_GRANT_OPERATIONS
        and operation["principal_kind"] == "agent"
        and operation["principal_identity"] == principal.identity
    ):
        return False
    with broker.store._connection() as conn:
        code = by_basis(conn, operation, broker._clock(), authoritative=True)
    if not code:
        return True
    if operation["state"] != "awaiting_decision" or operation["revision"] != expected_revision:
        return False
    ended, receipt = broker.store.transition_and_receipt(
        str(operation["operation_id"]), int(expected_revision), "refused", code or REQUIRED, strict=True,
    )
    broker.store.append("operation.refused", ended["operation_id"], head=code)
    journal_receipt(broker.store, ended, code)
    raise KernelRefused(code, operation_id=str(operation["operation_id"]), receipt=receipt)


def reject(broker: Any, operation_id: str, expected_revision: int) -> dict[str, Any]:
    """T4."""
    ended, receipt = broker.store.transition_and_receipt(
        operation_id, expected_revision, "refused", "owner_rejected", strict=True, decision="reject",
    )
    journal_receipt(broker.store, ended, "owner_rejected")
    return broker._handle(ended, receipt)


def claim_refusal(store: Any, operation: Mapping[str, Any], reason: str) -> dict[str, Any]:
    """T5."""
    try:
        ended, receipt = store.transition_and_receipt(
            operation["operation_id"], operation["revision"], "refused", reason, strict=True,
        )
    except KernelRefused:
        return {"operations": [], "refusal": store.receipt(operation["operation_id"])}
    journal_receipt(store, ended, reason)
    return {"operations": [], "refusal": receipt}


def reap(store: Any, operation: Mapping[str, Any], state: str, reason: str) -> bool:
    """T7: False when a winner already moved it (today's ``continue``)."""
    try:
        ended, _receipt = store.transition_and_receipt(
            operation["operation_id"], int(operation["revision"]), state, reason, strict=True, warrant_revoked=1,
        )
    except KernelRefused as exc:
        if exc.reason in STRICT_CONFLICTS:
            return False
        raise
    journal_receipt(store, ended, reason)
    return True


def recover_on_startup(broker: Any) -> int:
    """T6: a desk operation left admitting/awaiting_decision by a dead process ends indeterminate."""
    recovered = 0
    for state in ("admitting", "awaiting_decision"):
        for operation in broker.store.operations_in_state(state):
            if operation["name"] not in DESK_KERNEL_OPERATIONS:
                continue
            try:
                ended, _receipt = broker.store.transition_and_receipt(
                    operation["operation_id"], int(operation["revision"]), "indeterminate",
                    "hub_restart_during_decision", strict=True,
                )
            except KernelRefused:
                continue
            journal_receipt(broker.store, ended, "hub_restart_during_decision")
            recovered += 1
    return recovered
