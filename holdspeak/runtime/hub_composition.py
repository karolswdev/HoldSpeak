"""The hub's service construction (bootstrap move, 2026-11-08).

``MeetingWebServer._create_app`` built every service inline until the move; it
now asks :func:`compose_hub` for the composition, mounts the routers with it
and registers the lifespan. ``host`` is the web server: it supplies the runtime
callbacks (``on_*``), the ``broadcast`` thunk, the bind and token, and the
``gh``/``acli`` runners. This module never imports ``holdspeak.web_server``;
the host is passed in. The registry it installs into is
:mod:`holdspeak.runtime.composition`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from holdspeak.runtime.composition import (
    RuntimeServices,
    install_from_web_context,
    notify_desk_changed,
)


@dataclass
class HubComposition:
    """What :func:`compose_hub` builds for one hub process."""

    web_ctx: Any
    runtime_services: RuntimeServices
    refinement_coordinator: Any
    project_service: Any
    signin_targets: dict[str, Any]
    delivery_link: Any = None
    delivery_targets: Any = None
    delivery_cmd: Any = None
    delivery_live: Any = None


def compose_hub(host: Any, *, on_launch_hold: Callable[[str], Any]) -> HubComposition:
    """Build the hub's WebContext, every service on it, and install the root.

    The order is the order ``_create_app`` used: the services, the WebContext,
    the late bindings, :func:`install_from_web_context`, the agent-credential
    reload, then the desk actuator service.
    """
    import logging

    from holdspeak.principals import agent_credentials
    from holdspeak.web_auth import is_loopback_host

    log = logging.getLogger("holdspeak.web_server")

    from holdspeak.web.context import WebContext
    from holdspeak.services.authority_service import AuthorityService
    from holdspeak.services.credential_service import CredentialService
    from holdspeak.services.delivery_service import DeliveryService
    from holdspeak.services.cadence_service import CadenceService
    from holdspeak.services.coder_service import CoderService
    from holdspeak.services.dictation_service import DictationService
    from holdspeak.services.door_service import DoorService
    from holdspeak.services.refinement_thought_service import RefinementThoughtService
    from holdspeak.services.sync_service import SyncService
    from holdspeak.services.actuator_service import ActuatorProposalService
    from holdspeak.config import Config
    from holdspeak.services.gate_service import GateService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.services.mesh_service import MeshService
    from holdspeak.services.mission_control_service import MissionControlService
    from holdspeak.services.project_service import ProjectService
    from holdspeak.services.projection_service import ProjectionService
    from holdspeak.services.settings_service import SettingsService
    from holdspeak.services.setup_service import SetupService
    from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
    from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
    from holdspeak.services.model_library_service import ModelLibraryApplicationService
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from holdspeak.services.inference_capability_service import InferenceCapabilityApplicationService
    from holdspeak.services.profile_key_service import ProfileKeyService
    from holdspeak.services.connections_service import ConnectionsService
    from holdspeak.db import get_database, get_observer

    from holdspeak.services.meeting_aftercare_service import MeetingAftercareService
    from holdspeak.services.meeting_intel_service import MeetingIntelService
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.services.people_service import PeopleService, UnavailablePeopleStore
    from holdspeak.people.key_free import people_reads_allowed
    from holdspeak.people import production_people_store
    from holdspeak.services.reaction_service import ReactionService
    from holdspeak.services.watch_service import WatchService
    from holdspeak.services.github_provider import GitHubProviderAdapter
    from holdspeak.services.jira_provider import JiraProviderAdapter
    from holdspeak.services.project_door_service import ProjectDoorService
    from holdspeak.services.project_setup_service import ProjectSetupService
    from holdspeak.services.project_evidence_collector import ProjectEvidenceCollector
    from holdspeak.services.project_delta_service import ProjectDeltaService
    from holdspeak.services.project_update_service import ProjectUpdateService
    from holdspeak.services.preparation_brief_service import PreparationBriefService
    from holdspeak.services.project_steward_service import ProjectStewardService
    from holdspeak.services.refinement_coordinator import RefinementCoordinator
    from holdspeak.services.refinement_application_service import RefinementApplicationService

    from holdspeak.delivery.node_link import NodeTokenStore as _MeshNodeTokenStore

    def _mesh_token_store() -> Any:
        return _MeshNodeTokenStore(None)

    obs = get_observer()
    # HS-200-45 R4: the services the hub holds that write BELOW the two
    # primitive services (reaction projections, coder-materialized notes)
    # get the same desk_changed callback. Late-bound through the root the
    # block below installs.
    meeting_service = MeetingService(get_database(), observer=obs)
    notify = lambda message_type, data: host.broadcast(message_type, data)
    meeting_intel_service = MeetingIntelService(get_database(), notify=notify, observer=obs)
    meeting_aftercare_service = MeetingAftercareService(get_database(), notify=notify, observer=obs)
    refinement_coordinator = RefinementCoordinator(get_database(), host_kind="web")
    refinement_service = RefinementApplicationService(
        get_database(), coordinator=refinement_coordinator
    )

    def _update_meeting(*, title: Optional[str], tags: Optional[list[str]]) -> Any:
        """The title/tags fallback, mirrored from web/routes/meetings/live.py.

        HS-132-12: `live.py::_service` composes an update callback that
        falls back to `on_set_title`/`on_set_tags` when no
        `on_update_meeting` is wired — but that branch only runs for a
        PARTIAL context. Since the eager composition landed here (Phase
        123, f12731c7) the hub always hands the route a bound service, so
        the fallback became unreachable and a runtime wired with only
        title/tags callbacks answered 500 on PATCH /api/meeting. One
        update path, composed the same way in both places.
        """
        if host.on_update_meeting is not None:
            return host.on_update_meeting(title=title, tags=tags)
        if title is not None and host.on_set_title is not None:
            host.on_set_title(title)
        if tags is not None and host.on_set_tags is not None:
            host.on_set_tags(tags)
        return host.get_state() or {}

    meeting_service.bind_lifecycle(
        on_start=host.on_start,
        # HS-132-01: the meeting verb binds the no-fallback stop. The
        # runtime-fallback `on_stop` sets `runtime_stop_event` when no
        # meeting is live, so binding it here let a stop press with a stale
        # orb exit the hub main loop and still answer success. Mirrors the
        # partial-context composition in web/routes/meetings/live.py.
        on_stop=host.on_meeting_stop or host.on_stop,
        on_bookmark=host.on_bookmark,
        # Bound only when a runtime actually owns the live meeting's
        # metadata; otherwise the archive path in
        # `MeetingService.update_meeting` stays in charge, unchanged.
        on_update=(
            _update_meeting
            if (
                host.on_update_meeting is not None
                or host.on_set_title is not None
                or host.on_set_tags is not None
            )
            else None
        ),
    )
    # The encrypted People sidecar is deliberately composed outside the
    # normal database.  Key custody failures remain a named readiness state;
    # there is never a plaintext fallback.
    try:
        people_service = PeopleService(production_people_store())
    except Exception:
        people_service = PeopleService(UnavailablePeopleStore())
    # HS-149-04: bind person resolver so the meeting origin line can
    # extend with the resolved person display name (read-time only).
    def _resolve_person_label(uid: str, source_id: str) -> str | None:
        try:
            result = people_service.resolve_relationship_by_series(uid, source_id)
            if result.get("state") != "ready":
                return None
            rel = result.get("relationship")
            return str(rel.get("display_name") or "") if rel else None
        except Exception:
            return None

    meeting_service.bind_person_resolver(_resolve_person_label)

    follow_through_service = FollowThroughService(
        get_database(), observer=obs, people_projection=people_service
    )
    door_service = DoorService(
        follow_through_service,
        RefinementThoughtService(get_database()),
        get_database().scheduled_recordings,
        get_database().calendar_events,
        db=get_database(),
        config_loader=Config.load,
        people_service=people_service,
    )

    inference_setup_service = InferenceSetupApplicationService(get_database())
    inference_acquisition_service = InferenceAcquisitionApplicationService(
        get_database(), setup_service=inference_setup_service
    )
    model_library_service = ModelLibraryApplicationService(
        get_database(), setup_service=inference_setup_service,
        acquisition_service=inference_acquisition_service,
    )
    # The same frozen broker registry backs web and MCP.  Construction is
    # deliberately eager: invalid capability composition must prevent the
    # process from serving rather than become a lazy route-time surprise.
    from holdspeak.kernel.runtime import _configure

    broker = _configure(get_database())
    inference_capability_service = InferenceCapabilityApplicationService(
        broker.inference_capability_registry
    )
    inference_assignment_service = InferenceAssignmentService(
        get_database(),
        registry=broker.inference_capability_registry,
        tool_capability_foundation=getattr(
            getattr(broker, "tool_turn_foundation", None), "_foundation", None
        ),
    )
    # Meaning search: the one step that gets the local embedding model,
    # assigns it to ``memory.embed`` and wakes the memory conductor.
    from holdspeak.services.meaning_search_service import MeaningSearchService

    memory_service = MemoryService(get_database(), observer=obs)
    memory_service.meaning = MeaningSearchService(
        get_database(),
        assignment_service=inference_assignment_service,
        broker_provider=lambda: broker,
    )
    # Owner ruling 2026-10-05: a LOCAL engine becomes "Default for AI
    # work" by itself; a network or cloud engine waits for the owner.
    from holdspeak.services.inference_default_service import InferenceDefaultService

    inference_default_service = InferenceDefaultService(
        get_database(),
        assignment_service=inference_assignment_service,
        model_library_service=model_library_service,
        meaning_search=memory_service.meaning,
    )
    # "Set up local AI": only an explicit owner call starts its download.
    from holdspeak.services.local_ai_setup_service import LocalAISetupService

    local_ai_setup_service = LocalAISetupService(
        get_database(),
        meaning_search=memory_service.meaning,
        broker_provider=lambda: broker,
    )
    # HS-160-05 / S52: the Delta service (commands, frozen windows). The
    # Room's review section does not hold it: ProjectService reads the
    # open review through the repository and is told the capability
    # exists (``review_available=True`` below).
    _project_delta_service = ProjectDeltaService(
        get_database(),
        collector=ProjectEvidenceCollector(get_database()),
    )
    # ST8 binds the Accounts sign-in process to the terminal target
    # registry created with the delivery routes below.  The indirection is
    # intentional: the service is part of the one operation composition
    # before the delivery transport is mounted.
    from holdspeak.services.connection_signin_service import ConnectionSigninService
    _signin_targets: dict[str, Any] = {}
    web_ctx = WebContext(
        get_state=host.get_state,
        meeting_service=meeting_service,
        meeting_service_factory=lambda: MeetingService(get_database(), observer=obs),
        meeting_intel_service=meeting_intel_service,
        # PHILO-5-02 (gap C): no summary factory. The HTTP summary routes
        # and MCP reach the ONE instance above; a factory beside it made a
        # second, so the two transports never shared object identity.
        meeting_aftercare_service=meeting_aftercare_service,
        meeting_aftercare_service_factory=lambda: MeetingAftercareService(get_database(), notify=notify, observer=obs),
        brief_clock=host._brief_clock,
        # Late-bind broadcast: the prior inline handlers called
        # `host.broadcast(...)`, which resolves the attribute at call time
        # (tests reassign `server.broadcast` to spy on it). A thunk keeps
        # that dynamic dispatch instead of freezing the bound method.
        broadcast=lambda message_type, data: host.broadcast(message_type, data),
        on_bookmark=host.on_bookmark,
        on_start=host.on_start,
        on_stop=host.on_stop,
        on_meeting_stop=host.on_meeting_stop,
        on_update_action_item=host.on_update_action_item,
        on_update_action_item_review=host.on_update_action_item_review,
        on_edit_action_item=host.on_edit_action_item,
        on_update_meeting=host.on_update_meeting,
        on_set_title=host.on_set_title,
        on_set_tags=host.on_set_tags,
        project_service=(_project_service := ProjectService(
            get_database(), observer=obs,
            review_available=True,
        )),
        projection_service=ProjectionService(get_database(), observer=obs),
        authority_service=AuthorityService(get_database(), observer=obs),
        credential_service=CredentialService(
            get_database(), on_settings_applied=host.on_settings_applied, observer=obs
        ),
        cadence_service=CadenceService(get_database(), Config.load().cadence, observer=obs),
        follow_through_service=follow_through_service,
        door_service=door_service,
        people_service=people_service,
        sync_service=SyncService(get_database(), observer=obs),
        gate_service=GateService(
            get_database(), observer=obs,
            # Conductor R1: a held call of a launch notifies at once.
            on_launch_hold=on_launch_hold,
        ),
        # The Trust read states the bind and the token this runtime REALLY
        # serves with; the config alone cannot say where the hub listens.
        setup_service=SetupService(
            get_database(), observer=obs,
            web_bind=host.host, auth_token_set=bool(host.auth_token),
        ),
        inference_setup_service=inference_setup_service,
        local_ai_setup_service=local_ai_setup_service,
        inference_acquisition_service=inference_acquisition_service,
        model_library_service=model_library_service,
        inference_assignment_service=inference_assignment_service,
        inference_default_service=inference_default_service,
        inference_capability_service=inference_capability_service,
        delivery_service=DeliveryService(get_database(), observer=obs),
        # HS-131-16: the relay legs sign and revalidate dispatch offers, so
        # the service needs the hub's pairing custody. A separate
        # `NodeTokenStore` handle is deliberate and safe: the store keeps no
        # cached state and re-reads under lock on every verb, so this handle
        # and the node link's see the same rotation and revocation without a
        # restart (Sol Amendment 3).
        mesh_service=MeshService(
            get_database(), observer=obs, token_store=_mesh_token_store()
        ),
        memory_service=memory_service,
        mission_control_service=MissionControlService(get_database(), observer=obs),
        reaction_service=ReactionService(
            get_database(), observer=obs,
            on_changed=lambda kind, obj_id, op: notify_desk_changed(kind, obj_id, op),
        ),
        watch_service=WatchService(
            get_database(), observer=obs,
            **host._gh_watch_service_kwargs(),
        ),
        github_provider=GitHubProviderAdapter(
            db=get_database(), runner=host._gh_runner,
        ),
        jira_provider=JiraProviderAdapter(
            db=get_database(), runner=host._acli_runner,
        ),
        # HS-174-07 declared this field "construction only here" and then
        # never constructed it; the MCP `provider.confluence.*` family
        # built a bare adapter in the hub as a result. Same shape as the
        # Jira adapter above (counsel P1-3, caught by the asked-names fence).
        confluence_provider=(
            host._build_confluence_adapter()
            or __import__(
                "holdspeak.services.confluence_provider", fromlist=["ConfluenceProviderAdapter"]
            ).ConfluenceProviderAdapter(db=get_database(), runner=host._acli_runner)
        ),
        connections_service=ConnectionsService(
            github_adapter=GitHubProviderAdapter(
                db=get_database(), runner=host._gh_runner,
            ),
            jira_adapter=JiraProviderAdapter(
                db=get_database(), runner=host._acli_runner,
            ),
            # PHILO-9-02 (B1): the Confluence row and its real Recheck
            # probe need the adapter; the bare builder returns None
            # unless a test injects a runner, so fall back as :1004 does.
            confluence_adapter=(
                host._build_confluence_adapter()
                or __import__(
                    "holdspeak.services.confluence_provider", fromlist=["ConfluenceProviderAdapter"]
                ).ConfluenceProviderAdapter(db=get_database(), runner=host._acli_runner)
            ),
            config_loader=Config.load,
            inference_assignment_service=inference_assignment_service,
        ),
        connection_signin_service=ConnectionSigninService(
            target_provider=lambda: _signin_targets.get("targets"),
        ),
        project_setup_service=ProjectSetupService(
            get_database(),
            project_service=ProjectService(get_database(), observer=obs),
            watch_service=WatchService(
                get_database(), observer=obs,
                **host._gh_watch_service_kwargs(),
            ),
            github_adapter=GitHubProviderAdapter(
                db=get_database(), runner=host._gh_runner,
            ),
            jira_adapter=JiraProviderAdapter(
                db=get_database(), runner=host._acli_runner,
            ),
            connections_service=ConnectionsService(
                github_adapter=GitHubProviderAdapter(
                    db=get_database(), runner=host._gh_runner,
                ),
                jira_adapter=JiraProviderAdapter(
                    db=get_database(), runner=host._acli_runner,
                ),
                config_loader=Config.load,
                inference_assignment_service=inference_assignment_service,
            ),
        ),
        project_door_service=ProjectDoorService(
            project_service=ProjectService(get_database(), observer=obs),
            watch_service=WatchService(
                get_database(), observer=obs,
                **host._gh_watch_service_kwargs(),
            ),
            gh_runner=host._gh_runner,
            github_adapter=GitHubProviderAdapter(
                db=get_database(), runner=host._gh_runner,
            ),
            jira_adapter=JiraProviderAdapter(
                db=get_database(), runner=host._acli_runner,
            ),
            confluence_adapter=(
                host._build_confluence_adapter()
                or __import__(
                    "holdspeak.services.confluence_provider", fromlist=["ConfluenceProviderAdapter"]
                ).ConfluenceProviderAdapter(db=get_database(), runner=host._acli_runner)
            ),
            db=get_database(),
            meeting_service=meeting_service,
            primitive_service=None,
        ),
        project_evidence_collector=ProjectEvidenceCollector(get_database()),
        # PHILO-9-02: one suggested-source service over the hub's ProjectService.
        suggested_source_service=__import__(
            "holdspeak.services.suggested_source_service", fromlist=["SuggestedSourceService"]
        ).SuggestedSourceService(get_database(), project_service=_project_service),
        project_delta_service=_project_delta_service,
        project_update_service=(_project_update_service := ProjectUpdateService(
            get_database(),
            project_service=_project_service,
            delta_service=_project_delta_service,
            broker=broker,
            # Betterment P2: a 1:1 is told by its speakers too.
            people_names=lambda principal: [
                str(rel.get("display_name") or "")
                for rel in people_service.list_relationships(principal)
            ] if people_reads_allowed() else [],
        )),
        project_brief_service=PreparationBriefService(
            get_database(),
            project_service=_project_service,
            broker=broker,
        ),
        project_steward_service=ProjectStewardService(
            get_database(),
            ProjectEvidenceCollector(get_database()),
            _project_delta_service,
            update_service=_project_update_service,
            project_service=_project_service,
            door_service=door_service,
        ),
        refinement_coordinator=refinement_coordinator,
        refinement_service=refinement_service,
        settings_service=SettingsService(
            get_database(), on_settings_applied=host.on_settings_applied, observer=obs
        ),
        profile_key_service=ProfileKeyService(get_database()),
        on_get_intent_controls=host.on_get_intent_controls,
        on_set_intent_profile=host.on_set_intent_profile,
        on_set_intent_override=host.on_set_intent_override,
        on_route_preview=host.on_route_preview,
        on_dictation_config_changed=host.on_dictation_config_changed,
        on_remote_dictation=host.on_remote_dictation,
        coder_service=CoderService(
            get_database(), observer=obs,
            on_changed=lambda kind, obj_id, op: notify_desk_changed(kind, obj_id, op),
        ),
        dictation_service=DictationService(
            get_database(), observer=obs,
            journal_repository=getattr(host.dictation_journal, "repository", None),
            journal_available=host.dictation_journal is not None,
        ),
        on_process_plugin_jobs=host.on_process_plugin_jobs,
        device_registry=host.device_registry,
        project_detector=host._project_detector,
        ws=host._ws,
        on_get_status=host.on_get_status,
        on_settings_applied=host.on_settings_applied,
        on_wake_type=host.on_wake_type,
        on_preview_type=host.on_preview_type,
        on_preview_discard=host.on_preview_discard,
        on_transcribe=host.on_transcribe,
        on_transcribe_admitted=host.on_transcribe_admitted,
        current_formatted_duration=host._current_formatted_duration,
        corrections=host.dictation_corrections,
        telemetry=host.dictation_telemetry,
        journal=host.dictation_journal,
        voice_session=host.voice_session,
        # HSM-15-10: a server bound off-loopback requires the auth token; the
        # mesh identify endpoint surfaces that to an unpaired companion.
        mesh_requires_token=not is_loopback_host(host.host),
        web_host=host.host,
        web_auth_token=host.auth_token,
    )
    # HS-166-05 / S52: one-way composition. Delta needs the Project
    # service for create_item inside decide_proposal; the Project
    # service does not need Delta back (the review read is the
    # repository's).
    _project_delta_service.attach_project_service(_project_service)
    # Owner ruling 2026-10-05: the onboarding backends compose the
    # settings and connections services above (detect + "Use it").
    from holdspeak.services.onboarding_service import OnboardingService

    web_ctx.onboarding_service = OnboardingService(
        settings_service=web_ctx.settings_service,
        connections_service=web_ctx.connections_service,
        jira_provider=web_ctx.jira_provider,
        confluence_provider=web_ctx.confluence_provider,
    )
    # Betterment Setup ST3-ST5: the one Setup inventory reads the same
    # composition-owned producers as first run, Engines and People.
    web_ctx.setup_service.bind_found_sources(
        onboarding_service=web_ctx.onboarding_service,
        local_ai_setup_service=web_ctx.local_ai_setup_service,
        inference_default_service=web_ctx.inference_default_service,
        inference_assignment_service=web_ctx.inference_assignment_service,
        model_library_service=web_ctx.model_library_service,
        people_service=web_ctx.people_service,
        connections_service=web_ctx.connections_service,
    )

    # HS-200-45 R1/R4: ONE composition root. The desk-primitive services are
    # composed HERE, once, with the ``on_changed`` hook bound to the bus --
    # and then installed so every caller (the primitive HTTP routes, MCP
    # over /api/mcp, MCP over stdio proxied to this hub) writes through the
    # same instance. Before this, MCP dispatch and each HTTP route built
    # their own bare copy, so a write from anywhere but the acting browser
    # reached no open desk.
    _runtime_services = install_from_web_context(
        web_ctx, db=get_database(), observer=obs
    )

    # Conductor R2: the hub's agent credentials, their targets and launch
    # ownership survive a restart. After the composition is installed:
    # the revoke hook first (a credential that expired while the hub was
    # down ends its grants on load), then the reload, then every LIVE
    # launch grant left with no live credential is ended.
    from holdspeak.services.conductor_launch import install_revoke_hook, reconcile_launch_grants

    install_revoke_hook()
    agent_credentials.attach(get_database(), follow_hub=True)
    try:
        reconcile_launch_grants(get_database())
    except Exception:  # a start never fails on the sweep; it runs again next start
        log.warning("launch grant reconcile failed", exc_info=True)

    from holdspeak.web.routes.actuator_shared import DeskActuatorLifecycle
    web_ctx.actuator_service = ActuatorProposalService(
        get_database(), config_provider=lambda: Config.load(path=__import__("holdspeak.config", fromlist=["CONFIG_FILE"]).CONFIG_FILE),
        broadcast=lambda message_type, data: host.broadcast(message_type, data),
        lifecycle=DeskActuatorLifecycle(web_ctx, get_database()),
    )
    _runtime_services.actuator_service = web_ctx.actuator_service

    return HubComposition(
        web_ctx=web_ctx,
        runtime_services=_runtime_services,
        refinement_coordinator=refinement_coordinator,
        project_service=_project_service,
        signin_targets=_signin_targets,
    )
