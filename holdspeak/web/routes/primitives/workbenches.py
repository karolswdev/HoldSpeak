"""Workbench routes — thin HTTP adapters over :class:`WorkbenchService`.

The Automations face's verbs (When, With, Make one, the starters, a result's
open, the new results, the lessons) are produced from
``holdspeak/automation_operations.py`` through ``OperationRegistry.invoke``
(2026-11-08); the rest are hand-written until their descriptors exist."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ....services.workbench_service import WorkbenchService
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router
from ._shared import _json_body

log = get_logger("web.routes.workbenches")

# The route-plan refusals a Run can meet when no usable engine is assigned
# (the engine door reads the assignment, engine_door.chain).
_NO_ENGINE_WORDS = {
    "no_assignment": "No engine is set for this automation.",
    "no_compatible_assignment": "The engine set for this automation cannot run it.",
}


#: The 500 words of each produced route (the hand-written handlers' words).
_FAILED = {
    "automation.set_when": "Failed to change when the automation runs",
    "automation.set_engine": "Failed to choose the automation's engine",
    "automation.make_one": "Failed to make this one automation",
    "automation.template.list": "Failed to list templates",
    "automation.template.instantiate": "Failed to instantiate template",
    "automation.result.open": "Failed to open the result",
    "automation.new.list": "Failed to read new automation results",
    "automation.lesson.list": "Failed to read memory",
    "automation.lesson.forget": "Failed to forget the lesson",
    "automation.prepared.read": "Failed to read the prepared day",
    "automation.item.restore": "Failed to restore Workbench item",
    "automation.event_start.set_enabled": "Failed to change the event start",
}
#: These answer a ValidationError as a 400 in its own words.
_BAD_REQUEST = {"automation.make_one", "automation.item.restore", "automation.event_start.set_enabled"}
#: When and With answer a refusal in its own words, code and status (Betterment A4).
_A4 = {"automation.set_when", "automation.set_engine"}


def _a4_error(exc: ServiceError) -> JSONResponse:
    """A When or With refusal, in its own words and status."""
    status = int(exc.context.get("status") or 0)
    if not status:
        status = 400 if isinstance(exc, ValidationError) else 409 if isinstance(exc, ConflictError) else 502
    return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=status)


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except NotFound as exc:
            return JSONResponse({"error": exc.detail}, status_code=404)
        except operations.OperationRefused as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except ServiceError as exc:
            if name in _A4:
                return _a4_error(exc)
            if name in _BAD_REQUEST and isinstance(exc, ValidationError):
                return JSONResponse({"error": str(exc)}, status_code=400)
            if name == "automation.item.restore" and isinstance(exc, ConflictError):
                return JSONResponse({"error": str(exc)}, status_code=409)
            return error_500(exc, log, _FAILED[name])
        except Exception as exc:
            return error_500(exc, log, _FAILED[name])

    return answer


def build_workbenches_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> WorkbenchService:
        # HS-200-45: the hub's ONE composed instance (it carries the
        # ``on_changed`` hook that puts a ``desk_changed`` frame on the bus).
        # A bare instance is built only for a partially-wired context -- a
        # route test that supplies just the fields it exercises.
        if getattr(ctx, "workbench_service", None) is not None:
            return ctx.workbench_service
        from ....db import get_database, get_observer
        return WorkbenchService(get_database(), observer=get_observer())

    def _principal(request: Request) -> Any:
        return getattr(request.state, "principal", None)

    def _not_found(kind: str, item_id: str) -> JSONResponse:
        return JSONResponse({"error": f"Unknown {kind}: {item_id}"}, status_code=404)

    def _service_error(exc: ServiceError) -> JSONResponse:
        statuses = {"artifact_persist_failed": 500, "resolver_rate_limited": 429, "resolver_not_configured": 409, "resolver_unavailable": 503, "resolver_refused": 403}
        body: dict[str, Any] = {"error": exc.context.get("error", exc.detail)}
        if "detail" in exc.context:
            body["detail"] = exc.context["detail"]
        return JSONResponse(body, status_code=int(exc.context.get("status") or statuses.get(exc.code, 500)))

    @router.get("/api/workbenches")
    def api_list_workbenches(request: Request) -> Any:
        try:
            return JSONResponse({"workbenches": _svc().list_workbenches(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list automations")

    @router.post("/api/workbenches")
    async def api_create_workbench(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().create_workbench(
                _principal(request), name=str(body.get("name") or ""),
                **{k: v for k, v in body.items() if k != "name"},
            )
            return JSONResponse({"workbench": wb}, status_code=201)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create automation")

    @router.get("/api/workbenches/{workbench_id}")
    def api_get_workbench(
        workbench_id: str, request: Request, parked: bool = False
    ) -> Any:
        try:
            return JSONResponse(
                {"workbench": _svc().get_workbench(
                    _principal(request), workbench_id, parked=parked
                )}
            )
        except NotFound:
            return _not_found("automation", workbench_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to get automation")

    @router.put("/api/workbenches/{workbench_id}")
    async def api_update_workbench(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().update_workbench(_principal(request), workbench_id, **body)
            return JSONResponse({"workbench": wb})
        except NotFound:
            return _not_found("automation", workbench_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to update automation")

    @router.delete("/api/workbenches/{workbench_id}")
    def api_delete_workbench(workbench_id: str, request: Request) -> Any:
        try:
            _svc().delete_workbench(_principal(request), workbench_id)
            return JSONResponse({"success": True})
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except NotFound:
            return _not_found("automation", workbench_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete automation")

    @router.post("/api/workbenches/{workbench_id}/items")
    async def api_add_item(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            item = _svc().add_item(
                _principal(request), workbench_id, title=str(body.get("title") or ""),
                **{k: v for k, v in body.items() if k != "title"},
            )
            return JSONResponse({"item": item}, status_code=201)
        except NotFound:
            return _not_found("automation", workbench_id)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to add item")

    @router.put("/api/workbenches/{workbench_id}/items/{item_id}")
    async def api_update_item(workbench_id: str, item_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({"item": _svc().update_item(_principal(request), workbench_id, item_id, **body)})
        except NotFound:
            return _not_found("item", item_id)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update item")

    @router.delete("/api/workbenches/{workbench_id}/items/{item_id}")
    def api_delete_item(workbench_id: str, item_id: str, request: Request) -> Any:
        try:
            item = _svc().delete_item(_principal(request), workbench_id, item_id)
            return JSONResponse({"success": True, "parked": item_id, "item": item})
        except NotFound:
            return _not_found("item", item_id)
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete item")

    @router.post("/api/workbenches/{workbench_id}/run")
    async def api_run_workbench(workbench_id: str, request: Request) -> Any:
        try:
            body = await _json_body(request) or {}
            raw_ids = body.get("item_ids")
            item_ids = [str(item_id) for item_id in raw_ids if item_id] if isinstance(raw_ids, list) else None
            return JSONResponse({"run": await _svc().run(_principal(request), workbench_id, memory_enabled=bool(body.get("memory_enabled", True)), item_ids=item_ids or None)})
        except NotFound:
            return _not_found("automation", workbench_id)
        except ServiceError as exc:
            # No engine is a state the owner can repair, not a hub fault: a
            # named 409 with plain words, so the face can show its door.
            if exc.code in _NO_ENGINE_WORDS:
                return JSONResponse({"error": _NO_ENGINE_WORDS[exc.code], "code": exc.code}, status_code=409)
            if exc.code == "set_up_as_program":  # an old queue: Programs run it now
                return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=409)
            if exc.context.get("status"):
                return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=int(exc.context["status"]))
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to run automation")

    @router.get("/api/workbenches/{workbench_id}/runs")
    def api_list_runs(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"runs": _svc().list_runs(_principal(request), workbench_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list runs")

    def _registry() -> Any:
        return operations.for_context(ctx, workbench_service=_svc, watch_service=_watches)

    def _watches() -> Any:
        from ....db import get_database, get_observer
        from ....services.watch_service import WatchService

        return WatchService(get_database(), observer=get_observer())

    for descriptor in operations.AUTOMATION_OPERATIONS:
        mount_router(router, operation_router([descriptor], _registry, _answer(descriptor.name), module=__name__))

    return router
