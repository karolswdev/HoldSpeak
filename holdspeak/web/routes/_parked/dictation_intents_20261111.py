# PARKED: no live caller of the intent HTTP controls; MCP keeps the operations.
"""Intent routes produced from the dictation service's declared operations."""

from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from holdspeak.web.routes.dictation._declared import build_declared_router


def build_intents_router(ctx: WebContext) -> APIRouter:
    return build_declared_router(
        ctx, ("intents.controls", "intents.profile", "intents.preview")
    )
