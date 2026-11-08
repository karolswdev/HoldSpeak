"""PARKED 20261108 (subtraction day, Lane R): routes no client reads.

Parked from ``holdspeak/web/routes/system/coders.py``: POST /api/coders/clear-stale.
Not imported. Kept for history; restore with ``git revert`` of the parking commit.
"""
from __future__ import annotations
"""The coder board: which live coding session receives a spoken answer.

Bodies moved verbatim from routes/system.py (HS-79-02, the Phase-63 discipline).
The steering surface (attach/arm/steer/audit) is a sibling concern in
`coder_steering_routes.py` (HS-87-03); `_coder_frame` and
`_session_age_seconds` are shared from here.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from .....logging_config import get_logger
from .....services.coder_service import CoderService
from ....context import WebContext

log = get_logger("web.routes.system")

_COMPANION_TARGET_MAX_AGE_SECONDS = 120
_COMPANION_OVERVIEW_MAX_AGE_SECONDS = 30 * 60


def _coder_frame(ctx: WebContext, key: str) -> None:
    """One `scope:"coder"` frame on the one bus — arming moved, a grant
    expired, an awaiting flag flipped; every surface hears the same
    motion (the HS-86-03 frame shape, coder scope)."""
    if ctx.broadcast is None:
        return
    try:
        ctx.broadcast(
            "intel_status",
            {
                "state": "ready",
                "scope": "coder",
                "capability": {
                    "kind": "coder",
                    "id": key,
                    "name": key.split(":", 1)[0],
                },
            },
        )
    except Exception as exc:
        log.debug(f"coder frame dropped: {exc}")


def _session_age_seconds(stamp: Optional[str], now: datetime) -> Optional[int]:
    """Seconds since an ISO-8601 session timestamp, or None if unparseable."""
    if not isinstance(stamp, str) or not stamp.strip():
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, int((now - parsed).total_seconds()))




def parked_build_coders_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    def _companion_agent_target(payload: Optional[dict[str, Any]]) -> tuple[str, str] | JSONResponse:
        """Pull a required (agent, session_id) pair from a control-route body."""
        body = payload if isinstance(payload, dict) else {}
        agent = body.get("agent")
        session_id = body.get("session_id")
        if not isinstance(agent, str) or not agent.strip():
            return JSONResponse({"error": "agent is required"}, status_code=400)
        if not isinstance(session_id, str) or not session_id.strip():
            return JSONResponse({"error": "session_id is required"}, status_code=400)
        return agent, session_id

    def _service() -> CoderService:
        from .....db import get_database, get_observer

        return CoderService(get_database(), observer=get_observer())

    @router.post("/api/coders/clear-stale")
    def api_companion_clear_stale(payload: Optional[dict[str, Any]] = None) -> Any:
        """Clear all non-pinned waiting sessions older than the threshold."""
        from .....agent_context import (
            DEFAULT_STALE_AGENT_SESSION_SECONDS,
            clear_stale_agent_sessions,
        )

        body = payload if isinstance(payload, dict) else {}
        raw_age = body.get("max_age_seconds")
        try:
            max_age_seconds = int(raw_age) if raw_age is not None else DEFAULT_STALE_AGENT_SESSION_SECONDS
        except (TypeError, ValueError):
            return JSONResponse({"error": "max_age_seconds must be an integer"}, status_code=400)
        if max_age_seconds < 0:
            return JSONResponse({"error": "max_age_seconds must be >= 0"}, status_code=400)
        cleared = clear_stale_agent_sessions(max_age_seconds=max_age_seconds)
        return JSONResponse(
            {"success": True, "cleared": cleared, "max_age_seconds": max_age_seconds}
        )


    return router
