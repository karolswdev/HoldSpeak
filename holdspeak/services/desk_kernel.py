"""The complete kernel path for the desk writes that FILE or DECIDE (PHILO-7-02).

Article XI as the owner ruled it (D3, R1, R2, R4): one ADMITTED logical
operation is one kernel operation with one terminal receipt, inside the one
call. The path is the existing kernel path, the owner-gesture precedent
(``holdspeak/desktop_typing.py``):

1. **submission** under the transport's principal, with the payload, target
   and arguments fixed at admission (XI.3; ids a create or a supersede would
   mint are minted BEFORE submission);
2. **approval** -- an OWNER principal approves inline (its call IS the owner's
   gesture, XI.4); an AGENT principal is approved by the kernel only under a
   LIVE desk delegation (``holdspeak/kernel/desk.py``); without one the kernel
   refused it at admission with a receipt, and nothing is held;
3. **execution** -- the desk executor claims it (the grant is re-checked AT
   THE CLAIM) and the bound service method writes once;
4. **the terminal receipt** -- ``succeeded``, or ``refused`` naming the rule
   the service refused with, or ``failed``.

The contract refusals of an identifiable consequential attempt (R2 class 3)
and the adapter refusals before ``invoke`` (class 4) leave a refusal receipt
through :func:`refuse`. Nothing here decides what is admitted: the descriptor
(``holdspeak/operations.py``) declares it.
"""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from typing import Any, Callable, Mapping

from ..kernel.desk import DESK_EXECUTOR, DESK_PLACEMENT, desk_path
from ..kernel.desk_broker import journal_receipt
from ..kernel.model import KernelRefused, valid_ref
from ..principals import Principal, PrincipalKind
from .errors import ServiceError

_NODE = Principal(PrincipalKind.NODE, DESK_EXECUTOR)


class DeskKernelRefused(ServiceError):
    """The kernel refused an admitted desk write (at admission, approval or the claim).

    The code is the kernel's rule (``desk_delegation_required``,
    ``desk_delegation_revoked``, ``desk_delegation_expired``,
    ``owner_principal_required`` ...); the context carries the terminal refusal
    receipt. MCP answers ``{error, code, operation_id, receipt}``; the HTTP
    routes answer the code with its status.
    """

    def __init__(self, code: str, operation: str, *, operation_id: str, receipt: Any,
                 status: int | None = None) -> None:
        if status is None:
            status = (400 if code == "invalid_arguments"
                      else 403 if code.startswith("desk_delegation") or "principal" in code
                      or code == "declared_capability_required" else 409)
        super().__init__(
            code, f"The kernel refused {operation}: {code}",
            context={"status": status, "operation_id": operation_id or None, "receipt": receipt},
        )
        self.kernel = {"operation_id": operation_id or None, "receipt": receipt}


def _broker(database: Any) -> Any:
    from ..kernel.runtime import _configure

    return _configure(database)


def target_ref(kind: str, value: Any) -> str:
    """A journal-safe reference; an id the ref grammar cannot carry is named by its hash."""
    text = str(value or "")
    ref = text if ":" in text and kind == "primitive" else f"{kind}:{text}"
    if valid_ref(ref) and text:
        return ref
    return f"{kind if kind != 'primitive' else 'object'}:sha256-{hashlib.sha256(text.encode()).hexdigest()[:40]}"


def _target(name: str, args: Mapping[str, Any]) -> str:
    if name in {"zone.file", "zone.unfile"}:
        return target_ref("primitive", args.get("primitive_id"))
    if name.startswith("decision."):
        return target_ref("decision", args.get("decision_id"))
    if name.startswith("zone."):
        return target_ref("directory", args.get("directory_id"))
    if name.startswith("kb."):
        return target_ref("kb", args.get("kb_id"))
    if name.startswith("note."):
        return target_ref("note", args.get("note_id"))
    if name.startswith("delegation."):
        return target_ref("agent", args.get("agent_identity"))
    return target_ref("desk", name)


