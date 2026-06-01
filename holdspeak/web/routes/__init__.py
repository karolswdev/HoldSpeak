"""FastAPI route modules for the web runtime (Phase 26).

Each module exposes a `build_*_router(ctx: WebContext) -> APIRouter` factory that
`MeetingWebServer._create_app` mounts via `app.include_router(...)`. Routers read
from the shared `WebContext`; they never import the server.
"""

from .core import build_core_router

__all__ = ["build_core_router"]
