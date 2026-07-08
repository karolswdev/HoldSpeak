"""The system routes, composed (HS-79-02).

One public constructor, unchanged: ``build_system_router`` includes the
single-concern routers (health, the coder board, the steering surface,
settings, the voice lane, the /ws socket). Bodies moved verbatim from the
1,299-line routes/system.py; steering carved out at HS-87-03.
"""
from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from .coder_steering_routes import build_coder_steering_router
from .coders import build_coders_router
from .health import build_health_router
from .settings import build_settings_router
from .voice import build_voice_router
from .ws import build_ws_router


def build_system_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    router.include_router(build_health_router(ctx))
    router.include_router(build_coders_router(ctx))
    router.include_router(build_coder_steering_router(ctx))
    router.include_router(build_settings_router(ctx))
    router.include_router(build_voice_router(ctx))
    router.include_router(build_ws_router(ctx))
    return router
