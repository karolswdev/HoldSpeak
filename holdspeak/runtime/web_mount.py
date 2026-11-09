"""Mount every hub router on the app, in the hub's one mount order.

Split from :meth:`holdspeak.web_server.MeetingWebServer._create_app`
(2026-11-08). ``_create_app`` composes the hub (``compose_hub``,
``compose_delivery``), calls :func:`mount_routers`, and registers the
lifespan. The order of the mounts below is the order the app matches
overlapping paths in: keep it (``tests/unit/test_web_mount.py`` holds the
recorded route list). This module never imports ``holdspeak.web_server``.
"""

from __future__ import annotations

from typing import Any, Optional

from holdspeak.runtime.hub_composition import HubComposition
from holdspeak.web.routes._mount import mount_router


def mount_routers(app: Any, hub: HubComposition, *, auth_token: Optional[str]) -> None:
    """Mount every router on ``app`` with the composed hub's WebContext.

    ``hub`` carries the delivery fields too (``compose_delivery`` has run).
    """
    web_ctx = hub.web_ctx
    from holdspeak.web.routes import (
        build_activity_router,
        build_automations_router,
        build_authority_router,
        build_cadence_router,
        build_calendar_snapshot_router,
        build_calendar_sources_router,
        build_core_router,
        build_decisions_router,
        build_delivery_router,
        build_delivery_attempts_router,
        build_delivery_dossiers_router,
        build_delivery_prs_router,
        build_delivery_node_router,
        build_delivery_terminal_router,
        build_delivery_factory_router,
        build_dictation_router,
        build_door_router,
        build_concierge_router,
        build_follow_through_router,
        build_proposal_router,
        build_people_router,
        build_desk_actuators_router,
        build_desk_seed_router,
        build_desk_parked_router,
        build_desk_windows_router,
        build_meeting_import_router,
        build_meetings_router,
        build_memory_router,
        build_model_library_router,
        build_inference_assignments_router,
        build_monday_brief_router,
        build_today_router,
        build_mesh_router,
        build_missioncontrol_router,
        build_constitutional_router,
        build_pages_router,
        build_primitives_router,
        build_projections_router,
        build_projects_router,
        build_roadmaps_router,
        build_repositories_router,
        build_decision_records_router,
        build_scheduled_recordings_router,
        build_setup_router,
        build_sync_router,
        build_system_router,
        build_threads_router,
        build_tts_router,
        build_project_reviews_router,
        build_project_door_router,
        build_project_setup_router,
        build_project_updates_router,
        build_channels_router,
        build_project_briefs_router,
        build_providers_router,
        build_connections_router,
        build_steward_router,
        build_watches_router,
        build_mcp_http_router,
    )
    mount_router(app, build_core_router(web_ctx))
    mount_router(app, build_authority_router(web_ctx))
    mount_router(app, build_cadence_router(web_ctx))
    mount_router(app, build_calendar_snapshot_router(web_ctx))
    mount_router(app, build_calendar_sources_router(web_ctx))
    mount_router(app, build_follow_through_router(web_ctx))
    mount_router(app, build_proposal_router(web_ctx))
    mount_router(app, build_door_router(web_ctx))
    mount_router(app, build_concierge_router(web_ctx))
    mount_router(app, build_people_router(web_ctx))
    mount_router(app, build_automations_router(web_ctx))
    mount_router(app, build_decision_records_router(web_ctx))
    mount_router(app, build_decisions_router(web_ctx))
    mount_router(app, build_memory_router(web_ctx))
    mount_router(app, build_model_library_router(web_ctx))
    mount_router(app, build_inference_assignments_router(web_ctx))
    mount_router(app, build_monday_brief_router(web_ctx))
    mount_router(app, build_today_router(web_ctx))
    mount_router(app, build_meetings_router(web_ctx))
    mount_router(app, build_desk_actuators_router(web_ctx))
    mount_router(app, build_desk_seed_router(web_ctx))
    mount_router(app, build_desk_parked_router(web_ctx))
    mount_router(app, build_desk_windows_router(web_ctx))
    mount_router(app, build_meeting_import_router(web_ctx))
    mount_router(app, build_mesh_router(web_ctx))
    mount_router(app, build_missioncontrol_router(web_ctx))
    mount_router(app, build_delivery_router(web_ctx))
    mount_router(app, build_delivery_attempts_router(web_ctx))
    mount_router(app, build_delivery_dossiers_router(web_ctx))
    mount_router(app, build_delivery_prs_router(web_ctx))
    from holdspeak.web.routes.agent_hand import build_agent_hand_router

    mount_router(app, build_agent_hand_router(web_ctx))  # Conductor K2: Hand to an agent session
    mount_router(app, build_repositories_router(web_ctx))

    # One delivery spine (2026-11-09, one contract): the node link, the
    # terminal command service and target registry the hub built are the
    # DeliveryService's own, so a factory launch issues its envelopes and
    # pins the spawned pane's target on the same spine the terminals read.
    web_ctx.delivery_service.configure(
        link=hub.delivery_link, web_token=auth_token, commands=hub.delivery_cmd,
        targets=hub.delivery_targets, live=hub.delivery_live,
    )
    mount_router(app, build_delivery_node_router(web_ctx))
    mount_router(app, build_delivery_terminal_router(web_ctx))
    mount_router(app, build_delivery_factory_router(web_ctx))
    mount_router(app, build_dictation_router(web_ctx))
    mount_router(app, build_activity_router(web_ctx))
    mount_router(app, build_pages_router(web_ctx))
    mount_router(app,
        build_system_router(
            web_ctx, commands=hub.delivery_cmd, targets=hub.delivery_targets
        )
    )
    mount_router(app, build_projects_router(web_ctx))
    mount_router(app, build_roadmaps_router(web_ctx))
    mount_router(app, build_primitives_router(web_ctx))
    mount_router(app, build_projections_router(web_ctx))
    mount_router(app, build_constitutional_router())
    mount_router(app, build_scheduled_recordings_router(web_ctx))
    mount_router(app, build_setup_router(web_ctx))
    from holdspeak.web.routes.onboarding import build_onboarding_router

    mount_router(app, build_onboarding_router(web_ctx))
    mount_router(app, build_sync_router(web_ctx))
    mount_router(app, build_threads_router(web_ctx))
    mount_router(app, build_tts_router(web_ctx))
    # Calls (2026-10-28): HoldSpeak drives ai-phone and owns each turn.
    from holdspeak.web.routes.calls import build_calls_router

    mount_router(app, build_calls_router(web_ctx))
    # Programs (2026-10-28): a goal cut into steps, each handed to an agent.
    from holdspeak.web.routes.programs import build_programs_router

    mount_router(app, build_programs_router(web_ctx))
    # PG-DIRECTION DIR1 (2026-10-31): the briefing page for a held item,
    # tokened, read over the tailnet (no switch: it reads nothing of the machine).
    from holdspeak.web.routes.briefing import build_briefing_router

    mount_router(app, build_briefing_router(web_ctx))
    # The Walk (2026-11-07): a guided feedback walk on the desk from one link.
    from holdspeak.web.routes.walks import build_walks_router

    mount_router(app, build_walks_router(web_ctx))
    # Phone (2026-10-28): the desk reaches him on his phone and he reaches
    # it. HOLDSPEAK_PHONE=off (every rig) mounts nothing.
    from holdspeak.phone import phone_on

    if phone_on():
        from holdspeak.web.routes.phone import build_phone_router

        mount_router(app, build_phone_router(web_ctx))
    # Recordings (2026-10-28): a desk session as a video for the iPhone.
    from holdspeak.web.routes.recordings import build_recordings_router

    mount_router(app, build_recordings_router(web_ctx))
    mount_router(app, build_project_reviews_router(web_ctx))
    mount_router(app, build_project_door_router(web_ctx))
    mount_router(app, build_project_setup_router(web_ctx))
    mount_router(app, build_project_updates_router(web_ctx))
    mount_router(app, build_channels_router(web_ctx))  # PHILO-10-01: the Send
    mount_router(app, build_project_briefs_router(web_ctx))
    mount_router(app, build_providers_router(web_ctx))
    mount_router(app, build_connections_router(web_ctx))
    mount_router(app, build_steward_router(web_ctx))
    mount_router(app, build_watches_router(web_ctx))
    mount_router(app, build_mcp_http_router(web_ctx))
