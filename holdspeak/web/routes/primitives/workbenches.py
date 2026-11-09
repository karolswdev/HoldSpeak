"""Workbench routes — thin HTTP adapters over :class:`WorkbenchService`."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ....services.workbench_service import WorkbenchService
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body

log = get_logger("web.routes.workbenches")

# The route-plan refusals a Run can meet when no usable engine is assigned
# (inference_route_plan_service._effective_assignment).
_NO_ENGINE_WORDS = {
    "no_assignment": "No engine is set for this automation.",
    "no_compatible_assignment": "The engine set for this automation cannot run it.",
}


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
        return JSONResponse(body, status_code=statuses.get(exc.code, 500))

    @router.get("/api/workbenches")
    def api_list_workbenches(request: Request) -> Any:
        try:
            return JSONResponse({"workbenches": _svc().list_workbenches(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list automations")

    @router.get("/api/automations/new")
    def api_new_results(request: Request) -> Any:
        """Betterment A6: one row per automation with a NEW result."""
        try:
            rows = _svc().new_results(_principal(request))
            return JSONResponse({"automations": rows, "new_count": sum(r["new_count"] for r in rows)})
        except Exception as exc:
            return error_500(exc, log, "Failed to read new automation results")

    @router.get("/api/automations/prepared")
    def api_prepared_for_today(request: Request) -> Any:
        """Betterment daily D9: Today's Prepared block (the newest result of an
        automation whose Put it in is Today) and the automation Prepare now
        runs. Each is null when there is none."""
        try:
            return JSONResponse(_svc().prepared_for_today(_principal(request)))
        except Exception as exc:
            return error_500(exc, log, "Failed to read the prepared day")

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
        except Exception as exc:
            return error_500(exc, log, "Failed to update automation")

    def _a4_error(exc: ServiceError) -> JSONResponse:
        """A When or With refusal, in its own words and status."""
        status = int(exc.context.get("status") or 0)
        if not status:
            status = 400 if isinstance(exc, ValidationError) else 409 if isinstance(exc, ConflictError) else 502
        return JSONResponse({"error": exc.detail, "code": exc.code}, status_code=status)

    @router.put("/api/workbenches/{workbench_id}/when")
    async def api_set_workbench_when(workbench_id: str, request: Request) -> Any:
        """Betterment A4: one When choice (schedule, event or manual)."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().set_when(_principal(request), workbench_id, body)
            return JSONResponse({"workbench": wb})
        except NotFound:
            return _not_found("automation", workbench_id)
        except ServiceError as exc:
            return _a4_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to change when the automation runs")

    @router.put("/api/workbenches/{workbench_id}/engine")
    async def api_set_workbench_engine(workbench_id: str, request: Request) -> Any:
        """Betterment A4: With (the engine, and the Spend limit per run)."""
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().set_engine(_principal(request), workbench_id, **body)
            return JSONResponse({"workbench": wb})
        except NotFound:
            return _not_found("automation", workbench_id)
        except ServiceError as exc:
            return _a4_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to choose the automation's engine")

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

    @router.post("/api/workbenches/{workbench_id}/items/{item_id}/restore")
    def api_restore_item(workbench_id: str, item_id: str, request: Request) -> Any:
        try:
            item = _svc().restore_item(_principal(request), workbench_id, item_id)
            return JSONResponse({"item": item})
        except NotFound:
            return _not_found("item", item_id)
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to restore Workbench item")

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
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to run automation")

    @router.post("/api/workbenches/{workbench_id}/results/{artifact_id}/open")
    def api_open_result(workbench_id: str, artifact_id: str, request: Request) -> Any:
        """Betterment A2: opening a result reads it (``new`` becomes ``read``)."""
        try:
            return JSONResponse({"result": _svc().open_result(_principal(request), workbench_id, artifact_id)})
        except NotFound:
            return _not_found("result", artifact_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to open the result")

    @router.post("/api/workbenches/{workbench_id}/make-one")
    def api_make_one_automation(workbench_id: str, request: Request) -> Any:
        """Betterment A9: an old queue automation takes its agent's prompt as Do."""
        try:
            return JSONResponse({"workbench": _svc().make_one_automation(_principal(request), workbench_id)})
        except NotFound:
            return _not_found("workbench", workbench_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to make this one automation")

    @router.get("/api/workbenches/{workbench_id}/runs")
    def api_list_runs(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"runs": _svc().list_runs(_principal(request), workbench_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list runs")

    @router.get("/api/workbench-templates")
    def api_list_templates(request: Request) -> Any:
        try:
            return JSONResponse({"templates": _svc().list_templates(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list templates")

    @router.post("/api/workbench-templates/{template_id}/instantiate")
    async def api_instantiate_template(template_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        try:
            result = _svc().instantiate_template(_principal(request), template_id, body.get("profile_id") or None)
            return JSONResponse(result, status_code=201)
        except NotFound:
            return _not_found("template", template_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to instantiate template")

    @router.get("/api/workbenches/{workbench_id}/memory")
    def api_list_memory(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"entries": _svc().list_memory(_principal(request), workbench_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to read memory")

    @router.delete("/api/workbenches/{workbench_id}/memory/{index}")
    def api_forget_memory(workbench_id: str, index: int, request: Request, at: str = "") -> Any:
        """Betterment A3: Forget one lesson; ``at`` is its timestamp."""
        try:
            _svc().forget_memory(_principal(request), workbench_id, index, at)
            return JSONResponse({"success": True})
        except NotFound:
            return _not_found("lesson", str(index))
        except Exception as exc:
            return error_500(exc, log, "Failed to forget the lesson")

    return router
