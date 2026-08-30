"""Recipe routes — thin FastAPI adapters over :class:`RecipeService` (HS-122-03)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import Principal, PrincipalKind
from ....services.errors import NotFound, ServiceError, ValidationError
from ....services.recipe_service import RecipeService
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _run_frame

log = get_logger("web.routes.primitives")


def build_recipes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> RecipeService:
        from ....db import get_database, get_observer
        return RecipeService(get_database(), observer=get_observer())

    def _principal(request: Request) -> Principal:
        return getattr(
            request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session")
        )

    def _broadcast(state: str, **frame: Any) -> None:
        _run_frame(ctx, state, **frame)

    def _service_error(exc: ServiceError) -> JSONResponse:
        statuses = {"empty_input": 400, "target_unavailable": 409, "inference_failed": 502, "failed": 502, "cancelled": 409, "refused": 409, "indeterminate": 409, "empty_output": 502, "artifact_persist_failed": 500, "grounding_not_found": 400}
        return JSONResponse({"error": exc.detail, **exc.context}, status_code=int(exc.context.get("status", statuses.get(exc.code, 500))))

    @router.get("/api/recipes")
    async def api_list_recipes(request: Request) -> Any:
        try:
            kind = request.query_params.get("kind")
            if kind is not None:
                return JSONResponse({"recipes": _svc().list_recipes(_principal(request), kind=kind)})
            return JSONResponse({"recipes": _svc().list_recipes(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list recipes")

    @router.post("/api/recipes")
    async def api_create_recipe(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            fields = dict(body)
            recipe_id = str(fields.pop("id", "") or fields.pop("recipe_id", "") or "") or None
            recipe = _svc().create_recipe(
                _principal(request), recipe_id=recipe_id, **fields
            )
            return JSONResponse({"recipe": recipe}, status_code=201)
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, "Failed to create recipe")

    @router.get("/api/recipes/{recipe_id}")
    async def api_get_recipe(recipe_id: str, request: Request) -> Any:
        try:
            return JSONResponse({"recipe": _svc().get_recipe(_principal(request), recipe_id)})
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to get recipe")

    @router.put("/api/recipes/{recipe_id}")
    async def api_update_recipe(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            return JSONResponse({
                "recipe": _svc().update_recipe(_principal(request), recipe_id, **body)
            })
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to update recipe")

    @router.delete("/api/recipes/{recipe_id}")
    async def api_delete_recipe(recipe_id: str, request: Request) -> Any:
        try:
            _svc().delete_recipe(_principal(request), recipe_id)
            return JSONResponse({"success": True})
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except Exception as exc:
            return error_500(exc, log, "Failed to delete recipe")

    @router.post("/api/recipes/{recipe_id}/run")
    async def api_run_recipe(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        try:
            result = await _svc().run(
                _principal(request), recipe_id, broadcast=_broadcast, **body
            )
            return JSONResponse(result)
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to run recipe")

    @router.post("/api/recipes/{recipe_id}/chat")
    async def api_chat_recipe(recipe_id: str, request: Request) -> Any:
        # HS-151-04: recipe.chat is now an alias that creates/reuses a thread
        # bound to this recipe and starts a turn with the body's text.
        from .._thread_factory import thread_service_from_ctx
        from ....db import get_database
        body = await _json_body(request) or {}
        text = str(body.get("text") or body.get("question") or "")
        if not text.strip():
            return JSONResponse({"error": "text is required"}, status_code=400)
        db = get_database()
        thread_svc = thread_service_from_ctx(ctx)
        # Reuse newest non-deleted thread with this recipe_id, or create one.
        existing = [t for t in db.threads.list(limit=50) if t.recipe_id == recipe_id]
        if existing:
            thread_id = existing[0].id
        else:
            created = thread_svc.create(recipe_id=recipe_id, title=recipe_id)
            thread_id = created["id"]
        try:
            result = await thread_svc.start_turn(
                _principal(request), thread_id, text,
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to chat via recipe alias")

    @router.post("/api/recipes/{recipe_id}/keep")
    async def api_keep_recipe_reply(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        try:
            result = _svc().keep(
                _principal(request), recipe_id,
                output=str(body.get("output") or ""), input=str(body.get("question") or ""),
                sources=body.get("sources") if isinstance(body.get("sources"), list) else None,
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep chat reply")

    @router.post("/api/recipes/{recipe_id}/invocations/{invocation_id}/cancel")
    async def api_cancel_recipe_invocation(recipe_id: str, invocation_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_svc().cancel(_principal(request), invocation_id))
        except ServiceError as exc:
            return _service_error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to cancel recipe invocation")

    return router
