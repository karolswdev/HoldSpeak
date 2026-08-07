"""Thin HTTP adapters for the durable project boundary (HS-123-05)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ValidationError
from ...services.project_service import ProjectService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.projects")


def build_projects_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    service: ProjectService = ctx.project_service

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def not_found(exc: NotFound, *, success: bool = False) -> JSONResponse:
        body: dict[str, Any] = {"error": "Project not found" if exc.kind == "project" else str(exc)}
        if success:
            body["success"] = False
        return JSONResponse(body, status_code=404)

    @router.get("/api/projects/{project_id}/briefings")
    async def api_list_project_briefings(project_id: str, request: Request, limit: int = 50) -> Any:
        try:
            return JSONResponse(service.list_briefings(principal(request), project_id, limit))
        except NotFound:
            return JSONResponse({"error": f"Unknown project: {project_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list project briefings")

    @router.get("/api/projects")
    async def api_list_projects(request: Request, include_archived: bool = False) -> Any:
        try:
            return JSONResponse({"projects": service.list_projects(principal(request), {"include_archived": include_archived})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list projects")

    @router.post("/api/projects")
    async def api_create_project(payload: dict[str, Any], request: Request) -> Any:
        try:
            return JSONResponse({"success": True, "project": service.create_project(principal(request), payload)})
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error(f"Failed to create project: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.get("/api/projects/{project_id}")
    async def api_get_project(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.get_project(principal(request), project_id))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project")

    @router.patch("/api/projects/{project_id}")
    async def api_update_project(project_id: str, payload: dict[str, Any], request: Request) -> Any:
        try:
            return JSONResponse({"success": True, "project": service.update_project(principal(request), project_id, payload)})
        except NotFound as exc:
            return not_found(exc, success=True)
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error(f"Failed to update project: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.delete("/api/projects/{project_id}")
    async def api_archive_project(project_id: str, request: Request) -> Any:
        try:
            service.archive_project(principal(request), project_id)
            return JSONResponse({"success": True})
        except NotFound as exc:
            return not_found(exc, success=True)
        except Exception as exc:
            log.error(f"Failed to archive project: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.get("/api/projects/{project_id}/meetings")
    async def api_project_meetings(project_id: str, request: Request, limit: int = 50, offset: int = 0) -> Any:
        try:
            return JSONResponse({"meetings": service.list_meetings(principal(request), project_id, limit=limit, offset=offset)})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project meetings")

    @router.get("/api/projects/{project_id}/resources")
    async def api_project_resources(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"resources": service.list_resources(principal(request), project_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown Project: {project_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list Project resources")

    @router.put("/api/projects/{project_id}/resources/{resource_ref:path}")
    async def api_add_project_resource(project_id: str, resource_ref: str, request: Request, payload: dict[str, Any] | None = None) -> Any:
        try:
            return JSONResponse({"resource": service.add_resource(principal(request), project_id, resource_ref, payload)})
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add Project resource")

    @router.delete("/api/projects/{project_id}/resources/{resource_ref:path}")
    async def api_remove_project_resource(project_id: str, resource_ref: str, request: Request) -> Any:
        try:
            return JSONResponse({"success": True, "removed": service.remove_resource(principal(request), project_id, resource_ref)})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to remove Project resource")

    @router.get("/api/desk/relationships/{resource_ref:path}")
    async def api_resource_relationships(resource_ref: str, request: Request) -> Any:
        try:
            return JSONResponse(service.list_resource_relationships(principal(request), resource_ref))
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to inspect Desk relationships")

    @router.post("/api/projects/{project_id}/meetings/{meeting_id}")
    async def api_associate_meeting(project_id: str, meeting_id: str, request: Request) -> Any:
        try:
            service.associate_meeting(principal(request), project_id, meeting_id)
            return JSONResponse({"success": True})
        except NotFound as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=404)
        except Exception as exc:
            log.error(f"Failed to associate meeting: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.delete("/api/projects/{project_id}/meetings/{meeting_id}")
    async def api_disassociate_meeting(project_id: str, meeting_id: str, request: Request) -> Any:
        try:
            service.disassociate_meeting(principal(request), project_id, meeting_id)
            return JSONResponse({"success": True})
        except NotFound as exc:
            return JSONResponse({"success": False, "error": str(exc)}, status_code=404)
        except Exception as exc:
            log.error(f"Failed to disassociate meeting: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.get("/api/meetings/{meeting_id}/projects")
    async def api_meeting_projects(meeting_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"projects": service.list_meeting_projects(principal(request), meeting_id)})
        except NotFound as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get meeting projects")

    @router.get("/api/projects/{project_id}/since-last-meeting")
    async def api_project_since_last_meeting(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.since_last_meeting(principal(request), project_id))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to compare Project meetings")

    @router.get("/api/projects/{project_id}/summary")
    async def api_project_summary(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.summary(principal(request), project_id))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project summary")

    @router.get("/api/projects/{project_id}/action-items")
    async def api_project_action_items(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"action_items": service.list_action_items(principal(request), project_id)})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project action items")

    @router.get("/api/projects/{project_id}/artifacts")
    async def api_project_artifacts(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"artifacts": service.list_artifacts(principal(request), project_id)})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project artifacts")

    return router
