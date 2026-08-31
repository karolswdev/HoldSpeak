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
from .automations import build_automations_router
from .authority import build_authority_router
from .cadence import build_cadence_router
from .calendar_snapshot import build_calendar_snapshot_router
from .decisions import build_decisions_router
from .desk_actuators import build_desk_actuators_router
from .desk_seed import build_desk_seed_router
from .core import build_core_router
from .delivery import build_delivery_router
from .delivery_attempts import build_delivery_attempts_router
from .delivery_prs import build_delivery_prs_router
from .delivery_dossiers import build_delivery_dossiers_router
from .delivery_node import build_delivery_node_router
from .delivery_terminal import build_delivery_terminal_router
from .delivery_factory import build_delivery_factory_router
from .dictation import build_dictation_router
from .door import build_door_router
from .front_door import build_front_door_router
from .follow_through import build_follow_through_router
from .people import build_people_router
from .meeting_import import build_meeting_import_router
from .meetings import build_meetings_router
from .memory import build_memory_router
from .model_library import build_model_library_router
from .inference_assignments import build_inference_assignments_router
from .monday_brief import build_monday_brief_router
from .mesh import build_mesh_router
from .missioncontrol import build_missioncontrol_router
from .pages import build_pages_router
from .constitutional import build_constitutional_router
from .primitives import build_primitives_router
from .projections import build_projections_router
from .projects import build_projects_router
from .roadmaps import build_roadmaps_router
from .repositories import build_repositories_router
from .decision_records import build_decision_records_router
from .scheduled_recordings import build_scheduled_recordings_router
from .setup import build_setup_router
from .sync import build_sync_router
from .system import build_system_router
from .threads import build_threads_router
from .tts import build_tts_router
from .project_setup import build_project_setup_router
from .watches import build_watches_router

__all__ = [
    "build_activity_router",
    "build_automations_router",
    "build_authority_router",
    "build_cadence_router",
    "build_calendar_snapshot_router",
    "build_decisions_router",
    "build_desk_actuators_router",
    "build_desk_seed_router",
    "build_core_router",
    "build_delivery_router",
    "build_delivery_attempts_router",
    "build_delivery_prs_router",
    "build_delivery_dossiers_router",
    "build_delivery_node_router",
    "build_delivery_terminal_router",
    "build_delivery_factory_router",
    "build_dictation_router",
    "build_door_router",
    "build_front_door_router",
    "build_follow_through_router",
    "build_people_router",
    "build_meeting_import_router",
    "build_meetings_router",
    "build_memory_router",
    "build_model_library_router",
    "build_inference_assignments_router",
    "build_monday_brief_router",
    "build_mesh_router",
    "build_missioncontrol_router",
    "build_pages_router",
    "build_primitives_router",
    "build_projections_router",
    "build_projects_router",
    "build_roadmaps_router",
    "build_repositories_router",
    "build_decision_records_router",
    "build_constitutional_router",
    "build_scheduled_recordings_router",
    "build_setup_router",
    "build_sync_router",
    "build_system_router",
    "build_threads_router",
    "build_tts_router",
    "build_project_setup_router",
    "build_watches_router",
]
