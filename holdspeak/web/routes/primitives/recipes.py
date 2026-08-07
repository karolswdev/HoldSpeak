"""Recipe routes — thin FastAPI adapters over :class:`RecipeService` (HS-122-03)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ....principals import Principal, PrincipalKind
from ....services.primitive_service import NotFound, ValidationError
from ....services.recipe_service import RecipeService, RecipeServiceError
from ...context import WebContext
from ...runtime_support import error_500
from ._shared import _json_body, _run_frame

log = get_logger("web.routes.primitives")


def build_recipes_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _svc() -> RecipeService:
        from ....db import get_database
        return RecipeService(get_database())

    def _principal(request: Request) -> Principal:
        return getattr(
            request.state, "principal", Principal(PrincipalKind.OWNER, "owner-session")
        )

    def _broadcast(state: str, **frame: Any) -> None:
        _run_frame(ctx, state, **frame)

    @router.get("/api/recipes")
    async def api_list_recipes(request: Request) -> Any:
        try:
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
        except RecipeServiceError as exc:
            return JSONResponse(exc.payload, status_code=exc.status_code)
        except Exception as exc:
            return error_500(exc, log, "Failed to run recipe")

    @router.post("/api/recipes/{recipe_id}/chat")
    async def api_chat_recipe(recipe_id: str, request: Request) -> Any:
        body = await _json_body(request) or {}
        try:
            result = await _svc().chat(
                _principal(request), recipe_id,
                question=str(body.get("question") or ""),
                history=body.get("history") if isinstance(body.get("history"), list) else [],
                grounding=body.get("grounding"),
                inference_target_id=body.get("inference_target_id"),
                broadcast=_broadcast,
                egress_context=ctx,
            )
            return JSONResponse(result)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except NotFound:
            return JSONResponse({"error": f"Unknown Agent: {recipe_id}"}, status_code=404)
        except RecipeServiceError as exc:
            return JSONResponse(exc.payload, status_code=exc.status_code)
        except Exception as exc:
            return error_500(exc, log, "Failed to chat with recipe")

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
        except RecipeServiceError as exc:
            return JSONResponse(exc.payload, status_code=exc.status_code)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep chat reply")

    return router
