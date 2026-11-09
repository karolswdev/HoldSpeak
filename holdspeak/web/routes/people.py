"""Authenticated, content-redacting transport for the encrypted People sidecar."""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Callable

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from ...principals import UNAUTHENTICATED
from ...services.people_service import OwnerAliasTaken, PeopleServiceError, SeriesAlreadyLinked
from ...services.errors import NotFound
from ... import operations
from ...operations import OperationOwnerRequired, OperationRefused
from ...people_operations import workbenches
from ..context import WebContext
from ..operation_routes import operation_router
from ._mount import mount_router


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


def build_people_router(ctx: WebContext) -> APIRouter:
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

    @router.get("/readiness")
    def readiness(request: Request) -> dict[str, str]:
        try:
            return service.readiness(principal(request))
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/resolve")
    def resolve(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        """HS-172-04: resolve a Watch identity to a People relationship id.

        Returns only the relationship id -- never the name or alias
        (Article III: nothing crosses the People boundary).
        """
        try:
            identity = str(body.get("identity") or "").strip()
            if not identity:
                return {"relationship_id": None}
            result = service.resolve_relationship_by_watch_identity(identity)
            rel = result.get("relationship")
            return {"relationship_id": rel.get("id") if rel else None}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/suggestions")
    def suggestions(request: Request) -> dict[str, Any]:
        """Betterment D6: names from his meetings, calendar and Jira that no
        Person has yet. A read; adding one is the owner's press."""
        try:
            from ...db import get_database
            return {"suggestions": service.suggestions(principal(request), db=get_database())}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships")
    def relationships(
        request: Request, include_archived: bool = False, counts: bool = False,
    ) -> dict[str, list[dict[str, Any]]]:
        # PHILO-17 (MUST 4): `?counts=1` adds you_owe_count and owes_you_count
        # to each row (the owner's faces: one bounded read for the totals).
        try:
            from ...db import get_database
            return {"relationships": service.list_relationships(
                principal(request), include_archived=include_archived, with_counts=counts,
                db=get_database() if counts else None,
            )}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships", status_code=201)
    def create_relationship(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.create_relationship(principal(request), body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}")
    def relationship(request: Request, relationship_id: str) -> dict[str, Any]:
        try:
            from ...db import get_database
            return {"relationship": service.get_relationship(
                principal(request), relationship_id, db=get_database(),
            )}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}/brief")
    def relationship_brief(request: Request, relationship_id: str) -> dict[str, Any]:
        """HS-149-04: read-time 1:1 brief across the encrypted/plaintext boundary."""
        try:
            from ...db import get_database
            db = get_database()
            return {"brief": service.one_on_one_brief(principal(request), relationship_id, db=db)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/one-on-ones", status_code=201)
    def create_one_on_one(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"one_on_one": service.create_one_on_one(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/one-on-ones/{session_id}/agenda", status_code=201)
    def add_agenda_item(request: Request, session_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"agenda_item": service.add_agenda_item(principal(request), session_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/requests", status_code=201)
    def create_request(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"request": service.create_request(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/notes", status_code=201)
    def create_note(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"note": service.create_note(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/requests/{request_id}/accept")
    def accept_request(request: Request, request_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"commitment": service.accept_request(principal(request), request_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/commitments/{commitment_id}/execution")
    def commitment_execution(request: Request, commitment_id: str) -> dict[str, Any]:
        try:
            commitment = service.get_commitment(principal(request), commitment_id)
            items = []
            wb = workbenches()
            for link in commitment.get("execution_links") or []:
                if not isinstance(link, dict) or link.get("kind") != "workbench_item":
                    continue
                try:
                    item = wb.get_item(principal(request), str(link.get("workbench_id") or ""), str(link.get("item_id") or ""))
                except NotFound:
                    item = {**link, "status": "missing", "result": None, "result_artifact_id": None}
                items.append(item)
            return {"commitment": commitment, "items": items}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/commitments/{commitment_id}/transition")
    def transition_commitment(
        request: Request,
        commitment_id: str,
        body: dict[str, Any] = Body(default={}),
    ) -> dict[str, Any]:
        """Browser twin of the MCP commitment-transition application call."""
        try:
            # The done receipt itself (card_id, verb, status, done_at): the
            # shape /api/follow-through/complete answers.
            return service.transition(
                principal(request),
                f"people:{commitment_id}",
                str(body.get("verb") or ""),
            )
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    # 2026-11-08 (one contract): the verbs of ``holdspeak/people_operations.py``,
    # produced through ``OperationRegistry.invoke`` with the words above.
    produced = APIRouter(tags=["people"], dependencies=[Depends(note_caller)])
    produced.include_router(operation_router(
        operations.PEOPLE_OPERATIONS, lambda: operations.for_context(ctx), _answer, module=__name__))
    both = APIRouter()
    mount_router(both, router)
    mount_router(both, produced)
    return both


async def _answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
    """The produced verbs answer as the hand-written routes did: ``{"detail": code}`` on a refusal."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except PeopleServiceError as exc:
        refused = _failure(exc)
    except OperationOwnerRequired:
        refused = HTTPException(status_code=403, detail="people_owner_required")
    except OperationRefused as exc:
        refused = HTTPException(status_code=400, detail=exc.code)
    return JSONResponse({"detail": refused.detail}, status_code=refused.status_code)
