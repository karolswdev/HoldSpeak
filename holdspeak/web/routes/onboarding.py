"""Onboarding routes: detect what the owner already has; one "Use it" each.

Parse-and-serialize only; the behaviour and what each call touches live in
``services/onboarding_service.py``.

GET  /api/onboarding/calendar                 -- macOS calendars (no prompt, no network)
POST /api/onboarding/calendar/macos/access    -- the macOS Calendars prompt (explicit)
POST /api/onboarding/calendar/check           -- {url}: validate + read one ICS URL once
POST /api/onboarding/calendar/use             -- {id, label?}: add the calendar source
GET  /api/onboarding/connections              -- signed-in gh / acli accounts (files only)
POST /api/onboarding/connections/use          -- {id}: add the connector + its status probe
GET  /api/onboarding/agents                   -- claude / codex / tmux readiness (files and PATH only)
GET  /api/settings/people-access              -- Conductor R7: {mode, effective, source, agents}
PUT  /api/settings/people-access              -- {mode}: people_access.set (admitted config; receipt)
POST /api/onboarding/agents/use               -- {agent}: agent_hooks.install (admitted; answers
                                                 with its operation_id and terminal receipt)
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500
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


async def _body(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        raise ValidationError("The request body must be JSON.", code="onboarding_request_invalid")
    if not isinstance(body, dict):
        raise ValidationError("The request body must be an object.", code="onboarding_request_invalid")
    return body


def build_onboarding_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["onboarding"])

    def _service() -> Any:
        service = getattr(ctx, "onboarding_service", None)
        if service is None:
            raise ServiceError(
                "onboarding_unavailable", "Onboarding is not available on this hub.", context={"status": 503},
            )
        return service

    async def _call(request: Request, method: str, *args: Any) -> Any:
        try:
            return await run_in_threadpool(getattr(_service(), method), request.state.principal, *args)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, f"Onboarding {method} failed")

    @router.get("/api/onboarding/calendar")
    async def onboarding_calendar(request: Request) -> Any:
        return await _call(request, "calendar_detect")

    @router.post("/api/onboarding/calendar/macos/access")
    async def onboarding_calendar_access(request: Request) -> Any:
        return await _call(request, "calendar_request_access")

    @router.post("/api/onboarding/calendar/check")
    async def onboarding_calendar_check(request: Request) -> Any:
        try:
            body = await _body(request)
        except ServiceError as exc:
            return _error(exc)
        return await _call(request, "calendar_check", body.get("url"))

    @router.post("/api/onboarding/calendar/use")
    async def onboarding_calendar_use(request: Request) -> Any:
        try:
            body = await _body(request)
        except ServiceError as exc:
            return _error(exc)
        return await _call(request, "calendar_use", body)

    @router.get("/api/onboarding/connections")
    async def onboarding_connections(request: Request) -> Any:
        return await _call(request, "connections_detect")

    @router.post("/api/onboarding/connections/use")
    async def onboarding_connections_use(request: Request) -> Any:
        try:
            body = await _body(request)
        except ServiceError as exc:
            return _error(exc)
        return await _call(request, "connections_use", body)

    @router.get("/api/onboarding/agents")
    async def onboarding_agents(request: Request) -> Any:
        return await _call(request, "agents_detect")

    @router.post("/api/onboarding/agents/use")
    async def onboarding_agents_use(request: Request) -> Any:
        # The owner's press is the approval: one admitted kernel operation with
        # one terminal receipt (succeeded, refused by name, or failed).
        name = "agent_hooks.install"
        registry = operations.for_context(ctx)
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        data, refused = await body_or_refusal(request, registry, principal, name)
        if refused is not None:
            return refused
        if "settings_path" in data:
            # The hub binds the file; a client never names it.
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
                # The operation ended failed; its receipt rides on the answer.
                log.exception("Onboarding agents use failed")
                return JSONResponse({"success": False, "code": "failed", "error_code": "failed",
                                     "message": "The hook install failed.", **refusal_fields(exc)}, status_code=500)

        return await run_in_threadpool(run)

    # ── Conductor R7: People MCP access (config, owner only) ─────────

    @router.get("/api/settings/people-access")
    async def people_access(request: Request) -> Any:
        return await _call(request, "people_access")

    @router.put("/api/settings/people-access")
    async def people_access_set(request: Request) -> Any:
        # The owner's press: one admitted kernel operation, one receipt.
        name = "people_access.set"
        registry = operations.for_context(ctx)
        principal = getattr(request.state, "principal", UNAUTHENTICATED)
        data, refused = await body_or_refusal(request, registry, principal, name)
        if refused is not None:
            return refused

        def run() -> JSONResponse:
            try:
                result, kernel = registry.invoke_receipted(principal, name, dict(data))
                return JSONResponse({**result, **kernel_fields(kernel)})
            except OperationRefused as exc:
                return JSONResponse({"success": False, "code": exc.code, "error_code": exc.code,
                                     "message": exc.detail, **refusal_fields(exc)}, status_code=400)
            except ServiceError as exc:
                if (refused := kernel_refusal(exc)) is not None:
                    return refused
                return service_refusal(exc)

        return await run_in_threadpool(run)

    return router
