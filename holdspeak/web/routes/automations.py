"""HTTP adapters for typed service-event Watches and Workbench Reactions.

The route owns only request/response shaping.  Event durability, snapshot
comparison, projection idempotency, and kernel-backed Workbench execution stay
inside :class:`ReactionService`.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ...services.reaction_service import ReactionService
from ...web_requests import (
    _ReactionCreateRequest,
    _ReactionEnabledRequest,
    _ReactionProcessRequest,
    _ResourcefulPolicyRequest,
    _WorkbenchAutomationCreateRequest,
    _WatchCreateRequest,
    _WatchEnabledRequest,
)
from ..context import WebContext


def _error(exc: ServiceError) -> JSONResponse:
    """Map stable service failures without exposing an implementation trace."""
    if isinstance(exc, NotFound):
        status = 404
    elif isinstance(exc, ValidationError):
        status = 400
    else:
        status = int(exc.context.get("status") or 400)
    return JSONResponse(
        {"error": exc.detail, "code": exc.code, **exc.context}, status_code=status
    )


def _automation_view(value: dict[str, Any]) -> dict[str, Any]:
    """Shape the Workbench product read model; never leak persistence joins."""
    reaction = value.get("reaction") or value
    watch = value.get("watch") or {}
    connector = str(watch.get("connector_id") or "custom")
    provider = "github" if connector == "gh" else connector
    # HS-166: jira graduated the watch_sources gate (JiraWatchSource);
    # the read surface must not call a working adapter unavailable.
    adapter_status = "ready" if connector in ("gh", "jira") else "unavailable"
    enabled = bool(reaction.get("enabled")) and (
        not watch or bool(watch.get("enabled"))
    )
    if watch.get("last_error"):
        status = "attention"
    elif adapter_status == "unavailable":
        status = "unavailable"
    else:
        status = "active" if enabled else "paused"
    query = watch.get("query") if isinstance(watch.get("query"), dict) else {}
    return {
        "id": reaction.get("id") or value.get("id"),
        "name": reaction.get("name") or "Event automation",
        "provider": provider,
        "event_kind": reaction.get("event_pattern") or "",
        "enabled": enabled,
        "status": status,
        "adapter_status": adapter_status,
        "last_error": watch.get("last_error"),
        "last_good_at": watch.get("last_success_at"),
        "created_at": reaction.get("created_at"),
        "repository": query.get("repository"),
    }


def _watch_automation_view(watch: dict[str, Any]) -> dict[str, Any]:
    """The same product row for an event start that is a watch (2026-11-08)."""
    connector = str(watch.get("connector_id") or "custom")
    adapter_status = "ready" if connector in ("gh", "jira") else "unavailable"
    enabled = watch.get("state") in {"active", "tested"}
    if watch.get("last_error"):
        status = "attention"
    elif adapter_status == "unavailable":
        status = "unavailable"
    else:
        status = "active" if enabled else "paused"
    query = watch.get("query") if isinstance(watch.get("query"), dict) else {}
    return {
        "id": watch.get("id"),
        "name": watch.get("name") or "Event automation",
        "provider": "github" if connector == "gh" else connector,
        "event_kind": watch.get("event_pattern") or "",
        "enabled": enabled,
        "status": status,
        "adapter_status": adapter_status,
        "last_error": watch.get("last_error"),
        "last_good_at": watch.get("last_success_at"),
        "created_at": watch.get("created_at"),
        "repository": query.get("repository"),
    }


def _watch_history_view(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": value.get("item_id"),
        "occurred_at": value.get("created_at"),
        "outcome": "added",
        "event_kind": value.get("event_type") or "",
        "subject": value.get("entity_ref") or "",
        "receipt_id": None,
        "detail": None,
    }


def _history_view(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f'{value.get("reaction_id")}:{value.get("event_id")}',
        "occurred_at": value.get("projected_at") or value.get("event_created_at"),
        "outcome": "added",
        "event_kind": value.get("event_type") or "",
        "subject": value.get("subject_ref") or "",
        "receipt_id": value.get("receipt_id"),
        "detail": None,
    }


def build_automations_router(ctx: WebContext) -> APIRouter:
    """Mount the owner-only Watches, service-event, and Reactions API.

    The central web auth gate assigns the OWNER right to all routes below
    ``/api/automations`` before these adapters run.  Passing the edge principal
    through still keeps the application service usable from other transports.
    """
    router = APIRouter(prefix="/api", tags=["automations"])
    service = ctx.reaction_service
    if service is None:  # compatibility composition for isolated route fixtures
        service = ReactionService(get_database(), observer=get_observer())
    from ...services.resourceful_service import ResourcefulService

    resourceful = ResourcefulService(service._db)

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def watches() -> Any:
        """The one watch service (an Automation's event start is a watch)."""
        from ...services.watch_service import WatchService

        return WatchService(service._db, observer=get_observer())

    def _is_watch_start(workbench_id: str, automation_id: str) -> bool:
        from ...services.watch_service import AUTOMATION_INTENT_PREFIX

        watch = service._db.automations.get_watch(automation_id)
        return bool(watch) and watch.get("intent") == AUTOMATION_INTENT_PREFIX + workbench_id

    def _with_pattern(watch: dict[str, Any]) -> dict[str, Any]:
        from ...services.watch_service import _automation_event_pattern

        return {**watch, "event_pattern": _automation_event_pattern(
            service._db.automations.list_rules(str(watch.get("id") or "")))}

    @router.get("/automations/watches")
    def list_watches(request: Request) -> Any:
        try:
            return JSONResponse({"watches": service.list_watches(principal(request))})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/automations/watches", status_code=201)
    def create_watch(request: Request, payload: _WatchCreateRequest) -> Any:
        try:
            return JSONResponse(
                {"watch": service.create_watch(principal(request), **payload.model_dump())},
                status_code=201,
            )
        except ServiceError as exc:
            return _error(exc)

    @router.put("/automations/watches/{watch_id}/enabled")
    def set_watch_enabled(
        watch_id: str, request: Request, payload: _WatchEnabledRequest
    ) -> Any:
        try:
            return JSONResponse(
                {"watch": service.set_watch_enabled(principal(request), watch_id, payload.enabled)}
            )
        except ServiceError as exc:
            return _error(exc)

    @router.post("/automations/watches/{watch_id}/test")
    def test_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.preview_watch(principal(request), watch_id))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/automations/watches/{watch_id}/baseline")
    def baseline_watch(watch_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service.establish_baseline(principal(request), watch_id))
        except ServiceError as exc:
            return _error(exc)

    @router.get("/automations/events")
    def list_events(
        request: Request,
        event_type: str | None = None,
        producer: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> Any:
        try:
            return JSONResponse({"events": service.list_events(
                principal(request), event_type=event_type, producer=producer, limit=limit,
            )})
        except ServiceError as exc:
            return _error(exc)

    @router.get("/automations/presets")
    def list_presets(request: Request) -> Any:
        try:
            return JSONResponse({"presets": service.list_presets(principal(request))})
        except ServiceError as exc:
            return _error(exc)

    @router.get("/automations/reactions")
    def list_reactions(request: Request) -> Any:
        try:
            return JSONResponse({"reactions": service.list_reactions(principal(request))})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/automations/reactions", status_code=201)
    def create_reaction(request: Request, payload: _ReactionCreateRequest) -> Any:
        try:
            return JSONResponse(
                {"reaction": service.create_reaction(
                    principal(request), **payload.model_dump(), auto_run=False,
                )},
                status_code=201,
            )
        except ServiceError as exc:
            return _error(exc)

    @router.put("/automations/reactions/{reaction_id}/enabled")
    def set_reaction_enabled(
        reaction_id: str, request: Request, payload: _ReactionEnabledRequest
    ) -> Any:
        try:
            return JSONResponse({"reaction": service.set_reaction_enabled(
                principal(request), reaction_id, payload.enabled,
            )})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/automations/reactions/process")
    async def process_reactions(
        request: Request, payload: _ReactionProcessRequest | None = None
    ) -> Any:
        try:
            limit = payload.limit if payload is not None else 100
            return JSONResponse({"projections": await service.process_pending(
                principal(request), limit=limit,
            )})
        except ServiceError as exc:
            return _error(exc)

    @router.get("/workbenches/{workbench_id}/automations")
    def list_workbench_automations(workbench_id: str, request: Request) -> Any:
        try:
            values = service.list_workbench_automations(principal(request), workbench_id)
            starts = [_watch_automation_view(watch)
                      for watch in watches().automation_event_watches(workbench_id)]
            return JSONResponse({"automations": starts + [_automation_view(value) for value in values]})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/workbenches/{workbench_id}/automations", status_code=201)
    def create_workbench_automation(
        workbench_id: str, request: Request, payload: _WorkbenchAutomationCreateRequest,
    ) -> Any:
        try:
            # 2026-11-08: a new event start is a watch, read and on at once.
            value = watches().start_automation_event(
                principal(request), workbench_id=workbench_id,
                preset_id=payload.preset_id, repository=payload.repository or "",
            )
            return JSONResponse({"automation": _watch_automation_view(_with_pattern(value))}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.patch("/workbenches/{workbench_id}/automations/{automation_id}")
    def set_workbench_automation_enabled(
        workbench_id: str, automation_id: str, request: Request,
        payload: _ReactionEnabledRequest,
    ) -> Any:
        try:
            if _is_watch_start(workbench_id, automation_id):
                value = watches().set_automation_event_enabled(
                    principal(request), workbench_id=workbench_id,
                    watch_id=automation_id, enabled=payload.enabled,
                )
                return JSONResponse({"automation": _watch_automation_view(_with_pattern(value))})
            value = service.set_workbench_automation_enabled(
                principal(request), workbench_id=workbench_id,
                reaction_id=automation_id, enabled=payload.enabled,
            )
            return JSONResponse({"automation": _automation_view(value)})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/workbenches/{workbench_id}/automations/{automation_id}/test")
    def test_workbench_automation(
        workbench_id: str, automation_id: str, request: Request,
    ) -> Any:
        try:
            if _is_watch_start(workbench_id, automation_id):
                return JSONResponse(watches().test_watch(principal(request), automation_id))
            return JSONResponse(service.test_workbench_automation(
                principal(request), workbench_id=workbench_id, reaction_id=automation_id,
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.get("/workbenches/{workbench_id}/automations/{automation_id}/history")
    def workbench_automation_history(
        workbench_id: str, automation_id: str, request: Request,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> Any:
        try:
            if _is_watch_start(workbench_id, automation_id):
                rows = watches().automation_event_history(
                    principal(request), workbench_id=workbench_id,
                    watch_id=automation_id, limit=limit,
                )
                return JSONResponse({"history": [_watch_history_view(row) for row in rows]})
            values = service.workbench_automation_history(
                principal(request), workbench_id=workbench_id,
                reaction_id=automation_id, limit=limit,
            )
            return JSONResponse({"history": [_history_view(value) for value in values]})
        except ServiceError as exc:
            return _error(exc)

    @router.get("/workbenches/{workbench_id}/resourceful")
    def get_resourceful_policy(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"policy": resourceful.get_policy(
                principal(request), workbench_id,
            )})
        except ServiceError as exc:
            return _error(exc)

    @router.put("/workbenches/{workbench_id}/resourceful")
    def configure_resourceful_policy(
        workbench_id: str, request: Request, payload: _ResourcefulPolicyRequest,
    ) -> Any:
        try:
            return JSONResponse({"policy": resourceful.configure_policy(
                principal(request), workbench_id, **payload.model_dump(),
            )})
        except ServiceError as exc:
            return _error(exc)

    @router.get("/workbenches/{workbench_id}/resourceful/history")
    def resourceful_history(workbench_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"history": resourceful.history(
                principal(request), workbench_id,
            )})
        except ServiceError as exc:
            return _error(exc)

    return router


__all__ = ["build_automations_router"]
