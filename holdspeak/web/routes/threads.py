"""Thread HTTP routes (HS-151-04).

CRUD + turn + abort + branch + regenerate + keep + import + decide +
annotations + todo are produced from the declared rows
(``holdspeak/thread_operations.py``, 2026-11-09) through
``OperationRegistry.invoke``; the MCP tools come from the same rows. The
interview control stays hand-written: it is browser only (HS-200-10).
No SSE — the bus is the one live channel (Art. I, one bus).
"""
from __future__ import annotations

import inspect
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...principals import Principal, PrincipalKind
from ...services.errors import ServiceError, ValidationError
from ..context import WebContext
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.threads")


async def _json_body(request: Request) -> dict[str, Any] | None:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else None
    except Exception:
        return None


def _error(exc: ServiceError) -> JSONResponse:
    payload = dict(exc.context)
    payload.setdefault("error", exc.detail)
    status = int(payload.pop("status", 400 if exc.code == "validation_error" else 409))
    return JSONResponse(payload, status_code=status)


async def _answer(fn: Any, *, status: int = 200) -> JSONResponse:
    """The produced routes' envelope: the answer (a turn's coroutine is
    awaited here, on the hub's loop), else the words the hand-written routes
    answered with."""
    try:
        result = await run_in_threadpool(fn)
        if inspect.isawaitable(result):
            result = await result
        return JSONResponse(result, status_code=status)
    except ValidationError as exc:
        return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
    except ServiceError as exc:
        return _error(exc)
    except Exception as exc:
        return error_500(exc, log, "Thread request failed")


# HS-200-10: `promote` and `revoke_promotion` join the BROWSER allowlist and
# nothing else. The MCP interview family gains no tool: a model that could mint
# a canonical record is the precise failure the People boundary exists to
# prevent. The model records; the owner disposes (ruling C6 as amended).
#
# Hoisted out of the handler so the asymmetry is testable as DATA -- the guard
# that certifies it reads this set and the MCP dispatcher's own kind map, and
# the route below is the only consumer, so the two cannot drift.
INTERVIEW_BROWSER_EVENT_KINDS = frozenset(
    {"section", "remove_fact", "disposition", "status", "promote", "revoke_promotion"}
)


def build_threads_router(ctx: WebContext) -> APIRouter:
    from ... import operations
    from ...thread_operations import THREAD_OPERATIONS
    from ..operation_routes import operation_router

    router = APIRouter()

    def _principal(request: Request) -> Principal:
        return getattr(
            request.state,
            "principal",
            Principal(PrincipalKind.OWNER, "owner-session"),
        )

    def _service() -> Any:
        # One factory shared with the recipe chat alias (HS-151-04).
        from ...services.thread_service import hub_thread_service
        return hub_thread_service(ctx.broadcast)

    def _registry() -> Any:
        # The rows bind to the hub's ThreadService factory (a partial context: this one).
        return operations.for_context(ctx, hub_thread_service=lambda: _service)

    @router.post("/api/threads/{thread_id}/interview")
    async def api_interview_command(thread_id: str, request: Request) -> Any:
        from ...services.interview_service import InterviewService
        body = await _json_body(request)
        if body is None or set(body) != {"command_id", "expected_revision", "event"}:
            return JSONResponse({"error": "Expected command_id, expected_revision, and event"}, status_code=400)
        # The direct controls edit local interview state; domain execution still
        # goes through the existing conversation/tool and citizen services.
        event = body["event"]
        if not isinstance(event, dict) or event.get("kind") not in INTERVIEW_BROWSER_EVENT_KINDS:
            return JSONResponse({"error": "Unsupported interview control"}, status_code=400)
        try:
            return JSONResponse(InterviewService(_service()._db).command(_principal(request), thread_id, **body))
        except ServiceError as exc:
            return _error(exc)

    mount_router(router, operation_router(THREAD_OPERATIONS, _registry, _answer, module=__name__))
    return router
