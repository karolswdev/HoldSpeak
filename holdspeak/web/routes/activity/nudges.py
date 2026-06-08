"""Activity pre-briefing nudge routes (Phase 53, HS-53-02).

Thin HTTP surface over `holdspeak.activity_nudges.compute_nudges` and
`ActivityRepository.dismiss_nudge`:

- `GET /api/activity/nudges` — compute the current nudges (dismissed ones already
  filtered by the engine), return the top N with citations. Returns an empty
  ``nudges: []`` when activity tracking is off — the engine handles the gate.
- `POST /api/activity/nudges/{nudge_id}/dismiss` — persist a dismissal so the
  same nudge does not return. ``nudge_id`` is the deterministic ``Nudge.key``
  (e.g. ``record:42`` or ``window:2026-06-08T12:00:00``).
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ....logging_config import get_logger
from ...context import WebContext
from ...runtime_support import error_500

log = get_logger("web.routes.activity.nudges")


def build_nudges_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()

    @router.get("/api/activity/nudges")
    async def api_activity_nudges(
        project_id: Optional[str] = None,
        limit: int = 3,
    ) -> Any:
        try:
            from ....activity_nudges import compute_nudges
            from ....db import get_database

            db = get_database()
            nudges = compute_nudges(db, project_id=project_id, limit=limit)
            settings = db.activity.get_activity_privacy_settings()
            return JSONResponse(
                {
                    "nudges": [n.to_dict() for n in nudges],
                    "activity_enabled": bool(settings.get("enabled", False)),
                }
            )
        except Exception as e:
            return error_500(e, log, "Failed to compute activity nudges")

    @router.post("/api/activity/nudges/{nudge_id}/dismiss")
    async def api_dismiss_activity_nudge(nudge_id: str) -> Any:
        try:
            from ....db import get_database

            clean = (nudge_id or "").strip()
            if not clean:
                return JSONResponse(
                    {"error": "nudge_id is required"}, status_code=400
                )
            db = get_database()
            db.activity.dismiss_nudge(clean)
            return JSONResponse({"dismissed": clean})
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        except Exception as e:
            return error_500(e, log, "Failed to dismiss activity nudge")

    return router
