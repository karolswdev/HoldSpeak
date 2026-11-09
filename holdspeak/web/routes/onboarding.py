"""Onboarding routes: detect what the owner already has; one "Use it" each.

Produced from ``holdspeak/onboarding_operations.py`` (2026-11-09): every route
but the two agent-binding presses is ``OperationRegistry.invoke`` over its
declared row. The detections and plain presses answer ``{code, message}`` on a
refusal; the admitted presses (the Calendars privacy pane, People access)
answer with their ``operation_id`` and terminal ``receipt``.

Kept hand-written: ``POST /api/onboarding/agents/use`` and ``/stop``
(``agent_hooks.install`` / ``agent_hooks.remove``). The hub binds the agent's
own settings file into the admitted arguments before admission, so the
receipt names the file it wrote; the produced route has no such step.
``POST /api/onboarding/agents/use-all`` had no client and is parked
(the one ``/use`` press takes ``agents`` too).
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...onboarding_operations import CALENDAR_OPEN_SETTINGS, ONBOARDING_ROUTE_OPERATIONS, PEOPLE_ACCESS_SET
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router
from ._room_kernel import body_or_refusal, kernel_fields, kernel_refusal, refusal_fields, service_refusal

log = get_logger("web.routes.onboarding")


def _error(exc: ServiceError) -> JSONResponse:
    if isinstance(exc, NotFound):
        status = 404
    elif isinstance(exc, ValidationError):
        status = 400
    elif isinstance(exc, ConflictError):
        status = 409
    else:
        status = int(exc.context.get("status") or 400)
    return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=status)


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"code": exc.code, "message": exc.detail},
                            status_code=403 if exc.code == "owner_required" else 400)
    except ServiceError as exc:
        return _error(exc)
    except Exception as exc:
        return error_500(exc, log, "Onboarding failed")


async def _kernel_answer(fn: Callable[[], Any], *, status: int = 200) -> Any:
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                             "message": exc.detail, **refusal_fields(exc)},
                            status_code=403 if exc.code == "owner_required" else 400)
    except ServiceError as exc:
        if (refused := kernel_refusal(exc)) is not None:
            return refused
        return service_refusal(exc)
    except Exception as exc:
        return error_500(exc, log, "Onboarding failed")


def build_onboarding_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["onboarding"])

    def ops() -> Any:
        return operations.for_context(ctx)

    mount_router(router, operation_router(ONBOARDING_ROUTE_OPERATIONS, ops, _answer, module=__name__))
    mount_router(router, operation_router((CALENDAR_OPEN_SETTINGS, PEOPLE_ACCESS_SET), ops, _kernel_answer,
                                          module=__name__, receipted=True))

    @router.post("/api/onboarding/agents/use")
    async def onboarding_agents_use(request: Request) -> Any:
        # The agents row is one owner's press. Keep the old one-agent body for
        # direct callers; the same admitted operation accepts the discovered
        # agent list and preserves every per-agent outcome.
        name = "agent_hooks.install"
        registry = operations.for_context(ctx)
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        data, refused = await body_or_refusal(request, registry, principal, name)
        if refused is not None:
            return refused
        if "settings_path" in data or "settings_paths" in data:
            # The hub binds the file; a client never names it.
            kernel = registry.refuse(principal, name, "invalid_arguments", data)
            return JSONResponse({"success": False, "code": "invalid_arguments", "error_code": "invalid_arguments",
                                 "message": "agent settings paths come from the hub, not the request",
                                 **kernel_fields(kernel)}, status_code=400)
        args = dict(data)
        if isinstance(data.get("agents"), list):
            paths: dict[str, str] = {}
            for agent in data["agents"]:
                target = registry.target(name).agent_settings_target(str(agent or ""))
                if target is not None:
                    paths[str(agent)] = target
            args["settings_paths"] = paths
        else:
            target = registry.target(name).agent_settings_target(str(data.get("agent") or ""))
            if target is not None:
                args["settings_path"] = target

        def run() -> JSONResponse:
            try:
                result, kernel = registry.invoke_receipted(principal, name, args)
                return JSONResponse({**result, **kernel_fields(kernel)})
            except OperationRefused as exc:
                return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                                     "message": exc.detail, **refusal_fields(exc)}, status_code=400)
            except ServiceError as exc:
                if (refused := kernel_refusal(exc)) is not None:
                    return refused
                return service_refusal(exc)
            except Exception as exc:
                # The operation ended failed; its receipt rides on the answer.
                log.exception("Onboarding agents use failed")
                return JSONResponse({"success": False, "code": "failed", "error_code": "failed",
                                     "message": "The agent binding install failed.", **refusal_fields(exc)}, status_code=500)

        return await run_in_threadpool(run)

    @router.post("/api/onboarding/agents/stop")
    async def onboarding_agents_stop(request: Request) -> Any:
        """The owner's Stop removes only the bindings HoldSpeak installed."""
        name = "agent_hooks.remove"
        registry = operations.for_context(ctx)
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        data, refused = await body_or_refusal(request, registry, principal, name)
        if refused is not None:
            return refused
        if "settings_path" in data:
            kernel = registry.refuse(principal, name, "invalid_arguments", data)
            return JSONResponse({"success": False, "code": "invalid_arguments", "error_code": "invalid_arguments",
                                 "message": "settings_path comes from the hub, not the request",
                                 **kernel_fields(kernel)}, status_code=400)
        args = dict(data)
        target = registry.target(name).agent_settings_target(str(data.get("agent") or ""))
        if target is not None:
            args["settings_path"] = target

        def run() -> JSONResponse:
            try:
                result, kernel = registry.invoke_receipted(principal, name, args)
                return JSONResponse({**result, **kernel_fields(kernel)})
            except OperationRefused as exc:
                return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                                     "message": exc.detail, **refusal_fields(exc)}, status_code=400)
            except ServiceError as exc:
                if (refused := kernel_refusal(exc)) is not None:
                    return refused
                return service_refusal(exc)
            except Exception as exc:
                log.exception("Onboarding agents stop failed")
                return JSONResponse({"success": False, "code": "failed", "error_code": "failed",
                                     "message": "The agent binding stop failed.", **refusal_fields(exc)}, status_code=500)

        return await run_in_threadpool(run)

    return router