def _mint(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Ids the service would mint mid-write are minted BEFORE submission (one immutable payload)."""
    if name == "decision.create" and not args.get("decision_id"):
        args["decision_id"] = f"decision_{uuid.uuid4().hex[:12]}"
    if name == "decision.supersede" and not args.get("successor_id"):
        args["successor_id"] = f"decision_{uuid.uuid4().hex[:12]}"
    if name == "kb.create" and not args.get("kb_id"):
        args["kb_id"] = f"kb_{uuid.uuid4().hex[:12]}"
    return args


def _raw(name: str, native_id: str, target: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "request_schema": 1, "request_id": native_id, "idempotency_key": f"{name}:{native_id}",
        "operation": {"name": name, "version": 1}, "target": {"ref": target},
        "arguments": {"native_id": native_id, "payload": json.loads(json.dumps(dict(payload), default=str))},
        "placement": DESK_PLACEMENT,
    }


def _outcome(exc: BaseException) -> tuple[str, str]:
    """The terminal state and outcome a service refusal names (V.3: the rule by name)."""
    if isinstance(exc, ServiceError):
        # A generic code whose detail IS the rule (``ConflictError("zone_name_taken")``)
        # names the rule, not the family.
        code, detail = str(exc.code), str(exc.detail)
        if code in {"conflict", "validation_error"} and re.fullmatch(r"[a-z][a-z0-9_]{2,63}", detail):
            code = detail
        return "refused", code
    if isinstance(exc, (ValueError, LookupError)):
        return "refused", "invalid_value"
    return "failed", "failed"


def _attach(exc: BaseException, kernel: dict[str, Any]) -> None:
    try:
        exc.kernel = kernel  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover - an exception type that refuses attributes
        return
    if isinstance(exc, ServiceError):
        exc.context.setdefault("operation_id", kernel.get("operation_id"))
        exc.context.setdefault("receipt", kernel.get("receipt"))


def run(
    database: Any, principal: Any, name: str, args: Mapping[str, Any],
    call: Callable[[dict[str, Any]], Any] | None, *,
    effect_for: Callable[[str, dict[str, Any]], Any] | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Submit, approve, claim, execute once, receipt -- all inside this call.

    *call* receives the (minted) arguments and performs the write.
    *effect_for* (the delegation operations only) builds, from the operation
    id and the payload, a local-SQL callback run INSIDE the atomic terminal
    write (T9) instead of *call*.
    """
    broker = _broker(database)
    payload = _mint(name, dict(args))
    native_id = str(uuid.uuid4())
    target = _target(name, payload)
    with desk_path():
        handle = broker.submit(_raw(name, native_id, target, payload), principal)
    operation_id = str(handle.get("operation_id") or "")
    if handle.get("state") == "refused":
        receipt = handle.get("receipt") or broker.store.receipt(operation_id)
        raise DeskKernelRefused(str((receipt or {}).get("outcome") or "refused"), name,
                                operation_id=operation_id, receipt=receipt)
    try:
        broker.decide(operation_id, "approve", int(handle["revision"]), principal)
    except KernelRefused as exc:
        receipt = exc.receipt or broker.store.receipt(operation_id)
        raise DeskKernelRefused(exc.reason, name, operation_id=operation_id, receipt=receipt) from exc
    claimed = broker.claim(_NODE, native_id)
    if not claimed.get("operations"):
        refusal = claimed.get("refusal") or broker.store.receipt(operation_id) or {}
        raise DeskKernelRefused(str(refusal.get("outcome") or "desk_claim_refused"), name,
                                operation_id=operation_id, receipt=refusal)
    revision = int(claimed["operations"][0]["revision"])
    if effect_for is not None:
        return None, _terminal_with_effect(broker, name, operation_id, revision, target,
                                           effect_for(operation_id, payload))
    try:
        result = call(payload)
    except Exception as exc:
        state, outcome = _outcome(exc)
        operation, receipt = broker.store.transition_and_receipt(operation_id, revision, state, outcome)
        journal_receipt(broker.store, operation, outcome)
        _attach(exc, {"operation_id": operation_id, "receipt": receipt})
        raise
    receipt = broker.receipt(operation_id, "succeeded", _result_ref(name, payload, target), _NODE)
    return result, {"operation_id": operation_id, "receipt": receipt}


def _result_ref(name: str, payload: Mapping[str, Any], target: str) -> str:
    if name == "decision.supersede":
        return target_ref("decision", payload.get("successor_id"))
    if name in {"kb.member.add", "kb.member.remove"}:
        return target_ref("primitive", payload.get("resource_ref"))
    if name in {"zone.file", "zone.unfile"}:
        return target_ref("directory", payload.get("directory_id"))
    return target


def _terminal_with_effect(broker: Any, name: str, operation_id: str, revision: int,
                          target: str, effect: Any) -> dict[str, Any]:
    """T9: the grant-table write, the terminal state and the receipt in ONE transaction."""
    from ..kernel.desk import DeskEffectRefused

    result_ref = getattr(effect, "result_ref", "") or target
    try:
        operation, receipt = broker.store.transition_and_receipt(
            operation_id, revision, "succeeded", "succeeded", result_ref, effect=effect,
        )
    except DeskEffectRefused as exc:
        # A domain refusal inside the effect (revoke with no LIVE grant): the
        # effect rolled back with the transaction; the refusal gets its receipt.
        operation, receipt = broker.store.transition_and_receipt(operation_id, revision, "refused", exc.code, strict=True)
        journal_receipt(broker.store, operation, exc.code)
        raise DeskKernelRefused(exc.code, name, operation_id=operation_id, receipt=receipt, status=409) from exc
    journal_receipt(broker.store, operation, "succeeded", result_ref)
    return {"operation_id": operation_id, "receipt": receipt}


def refuse(database: Any, principal: Any, name: str, code: str, args: Any = None) -> dict[str, Any] | None:
    """A refusal receipt for an identifiable consequential attempt (R2 classes 3 and 4).

    Only for an authenticated principal (the protocol boundary: an
    unauthenticated call never reaches here). The named error the transport
    returns is unchanged; the effect is zero.
    """
    kind = getattr(principal, "kind", None)
    if not isinstance(kind, PrincipalKind) or kind is PrincipalKind.NONE:
        return None
    broker = _broker(database)
    operation_id = "op_" + uuid.uuid4().hex
    raw = {"request_schema": 1, "request_id": operation_id, "idempotency_key": operation_id,
           "operation": {"name": name, "version": 1}, "target": {}, "arguments": {}}
    target = _target(name, args) if isinstance(args, Mapping) else ""
    handle = broker._refuse_attempt(raw, principal, operation_id, code, unique=True,
                                    provenance={"target_ref": target} if target else None)
    return {"operation_id": handle.get("operation_id"), "receipt": handle.get("receipt")}
