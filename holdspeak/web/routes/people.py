"""Authenticated, content-redacting transport for the encrypted People sidecar."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException, Request

from ...principals import UNAUTHENTICATED
from ...services.people_service import PeopleServiceError
from ..context import WebContext


def _failure(exc: PeopleServiceError) -> HTTPException:
    """The public error code deliberately never contains relationship content."""
    code = str(exc)
    if code == "people_owner_required":
        return HTTPException(status_code=403, detail=code)
    if code in {"people_store_unavailable", "people_store_write_failed"}:
        return HTTPException(status_code=503, detail="people_store_unavailable")
    if code.endswith("_not_found"):
        return HTTPException(status_code=404, detail=code)
    return HTTPException(status_code=400, detail=code)


def build_people_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(prefix="/api/people", tags=["people"])
    service = ctx.people_service
    if service is None:
        # Isolated route fixtures must inject the encrypted service.  There is no
        # fallback to the ordinary database or an in-memory plaintext notebook.
        raise RuntimeError("People service is not configured")

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/readiness")
    async def readiness(request: Request) -> dict[str, str]:
        try:
            return service.readiness(principal(request))
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/setup")
    async def setup(request: Request) -> dict[str, str]:
        try:
            return service.setup(principal(request))
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships")
    async def relationships(request: Request, include_archived: bool = False) -> dict[str, list[dict[str, Any]]]:
        try:
            return {"relationships": service.list_relationships(principal(request), include_archived=include_archived)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships", status_code=201)
    async def create_relationship(request: Request, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"relationship": service.create_relationship(principal(request), body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}")
    async def relationship(request: Request, relationship_id: str) -> dict[str, Any]:
        try:
            return {"relationship": service.get_relationship(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/archive")
    async def archive_relationship(request: Request, relationship_id: str) -> dict[str, Any]:
        try:
            return {"relationship": service.archive_relationship(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}/one-on-ones")
    async def one_on_ones(request: Request, relationship_id: str) -> dict[str, list[dict[str, Any]]]:
        try:
            return {"one_on_ones": service.list_one_on_ones(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/one-on-ones", status_code=201)
    async def create_one_on_one(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"one_on_one": service.create_one_on_one(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/one-on-ones/{session_id}/agenda", status_code=201)
    async def add_agenda_item(request: Request, session_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"agenda_item": service.add_agenda_item(principal(request), session_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/requests", status_code=201)
    async def create_request(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"request": service.create_request(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.get("/relationships/{relationship_id}/notes")
    async def notes(request: Request, relationship_id: str) -> dict[str, list[dict[str, Any]]]:
        try:
            return {"notes": service.list_notes(principal(request), relationship_id)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/relationships/{relationship_id}/notes", status_code=201)
    async def create_note(request: Request, relationship_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"note": service.create_note(principal(request), relationship_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    @router.post("/requests/{request_id}/accept")
    async def accept_request(request: Request, request_id: str, body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        try:
            return {"commitment": service.accept_request(principal(request), request_id, body)}
        except PeopleServiceError as exc:
            raise _failure(exc) from exc

    return router
