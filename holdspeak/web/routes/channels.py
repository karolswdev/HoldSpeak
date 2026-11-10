"""PHILO-10-01: the Send over HTTP, produced from ``holdspeak/channel_operations.py``.

Each route is ``OperationRegistry.invoke`` over its declared row
(``operation_router``, receipted): an admitted route answers with its
``operation_id`` and terminal ``receipt``; a refusal of an admitted operation
carries them (``_room_kernel``). The two secret saves keep a handler of their
own: the key or the URL is HELD, taken out of the body before anything
validates or journals the arguments (PHILO-10-03 key custody).

PHILO-10-02 GATE 2 (Codex Astra r2 on #692): every produced call runs off the
event loop (the threadpool), so a CLI send never stalls the hub.
"""
from __future__ import annotations

import inspect
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...channel_operations import CHANNEL_OPERATIONS
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router
from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields

log = get_logger("web.routes.channels")


def _refused(exc: BaseException, name: str) -> JSONResponse:
    if isinstance(exc, OperationRefused):
        return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code, "message": exc.detail,
                             **refusal_fields(exc)}, status_code=400)
    if isinstance(exc, ServiceError):
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        status = (404 if isinstance(exc, NotFound)
                  else int(exc.context.get("status") or (400 if isinstance(exc, ValidationError) else 409)))
        # Named pre-boundary refusals may carry measured facts.  Slack's
        # size fence exposes ``size`` and ``limit`` so the owner knows why
        # the real producer stopped before any byte left.
        context = {k: v for k, v in exc.context.items() if k not in {"status", "operation_id", "receipt"}}
        return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code, "message": exc.detail,
                             **context, **refusal_fields(exc)}, status_code=status)
    return error_500(exc, log, f"{name} failed")


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except Exception as exc:  # a contract refusal is an OperationRefused first (operation_routes.ContractRefusal)
        return _refused(exc, "channel")


def build_channels_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def ops() -> Any:
        return operations.for_context(ctx)

    def held(field: str, *, path: str | None = None) -> Callable[[Any], Callable[..., Any]]:
        """A secret save: ``field`` is taken out of the body and HELD, never an argument."""

        def build(descriptor: Any) -> Callable[..., Any]:
            name = descriptor.name

            async def endpoint(request: Request, **params: str) -> Any:
                principal = getattr(request.state, "principal", UNAUTHENTICATED)
                data, refused = await body_or_refusal(request, ops(), principal, name)
                if refused is not None:
                    return refused
                secret = data.pop(field, None)
                if path is not None and path in data:
                    kernel = ops().refuse(principal, name, "invalid_arguments", data)
                    return JSONResponse({"success": False, "code": "invalid_arguments",
                                         "message": f"Invalid arguments for {name}: {path} comes from the path",
                                         **kernel_fields(kernel)}, status_code=400)
                args = {**data, **params}

                def run() -> Any:
                    result, kernel = ops().invoke_receipted(principal, name, args, held={field: secret})
                    return {**result, **kernel_fields(kernel)}

                try:
                    return JSONResponse(await run_in_threadpool(run))
                except Exception as exc:
                    return _refused(exc, name)

            endpoint.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
                ([inspect.Parameter(path, inspect.Parameter.KEYWORD_ONLY, annotation=str)] if path else [])
                + [inspect.Parameter("request", inspect.Parameter.KEYWORD_ONLY, annotation=Request)])
            endpoint.__name__ = endpoint.__qualname__ = descriptor.handler
            endpoint.__module__ = __name__
            return endpoint

        return build

    mount_router(router, operation_router(
        CHANNEL_OPERATIONS, ops, _answer, module=__name__, receipted=True,
        hand_written={"settings.secret.email_key": held("api_key", path="key_ref"),
                      "settings.secret.slack_webhook": held("webhook_url")},
    ))
    return router
