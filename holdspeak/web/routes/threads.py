"""Thread HTTP routes (HS-151-04).

CRUD + turn + abort + branch + regenerate + keep + import.
No SSE — the bus is the one live channel (Art. I, one bus).
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import db as hsdb
from ...principals import Principal, PrincipalKind
from ...services.errors import ServiceError, ValidationError
from ...services.thread_service import ThreadService, _UNSET
from ..context import WebContext
from ..runtime_support import error_500
from ...logging_config import get_logger

log = get_logger("web.routes.threads")


def _database() -> Any:
    return getattr(hsdb, "get_database")()


async def _json_body(request: Request) -> dict[str, Any] | None:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else None
    except Exception:
        return None


def _normalize_refs(raw: Any) -> list[str] | None:
    """Accept refs as ``["kind:id", ...]`` OR ``[{ref_kind, ref_id}, ...]``.

    The composer sends the object shape; the CLI may send strings.  Normalize
    both to qualified ``"kind:id"`` strings for ``start_turn``.
    """
    if not isinstance(raw, list):
        return None
    result: list[str] = []
    for item in raw:
        if isinstance(item, str):
            result.append(item)
        elif isinstance(item, dict) and item.get("ref_kind") and item.get("ref_id"):
            result.append(f"{item['ref_kind']}:{item['ref_id']}")
        elif isinstance(item, dict) and item.get("kind") and item.get("id"):
            result.append(f"{item['kind']}:{item['id']}")
    return result or None


def build_threads_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _principal(request: Request) -> Principal:
        return getattr(
            request.state,
            "principal",
            Principal(PrincipalKind.OWNER, "owner-session"),
        )

    def _service() -> ThreadService:
        # One factory shared with the recipe chat alias (HS-151-04).
        from ._thread_factory import thread_service_from_ctx
        return thread_service_from_ctx(ctx)

    def _error(exc: ServiceError) -> JSONResponse:
        payload = dict(exc.context)
        payload.setdefault("error", exc.detail)
        status = int(payload.pop("status", 400 if exc.code == "validation_error" else 409))
        return JSONResponse(payload, status_code=status)

    # ── Thread CRUD ─────────────────────────────────────────────────

    @router.post("/api/threads")
    async def api_create_thread(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _service().create(
                title=str(body.get("title") or ""),
                recipe_id=str(body.get("recipe_id") or ""),
                seed_refs=body.get("seed_refs") if isinstance(body.get("seed_refs"), list) else None,
                profile_override=str(body.get("profile_override") or ""),
            )
            return JSONResponse(result, status_code=201)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to create thread")

    @router.get("/api/threads")
    async def api_list_threads(request: Request) -> Any:
        try:
            limit = int(request.query_params.get("limit", 100))
            ref_id = str(request.query_params.get("ref_id", ""))
            return JSONResponse({"threads": _service().list_threads(limit=limit, ref_id=ref_id)})
        except Exception as exc:
            return error_500(exc, log, "Failed to list threads")

    @router.get("/api/threads/{thread_id}")
    async def api_get_thread(thread_id: str, request: Request) -> Any:
        try:
            return JSONResponse(_service().get(thread_id))
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to get thread")

    @router.patch("/api/threads/{thread_id}")
    async def api_patch_thread(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _service().patch(
                thread_id,
                title=body.get("title"),
                profile_override=body.get("profile_override"),
            )
            return JSONResponse(result)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to patch thread")

    @router.delete("/api/threads/{thread_id}")
    async def api_delete_thread(thread_id: str, request: Request) -> Any:
        try:
            deleted = _service().soft_delete(thread_id)
            if not deleted:
                return JSONResponse({"error": "thread_not_found"}, status_code=404)
            return JSONResponse({"deleted": True})
        except Exception as exc:
            return error_500(exc, log, "Failed to delete thread")

    # ── Turn ────────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/turns")
    async def api_start_turn(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await _service().start_turn(
                _principal(request),
                thread_id,
                str(body.get("text") or ""),
                refs=_normalize_refs(body.get("refs")),
                parent_id=body.get("parent_id") if "parent_id" in body else _UNSET,
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to start turn")

    # ── Abort ───────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/abort")
    async def api_abort(thread_id: str, request: Request) -> Any:
        try:
            result = _service().abort(thread_id)
            return JSONResponse(result)
        except Exception as exc:
            return error_500(exc, log, "Failed to abort")

    # ── Branch ──────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/branch")
    async def api_branch(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await _service().branch(
                _principal(request),
                thread_id,
                str(body.get("message_id") or ""),
                str(body.get("text") or ""),
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to branch")

    # ── Regenerate ──────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/regenerate")
    async def api_regenerate(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = await _service().regenerate(
                _principal(request),
                thread_id,
                str(body.get("message_id") or ""),
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to regenerate")

    # ── Keep ────────────────────────────────────────────────────────

    @router.post("/api/threads/{thread_id}/keep")
    async def api_keep(thread_id: str, request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            result = _service().keep(
                _principal(request),
                thread_id,
                str(body.get("message_id") or ""),
                as_kind=str(body.get("as") or "artifact"),
            )
            return JSONResponse(result, status_code=201)
        except ValidationError as exc:
            return JSONResponse({"error": str(exc), "code": exc.code}, status_code=400)
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to keep")

    # ── Import ──────────────────────────────────────────────────────

    @router.post("/api/threads/import")
    async def api_import_threads(request: Request) -> Any:
        body = await _json_body(request)
        if body is None:
            return JSONResponse({"error": "expected a JSON object"}, status_code=400)
        try:
            payload = body.get("threads") if isinstance(body.get("threads"), list) else []
            result = _service().import_threads(payload)
            return JSONResponse({"imported": result})
        except Exception as exc:
            return error_500(exc, log, "Failed to import threads")

    return router
