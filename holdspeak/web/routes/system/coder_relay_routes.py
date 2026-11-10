"""Owner relay routes, declared HTTP-only because the hub holds node credentials."""
from __future__ import annotations
from typing import Any
from fastapi import APIRouter
from .._mount import mount_router
from .coders import produce


def register_relay_routes(router: APIRouter, registry: Any) -> None:
    from ....coder_operations import CODER_OPERATIONS

    mount_router(router, produce(tuple(op.name for op in CODER_OPERATIONS
        if op.name.startswith("coder.relay.")), registry))
