"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/people.py``: GET /history.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Authenticated, content-redacting transport for the encrypted People sidecar."""

import logging
from contextvars import ContextVar
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from ....principals import UNAUTHENTICATED
from ....services.people_service import OwnerAliasTaken, PeopleServiceError, SeriesAlreadyLinked
from ....services.workbench_service import WorkbenchService
from .... import operations
from ...context import WebContext


log = logging.getLogger(__name__)

#: Betterment D6: the request a People failure answers, for the 503 log line.
_CALLER: ContextVar[str] = ContextVar("people_route_caller", default="")
#: The service whose readiness a 503 log line reads (set per router).
_SERVICE: ContextVar[Any] = ContextVar("people_route_service", default=None)


def _log_unavailable(code: str) -> None:
    """Every People 503 says the store's readiness and who asked, so the
    open intermittent 503 (daily MODEL.md §1) can be traced. No content."""
    service = _SERVICE.get()
    try:
        readiness = service.readiness_state() if service is not None else "no_service"
    except Exception as exc:  # the read that failed is itself the answer
        readiness = f"readiness_raised:{type(exc).__name__}"
    log.warning("people 503: code=%s readiness=%s caller=%s", code, readiness, _CALLER.get() or "unknown")


def _failure(exc: PeopleServiceError) -> HTTPException:
    """The public error code deliberately never contains relationship content."""
    code = str(exc)
    if code in {"people_plaintext_unavailable", "people_store_unavailable", "people_store_write_failed"}:
        _log_unavailable(code)
    if code == "people_owner_required":
        return HTTPException(status_code=403, detail=code)
    if code in {"people_plaintext_unavailable", "people_key_store_unavailable"}:
        return HTTPException(status_code=503, detail=code)
    if code in {"people_store_unavailable", "people_store_write_failed"}:
        return HTTPException(status_code=503, detail="people_store_unavailable")
    if code == "series_already_linked" and isinstance(exc, SeriesAlreadyLinked):
        return HTTPException(status_code=409, detail={
            "code": "series_already_linked",
            "holder_id": exc.holder_id,
            "holder_name": exc.holder_name,
        })
    if code == "owner_alias_taken" and isinstance(exc, OwnerAliasTaken):
        return HTTPException(status_code=409, detail={
            "code": "owner_alias_taken",
            "holder_id": exc.holder_id,
            "holder_name": exc.holder_name,
        })
    if code == "owner_alias_reserved":
        return HTTPException(status_code=422, detail=code)
    if code.endswith("_not_found"):
        return HTTPException(status_code=404, detail=code)
    return HTTPException(status_code=400, detail=code)


def parked_build_people_router(ctx: WebContext) -> APIRouter:
    service = ctx.people_service
    if service is None:
        # Isolated route fixtures must inject the encrypted service.  There is no
        # fallback to the ordinary database or an in-memory plaintext notebook.
        raise RuntimeError("People service is not configured")

    async def note_caller(request: Request) -> None:
        # The face that asked (its Referer) and the route; never a body.
        _CALLER.set(f"{request.method} {request.url.path} from {request.headers.get('referer') or '-'}")
        _SERVICE.set(service)

    router = APIRouter(prefix="/api/people", tags=["people"], dependencies=[Depends(note_caller)])

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    def workbenches() -> WorkbenchService:
        # HS-200-45: the hub's ONE composed instance (on_changed -> the bus).
        if getattr(ctx, "workbench_service", None) is not None:
            return ctx.workbench_service
        from ....db import get_database, get_observer
        return WorkbenchService(get_database(), observer=get_observer())

    def projects() -> Any:
        """PHILO-9-01: the Room's declared operations on the hub's ProjectService."""
        return operations.for_context(ctx, "project_service")

    @router.get("/history")
    def history(request: Request, relationship_id: str | None = None) -> dict[str, Any]:
        try:
            return {"history": service.history_summary(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    return router
