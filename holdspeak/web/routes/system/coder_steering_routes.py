"""Coder steering routes: watch, authorize, deliver, audit, and the factory.

2026-11-09 (one contract): produced from the declared rows in
``holdspeak/coder_operations.py`` (``CoderService`` verbs) with the board's
registry and envelope (``coders.py``). ``coder.steer`` and ``coder.keys`` hold
the hub's process-input services (its command service and target registry):
no client sends them. The relay routes (``/api/coders/relay/{node}/*``) stay
hand-written in ``coder_relay_routes.py``: they forward to another machine.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...context import WebContext
from .._mount import mount_router
from .coder_relay_routes import register_relay_routes
from .coder_steering_support import ProcessInputServices
from .coders import Holding, produce, registry_for

#: The factory and steering rows, in route order.
FACTORY = ("coder.spawn", "coder.rename")
STEERING = ("coder.peek", "coder.arm", "coder.disarm", "coder.grants", "coder.nodes", "coder.panes",
            "coder.kill", "coder.audit", "coder.keep_note")
DELIVERY = ("coder.steer", "coder.keys")


def build_coder_steering_router(
    ctx: WebContext, *, commands: Any = None, targets: Any = None
) -> APIRouter:
    router = APIRouter()
    registry = registry_for(ctx)
    mount_router(router, produce(FACTORY, registry))
    register_relay_routes(router)
    mount_router(router, produce(STEERING, registry))
    process_input: list[ProcessInputServices] = []

    def held() -> dict[str, Any]:
        """One process-input adapter per router, over the service the steer is bound to."""
        if not process_input:
            service = registry().target("coder.steer")
            process_input.append(ProcessInputServices(service=service, commands=commands, targets=targets))
        return {"process_input": process_input[0]}

    holding = Holding(registry, held)
    mount_router(router, produce(DELIVERY, lambda: holding))
    return router
