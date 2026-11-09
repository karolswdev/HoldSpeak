"""Recipe routes — thin FastAPI adapters over :class:`RecipeService` (HS-122-03).

The writes (create, change, delete) are produced from
``holdspeak/recipe_operations.py`` through ``OperationRegistry.invoke``
(2026-11-09); the list and the run stay hand-written."""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .... import operations
from ....logging_config import get_logger
from ....principals import Principal, PrincipalKind
from ....services.errors import NotFound, ServiceError, ValidationError
from ....services.recipe_service import RecipeService
from ...context import WebContext
from ...operation_routes import operation_router
from ...runtime_support import error_500
from .._mount import mount_router
from ._shared import _json_body, _run_frame

log = get_logger("web.routes.primitives")


#: The 500 words of each produced route (the hand-written handlers' words).
_FAILED = {"recipe.create": "Failed to create recipe", "recipe.update": "Failed to update recipe",
           "recipe.delete": "Failed to delete recipe"}


def _answer(name: str) -> Callable[..., Any]:
    async def answer(fn: Callable[[], Any], *, status: int = 200) -> JSONResponse:
        try:
            return JSONResponse(await run_in_threadpool(fn), status_code=status)
        except NotFound as exc:
            return JSONResponse({"error": exc.detail}, status_code=404)
        except (ValidationError, ValueError, operations.OperationRefused) as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return error_500(exc, log, _FAILED[name])

    return answer


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
    def api_list_recipes(request: Request) -> Any:
        try:
            kind = request.query_params.get("kind")
            if kind is not None:
                return JSONResponse({"recipes": _svc().list_recipes(_principal(request), kind=kind)})
            return JSONResponse({"recipes": _svc().list_recipes(_principal(request))})
        except Exception as exc:
            return error_500(exc, log, "Failed to list recipes")

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

    def _registry() -> Any:
        return operations.for_context(ctx, recipe_service=_svc)

    for descriptor in operations.RECIPE_OPERATIONS:
        mount_router(router, operation_router([descriptor], _registry, _answer(descriptor.name), module=__name__))

    return router
