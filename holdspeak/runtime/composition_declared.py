"""The declared tables' services on the one composition root, carved from ``composition.py``.

``install_from_web_context`` calls :func:`compose_declared_services` once. Each
service a declared operation binds to (the loop, Programs, phone, Calls,
People, Settings credentials, Decisions, Follow-through, ...) is the hub's own
instance when the root or the context holds one, else the bare build below,
put on BOTH the context and the root so a route and an MCP call reach one
object.
"""

from __future__ import annotations

from typing import Any, Callable


def _bare_onboarding() -> Any:
    from holdspeak.services.onboarding_service import OnboardingService

    return OnboardingService()


def _bare_credentials(db: Any, observer: Any) -> Any:
    from holdspeak.services.credential_service import CredentialService

    return CredentialService(db, observer=observer)


def _bare_recipes(db: Any, observer: Any) -> Any:
    from holdspeak.services.recipe_service import RecipeService

    return RecipeService(db, observer=observer)


def _bare_thoughts(db: Any) -> Any:
    from holdspeak.services.refinement_thought_service import RefinementThoughtService

    return RefinementThoughtService(db)


def _bare_recall(db: Any) -> Any:
    from holdspeak.services.recall_service import RecallService

    return RecallService(db)


def _bare_desk(db: Any, observer: Any) -> Any:
    from holdspeak.services.desk_service import DeskService

    return DeskService(db, observer=observer)


def _bare_projections(db: Any, observer: Any) -> Any:
    from holdspeak.services.projection_service import ProjectionService

    return ProjectionService(db, observer=observer)


def _constitutional() -> Any:
    from holdspeak.constitutional_context import ConstitutionalContextService

    return ConstitutionalContextService()
def _invocations(db: Any, observer: Any) -> Any:
    from holdspeak.services.invocation_service import InvocationService

    return InvocationService(db, observer=observer)


def _bare_coders(db: Any, observer: Any, services: Any) -> Any:
    from holdspeak.services.coder_service import CoderService

    return CoderService(db, observer=observer, broadcast=services.broadcast)


def _bare_delivery(db: Any, observer: Any) -> Any:
    from holdspeak.services.delivery_service import DeliveryService

    return DeliveryService(db, observer=observer)


def _bare_plain(module: str, cls: str, db: Any, observer: Any) -> Any:
    import importlib

    return getattr(importlib.import_module(f"holdspeak.services.{module}"), cls)(db, observer=observer)


def _bare_cadence(db: Any, observer: Any) -> Any:
    from holdspeak.config import Config
    from holdspeak.services.cadence_service import CadenceService

    return CadenceService(db, Config.load().cadence, observer=observer)


def _hub_threads(services: Any) -> Any:
    """The threads' rows bind to a factory: one ThreadService per verb over the hub's bus (``thread_operations.py``)."""

    def make() -> Any:
        from holdspeak.services.thread_service import hub_thread_service

        return hub_thread_service(lambda topic, data: services.broadcast(topic, data) if services.broadcast else None)

    return make


def _ops_projects_builders(db: Any, observer: Any) -> dict[str, Callable[[], Any]]:
    """The bare builds of the services the project, activity, walk and repository rows bind to."""

    def _plain(module: str, cls: str) -> Callable[[], Any]:
        def build() -> Any:
            import importlib

            return getattr(importlib.import_module(f"holdspeak.services.{module}"), cls)(db, observer=observer)

        return build

    def _proposals() -> Any:
        from holdspeak.services.proposal_bridge_service import ProposalBridgeService

        return ProposalBridgeService(db)

    def _briefing() -> Any:
        from holdspeak.services.briefing_service import default_briefing_service

        return default_briefing_service(db)

    def _walks() -> Any:
        from holdspeak.services.walk_service import default_walk_service

        return default_walk_service()

    return {
        "proposal_bridge_service": _proposals,
        "decision_record_service": _plain("decision_record_service", "DecisionRecordService"),
        "briefing_service": _briefing,
        "walk_service": _walks,
        "activity_ledger_service": _plain("activity_ledger_service", "ActivityLedgerService"),
        "activity_rules_service": _plain("activity_rules_service", "ActivityRulesService"),
        "activity_enrichment_service": _plain("activity_enrichment_service", "ActivityEnrichmentService"),
        "activity_meeting_candidate_service": _plain("activity_meeting_candidate_service",
                                                     "ActivityMeetingCandidateService"),
        "activity_nudge_service": _plain("activity_nudge_service", "ActivityNudgeService"),
        "repository_drawer_service": _plain("repository_drawer_service", "RepositoryDrawerService"),
        "roadmap_service": _plain("roadmap_service", "RoadmapService"),
    }
