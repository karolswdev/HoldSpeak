"""The HTTP adapters' half of the Room's kernel path (PHILO-9-02).

An ADMITTED Room route answers with its ``operation_id`` and terminal
``receipt`` beside the envelope it always had; a refusal of an admitted
operation carries them on the error (the steward beat, section 6: "HTTP keeps
its status/envelope compatibility while carrying operation_id and receipt on
the error"). A body an admitted route cannot read is its operation's
``invalid_arguments`` refusal WITH a receipt (Phase 7 R2 class 4), never a
FastAPI 422. A conditional route's exempt form re-applies its previous edge
right here, before any service call: a protocol refusal, no receipt.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import Request
from fastapi.responses import JSONResponse

from ...principals import PrincipalKind, PrincipalRight, refusal
from ...services.errors import ServiceError

_ABSENT = object()


def kernel_fields(kernel: Any) -> dict[str, Any]:
    """``{operation_id, receipt}`` of an admitted call (``{}`` when exempt)."""
    if not isinstance(kernel, dict):
        return {}
    return {key: kernel[key] for key in ("operation_id", "receipt") if key in kernel}


def refusal_fields(exc: BaseException) -> dict[str, Any]:
    """The refusal receipt an admitted, refused call carries (``{}`` when none)."""
    return kernel_fields(getattr(exc, "kernel", None))


def kernel_refusal(exc: BaseException) -> Optional[JSONResponse]:
    """A kernel refusal of an admitted Room operation, as its HTTP answer (else ``None``)."""
    from ...services.project_kernel import ProjectKernelRefused

    if not isinstance(exc, ProjectKernelRefused):
        return None
    status = int(exc.context.get("status") or 409)
    return JSONResponse({"success": False, "error": exc.detail, "code": exc.code, "error_code": exc.code,
                         **refusal_fields(exc)}, status_code=status)


def service_refusal(exc: ServiceError, *, default_status: int = 409) -> JSONResponse:
    """A named service refusal, with the receipt when the operation was admitted."""
    context = {k: v for k, v in exc.context.items() if k not in {"status", "operation_id", "receipt"}}
    status = int(exc.context.get("status") or default_status)
    return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code, "message": exc.detail,
                         "error": exc.detail, **context, **refusal_fields(exc)}, status_code=status)


async def body_or_refusal(request: Request, registry: Any, principal: Any, name: str, *,
                          optional: bool = False) -> tuple[Optional[dict[str, Any]], Optional[JSONResponse]]:
    """The JSON object body of an admitted route, or its ``invalid_arguments`` refusal with a receipt.

    ``optional``: an empty body reads as ``{}``.
    """
    raw_bytes = await request.body()
    if not raw_bytes.strip():
        if optional:
            return {}, None
        raw: Any = None
    else:
        try:
            raw = json.loads(raw_bytes)
        except ValueError:
            raw = _ABSENT
    if isinstance(raw, dict):
        return raw, None
    kernel = refuse_identifiable(registry, principal, name, "invalid_arguments")
    return None, JSONResponse({"success": False, "error": "the body must be a JSON object", "code": "invalid_arguments",
                               "error_code": "invalid_arguments", **kernel_fields(kernel)}, status_code=400)


def refuse_identifiable(registry: Any, principal: Any, name: str, code: str) -> Optional[dict[str, Any]]:
    """The refusal receipt of an identifiable admitted (or conditional) Room operation.

    The beat, section 6: a conditional route's malformed arguments that
    prevent proving the exempt form are recorded ``invalid_arguments`` too.
    """
    from ...services import project_kernel

    database = getattr(registry.target(name), "_db", None)
    if database is None:
        from ...db import get_database

        database = get_database()
    return project_kernel.refuse(database, principal, name, code, None)


def exempt_form_right(principal: Any) -> Optional[JSONResponse]:
    """The exempt form of a conditional route keeps its previous edge right (OWNER): a protocol refusal."""
    if getattr(principal, "kind", None) is PrincipalKind.OWNER:
        return None
    status = 401 if getattr(principal, "kind", None) is PrincipalKind.NONE else 403
    return JSONResponse(refusal(principal, PrincipalRight.OWNER), status_code=status)
