# PARKED 2026-11-09 (ops/programs-work): the last automations router, kept verbatim.
# Its one called route, PATCH /api/workbenches/{id}/automations/{automation_id} (the
# Automations face's event-start switch), is the declared row
# automation.event_start.set_enabled (automation_operations.py) now. Six routes no
# client calls are parked with it: list, create, test and history of an event start,
# and the resourceful policy (GET/PUT /api/workbenches/{id}/resourceful). The face
# makes an event start through automation.set_when.
# Not mounted, not imported. Restore with git revert of the parking commit.
# ruff: noqa
"""HTTP adapters for an Automation's event starts and its resourceful policy.

An event start is a watch (WatchService, the watch fold of 2026-11-08). The
route owns only request/response shaping. The legacy Watch, service-event and
Reaction routes are parked in ``_parked/automations_reactions.py``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from ...db import get_database, get_observer
from ...principals import UNAUTHENTICATED
from ...services.errors import NotFound, ServiceError, ValidationError
from ...web_requests import (
    _ReactionEnabledRequest,
    _ResourcefulPolicyRequest,
    _WorkbenchAutomationCreateRequest,
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


def build_automations_router(ctx: WebContext) -> APIRouter:
    """Mount an Automation's event-start and resourceful routes (owner only)."""
    from ...services.resourceful_service import ResourcefulService
    from ...services.watch_service import WatchService

    router = APIRouter(prefix="/api", tags=["automations"])
    composed = getattr(ctx, "watch_service", None)
    db = composed._db if composed is not None else get_database()
    resourceful = ResourcefulService(db)

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def watches() -> Any:
        """The one watch service (an Automation's event start is a watch)."""
        return composed if composed is not None else WatchService(db, observer=get_observer())

    def _is_watch_start(workbench_id: str, automation_id: str) -> bool:
        from ...services.watch_service import AUTOMATION_INTENT_PREFIX

        watch = db.automations.get_watch(automation_id)
        return bool(watch) and watch.get("intent") == AUTOMATION_INTENT_PREFIX + workbench_id

    def _with_pattern(watch: dict[str, Any]) -> dict[str, Any]:
        from ...services.watch_service import _automation_event_pattern

        return {**watch, "event_pattern": _automation_event_pattern(
            db.automations.list_rules(str(watch.get("id") or "")))}

    @router.get("/workbenches/{workbench_id}/automations")
    def list_workbench_automations(workbench_id: str, request: Request) -> Any:
        try:
            if db.workbenches.get(workbench_id) is None:
                raise NotFound("workbench", workbench_id)
            starts = [_watch_automation_view(watch)
                      for watch in watches().automation_event_watches(workbench_id)]
            return JSONResponse({"automations": starts})
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
            raise NotFound("automation event", automation_id)
        except ServiceError as exc:
            return _error(exc)

    @router.post("/workbenches/{workbench_id}/automations/{automation_id}/test")
    def test_workbench_automation(
        workbench_id: str, automation_id: str, request: Request,
    ) -> Any:
        try:
            if _is_watch_start(workbench_id, automation_id):
                return JSONResponse(watches().test_watch(principal(request), automation_id))
            raise NotFound("automation event", automation_id)
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
            raise NotFound("automation event", automation_id)
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

    return router


__all__ = ["build_automations_router"]
