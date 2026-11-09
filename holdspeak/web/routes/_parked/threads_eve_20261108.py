"""PARKED 20261108 (evening, the unreached-routes census): routes no client calls.

Parked from ``holdspeak/web/routes/threads.py``: POST /api/threads/{thread_id}/compact.
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
from ....services.thread_service import ThreadService, _UNSET
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

    @router.post("/api/threads/{thread_id}/compact")
    async def api_compact_thread(thread_id: str, request: Request) -> Any:
        try:
            result = await _service().compact_thread(_principal(request), thread_id)
            return result
        except (ServiceError, ValidationError) as exc:
            return _error(exc)
        except Exception as exc:
            return error_500(exc, log, "Failed to compact thread")

    return router
