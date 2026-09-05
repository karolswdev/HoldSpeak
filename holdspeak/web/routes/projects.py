"""Thin HTTP adapters for the durable project boundary (HS-123-05).

HS-158-02: routes pass expected_revision / command_id through from
request bodies; typed errors surface as structured JSON with correct
HTTP statuses (409 for conflicts).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ...logging_config import get_logger
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ValidationError
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

    @router.get("/api/projects/{project_id}/room")
    async def api_project_room(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.room(principal(request), project_id))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project room")

    @router.post("/api/projects/{project_id}/room/read")
    async def api_mark_room_read(project_id: str, request: Request) -> Any:
        """HS-169-04: set the per-project read marker to now."""
        try:
            return JSONResponse(service.mark_room_read(principal(request), project_id))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to mark room read")

    @router.get("/api/projects")
    async def api_list_projects(request: Request, include_archived: bool = False) -> Any:
        try:
            return JSONResponse({"projects": service.list_projects(principal(request), {"include_archived": include_archived})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list projects")

    @router.post("/api/projects")
    async def api_create_project(payload: dict[str, Any], request: Request) -> Any:
        try:
            cmd_id = payload.pop("command_id", None)
            return JSONResponse({"success": True, "project": service.create_project(
                principal(request), payload, command_id=cmd_id,
            )})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
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
            expected_rev = payload.pop("expected_revision", None)
            cmd_id = payload.pop("command_id", None)
            return JSONResponse({"success": True, "project": service.update_project(
                principal(request), project_id, payload,
                expected_revision=expected_rev, command_id=cmd_id,
            )})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
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
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
        except NotFound as exc:
            return not_found(exc, success=True)
        except Exception as exc:
            log.error(f"Failed to archive project: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.post("/api/projects/{project_id}/restore")
    async def api_restore_project(project_id: str, request: Request,
                                  payload: dict[str, Any] | None = None) -> Any:
        try:
            body = payload or {}
            expected_rev = body.get("expected_revision")
            cmd_id = body.get("command_id")
            result = service.restore_project(
                principal(request), project_id,
                expected_revision=expected_rev, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "project": result})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
        except NotFound as exc:
            return not_found(exc, success=True)
        except Exception as exc:
            log.error(f"Failed to restore project: {exc}")
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
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
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
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
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

    # ── Item routes (HS-158-03) ─────────────────────────────────────

    @router.get("/api/projects/{project_id}/items")
    async def api_list_items(
        project_id: str, request: Request,
        item_type: str | None = None,
        limit: int = 200, offset: int = 0,
    ) -> Any:
        try:
            return JSONResponse(service.list_items(
                principal(request), project_id,
                item_type=item_type, limit=limit, offset=offset,
            ))
        except NotFound as exc:
            return not_found(exc)
        except ValidationError as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to list project items")

    @router.post("/api/projects/{project_id}/items")
    async def api_create_item(
        project_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            expected_rev = payload.pop("expected_revision", None)
            cmd_id = payload.pop("command_id", None)
            result = service.create_item(
                principal(request), project_id, payload,
                expected_revision=expected_rev, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "item": result})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
        except NotFound as exc:
            return not_found(exc, success=True)
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error(f"Failed to create item: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.patch("/api/projects/{project_id}/items/{item_id}")
    async def api_update_item(
        project_id: str, item_id: str,
        payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            expected_rev = payload.pop("expected_revision", None)
            cmd_id = payload.pop("command_id", None)
            result = service.update_item(
                principal(request), project_id, item_id, payload,
                expected_revision=expected_rev, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "item": result})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
        except NotFound as exc:
            return not_found(exc, success=True)
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error(f"Failed to update item: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    @router.post("/api/projects/{project_id}/items/{item_id}/transition")
    async def api_transition_item(
        project_id: str, item_id: str,
        payload: dict[str, Any], request: Request,
    ) -> Any:
        """Explicit lifecycle transition (DOM-007).

        Follows the people service transition convention: POST with
        ``verb`` in the request body.
        """
        try:
            verb = str(payload.pop("verb", "")).strip()
            if not verb:
                return JSONResponse(
                    {"success": False, "error": "verb is required"},
                    status_code=400,
                )
            expected_rev = payload.pop("expected_revision", None)
            cmd_id = payload.pop("command_id", None)
            result = service.transition_item(
                principal(request), project_id, item_id, verb, payload,
                expected_revision=expected_rev, command_id=cmd_id,
            )
            return JSONResponse({"success": True, "item": result})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
        except NotFound as exc:
            return not_found(exc, success=True)
        except ValidationError as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
        except Exception as exc:
            log.error(f"Failed to transition item: {exc}")
            return JSONResponse({"success": False, "error": str(exc)}, status_code=500)

    # ── HS-170-04 / HS-171-03: desk needs-you aggregate (cached) ────────

    from ...services.needs_you_aggregate import NeedsYouCache, build_aggregate

    # The owner principal for background rebuilds (the cache builder runs
    # outside a request context).
    _owner_principal = UNAUTHENTICATED  # will be replaced on first request

    def _build_needs_you() -> dict:
        door = ctx.door_service
        door_upcoming = getattr(door, "_upcoming", None) if door else None
        aggregate = build_aggregate(
            list_projects=service.list_projects,
            room=service.room,
            principal=_owner_principal,
            door_upcoming=door_upcoming,
        )
        # M1 (counsel): apply the mute list from heartbeat settings so
        # the route's count matches the notification edge count (one count
        # everywhere).  Muted items get ``muted: true`` and are excluded
        # from ``count`` but included in ``mutedCount``.
        try:
            from ...services.heartbeat_service import HeartbeatService
            from ...db import get_database
            hb = HeartbeatService(get_database())
            muted_ids = set(hb.get_settings().get("muted_projects", []))
        except Exception:
            muted_ids = set()
        if muted_ids:
            unmuted = []
            muted_count = 0
            for item in aggregate.get("items", []):
                if item.get("projectId") in muted_ids:
                    item["muted"] = True
                    muted_count += 1
                else:
                    item["muted"] = False
                    unmuted.append(item)
            aggregate["count"] = len(unmuted)
            aggregate["mutedCount"] = muted_count
            # One count everywhere: "across M projects" counts only Rooms
            # that still contribute (counsel C2).
            aggregate["projects"] = sorted(
                {str(i.get("projectId")) for i in unmuted if i.get("projectId")}
            )
        return aggregate

    _needs_you_cache = NeedsYouCache(_build_needs_you, max_age_s=900.0)

    # Expose the cache on the context so the cadence tick can invalidate it.
    ctx._needs_you_cache = _needs_you_cache  # type: ignore[attr-defined]

    @router.get("/api/desk/needs-you")
    async def api_desk_needs_you(request: Request, fresh: str | None = None) -> Any:
        """HS-171-03: cached needs-you aggregate.

        Reads from the in-memory cache; ``?fresh=1`` forces a rebuild.
        Response includes ``computedAt``, ``stale``, ``sweepId``.
        """
        try:
            nonlocal _owner_principal
            _owner_principal = principal(request)
            force = fresh == "1"
            data = _needs_you_cache.get(force=force)
            return JSONResponse(data)
        except Exception as exc:
            return error_500(exc, log, "Failed to build desk needs-you")

    return router
