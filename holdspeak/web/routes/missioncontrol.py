"""The iPad belt's two reads (HS-82-02, HS-88-03).

The iPad desk (`apple/App/MeetingCapture/DeskBelt.swift`, through
`HTTPDesktopClient+MissionControl.swift`) polls the rails state feed and the
rails observer's journal. These are the only callers left.

The rest of Mission control (the web belt, its reads, the rails size and the
`dw story` proposal flow) is parked in `_parked/missioncontrol_20261109.py`:
Programs own delivery now.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Request

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
    del ctx
    router = APIRouter()

    def _principal(request: Request):
        from ...principals import UNAUTHENTICATED

        return getattr(request.state, "principal", UNAUTHENTICATED)

    @router.get("/api/missioncontrol/state")
    async def api_missioncontrol_state(request: Request) -> Any:
        try:
            from ...missioncontrol_bridge import load_project_map, state_payload

            # to_thread: the bridge runs a CLI per repo.
            return await asyncio.to_thread(
                state_payload,
                load_project_map(map_path),
                runner,
                principal=_principal(request),
            )
        except Exception as exc:
            log.warning(f"mission control state failed ({exc})")
            return {"repos": [], "error": "mission control state failed"}

    @router.get("/api/missioncontrol/rails/journal")
    async def api_missioncontrol_rails_journal(limit: int = 50) -> Any:
        """The rails observer's journal, newest first."""
        try:
            from ...db import get_database
            from ...rails_observer import list_journal

            entries = await asyncio.to_thread(
                lambda: list_journal(get_database(), limit=limit)
            )
            return {"entries": [
                {
                    "id": note.id,
                    "title": note.title,
                    "body_markdown": note.body_markdown,
                    "created_at": getattr(note, "created_at", ""),
                }
                for note in entries
            ]}
        except Exception as exc:
            log.warning(f"rails journal read failed ({exc})")
            return {"entries": [], "error": "rails journal read failed"}

    return router
