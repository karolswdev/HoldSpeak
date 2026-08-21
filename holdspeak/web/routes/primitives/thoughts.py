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
    if exc.code == "refinement_continuation_unavailable":
        body["message"] = str(exc)
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
            if set(body) - {"request_id", "raw_text", "source", "initial_note"}:
                raise ValidationError("thought create schema is closed", code="thought_create_request_invalid")
            result = application().create_thought(
                principal(request), request_id=body.get("request_id"),
                raw_text=body.get("raw_text"), source=body.get("source"),
                initial_note=body.get("initial_note"),
            )
            return JSONResponse(result, status_code=201)
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
            if set(body) - {"request_id", "note_id", "expected_source_content_sha256", "expected_source_last_modified"}:
                raise ValidationError("thought adopt schema is closed", code="thought_adopt_request_invalid")
            result = application().adopt_note(
                principal(request), request_id=body.get("request_id"),
                note_id=body.get("note_id"),
                expected_source_content_sha256=body.get("expected_source_content_sha256"),
                expected_source_last_modified=body.get("expected_source_last_modified"),
            )
            return JSONResponse(result, status_code=201)
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/default-context")
    async def get_default_context(request: Request) -> Any:
        try:
            return JSONResponse(application().get_default_context(principal(request)))
        except ServiceError as exc:
            return _error(exc)

    @router.put("/api/thoughts/default-context")
    async def replace_default_context(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"request_id", "expected_revision", "refs"}:
                raise ValidationError("default context commands accept refs and cursors only",
                                      code="default_context_request_invalid")
            return JSONResponse(application().replace_default_context(
                principal(request), request_id=body.get("request_id"),
                expected_revision=body.get("expected_revision"), refs=body.get("refs"),
            ))
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
            return JSONResponse(application().get_original(
                principal(request), thought_id=thought_id
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}/workbench")
    async def workbench(thought_id: str, request: Request) -> Any:
        try:
            return JSONResponse(application().get_workbench(
                principal(request), thought_id=thought_id
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.get("/api/thoughts/{thought_id}/context")
    async def list_context(thought_id: str, request: Request) -> Any:
        try:
            raw_limit = request.query_params.get("limit", "20")
            try: limit = int(raw_limit)
            except ValueError: raise ValidationError("context limit must be an integer", code="context_limit_invalid")
            return JSONResponse(application().list_context(
                principal(request), thought_id=thought_id,
                query=request.query_params.get("query", ""),
                view=request.query_params.get("view", "compact"),
                cursor=request.query_params.get("cursor"), limit=limit,
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/context/{action}")
    async def mutate_context(thought_id: str, action: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"request_id", "ref", "expected_aggregate_revision", "expected_working_revision", "expected_attachment_revision", "workspace_cursor"}:
                raise ValidationError("context commands accept refs and cursors only", code="context_request_invalid")
            return JSONResponse(application().mutate_context(
                principal(request), action=action, thought_id=thought_id,
                ref=str(body.get("ref") or ""), request_id=str(body.get("request_id") or ""),
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
                expected_attachment_revision=body.get("expected_attachment_revision"),
                workspace_cursor=body.get("workspace_cursor"),
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.patch("/api/thoughts/{thought_id}/working")
    async def update(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"expected_aggregate_revision","expected_working_revision","title","body_markdown","tags","workspace_cursor"}:
                raise ValidationError("working update schema is closed", code="thought_update_request_invalid")
            return JSONResponse(application().update_working(
                principal(request), thought_id=thought_id,
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
                title=body.get("title"), body_markdown=body.get("body_markdown"),
                tags=body.get("tags"), workspace_cursor=body.get("workspace_cursor")))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/reconcile")
    async def reconcile(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"expected_aggregate_revision","invocation_id","workspace_cursor"}:
                raise ValidationError("reconcile schema is closed", code="thought_reconcile_request_invalid")
            return JSONResponse(
                application().reconcile(
                    principal(request),
                    thought_id=thought_id,
                    expected_aggregate_revision=body.get("expected_aggregate_revision"),
                    invocation_id=body.get("invocation_id"),
                    workspace_cursor=body.get("workspace_cursor"),
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
            if set(body) - {"request_id","expected_aggregate_revision","expected_working_revision","expected_attachment_revision","workspace_cursor"}:
                raise ValidationError("refine schema is closed", code="thought_refine_request_invalid")
            result = await application().refine(
                principal(request),
                thought_id=thought_id,
                request_id=str(body.get("request_id") or ""),
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
                expected_attachment_revision=body.get("expected_attachment_revision"),
                workspace_cursor=body.get("workspace_cursor"),
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
            if set(body) - {"expected_aggregate_revision","workspace_cursor"}:
                raise ValidationError("stop schema is closed", code="thought_stop_request_invalid")
            result = await application().stop(
                principal(request),
                thought_id=thought_id,
                invocation_id=invocation_id,
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                workspace_cursor=body.get("workspace_cursor"),
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

    @router.post("/api/thoughts/{thought_id}/reviews/{review_result_id}/answer-and-continue")
    async def answer_and_continue(thought_id: str, review_result_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            allowed = {"command_id","answer","expected_aggregate_revision",
                       "expected_working_revision","expected_attachment_revision","workspace_cursor"}
            if set(body) != allowed:
                raise ValidationError("answer-and-continue schema is closed",
                                      code="answer_continue_request_invalid")
            result = await application().answer_and_continue(
                principal(request), thought_id=thought_id, review_result_id=review_result_id,
                command_id=body.get("command_id"), answer=body.get("answer"),
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
                expected_attachment_revision=body.get("expected_attachment_revision"),
                workspace_cursor=body.get("workspace_cursor"),
            )
            return JSONResponse(result, status_code=202)
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/reviews/{review_result_id}/{action}")
    async def review_action(thought_id: str, review_result_id: str, action: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"request_id","expected_aggregate_revision","expected_working_revision","expected_attachment_revision","answer","workspace_cursor"}:
                raise ValidationError("review action schema is closed", code="thought_review_action_request_invalid")
            return JSONResponse(application().act_on_review(
                principal(request), thought_id=thought_id, review_result_id=review_result_id,
                request_id=str(body.get("request_id") or ""), action=action,
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_working_revision=body.get("expected_working_revision"),
                expected_attachment_revision=body.get("expected_attachment_revision"),
                answer=str(body.get("answer") or ""), workspace_cursor=body.get("workspace_cursor"),
            ))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/complete")
    async def complete(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"request_id","expected_aggregate_revision","expected_lifecycle_revision","workspace_cursor"}:
                raise ValidationError("completion schema is closed", code="thought_complete_request_invalid")
            return JSONResponse(application().complete(
                principal(request), thought_id=thought_id,
                request_id=str(body.get("request_id") or ""), expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_lifecycle_revision=body.get("expected_lifecycle_revision"),
                workspace_cursor=body.get("workspace_cursor")))
        except ServiceError as exc:
            return _error(exc)

    @router.post("/api/thoughts/{thought_id}/resume")
    async def resume(thought_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            if set(body) - {"expected_aggregate_revision","expected_lifecycle_revision","workspace_cursor"}:
                raise ValidationError("resume schema is closed", code="thought_resume_request_invalid")
            return JSONResponse(application().resume(principal(request), thought_id=thought_id,
                expected_aggregate_revision=body.get("expected_aggregate_revision"),
                expected_lifecycle_revision=body.get("expected_lifecycle_revision"),
                workspace_cursor=body.get("workspace_cursor")))
        except ServiceError as exc:
            return _error(exc)

    return router
