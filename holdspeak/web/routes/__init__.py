"""FastAPI route modules for the web runtime (Phase 26).

Each module exposes a `build_*_router(ctx: WebContext) -> APIRouter` factory that
`MeetingWebServer._create_app` mounts via `app.include_router(...)`. Routers read
all server state from the shared `WebContext` — never the `MeetingWebServer`
instance. During the migration a router may still import server-agnostic, module-
level helpers from `web_server` (e.g. `_meeting_callback_payload`); the load-order
invariant that matters is that `web_server` imports the routes lazily (inside
`_create_app`), so this stays acyclic. `WebContext` imports no route module.
"""

from .activity import build_activity_router
from .core import build_core_router
from .dictation import build_dictation_router
from .meetings import build_meetings_router

__all__ = [
    "build_activity_router",
    "build_core_router",
    "build_dictation_router",
    "build_meetings_router",
]
