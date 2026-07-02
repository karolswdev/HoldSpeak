"""Meeting / speaker / intel routes (HS-26-02; a package since Phase 72).

The largest cluster moved off `MeetingWebServer._create_app`: meeting
lifecycle + bookmark, meeting-scoped action-item mutations, the DB-backed
meeting/speaker listings and exports, global action-item routes, and the
deferred-intel queue routes. Handlers were moved verbatim — only the closure
target changed from the server instance to the shared `WebContext`.

Phase 72 split the single 1,400-line module into this package. Each submodule
owns one route cluster and exposes `build_<name>_router(ctx)`; this package's
`build_meetings_router` composes them into the one router the app mounts, so
`from .meetings import build_meetings_router` keeps working unchanged.

The lifecycle/mutation handlers read callbacks (`on_*`, `broadcast`) from the
context; the DB-backed read routes close over no server state and call the
module-level `get_database()` directly, exactly as before.
"""

from __future__ import annotations

from fastapi import APIRouter

from ...context import WebContext
from .action_items import build_action_items_router
from .aftercare import build_aftercare_router
from .crud import build_crud_router
from .insights import build_insights_router
from .intel import build_intel_router
from .live import build_live_router
from .speakers import build_speakers_router

__all__ = ["build_meetings_router"]


def build_meetings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    router.include_router(build_live_router(ctx))
    router.include_router(build_crud_router(ctx))
    router.include_router(build_speakers_router(ctx))
    router.include_router(build_insights_router(ctx))
    router.include_router(build_aftercare_router(ctx))
    router.include_router(build_action_items_router(ctx))
    router.include_router(build_intel_router(ctx))
    return router
