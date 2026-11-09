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

import pytest

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


# Each class compose_hub built more than once with the same inputs before
# 2026-11-08, and how many it builds now. ProjectService and ConnectionsService
# keep two: the Room's copy says ``review_available=True`` and the Setup/Door
# copy does not; the Connections copy on the WebContext holds the Confluence
# adapter and the Setup copy does not.
BUILT_ONCE = {
    ("holdspeak.services.github_provider", "GitHubProviderAdapter"): 1,
    ("holdspeak.services.jira_provider", "JiraProviderAdapter"): 1,
    ("holdspeak.services.confluence_provider", "ConfluenceProviderAdapter"): 1,
    ("holdspeak.services.watch_service", "WatchService"): 1,
    ("holdspeak.services.project_evidence_collector", "ProjectEvidenceCollector"): 1,
    ("holdspeak.services.project_service", "ProjectService"): 2,
    ("holdspeak.services.connections_service", "ConnectionsService"): 2,
    ("holdspeak.delivery.node_link", "NodeTokenStore"): 1,
}


@pytest.mark.parametrize("acli_runner", [None, lambda *_a, **_k: None], ids=["bare", "acli"])
def test_compose_hub_builds_each_shared_service_once(tmp_path, monkeypatch, acli_runner) -> None:
    import importlib

    from holdspeak.db import get_database, reset_database
    from holdspeak.runtime.delivery_composition import compose_delivery
    from holdspeak.runtime.hub_composition import compose_hub
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    counts: dict[str, int] = {}
    for (module_name, class_name) in BUILT_ONCE:
        module = importlib.import_module(module_name)
        real = getattr(module, class_name)

        def counted(*args, _real=real, _name=class_name, **kwargs):
            counts[_name] = counts.get(_name, 0) + 1
            return _real(*args, **kwargs)

        monkeypatch.setattr(module, class_name, counted)

    reset_database()
    get_database(tmp_path / "hub-composition-once.db")
    try:
        server = MeetingWebServer(
            WebRuntimeCallbacks(
                on_bookmark=lambda *_: None,
                on_stop=lambda: None,
                get_state=lambda: {},
            ),
            host="127.0.0.1",
            acli_runner=acli_runner,
        )
        counts.clear()  # the server composed once already; count one call
        hub = compose_delivery(
            compose_hub(server, on_launch_hold=lambda _key: None), auth_token=None
        )
        built = sorted(
            field.name
            for field in dataclasses.fields(WebContext)
            if getattr(hub.web_ctx, field.name) is not None
        )
        assert built == FIELDS_BEFORE_THE_MOVE
        ctx = hub.web_ctx
        setup, door = ctx.project_setup_service, ctx.project_door_service
        assert hub.delivery_link.token_store is hub.node_token_store
        assert setup._project_service is door._project_service is not ctx.project_service
        assert setup._watch_service is door._watch_service is ctx.watch_service
        assert setup._github_adapter is door._github_adapter is ctx.github_provider
    finally:
        reset_database()
    assert counts == {name: n for (_m, name), n in BUILT_ONCE.items()}
