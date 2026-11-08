"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/threads.py``: POST /api/threads/{thread_id}/agent, GET /api/threads/{thread_id}/interview/promotions.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""Thread HTTP routes (HS-151-04).

CRUD + turn + abort + branch + regenerate + keep + import.
No SSE — the bus is the one live channel (Art. I, one bus).
"""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import db as hsdb
from ....principals import Principal, PrincipalKind
from ....services.errors import ServiceError, ValidationError
from ....services.thread_service import ThreadService
from ...context import WebContext
from ...runtime_support import error_500
from ....logging_config import get_logger

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


# HS-200-10: `promote` and `revoke_promotion` join the BROWSER allowlist and
# nothing else. The MCP interview family gains no tool: a model that could mint
# a canonical record is the precise failure the People boundary exists to
# prevent. The model records; the owner disposes (ruling C6 as amended).
#
# Hoisted out of the handler so the asymmetry is testable as DATA -- the guard
# that certifies it reads this set and the MCP dispatcher's own kind map, and
# the route below is the only consumer, so the two cannot drift.
INTERVIEW_BROWSER_EVENT_KINDS = frozenset(
    {"section", "remove_fact", "disposition", "status", "promote", "revoke_promotion"}
)


def parked_build_threads_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _principal(request: Request) -> Principal:
        return getattr(
            request.state,
            "principal",
            Principal(PrincipalKind.OWNER, "owner-session"),
        )

    def _service() -> ThreadService:
        # One factory shared with the recipe chat alias (HS-151-04).
        from .._thread_factory import thread_service_from_ctx
        return thread_service_from_ctx(ctx)

    def _error(exc: ServiceError) -> JSONResponse:
        payload = dict(exc.context)
        payload.setdefault("error", exc.detail)
        status = int(payload.pop("status", 400 if exc.code == "validation_error" else 409))
        return JSONResponse(payload, status_code=status)

    # ── Thread CRUD ─────────────────────────────────────────────────

    @router.get("/api/threads/{thread_id}/interview/promotions")
    def api_interview_promotions(thread_id: str, request: Request) -> Any:
        # HS-200-10 (AC4): the read half. `promotion_id` otherwise existed only
        # inside the single `promote` response, so nothing the owner could reach
        # named a promotion and `revoke_promotion` was unreachable. Owner-only,
        # enforced in the service exactly as the verbs are. Routes only --
        # there is no MCP tool here either.
        from ....services.interview_service import InterviewService
        try:
            promotions = InterviewService(_service()._db).promotions(_principal(request), thread_id)
            return JSONResponse({"promotions": promotions})
        except ServiceError as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to list interview promotions")

    # ── Turn ────────────────────────────────────────────────────────

    # ── Abort ───────────────────────────────────────────────────────

    # ── Branch ──────────────────────────────────────────────────────

    # ── Regenerate ──────────────────────────────────────────────────

    # ── Keep ────────────────────────────────────────────────────────

    # ── Import ──────────────────────────────────────────────────────

    # ── Tool decision (HS-152-02) ──────────────────────────────────

    # ── Annotations (HS-153-04) ────────────────────────────────────

    # ── HS-153-05: compaction + todo ─────────────────────────────────

    @router.post("/api/threads/{thread_id}/agent")
    async def api_agent(thread_id: str, request: Request) -> Any:
        """``/agent <text>``: file the text as an action item, then hand it
        to a coding agent (Conductor K2)."""
        body = await _json_body(request)
        text = str((body or {}).get("text", "")).strip()
        if not text:
            return JSONResponse(
                {"error": "agent_empty", "message": "Text is required"},
                status_code=400,
            )
        try:
            result = await _service().agent_from_thread(
                _principal(request), thread_id, text,
                profile=(body or {}).get("profile") or None,
                project_id=(body or {}).get("project_id") or None,
            )
            status = 202 if result.get("status") == "ok" else 409
            return JSONResponse(result, status_code=status)
        except (ServiceError, ValidationError) as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to hand to agent")

    return router
