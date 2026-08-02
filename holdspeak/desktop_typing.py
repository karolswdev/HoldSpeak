"""Owner-gesture adapter for the ``desktop.type_text@1`` operation."""
from __future__ import annotations

import hashlib
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Mapping

from .kernel.admission import parse_request
from .desktop_focus import focused_signature as _focused_signature
from .principals import Principal, PrincipalKind


@dataclass(frozen=True)
class FocusBinding:
    generation: str
    signature: str

    @property
    def ref(self) -> str:
        return f"desktop-input:{self.generation}"


class DesktopTypeRefused(RuntimeError):
    def __init__(self, reason: str, *, operation_id: str = "", receipt: Any = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.operation_id = operation_id
        self.receipt = receipt


class _FocusTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._signature = ""
        self._sequence = 0

    def bind(self) -> FocusBinding:
        signature = _focused_signature()
        with self._lock:
            if signature and signature != self._signature:
                self._signature = signature
                self._sequence += 1
            generation = (
                f"focus-{self._sequence}-{hashlib.sha256(signature.encode()).hexdigest()[:20]}"
                if signature
                else "unresolved"
            )
        return FocusBinding(generation, signature)


_FOCUS = _FocusTracker()
_OWNER = Principal(PrincipalKind.OWNER, "owner-session")
_NODE = Principal(PrincipalKind.NODE, "local-desktop")


def _reason_from_handle(handle: Mapping[str, Any]) -> str:
    receipt = handle.get("receipt") or {}
    return str(receipt.get("outcome") or handle.get("state") or "desktop_type_refused")


def type_text_from_owner_gesture(
    text: str,
    *,
    typer: Any,
    gesture: str,
    target_profile: str | None = None,
    submit: bool = False,
    preview_ref: str = "",
    macro_ref: str = "",
    requested_target: str = "focused",
    delivery_method: str = "desktop",
    subject_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Admit, warrant, execute, and receipt one already-approved owner act."""
    from .kernel import runtime as kernel_runtime

    native_id = str(uuid.uuid4())
    binding = _FOCUS.bind()
    arguments: dict[str, Any] = {
        "text": text,
        "submit": bool(submit),
        "expected_generation": binding.generation,
        "native_id": native_id,
        "gesture": gesture,
        "requested_target": requested_target,
        "delivery_method": delivery_method,
    }
    optional = {
        "target_profile": target_profile,
        "preview_ref": preview_ref,
        "macro_ref": macro_ref,
    }
    arguments.update({key: value for key, value in optional.items() if value})
    raw = {
        "request_schema": 1,
        "request_id": native_id,
        "idempotency_key": f"desktop.type_text:{native_id}",
        "operation": {"name": "desktop.type_text", "version": 1},
        "subject_refs": list(subject_refs),
        "target": {"ref": binding.ref},
        "arguments": arguments,
        "placement": "node:local-desktop",
    }
    broker = kernel_runtime._service()
    codec = broker._specs[("desktop.type_text", 1)].codec
    request = parse_request(raw)
    admission = codec.validate(request)
    handle = broker.submit(raw, _OWNER)
    if handle.get("state") == "refused":
        raise DesktopTypeRefused(
            _reason_from_handle(handle),
            operation_id=str(handle.get("operation_id") or ""),
            receipt=handle.get("receipt"),
        )
    # The owner's admitted gesture drives the compatibility transition inline;
    # there is no second policy evaluation or external decision wait.
    handle = broker.decide(handle["operation_id"], "approve", int(handle["revision"]), _OWNER)
    claimed = broker.claim(_NODE, native_id)
    if not claimed.get("operations"):
        refusal = claimed.get("refusal") or {}
        raise DesktopTypeRefused(
            str(refusal.get("outcome") or "desktop_type_claim_refused"),
            operation_id=handle["operation_id"],
            receipt=refusal,
        )

    reason = ""
    outcome = "succeeded"
    if binding.generation == "unresolved":
        reason = "desktop_focus_unresolved"
        outcome = "refused"
    elif typer is None:
        reason = "desktop_type_driver_unavailable"
        outcome = "refused"
    else:
        try:
            execution = typer.type_text(
                text,
                target_profile=target_profile,
                submit=bool(submit),
                operation_id=handle["operation_id"],
                warrant=claimed["operations"][0]["warrant"],
                request=raw,
                executor=codec.executor,
            )
            if isinstance(execution, Mapping):
                outcome = str(execution.get("state") or "failed")
                reason = str(execution.get("outcome") or outcome)
        except Exception:
            reason = "desktop_type_driver_failed"
            outcome = "failed"

    result_ref = f"desktop-type:{native_id}"
    native_receipt = codec.record_receipt(
        request=request,
        admission=admission,
        operation_id=handle["operation_id"],
        outcome=reason or outcome,
        result_ref=result_ref,
    )
    kernel_receipt = broker.receipt(handle["operation_id"], outcome, result_ref, _NODE)
    result = {
        "operation_id": handle["operation_id"],
        "state": outcome,
        "outcome": reason or outcome,
        "target_ref": binding.ref,
        "receipt": kernel_receipt,
        "native_receipt": native_receipt,
    }
    if outcome != "succeeded":
        raise DesktopTypeRefused(
            reason,
            operation_id=handle["operation_id"],
            receipt=result,
        )
    return result


__all__ = ["DesktopTypeRefused", "FocusBinding", "type_text_from_owner_gesture"]
