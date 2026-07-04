"""Mission-control bridge routes (HS-82-02).

The Desk consumes exactly the three documents the Delivery
Workbench contract allows a client (their `docs/mission-control.md`
§5) — the state feed, the correlation document, and the event log —
relayed byte-honest from the dw CLI of each rails repo the
operator's project map names. Schema drift and dead CLIs surface
as typed statuses (`compatibility` / `unavailable`) the belt
renders honestly. Design: docs/MISSION_CONTROL_DESK.md §1.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter

from ...logging_config import get_logger
from ..context import WebContext

log = get_logger("web.routes.missioncontrol")


def build_missioncontrol_router(
    ctx: WebContext,
    *,
    runner: Any = None,
    map_path: Optional[Path] = None,
) -> APIRouter:
    """`runner` and `map_path` are test seams (the connector-runtime
    precedent); production uses the defaults."""
    router = APIRouter()

    def _map() -> dict[str, Any]:
        from ...missioncontrol_bridge import load_project_map

        return load_project_map(map_path)

    @router.get("/api/missioncontrol/state")
    async def api_missioncontrol_state() -> Any:
        try:
            from ...missioncontrol_bridge import state_payload

            return state_payload(_map(), runner)
        except Exception as exc:
            log.warning(f"mission control state failed ({exc})")
            return {"repos": [], "error": "mission control state failed"}

    @router.get("/api/missioncontrol/sessions")
    async def api_missioncontrol_sessions() -> Any:
        try:
            from ...missioncontrol_bridge import sessions_payload

            return sessions_payload(_map(), runner)
        except Exception as exc:
            log.warning(f"mission control sessions failed ({exc})")
            return {"status": "unavailable", "detail": "sessions read failed"}

    @router.get("/api/missioncontrol/events")
    async def api_missioncontrol_events(tail: int = 20) -> Any:
        try:
            from ...missioncontrol_bridge import events_payload

            return events_payload(_map(), tail, runner)
        except Exception as exc:
            log.warning(f"mission control events failed ({exc})")
            return {"repos": [], "error": "mission control events failed"}

    return router