def _unavailable() -> Any:
    from holdspeak.setup_operations import Unavailable

    return Unavailable()


def _bare_profiles(db: Any, observer: Any) -> Any:
    from holdspeak.services.profile_service import ProfileService

    return ProfileService(db, observer=observer)


def _bare_settings(db: Any, observer: Any) -> Any:
    from holdspeak.services.settings_service import SettingsService

    return SettingsService(db=db, on_settings_applied=None, observer=observer)


def _bare_authority(db: Any, observer: Any) -> Any:
    from holdspeak.services.authority_service import AuthorityService

    return AuthorityService(db, observer=observer)


def _settings_hub(services: Any, ctx: Any) -> Any:
    from holdspeak.services.settings_hub_service import SettingsHubService

    def live(name: str) -> Any:
        found = getattr(services, name, None)
        return found if found is not None else getattr(ctx, name, None)

    return SettingsHubService(model_library_service=live("model_library_service"),
                              inference_assignment_service=live("inference_assignment_service"),
                              cadence_service=live("cadence_service"))


def _ops_connections_builders(ctx: Any) -> dict[str, Callable[[], Any]]:
    """The concierge, calendar, feedback and provider services' builds (ops/connections)."""
    def concierge() -> Any:
        from holdspeak.services.concierge_service import ConciergeService

        return ConciergeService(ctx)

    def calendar() -> Any:
        from holdspeak.services.calendar_service import CalendarService

        return CalendarService(ctx)

    def feedback() -> Any:
        from holdspeak.services.ui_feedback import FeedbackService

        return FeedbackService(ctx)

    def providers() -> Any:
        from holdspeak.services.provider_service import from_context

        return from_context(ctx)

    return {"concierge_service": concierge, "calendar_service": calendar, "feedback_service": feedback,
            "provider_service": providers}


