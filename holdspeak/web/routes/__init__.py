"""FastAPI route modules for the web runtime (Phase 26).

Each module exposes a `build_*_router(ctx: WebContext) -> APIRouter` factory that
`MeetingWebServer._create_app` mounts via `app.include_router(...)`. Routers read
all server state from the shared `WebContext` — never the `MeetingWebServer`
instance. As of HS-26-06 **no route module imports `web_server`**: single-domain
helpers live in their route module, and the few cross-cutting, server-agnostic
helpers (`_meeting_callback_payload`, `_parse_iso_datetime`, `_UnknownDeviceError`)
live in the neutral `web/runtime_support` module. `WebContext` imports no route
module.
"""

from .activity import build_activity_router
from .authority import build_authority_router
from .cadence import build_cadence_router
from .desk_actuators import build_desk_actuators_router
from .core import build_core_router
from .dictation import build_dictation_router
from .meeting_import import build_meeting_import_router
from .meetings import build_meetings_router
from .mesh import build_mesh_router
from .missioncontrol import build_missioncontrol_router
from .pages import build_pages_router
from .primitives import build_primitives_router
from .projects import build_projects_router
from .setup import build_setup_router
from .sync import build_sync_router
from .system import build_system_router

__all__ = [
    "build_activity_router",
    "build_authority_router",
    "build_cadence_router",
    "build_desk_actuators_router",
    "build_core_router",
    "build_dictation_router",
    "build_meeting_import_router",
    "build_meetings_router",
    "build_mesh_router",
    "build_missioncontrol_router",
    "build_pages_router",
    "build_primitives_router",
    "build_projects_router",
    "build_setup_router",
    "build_sync_router",
    "build_system_router",
]
