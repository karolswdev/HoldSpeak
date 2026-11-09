"""Routes produced from declared operations, with one error envelope (2026-11-09, ops/projects).

A route module names its descriptors and the bare builds a partially wired
context falls back to; ``produced`` mounts one route per descriptor through
``operation_router`` (``OperationRegistry.invoke``, off the event loop). The
envelope keeps the words the hand-written handlers answered with:

- a contract refusal: 400 ``{error, code}``; ``owner_required``: 403;
- ``NotFound``: 404 ``{error}`` (``not_found`` may name the words);
- ``ValidationError``: 400; ``ConflictError``: 409; any other
  ``ServiceError``: its context's ``status`` (else 400), with ``error_code``;
- anything else: 500 through ``error_500`` (redacted).
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...services.errors import ConflictError, NotFound, ServiceError
from ..operation_routes import ContractRefusal, operation_router
from ..runtime_support import error_500
from ._mount import mount_router

Answer = Callable[..., Any]


def _body(exc: ServiceError) -> dict[str, Any]:
    body = {key: value for key, value in exc.context.items() if key != "status"}
    body.setdefault("error", exc.detail)
    body.setdefault("error_code", exc.code)
    return body


def envelope(log: Any, what: str, *, not_found: Optional[Callable[[NotFound], dict[str, Any]]] = None,
             statuses: Mapping[type, int] | None = None,
             shape: Optional[Callable[[ServiceError], dict[str, Any]]] = None) -> Answer:
    """The answer of a produced route: the result as JSON, or the error as the module answered it.

    ``what``: the 500 log words (``"Failed to read the brief"``). ``statuses``:
    an error class -> its status, checked first (a brief's refusal is 409; a
    ValueError is 400). ``shape``: the body of a service error (default
    ``{error, error_code, **context}``)."""
    body = shape or _body

    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except ContractRefusal as exc:
            return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=400)
        except operations.OperationOwnerRequired as exc:
            return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
        except Exception as exc:
            for kind, code in (statuses or {}).items():
                if isinstance(exc, kind):
                    return JSONResponse(body(exc) if isinstance(exc, ServiceError) else {"error": str(exc)},
                                        status_code=code)
            if not isinstance(exc, ServiceError):
                return error_500(exc, log, what)
            if isinstance(exc, NotFound):
                return JSONResponse(not_found(exc) if not_found else {"error": str(exc)}, status_code=404)
            default = 409 if isinstance(exc, ConflictError) else 400
            return JSONResponse(body(exc), status_code=int(exc.context.get("status") or default))

    return answer


def produced(ctx: Any, descriptors: Iterable[Any], answer: Answer | Mapping[str, Answer], *, module: str,
             hand_written: Mapping[str, Callable[[Any], Callable[..., Any]]] | None = None,
             **fallbacks: Callable[[], Any]) -> APIRouter:
    """One route per descriptor with ``http``, in order. ``answer``: one envelope, or one per operation name.

    ``fallbacks``: service field -> bare build, for a context the hub did not
    compose (``operations.for_context``)."""

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, **fallbacks)

    router = APIRouter()
    for descriptor in descriptors:
        if descriptor.http is None:
            continue
        chosen = answer[descriptor.name] if isinstance(answer, Mapping) else answer
        mount_router(router, operation_router([descriptor], registry, chosen, module=module,
                                              hand_written=hand_written))
    return router


__all__ = ["envelope", "produced"]