def compose_declared_services(services: Any, ctx: Any, resolved_db: Any, resolved_observer: Any) -> None:
    """Put every declared table's service on the root and the context."""
    from holdspeak.services.setup_service import SetupService

    # PHILO-5-02: the rest of the loop's services. The hub composes every one
    # of them itself (``MeetingWebServer._create_app``); the brief service is
    # composed HERE, once, with the hub's producer clock (gap A). A partially
    # wired context (a fence's stand-in) gets the same bare builds its routes
    # would make, put on BOTH the context and the root so the two still share
    # one instance.
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from holdspeak.services.follow_through_service import FollowThroughService
    from holdspeak.services.meeting_aftercare_service import MeetingAftercareService
    from holdspeak.services.meeting_intel_service import MeetingIntelService
    from holdspeak.services.meeting_service import MeetingService
    from holdspeak.services.monday_brief_service import MondayBriefService
    from holdspeak.services.refinement_application_service import RefinementApplicationService
    from holdspeak.services.kernel_read_service import KernelReadService
    from holdspeak.services.memory_service import MemoryService
    from holdspeak.services.agent_hand_service import default_agent_hand_service
    from holdspeak.services.desk_window_service import DeskWindowService
    from holdspeak.services.note_outcomes_service import NoteOutcomesService
    from holdspeak.services.today_service import TodayService
    from holdspeak.services.connection_signin_service import ConnectionSigninService

    def _intel_notify(topic: str, value: Any) -> None:
        if services.broadcast is not None:
            services.broadcast(topic, value)

    from holdspeak.operations import LIVE_CALLS_SERVICE, LIVE_PHONE_SERVICE, LIVE_PROGRAM_SERVICE
    from holdspeak.operations import LIVE_RECORDINGS_SERVICE
    from holdspeak.services.tts_service import TtsService
    from holdspeak.operations import LIVE_KERNEL_SERVICE
    from holdspeak.services.gate_service import GateService
    from holdspeak.settings_operations import LIVE_HEARTBEAT_SERVICE, LIVE_REACH_SERVICE, LIVE_TELEGRAM_SERVICE
    from holdspeak.services.people_service import PeopleService, UnavailablePeopleStore

    builders: dict[str, Callable[[], Any]] = {
        "meeting_service": lambda: MeetingService(resolved_db, observer=resolved_observer),
        "meeting_intel_service": lambda: MeetingIntelService(
            resolved_db, notify=_intel_notify, observer=resolved_observer
        ),
        "meeting_aftercare_service": lambda: MeetingAftercareService(
            resolved_db, notify=_intel_notify, observer=resolved_observer
        ),
        "monday_brief_service": lambda: MondayBriefService(
            resolved_db, observer=resolved_observer,
            clock=getattr(ctx, "brief_clock", None),
        ),
        "refinement_service": lambda: RefinementApplicationService(
            resolved_db, coordinator=getattr(ctx, "refinement_coordinator", None)
        ),
        "today_service": lambda: TodayService(resolved_db),
        "kernel_read_service": lambda: KernelReadService(resolved_db),
        # Memory slice 4: memory.observations.read binds to it.
        "memory_service": lambda: MemoryService(resolved_db, observer=resolved_observer),
        # The Conductor K1: agent_hooks.install binds to it (the hub composes its own).
        "onboarding_service": _bare_onboarding,
        "setup_service": lambda: SetupService(
            resolved_db, observer=resolved_observer,
            onboarding_service=services.onboarding_service,
            people_service=getattr(ctx, "people_service", None),
            local_ai_setup_service=getattr(ctx, "local_ai_setup_service", None),
            inference_default_service=getattr(ctx, "inference_default_service", None),
            model_library_service=getattr(ctx, "model_library_service", None),
            inference_assignment_service=getattr(ctx, "inference_assignment_service", None),
            connections_service=getattr(ctx, "connections_service", None),
        ),
        # Conductor K2: agent.hand binds to it (the one shared launch driver).
        "agent_hand_service": lambda: default_agent_hand_service(
            resolved_db, delivery_service=getattr(ctx, "delivery_service", None)
        ),
        # PHILO-16 16b: the windows.* rows bind to it (the MCP family).
        "desk_window_service": lambda: DeskWindowService(resolved_db),
        "note_outcomes_service": lambda: NoteOutcomesService.composed(resolved_db, services, ctx),
        # ST8: a partial composition can bind the owner-only operation even
        # though the live hub supplies the delivery target registry later.
        "connection_signin_service": lambda: ConnectionSigninService(
            target_provider=lambda: None,
        ),
        # 2026-11-08 (one contract): the Programs descriptors bind to the
        # process's one ProgramService, read at each call.
        "program_service": lambda: LIVE_PROGRAM_SERVICE,
        # The phone descriptors (phone_operations.py): the process's one PhoneService.
        "phone_service": lambda: LIVE_PHONE_SERVICE,
        # The Calls window's descriptors (calls_operations.py): the process's one CallsService.
        "calls_service": lambda: LIVE_CALLS_SERVICE,
        # The Settings credential verbs (settings_operations.py): the hub composes its
        # own (with the settings-applied hook); a partial context's writes the file only.
        "credential_service": lambda: _bare_credentials(resolved_db, resolved_observer),
        # The People verbs: the hub composes the encrypted store; a partial context's refuses every call.
        "people_service": lambda: PeopleService(UnavailablePeopleStore()),
        # The Decisions verbs (decision_operations.py): the ledger and Commit.
        "decision_lifecycle_service": lambda: DecisionLifecycleService(resolved_db, observer=resolved_observer),
        "follow_through_service": lambda: FollowThroughService(resolved_db, observer=resolved_observer),
        # 2026-11-09 (ops/programs-work): the recipe writes, the note window's
        # for-note read and memory's Recall (recipe_operations.py,
        # thought_operations.py, memory_operations.py).
        "recipe_service": lambda: _bare_recipes(resolved_db, resolved_observer),
        "refinement_thought_service": lambda: _bare_thoughts(resolved_db),
        "recall_service": lambda: _bare_recall(resolved_db),
        "desk_service": lambda: _bare_desk(resolved_db, resolved_observer),
        "projection_service": lambda: _bare_projections(resolved_db, resolved_observer),
        "constitutional_context_service": _constitutional,
        # The threads' verbs (thread_operations.py): the hub's ThreadService factory.
        "hub_thread_service": lambda: _hub_threads(services),
        "ask_service": lambda: services.ask_service,
        # The coder sessions and the delivery runtime (coder_operations.py,
        # delivery_operations.py): the hub composes its own; a partial context's are bare.
        "coder_service": lambda: _bare_coders(resolved_db, resolved_observer, services),
        "delivery_service": lambda: _bare_delivery(resolved_db, resolved_observer),
        # The speech family (dictation_operations.py, device_operations.py) and the
        # cadence loops (project_operations.py): the hub composes its own; a partial context's are bare.
        "dictation_service": lambda: _bare_plain("dictation_service", "DictationService", resolved_db, resolved_observer),
        "sync_service": lambda: _bare_plain("sync_service", "SyncService", resolved_db, resolved_observer),
        "mesh_service": lambda: _bare_plain("mesh_service", "MeshService", resolved_db, resolved_observer),
        "cadence_service": lambda: _bare_cadence(resolved_db, resolved_observer),
        # The capability run receipts (invocation_operations.py); the kernel broker at first use.
        "invocation_service": lambda: _invocations(resolved_db, resolved_observer),
        # The recordings descriptors (media_operations.py): the process's one RecordingsService.
        "recordings_service": lambda: LIVE_RECORDINGS_SERVICE,
        # The hub's voice (media_operations.py): the Line's TTS weights, read and fetched.
        "tts_service": TtsService,
        # 2026-11-09 (ops/projects): the declared project, activity, walk and
        # repository tables (project_operations.py, activity_operations.py,
        # walk_operations.py, repository_operations.py, decision_operations.py).
        **_ops_projects_builders(resolved_db, resolved_observer),
        # The gate and principals verbs (gate_operations.py): the hub composes its own GateService.
        "gate_service": lambda: GateService(resolved_db, observer=resolved_observer),
        # The kernel verbs: the process's one broker, read at each call.
        "kernel_service": lambda: LIVE_KERNEL_SERVICE,
        # The Setup routes (setup_operations.py): the hub composes local AI and the
        # model downloads; a partial context's stand-in refuses every call as unavailable.
        "local_ai_setup_service": _unavailable,
        "inference_acquisition_service": _unavailable,
        "profile_service": lambda: _bare_profiles(resolved_db, resolved_observer),
        # The rest of Settings (settings_operations.py): the settings file, its hub
        # read, the posture; the heartbeat, Reach and Telegram are read at each call.
        "settings_service": lambda: _bare_settings(resolved_db, resolved_observer),
        "settings_hub_service": lambda: _settings_hub(services, ctx),
        "authority_service": lambda: _bare_authority(resolved_db, resolved_observer),
        "heartbeat_service": lambda: LIVE_HEARTBEAT_SERVICE,
        "reach_service": lambda: LIVE_REACH_SERVICE,
        "telegram_service": lambda: LIVE_TELEGRAM_SERVICE,
        # 2026-11-09 (ops/connections): the Engines window, the calendar and the
        # Desk's UI feedback and the providers read the hub's context at each call.
        **_ops_connections_builders(ctx),
    }
    for name, build in builders.items():
        instance = getattr(services, name, None)
        if instance is None:
            instance = getattr(ctx, name, None)
        if instance is None:
            instance = build()
        setattr(services, name, instance)
        try:
            setattr(ctx, name, instance)
        except AttributeError:  # pragma: no cover - a non-dataclass stand-in
            pass
