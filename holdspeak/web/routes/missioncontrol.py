"""The iPad belt's two reads (HS-82-02, HS-88-03).

The iPad desk (`apple/App/MeetingCapture/DeskBelt.swift`, through
`HTTPDesktopClient+MissionControl.swift`) polls the rails state feed and the
rails observer's journal. These are the only callers left.

The rest of Mission control (the web belt, its reads, the rails size and the
`dw story` proposal flow) is parked in `_parked/missioncontrol_20261109.py`:
Programs own delivery now.
"""
from __future__ import annotations

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
    from ... import operations
    from ...parity_operations import PARITY_OPERATIONS
    from ...services.delivery_service import DeliveryService
    from ._produced import envelope

    service = ctx.delivery_service
    if service is None:
        service = DeliveryService(None)
        ctx.delivery_service = service
    service.configure(runner=runner, map_path=map_path)
    from ..operation_routes import operation_router
    answer = envelope(log, "Failed to read the belt")
    def registry():
        return operations.for_context(ctx, delivery_service=lambda: service)

    def state(descriptor):
        async def api_missioncontrol_state(request: Request):
            from ...principals import UNAUTHENTICATED
            who = getattr(request.state, "principal", UNAUTHENTICATED)
            return await answer(lambda: registry().invoke(who, descriptor.name))
        return api_missioncontrol_state

    def journal(descriptor):
        async def api_missioncontrol_rails_journal(request: Request, limit: int = 50):
            from ...principals import UNAUTHENTICATED
            who = getattr(request.state, "principal", UNAUTHENTICATED)
            return await answer(lambda: registry().invoke(who, descriptor.name, {"limit": limit}))
        return api_missioncontrol_rails_journal

    return operation_router(
        [d for d in PARITY_OPERATIONS if d.name.startswith("delivery.belt.")], registry, answer, module=__name__,
        hand_written={"delivery.belt.state": state, "delivery.belt.journal": journal})
