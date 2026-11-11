"""First-run setup routes (HS-42-01), produced from ``holdspeak/setup_operations.py``.

Every ``/api/setup`` route (and the model download read, the inference
targets list) is ``OperationRegistry.invoke`` over its declared row. Each
answers in the envelope its hand-written handler had: the Setup window's
admitted presses (found, use, people, the LAN look) with the kernel receipt;
the first-value rows with ``{success: false, error}``; the local-AI rows with
``{code, message, recovery}``.

Kept hand-written: ``POST /api/setup/discover-models`` parses its optional key body and
keeps its 200/400/422 envelope. SetupService owns key custody and endpoint policy.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...services.errors import NotFound, ServiceError, ValidationError
from ...db import get_database, get_observer
from ...setup_operations import SETUP_OPERATIONS, Unavailable
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router
from ._room_kernel import kernel_refusal, refusal_fields, service_refusal

log = get_logger("web.routes.setup")

#: The Setup window's admitted presses and reads: the kernel receipt rides the answer.
_KERNEL = frozenset({"setup.found", "setup.use", "setup.people.add", "setup.lan.scan"})
#: The local-AI rows and the download read: ``{code, message, recovery}``.
_INFERENCE = frozenset({"setup.local_ai.status", "setup.local_ai.start", "setup.local_ai.cancel",
                        "inference.acquisition.get"})


def _refused(exc: OperationRefused) -> JSONResponse:
    status = 403 if exc.code == "owner_required" else 400
    return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                         "message": exc.detail, **refusal_fields(exc)}, status_code=status)


async def _kernel_answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return _refused(exc)
    except ServiceError as exc:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        return service_refusal(exc)
    except Exception as exc:
        return error_500(exc, log, "Setup failed")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return _refused(exc)
    except NotFound as exc:
        return JSONResponse({"success": False, "error": repr(exc.id)}, status_code=404)
    except ValidationError as exc:
        return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
    except ServiceError as exc:
        if exc.code == "owner_required" or exc.context.get("status") == 403:
            return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
        return JSONResponse({"success": False, "error": exc.detail, "code": exc.code},
                            status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Setup failed")


async def _inference_answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return _refused(exc)
    except ServiceError as exc:
        body: dict[str, Any] = {"code": exc.code, "message": exc.detail, "recovery": exc.context.get("recovery")}
        if "current" in exc.context:
            body["current"] = exc.context["current"]
        return JSONResponse(body, status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Local AI failed")


def build_setup_router(ctx: WebContext) -> APIRouter:
    if ctx.setup_service is None:
        raise RuntimeError("SetupService must be supplied at application composition")
    router = APIRouter()

    def ops() -> Any:
        from ...services.profile_service import ProfileService

        return operations.for_context(ctx, local_ai_setup_service=Unavailable,
                                      inference_acquisition_service=Unavailable,
                                      profile_service=lambda: ProfileService(get_database(), observer=get_observer()))

    mount_router(router, operation_router(
        [d for d in SETUP_OPERATIONS if d.name in _KERNEL], ops, _kernel_answer, module=__name__, receipted=True))
    mount_router(router, operation_router(
        [d for d in SETUP_OPERATIONS if d.name in _INFERENCE], ops, _inference_answer, module=__name__))
    mount_router(router, operation_router(
        [d for d in SETUP_OPERATIONS if d.name not in _KERNEL | _INFERENCE], ops, _answer, module=__name__))

    async def api_discover_models(request: Request) -> Any:
        try:
            body = await request.json()
        except Exception:
            body = None
        if not isinstance(body, dict):
            return JSONResponse({"ok": False, "models": [], "detail": "Expected a JSON object."}, status_code=400)
        try:
            status, result = await run_in_threadpool(
                ops().invoke, request.state.principal, "setup.discover_models", body,
            )
            return JSONResponse(result, status_code=status)
        except operations.OperationOwnerRequired as exc:
            return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=403)
        except operations.OperationRefused as exc:
            return JSONResponse({"ok": False, "models": [], "detail": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to discover endpoint models")

    from ...parity_operations import PARITY_OPERATIONS
    mount_router(router, operation_router(
        [d for d in PARITY_OPERATIONS if d.name == "setup.discover_models"], ops, _answer,
        module=__name__, hand_written={"setup.discover_models": lambda d: api_discover_models}))
    return router
