"""The meeting routes produced from ``holdspeak/meeting_operations.py`` (2026-11-08), through
``OperationRegistry.invoke``; the answer keeps the words the hand-written handlers answered with."""
from __future__ import annotations

from typing import Any, Callable, Iterable, Mapping

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....redaction import redact_error
from ....services.errors import ConflictError, NotFound, ValidationError
from ....services.meeting_service import ActionItemTriageUnavailable
from ...context import WebContext
from ...operation_routes import operation_router
from .._mount import mount_router

log = get_logger("web.routes.meetings")

#: The 500 words of a verb whose failure keeps something (``{}``: the cause).
_FAILED = {
    "meeting.recover_capture": "Recovery failed; the original Meeting is retained: {}. Retry recovery.",
    "meeting.resolve_sync_conflict": "Conflict recovery failed; both versions remain: {}. Retry the resolution.",
}
#: The verbs whose refusals carry ``success: false`` (the triage answer shape).
_FLAGGED = {"action_item.update", "action_item.review"}
_STATUS = ((NotFound, 404), (ValidationError, 400), (ConflictError, 409), (ActionItemTriageUnavailable, 501))


def registry_for(ctx: WebContext) -> Callable[[], operations.OperationRegistry]:
    """The routes' registry: the hub's bound contract, else one over the context's meeting service."""

    def fallback() -> Any:
        """A partial context's service (the hub composes its own, wired, in ``runtime/hub_composition.py``)."""
        if ctx.meeting_service_factory is not None:
            service = ctx.meeting_service_factory()
        else:
            from .live import _service

            service = _service(ctx)
        # HS-132-02: the live meeting's action items first, then the archive.
        service.bind_live_triage(on_update=ctx.on_update_action_item, on_review=ctx.on_update_action_item_review,
                                 on_edit=ctx.on_edit_action_item)
        return service

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, meeting_service=fallback)

    return registry


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except Exception as exc:
            code = next((code for kind, code in _STATUS if isinstance(exc, kind)), 500)
            if code == 404:
                error = f"{exc.kind[:1].upper()}{exc.kind[1:]} not found"  # type: ignore[attr-defined]
            elif code != 500:
                error = str(exc)
            else:
                error = redact_error(exc)
                log.error(f"{name} failed: {error}")
                error = _FAILED.get(name, "{}").format(error)
        return JSONResponse({"success": False, "error": error} if name in _FLAGGED else {"error": error},
                            status_code=code)

    return answer


def router(ctx: WebContext, names: Iterable[str], *, module: str,
           hand_written: Mapping[str, Callable[[Any], Callable[..., Any]]] | None = None) -> APIRouter:
    """The routes of the named meeting operations, in the order named."""
    by_name = {descriptor.name: descriptor for descriptor in operations.MEETING_OPERATIONS}
    registry = registry_for(ctx)
    produced = APIRouter()
    for name in names:
        mount_router(produced, operation_router([by_name[name]], registry, _answer(name), module=module,
                                                hand_written=hand_written))
    return produced
