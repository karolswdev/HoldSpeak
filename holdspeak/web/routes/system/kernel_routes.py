"""HTTP transport for the kernel's four caller and three executor calls: produced from ``holdspeak/gate_operations.py``.

One route per declared verb, through ``OperationRegistry.invoke``; the paths and
the answers are the ones the hand-written routes had (parked in
``_parked/kernel_routes_20261109.py``). ``GET /api/kernel/read`` stays a
hand-written shell: its query repeats ``refs``, which the producer reads as one.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....gate_operations import KERNEL_OPERATIONS, LIVE_KERNEL_SERVICE
from ....logging_config import get_logger
from ....principals import UNAUTHENTICATED
from ....services.errors import ServiceError
from ...operation_routes import operation_router
from ...runtime_support import error_500

log = get_logger("web.routes.kernel")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    """A refusal is ``{error: <reason>, ...}``: 403 for a principal reason, else its status."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        context = {key: value for key, value in exc.context.items() if key != "status"}
        return JSONResponse({"error": exc.code, **context}, status_code=int(exc.context.get("status") or 409))
    except operations.OperationRefused as exc:
        return JSONResponse({"error": exc.code}, status_code=400)
    except Exception as exc:
        return error_500(exc, log, "The kernel call failed")


def build_kernel_router(ctx: Optional[Any] = None) -> APIRouter:
    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, kernel_service=lambda: LIVE_KERNEL_SERVICE)

    def read(descriptor: Any) -> Callable[..., Awaitable[Any]]:
        async def api_kernel_read(request: Request) -> Any:
            query = request.query_params
            args = {**query, "refs": query.getlist("refs")}
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            return await _answer(lambda: registry().invoke(principal, descriptor.name, args, shape="web"))
        return api_kernel_read

    return operation_router(KERNEL_OPERATIONS, registry, _answer, module=__name__,
                            hand_written={"kernel.read": read})

