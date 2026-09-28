"""Thin HTTP adapters for the durable project boundary (HS-123-05).

HS-158-02: routes pass expected_revision / command_id through from
request bodies; typed errors surface as structured JSON with correct
HTTP statuses (409 for conflicts).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...logging_config import get_logger
from ...operations import OperationRefused
from ...principals import UNAUTHENTICATED
from ...services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ...services.project_service import ProjectService
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.projects")


def build_projects_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    service: ProjectService = ctx.project_service

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def url_owns(body: dict[str, Any], operation: str, **ids: str) -> dict[str, Any]:
        """PHILO-9-01 round two (Codex Astra r1, P1): the URL names the target.

        A body that names a target identifier (``project_id``, ``resource_ref``,
        ``item_id``) is refused 400 -- also when it agrees with the URL -- so a
        request to one Room can never write another. The URL's identifiers are
        the operation's.
        """
        named = sorted(set(ids) & set(body))
        if named:
            raise OperationRefused(
                "invalid_arguments", operation,
                f"Invalid arguments for {operation}: {', '.join(named)} "
                f"{'comes' if len(named) == 1 else 'come'} from the path, not the body",
            )
        return {**body, **ids}

    def ops() -> Any:
        """PHILO-9-01: the Room's declared operations (``holdspeak.operations``).

        In the hub: the registry bound at composition to the hub's
        ProjectService (the same object MCP reaches). A partially wired
        context binds over the service it carries.
        """
        return operations.for_context(ctx, "project_service")

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
            return JSONResponse(ops().invoke(principal(request), "project.get_room", {"project_id": project_id}))
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

    # ── HS-200-41: the saved ask ─────────────────────────────────────
    #
    # Four thin adapters over ProjectService.  The Resume route dispatches
    # through the SAME Ask transport `/api/ask` uses, under the task's saved
    # `invocation_id`, so the kernel's `operation_id` UNIQUE is the only
    # double-spend guard there is (ruling B3).

    def host_identity() -> tuple[str, int]:
        """This hub process's refinement lease, for the custody token (B7).

        Absent (an MCP sidecar, a test rig, a hub whose coordinator has not
        started), custody is simply unknown and the row draws no token.
        """
        coordinator = getattr(ctx, "refinement_coordinator", None)
        if coordinator is None:
            return "", 0
        return str(getattr(coordinator, "host_id", "") or ""), int(
            getattr(coordinator, "_lease_epoch", 0) or 0
        )

    def service_error(exc: ServiceError) -> JSONResponse:
        body: dict[str, Any] = dict(exc.context)
        body.setdefault("error", exc.detail)
        body.setdefault("error_code", exc.code)
        status = int(body.pop("status", 409 if isinstance(exc, ConflictError) else 400))
        return JSONResponse(body, status_code=status)

    @router.post("/api/projects/{project_id}/ask-tasks")
    async def api_save_ask_task(project_id: str, payload: dict[str, Any], request: Request) -> Any:
        try:
            host_id, lease_epoch = host_identity()
            return JSONResponse(
                service.save_ask(
                    principal(request), project_id, payload,
                    host_id=host_id, lease_epoch=lease_epoch,
                ),
                status_code=201,
            )
        except NotFound as exc:
            return not_found(exc)
        except ServiceError as exc:
            return service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to save ask")

    @router.get("/api/ask-tasks")
    async def api_list_ask_tasks(
        request: Request,
        state: str = "unfinished",
        limit: int = 20,
        cursor: str | None = None,
        project_id: str | None = None,
    ) -> Any:
        # A closed `state` param: the Resume projection is the only view.
        if state != "unfinished":
            return JSONResponse(
                {"error": "state must be 'unfinished'", "error_code": "ask_task_state_invalid"},
                status_code=400,
            )
        try:
            host_id, _ = host_identity()
            return JSONResponse(service.list_unfinished_asks(
                principal(request), limit=limit, cursor=cursor,
                project_id=project_id, host_id=host_id,
            ))
        except ServiceError as exc:
            return service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to list unfinished asks")

    @router.post("/api/ask-tasks/{task_id}/resume")
    async def api_resume_ask_task(task_id: str, request: Request) -> Any:
        from .primitives.ask import build_ask_service

        host_id, lease_epoch = host_identity()

        async def dispatch(task: dict[str, Any]) -> Any:
            return await build_ask_service(ctx).ask(
                principal(request),
                str(task["purpose"]),
                task.get("grounding") or None,
                lens=str(task.get("lens") or "Project"),
                invocation_id=str(task["invocationId"]),
            )

        try:
            return JSONResponse(await service.resume_ask(
                principal(request), task_id,
                dispatcher=dispatch, host_id=host_id, lease_epoch=lease_epoch,
            ))
        except NotFound as exc:
            return not_found(exc)
        except ServiceError as exc:
            return service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to resume ask")

    @router.post("/api/ask-tasks/{task_id}/stopped")
    async def api_record_ask_stop(task_id: str, payload: dict[str, Any], request: Request) -> Any:
        """Record why a saved ask stopped, from the refusal CODE alone.

        The body carries `code` and nothing else that reaches the store: the
        service resolves that token against its own live placement and quotes
        the destination's words, so no caller-supplied sentence can ever land
        on a row (ruling B5).  `saved` -> `failed` only; a repeat is a no-op.
        """
        try:
            host_id, _ = host_identity()
            return JSONResponse(service.record_ask_stop(
                principal(request), task_id,
                str(payload.get("code") or ""), host_id=host_id,
            ))
        except NotFound as exc:
            return not_found(exc)
        except ServiceError as exc:
            return service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to record ask stop")

    @router.post("/api/ask-tasks/{task_id}/discard")
    async def api_discard_ask_task(task_id: str, request: Request) -> Any:
        try:
            host_id, _ = host_identity()
            return JSONResponse(service.discard_ask(
                principal(request), task_id, host_id=host_id,
            ))
        except NotFound as exc:
            return not_found(exc)
        except ServiceError as exc:
            return service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to discard ask")

    @router.get("/api/projects")
    async def api_list_projects(request: Request, include_archived: bool = False) -> Any:
        try:
            return JSONResponse({"projects": ops().invoke(principal(request), "project.list", {"include_archived": include_archived})})
        except Exception as exc:
            return error_500(exc, log, "Failed to list projects")

    @router.post("/api/projects")
    async def api_create_project(payload: dict[str, Any], request: Request) -> Any:
        try:
            return JSONResponse({"success": True, "project": ops().invoke(
                principal(request), "project.create", payload,
            )})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
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
            return JSONResponse(ops().invoke(principal(request), "project.get", {"project_id": project_id}))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project")

    @router.patch("/api/projects/{project_id}")
    async def api_update_project(project_id: str, payload: dict[str, Any], request: Request) -> Any:
        try:
            expected_rev = payload.pop("expected_revision", None)
            cmd_id = payload.pop("command_id", None)
            return JSONResponse({"success": True, "project": ops().invoke(principal(request), "project.update", {
                "project_id": project_id, "patch": payload,
                "expected_revision": expected_rev, "command_id": cmd_id,
            })})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
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
            ops().invoke(principal(request), "project.archive", {"project_id": project_id})
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
            result = ops().invoke(principal(request), "project.restore", {
                "project_id": project_id, "expected_revision": expected_rev, "command_id": cmd_id,
            })
            return JSONResponse({"success": True, "project": result})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
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
            return JSONResponse({"resources": ops().invoke(principal(request), "project.resource.list", {"project_id": project_id})})
        except NotFound:
            return JSONResponse({"error": f"Unknown Project: {project_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list Project resources")

    @router.put("/api/projects/{project_id}/resources/{resource_ref:path}")
    async def api_add_project_resource(project_id: str, resource_ref: str, request: Request, payload: dict[str, Any] | None = None) -> Any:
        # PHILO-9-01 (A1): the body's expected_revision and command_id reach
        # the service (they were dropped, so a stale revision and a reused
        # command id both wrote).
        try:
            body = dict(payload or {})
            return JSONResponse({"resource": ops().invoke(principal(request), "project.resource.add", url_owns(
                body, "project.resource.add", project_id=project_id, resource_ref=resource_ref,
            ))})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
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
        # PHILO-9-01 (A1): an optional JSON body carries expected_revision and
        # command_id to the service.
        try:
            try:
                body = await request.json() if await request.body() else {}
            except ValueError:
                return JSONResponse({"error": "the body must be a JSON object"}, status_code=400)
            if not isinstance(body, dict):
                return JSONResponse({"error": "the body must be a JSON object"}, status_code=400)
            return JSONResponse({"success": True, "removed": ops().invoke(principal(request), "project.resource.remove", url_owns(
                body, "project.resource.remove", project_id=project_id, resource_ref=resource_ref,
            ))})
        except ConflictError as exc:
            return JSONResponse({"success": False, "error": exc.detail,
                                 "error_code": exc.code}, status_code=409)
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
            ops().invoke(principal(request), "project.link", {"project_id": project_id, "meeting_id": meeting_id})
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
            ops().invoke(principal(request), "project.unlink", {"project_id": project_id, "meeting_id": meeting_id})
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
            return JSONResponse(ops().invoke(principal(request), "project.item.list", {
                "project_id": project_id, "item_type": item_type, "limit": limit, "offset": offset,
            }))
        except NotFound as exc:
            return not_found(exc)
        except (ValidationError, OperationRefused) as exc:
            return JSONResponse({"error": exc.detail}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to list project items")

    @router.post("/api/projects/{project_id}/items")
    async def api_create_item(
        project_id: str, payload: dict[str, Any], request: Request,
    ) -> Any:
        try:
            result = ops().invoke(principal(request), "project.item.create",
                                  url_owns(payload, "project.item.create", project_id=project_id))
            return JSONResponse({"success": True, "item": result})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
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
            result = ops().invoke(principal(request), "project.item.update", {
                "project_id": project_id, "item_id": item_id, "patch": payload,
                "expected_revision": expected_rev, "command_id": cmd_id,
            })
            return JSONResponse({"success": True, "item": result})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
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
            result = ops().invoke(principal(request), "project.item.transition", {
                **url_owns(payload, "project.item.transition", project_id=project_id, item_id=item_id), "verb": verb,
            })
            return JSONResponse({"success": True, "item": result})
        except OperationRefused as exc:
            return JSONResponse({"success": False, "error": exc.detail}, status_code=400)
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

    from ...services.needs_you_aggregate import NeedsYouCache, shared_last_known

    # The owner principal for background rebuilds (the cache builder runs
    # outside a request context).
    _owner_principal = UNAUTHENTICATED  # will be replaced on first request

    def _get_db():
        from ...db import get_database
        return get_database()

    # HS-200-13 (AC5): the ONE durable last-known store (shared with the
    # heartbeat and the sidecar through the composition root), so a restart
    # replays what a failed source last said.
    _last_known = shared_last_known(_get_db)
    ctx.needs_you_last_known = _last_known  # type: ignore[attr-defined]

    def _build_needs_you() -> dict:
        # PHILO-9-01 (F13): the declared desk.needs_you operation -- the one
        # MCP reaches -- builds the aggregate and applies the heartbeat's
        # muted projects (one count everywhere). The Door's upcoming meetings
        # are the hub's, held by this transport.
        door = ctx.door_service
        door_upcoming = getattr(door, "_upcoming", None) if door else None
        return ops().invoke(_owner_principal, "desk.needs_you", {}, held={"door_upcoming": door_upcoming})

    _needs_you_cache = NeedsYouCache(
        _build_needs_you, max_age_s=900.0, db_factory=_get_db,
    )

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

    # ── HS-172-06: suggested sources ────────────────────────────────

    @router.get("/api/projects/{project_id}/suggested-sources")
    async def api_suggested_sources(project_id: str, request: Request) -> Any:
        """List pending suggested sources for a Room."""
        try:
            service.get_project(principal(request), project_id)
            from ...services.suggested_source_service import SuggestedSourceService
            sug = SuggestedSourceService(service._db)
            rows = sug.list_suggestions(project_id, status="pending")
            return JSONResponse({"suggestions": rows})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to list suggested sources")

    @router.post("/api/projects/{project_id}/suggested-sources/{ref}/add")
    async def api_add_suggested_source(project_id: str, ref: str, request: Request) -> Any:
        """Accept a suggested source -- creates a Watch source via the existing path."""
        try:
            p = principal(request)
            service.get_project(p, project_id)
            from ...services.suggested_source_service import SuggestedSourceService
            sug = SuggestedSourceService(service._db)

            # Find the suggestion by reference.
            with service._db._connection() as conn:
                row = conn.execute(
                    "SELECT * FROM source_suggestions WHERE project_id=? AND reference=? AND status='pending'",
                    (project_id, ref),
                ).fetchone()
            if row is None:
                return JSONResponse({"error": "Suggestion not found or already resolved"}, status_code=404)

            suggestion = dict(row)
            # Accept: mark as accepted and create the source.
            sug.accept_suggestion(suggestion["id"])

            # Create the Watch source through add_resource.
            resource_ref = f"{suggestion['provider']}:{suggestion['reference']}"
            try:
                result = service.add_resource(
                    p, project_id, resource_ref,
                    {"relationship": "source", "provider": suggestion["provider"]},
                )
            except Exception:
                # Resource add failed but suggestion is already accepted -- still report.
                result = {"resource_ref": resource_ref, "state": "accepted_no_watch"}

            return JSONResponse({"suggestion": suggestion, "resource": result})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to add suggested source")

    @router.post("/api/projects/{project_id}/suggested-sources/{ref}/dismiss")
    async def api_dismiss_suggested_source(project_id: str, ref: str, request: Request) -> Any:
        """Dismiss a suggested source -- never suggest again for this Room."""
        try:
            service.get_project(principal(request), project_id)
            from ...services.suggested_source_service import SuggestedSourceService
            sug = SuggestedSourceService(service._db)

            with service._db._connection() as conn:
                row = conn.execute(
                    "SELECT * FROM source_suggestions WHERE project_id=? AND reference=? AND status='pending'",
                    (project_id, ref),
                ).fetchone()
            if row is None:
                return JSONResponse({"error": "Suggestion not found or already resolved"}, status_code=404)

            suggestion = sug.dismiss_suggestion(dict(row)["id"])
            return JSONResponse({"suggestion": suggestion})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to dismiss suggested source")

    # ── HS-172-07: Room people ──────────────────────────────────────

    @router.get("/api/projects/{project_id}/people")
    async def api_project_people(project_id: str, request: Request) -> Any:
        """The Room's PEOPLE projection (read-only).

        HS-200-14: linked people with their open commitments and observable
        facts, the owners nobody is linked to (ambiguous / not linked), and
        the ledger's own state -- a locked or missing store is NAMED here,
        never an empty list.  The ``people`` key keeps 172-07's row shape.
        """
        try:
            from ...services.room_people_service import room_people_preparation
            people_svc = ctx.people_service
            result = room_people_preparation(
                service, people_svc, project_id, principal(request),
            )
            return JSONResponse(result)
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project people")

    return router
