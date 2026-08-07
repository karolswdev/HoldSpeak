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


def build_workbenches_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> WorkbenchService:
        from ....db import get_database
        return WorkbenchService(get_database())

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
    async def api_list_workbenches(request: Request) -> Any:
        try:
            return JSONResponse({"workbenches": _svc().list_workbenches(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list workbenches")

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
            return error_500(exc, log, "Failed to create workbench")

    @router.get("/api/workbenches/{workbench_id}")
    async def api_get_workbench(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"workbench": _svc().get_workbench(_principal(request), workbench_id)})
        except NotFound:
            return _not_found("workbench", workbench_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to get workbench")

    @router.put("/api/workbenches/{workbench_id}")
    async def api_update_workbench(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            wb = _svc().update_workbench(_principal(request), workbench_id, **body)
            return JSONResponse({"workbench": wb})
        except NotFound:
            return _not_found("workbench", workbench_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to update workbench")

    @router.delete("/api/workbenches/{workbench_id}")
    async def api_delete_workbench(workbench_id: str, request: Request) -> Any:
        try:
            _svc().delete_workbench(_principal(request), workbench_id)
            return JSONResponse({"success": True})
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except NotFound:
            return _not_found("workbench", workbench_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete workbench")

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
            return _not_found("workbench", workbench_id)
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
    async def api_delete_item(workbench_id: str, item_id: str, request: Request) -> Any:
        try:
            _svc().delete_item(_principal(request), workbench_id, item_id)
            return JSONResponse({"success": True})
        except NotFound:
            return _not_found("item", item_id)
        except ConflictError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete item")

    @router.post("/api/workbenches/{workbench_id}/items/{item_id}/retry-mint")
    async def api_retry_mint(workbench_id: str, item_id: str, request: Request) -> Any:
        try:
            result = _svc().retry_mint(_principal(request), workbench_id, item_id)
            return JSONResponse({"artifact_id": result["artifact_id"]}, status_code=201 if result["created"] else 200)
        except NotFound:
            return _not_found("item", item_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to retry mint")

    @router.post("/api/workbenches/{workbench_id}/run")
    async def api_run_workbench(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"run": await _svc().run(_principal(request), workbench_id)})
        except NotFound:
            return _not_found("workbench", workbench_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to run workbench")

    @router.post("/api/workbenches/{workbench_id}/voice/resolve")
    async def api_voice_resolve(workbench_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _svc().resolve_voice(
                _principal(request), workbench_id, str(body.get("transcript") or "").strip(),
                str(body.get("request_id") or ""),
            )
            return JSONResponse(result)
        except NotFound:
            return _not_found("workbench", workbench_id)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to resolve voice references")

    @router.get("/api/workbenches/{workbench_id}/runs")
    async def api_list_runs(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"runs": _svc().list_runs(_principal(request), workbench_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list runs")

    @router.get("/api/workbench-templates")
    async def api_list_templates(request: Request) -> Any:
        try:
            return JSONResponse({"templates": _svc().list_templates(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list templates")

    @router.get("/api/skills")
    async def api_list_skills(request: Request, recipe_id: str | None = None) -> Any:
        try:
            return JSONResponse({"skills": _svc().list_skills(_principal(request), recipe_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list skills")

    @router.post("/api/skills")
    async def api_create_skill(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            skill = _svc().create_skill(
                _principal(request), title=str(body.get("title") or ""), body=str(body.get("body", "")),
                **{k: v for k, v in body.items() if k not in {"title", "body"}},
            )
            return JSONResponse({"skill": skill}, status_code=201)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create skill")

    @router.put("/api/skills/{skill_id}")
    async def api_update_skill(skill_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({"skill": _svc().update_skill(_principal(request), skill_id, **body)})
        except NotFound:
            return _not_found("skill", skill_id)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to update skill")

    @router.delete("/api/skills/{skill_id}")
    async def api_delete_skill(skill_id: str, request: Request) -> Any:
        try:
            _svc().delete_skill(_principal(request), skill_id)
            return JSONResponse({"success": True})
        except NotFound:
            return _not_found("skill", skill_id)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete skill")

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
    async def api_list_memory(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"entries": _svc().list_memory(_principal(request), workbench_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to read memory")

    @router.delete("/api/workbenches/{workbench_id}/memory")
    async def api_clear_memory(workbench_id: str, request: Request) -> Any:
        try:
            _svc().clear_memory(_principal(request), workbench_id)
            return JSONResponse({"success": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to clear memory")

    @router.post("/api/workbenches/{workbench_id}/memory/{index}/promote")
    async def api_promote_memory(workbench_id: str, index: int, request: Request) -> Any:
        try:
            skill = _svc().promote_memory(_principal(request), workbench_id, index)
            return JSONResponse({"skill": skill}, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to promote memory to skill")

    return router
