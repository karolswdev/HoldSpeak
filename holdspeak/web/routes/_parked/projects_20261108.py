"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/projects.py``: GET /api/projects/{project_id}/action-items, GET /api/projects/{project_id}/briefings, GET /api/projects/{project_id}/summary.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Thin HTTP adapters for the durable project boundary (HS-123-05).

HS-158-02: routes pass expected_revision / command_id through from
request bodies; typed errors surface as structured JSON with correct
HTTP statuses (409 for conflicts).
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....logging_config import get_logger
from ....operations import OperationRefused
from ....principals import UNAUTHENTICATED
from ....services.errors import ConflictError, NotFound, ServiceError
from ....services.project_service import ProjectService
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.projects")


def parked_build_projects_router(ctx: WebContext) -> APIRouter:
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
    def api_list_project_briefings(project_id: str, request: Request, limit: int = 50) -> Any:
        try:
            return JSONResponse(service.list_briefings(principal(request), project_id, limit))
        except NotFound:
            return JSONResponse({"error": f"Unknown project: {project_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to list project briefings")

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

    @router.get("/api/projects/{project_id}/summary")
    def api_project_summary(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.summary(principal(request), project_id))
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project summary")

    @router.get("/api/projects/{project_id}/action-items")
    def api_project_action_items(project_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"action_items": service.list_action_items(principal(request), project_id)})
        except NotFound as exc:
            return not_found(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get project action items")

    # ── Item routes (HS-158-03) ─────────────────────────────────────

    # ── HS-170-04 / HS-171-03: desk needs-you aggregate (cached) ────────

    from ....services.needs_you_aggregate import NeedsYouCache, shared_last_known

    # The owner principal for background rebuilds (the cache builder runs
    # outside a request context).
    _owner_principal = UNAUTHENTICATED  # will be replaced on first request

    def _get_db():
        from ....db import get_database
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
        answer = ops().invoke(_owner_principal, "desk.needs_you", {}, held={"door_upcoming": door_upcoming})
        # Only the Room read is cached. The Door rows (People commitments
        # among them) never enter a cache: the route applies the rule again
        # on every request, over ``roomItems``.
        from holdspeak.services.needs_you_membership import room_part

        return room_part(answer)

    _needs_you_cache = NeedsYouCache(
        _build_needs_you, max_age_s=900.0, db_factory=_get_db,
    )

    # Expose the cache on the context so the cadence tick can invalidate it.
    ctx._needs_you_cache = _needs_you_cache  # type: ignore[attr-defined]

    # ── HS-172-06: suggested sources ────────────────────────────────

    # ── HS-172-07: Room people ──────────────────────────────────────

    return router
