"""The hub's services are built in ONE runtime composition module.

``MeetingWebServer._create_app`` mounts routers and registers the lifespan;
``holdspeak.runtime.hub_composition.compose_hub`` builds the WebContext and every
service on it. The field set below was snapshotted from ``_create_app`` on
main 5ca166897 before the move (the WebContext fields that are not None once
the composition is installed and the actuator service is set).
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys

from holdspeak.web.context import WebContext

FIELDS_BEFORE_THE_MOVE = [
    "actuator_service",
    "authority_service",
    "broadcast",
    "cadence_service",
    "channel_service",
    "coder_service",
    "confluence_provider",
    "connection_signin_service",
    "connections_service",
    "corrections",
    "credential_service",
    "current_formatted_duration",
    "delivery_service",
    "device_registry",
    "dictation_service",
    "door_service",
    "follow_through_service",
    "gate_service",
    "get_state",
    "github_provider",
    "inference_acquisition_service",
    "inference_assignment_service",
    "inference_capability_service",
    "inference_default_service",
    "inference_setup_service",
    "jira_provider",
    "journal",
    "local_ai_setup_service",
    "meeting_aftercare_service",
    "meeting_aftercare_service_factory",
    "meeting_intel_service",
    "meeting_service",
    "meeting_service_factory",
    "memory_service",
    "mesh_requires_token",
    "mesh_service",
    "mission_control_service",
    "model_library_service",
    "monday_brief_service",
    "note_outcomes_service",
    "on_bookmark",
    "on_stop",
    "onboarding_service",
    "operations",
    "people_service",
    "primitive_service",
    "profile_key_service",
    "project_brief_service",
    "project_delta_service",
    "project_door_service",
    "project_evidence_collector",
    "project_service",
    "project_setup_service",
    "project_steward_service",
    "project_update_service",
    "projection_service",
    "reaction_service",
    "refinement_coordinator",
    "refinement_service",
    "settings_service",
    "setup_service",
    "suggested_source_service",
    "sync_service",
    "telemetry",
    "today_service",
    "watch_service",
    "web_auth_token",
    "web_host",
    "workbench_service",
    "ws",
]


def test_compose_hub_builds_the_same_web_context_field_set(tmp_path) -> None:
    from holdspeak.db import get_database, reset_database
    from holdspeak.runtime import composition
    from holdspeak.runtime.hub_composition import compose_hub
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    reset_database()
    get_database(tmp_path / "hub-composition.db")
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
            host="127.0.0.1",
        )
        hub = compose_hub(server, on_launch_hold=lambda _key: None)
        built = sorted(
            field.name
            for field in dataclasses.fields(WebContext)
            if getattr(hub.web_ctx, field.name) is not None
        )
        assert built == FIELDS_BEFORE_THE_MOVE
        assert composition.installed() is hub.runtime_services
        assert hub.runtime_services.actuator_service is hub.web_ctx.actuator_service
    finally:
        reset_database()


def test_importing_the_compositions_does_not_import_the_web_server() -> None:
    probe = (
        "import sys, holdspeak.runtime.composition, holdspeak.runtime.delivery_composition as d, holdspeak.runtime.hub_composition as c; "
        "assert callable(c.compose_hub) and callable(d.compose_delivery); "
        "assert 'holdspeak.web_server' not in sys.modules, 'web_server imported'"
    )
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
