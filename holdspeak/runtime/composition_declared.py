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


def _invocations(db: Any, observer: Any) -> Any:
    from holdspeak.services.invocation_service import InvocationService

    return InvocationService(db, observer=observer)


def _hub_threads(services: Any) -> Any:
    """The threads' rows bind to a factory: one ThreadService per verb over the hub's bus (``thread_operations.py``)."""

    def make() -> Any:
        from holdspeak.services.thread_service import hub_thread_service

        return hub_thread_service(lambda topic, data: services.broadcast(topic, data) if services.broadcast else None)

    return make


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
        # The threads' verbs (thread_operations.py): the hub's ThreadService factory.
        "hub_thread_service": lambda: _hub_threads(services),
        # The capability run receipts (invocation_operations.py); the kernel broker at first use.
        "invocation_service": lambda: _invocations(resolved_db, resolved_observer),
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
