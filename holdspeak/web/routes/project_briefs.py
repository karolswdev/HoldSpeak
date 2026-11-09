"""HS-200-11: the preparation brief routes -- the verb wire.

GET  /api/projects/{id}/briefs/route    -- the route the model drafter would use (no dispatch)
GET  /api/projects/{id}/briefs/manifest -- the manifest a prepare would bind now (no write)
POST /api/projects/{id}/briefs/prepare  -- prepare (body {purpose, generator?, attempt_id?})
POST /api/projects/{id}/briefs/stop     -- stop an attempt (body {attempt_id}); no orphan draft
GET  /api/projects/{id}/briefs          -- list (lifecycle-filterable; discarded hidden)
GET  /api/briefs/{id}                   -- one brief, manifest integrity re-verified
POST /api/briefs/{id}/keep              -- the lifecycle flip
POST /api/briefs/{id}/discard           -- a state, never a DELETE

Parse-and-serialize ONLY; the service owns logic.  A refused preparation is a
409 carrying the bounded route state AND the purpose, so the face keeps the
owner's words and draws the repair (AC5).
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ... import operations
from ...logging_config import get_logger
from ...project_operations import PROJECT_OPERATIONS
from ...services.errors import ConflictError, NotFound, ValidationError
from ...services.preparation_brief_service import PreparationRefused
from ..context import WebContext
from ..operation_routes import _invoke, _principal
from ._produced import envelope, produced

log = get_logger("web.routes.project_briefs")


def _prepare(registry: Callable[[], Any], answer: Any) -> Callable[[Any], Callable[..., Any]]:
    """The prepare route: the declared ``project.brief.prepare``, off the event
    loop, so the stop route can land while it runs; the route watches for the
    client leaving, and a Stop that aborted the fetch stops the attempt, so the
    completing run writes no draft (P1-4)."""

    def build(descriptor: Any) -> Callable[..., Any]:
        async def api_prepare_brief(project_id: str, request: Request) -> Any:
            try:
                payload = await request.json()
            except Exception:
                payload = None
            if not isinstance(payload, dict):
                return JSONResponse({"error": "expected a JSON object", "error_code": "validation_error"},
                                    status_code=422)
            args = {**payload, "project_id": project_id}
            attempt_id = str(payload.get("attempt_id") or "").strip()
            who = _principal(request)
            task = asyncio.ensure_future(asyncio.to_thread(_invoke, registry, who, descriptor.name, args))
            while not task.done():
                await asyncio.wait({task}, timeout=0.25)
                if task.done() or not attempt_id:
                    continue
                try:
                    gone = await request.is_disconnected()
                except Exception:
                    gone = False
                if gone:
                    _invoke(registry, who, "project.brief.stop", {"project_id": project_id, "attempt_id": attempt_id})
            return await answer(task.result)

        return api_prepare_brief

    return build


def build_project_briefs_router(ctx: WebContext) -> APIRouter:
    """HS-200-11's routes, produced from their declared rows (``project_operations.py``).

    A refused preparation is a 409 carrying the bounded route state AND the
    purpose, so the face keeps the owner's words and draws the repair (AC5)."""
    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx)

    answer = envelope(log, "Failed to run the brief verb", statuses={
        PreparationRefused: 409, NotFound: 404, ValidationError: 422, ConflictError: 409})
    return produced(ctx, [d for d in PROJECT_OPERATIONS if d.service == "project_brief_service"], answer,
                    module=__name__, hand_written={"project.brief.prepare": _prepare(registry, answer)})
