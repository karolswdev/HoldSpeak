"""HS-141-01 refinement-thought custody routes."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....services.errors import ConflictError, NotFound, ServiceError, ValidationError
from ....services.refinement_thought_service import RefinementThoughtService
from ....principals import UNAUTHENTICATED
from ...context import WebContext
from ._shared import _json_body


def _error(exc: ServiceError) -> JSONResponse:
    body = {"error": exc.code, **exc.context}
    if isinstance(exc, ConflictError):
        return JSONResponse(body, status_code=409)
    if isinstance(exc, NotFound):
        return JSONResponse(body, status_code=404)
    status = exc.context.get("status") if isinstance(exc.context, dict) else None
    fallback = 422 if isinstance(exc, ValidationError) else 400
    return JSONResponse(
        body, status_code=int(status) if isinstance(status, int) else fallback
    )


def build_thoughts_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def service() -> RefinementThoughtService:
        from ....db import get_database
        return RefinementThoughtService(get_database())

    def application() -> Any:
        if ctx.refinement_service is not None:
            return ctx.refinement_service
        from ....db import get_database
        from ....services.refinement_application_service import RefinementApplicationService

        return RefinementApplicationService(
            get_database(), coordinator=ctx.refinement_coordinator
        )

    def principal(request: Request) -> Any:
        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.post("/api/thoughts")
    async def create(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            thought = service().create(principal(request), request_id=str(body.get("request_id") or ""),
                                       raw_text=body.get("raw_text"), source=body.get("source"),
                                       initial_note=body.get("initial_note"))
            return JSONResponse({"thought": thought}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts")
    async def list_unfinished(request: Request) -> Any:
        try:
            state = request.query_params.get("state", "unfinished")
            if state != "unfinished":
                raise ValidationError("only unfinished thoughts can be listed", code="thought_list_state_invalid")
            raw_limit = request.query_params.get("limit", "20")
            try: limit = int(raw_limit)
            except ValueError: raise ValidationError("limit must be an integer", code="thought_list_limit_invalid")
            page = service().list_unfinished(principal(request), limit=limit, cursor=request.query_params.get("cursor"))
            return JSONResponse(page)
        except ServiceError as exc:
            return _error(exc)

    # Static Note lookup must precede `/{thought_id}` so a Note id can never be
    # mistaken for a thought id by route matching.
    @router.get("/api/thoughts/for-note/{note_id}")
    async def for_note(note_id: str, request: Request) -> Any:
        try:
            return JSONResponse(service().for_note(principal(request), note_id))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/adopt")
    async def adopt(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            thought = service().adopt_note(
                principal(request), request_id=str(body.get("request_id") or ""), note_id=str(body.get("note_id") or ""),
                expected_source_content_sha256=str(body.get("expected_source_content_sha256") or ""),
                expected_source_last_modified=str(body.get("expected_source_last_modified") or ""),
            )
            return JSONResponse({"thought": thought}, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}")
    async def get(thought_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"thought": service().get(principal(request), thought_id)})
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}/original")
    async def original(thought_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"thought": service().get(principal(request), thought_id, include_raw=True)})
        except ServiceError as exc:
            return _error(exc)

    @router.patch("/api/thoughts/{thought_id}/working")
    async def update(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            thought = service().update_working(principal(request), thought_id,
                                               expected_aggregate_revision=body.get("expected_aggregate_revision"),
                                               expected_working_revision=body.get("expected_working_revision"),
                                               title=body.get("title"), body_markdown=body.get("body_markdown"),
                                               tags=body.get("tags"))
            return JSONResponse({"thought": thought})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/reconcile")
    async def reconcile(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse(
                application().reconcile(
                    principal(request),
                    thought_id=thought_id,
                    expected_aggregate_revision=body.get("expected_aggregate_revision"),
                    invocation_id=body.get("invocation_id"),
                )
            )
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/refine")
    async def refine(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await application().refine(
                principal(request),
                thought_id=thought_id,
                request_id=str(body.get("request_id") or ""),
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
                expected_attachment_revision=body.get("expected_attachment_revision"),
            )
            return JSONResponse(result, status_code=202)
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/refinements/{invocation_id}/stop")
    async def stop_refinement(thought_id: str, invocation_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await application().stop(
                principal(request),
                thought_id=thought_id,
                invocation_id=invocation_id,
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
            )
            return JSONResponse(result)
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}/reviews/{review_result_id}")
    async def review(thought_id: str, review_result_id: str, request: Request) -> Any:
        try:
            return JSONResponse(
                application().review(
                    principal(request),
                    thought_id=thought_id,
                    review_result_id=review_result_id,
                )
            )
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/reviews/{review_result_id}/{action}")
    async def review_action(thought_id: str, review_result_id: str, action: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse(
                application().act_on_review(
                    principal(request),
                    thought_id=thought_id,
                    review_result_id=review_result_id,
                    request_id=str(body.get("request_id") or ""),
                    action=action,
                    expected_aggregate_revision=body.get("expected_aggregate_revision"),
                    expected_working_revision=body.get("expected_working_revision"),
                    expected_attachment_revision=body.get("expected_attachment_revision"),
                    answer=str(body.get("answer") or ""),
                )
            )
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/complete")
    async def complete(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            thought, receipt = service().complete_with_receipt(principal(request), thought_id,
                request_id=str(body.get("request_id") or ""), expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_lifecycle_revision=body.get("expected_lifecycle_revision"))
            return JSONResponse({"thought": thought, "receipt": receipt})
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/resume")
    async def resume(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({"thought": service().resume(principal(request), thought_id,
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_lifecycle_revision=body.get("expected_lifecycle_revision"))})
        except ServiceError as exc:
            return _error(exc)

    return router
