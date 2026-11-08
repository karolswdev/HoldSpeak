"""The product's ONE composition root (HS-200-45).

Before this module there were two. The hub composed the service layer in
``MeetingWebServer._create_app`` with its live wiring — ``notify=``/
``broadcast=`` callbacks, the meeting lifecycle hooks, the ``gh``/``acli``
runners, the refinement coordinator — and ``holdspeak/mcp`` composed the *same
classes* a second time from ``get_database()``, **bare**. The 2026-09-13
operational-surface audit (§9, §10.1) traced four symptoms to that single fact:
an MCP write never reached the open browser, the stdio sidecar needed its own
database handle (and so walked around the owner lock), concurrent access was
not made safe, and a handful of tools silently meant something different
depending on which root built them.

The arrangement now:

* The hub calls :func:`install` once, in ``_create_app``, with a
  :class:`RuntimeServices` filled from the same objects its HTTP routes use.
* Every other caller — MCP dispatch, each MCP family, the primitive HTTP
  routes — reads :func:`current` and takes what it needs. When the hub holds a
  live instance, that instance is used; when it does not, the caller builds a
  bare one through :func:`service`, which is lawful only in the cases that
  function's docstring names.
* Outside a hub, :func:`current` raises :class:`NoRuntimeError` naming the
  owner and the remedy. The MCP sidecar's standalone hatch
  (``HOLDSPEAK_MCP_STANDALONE=1``) is RETIRED (PHILO-5-01, the owner's D2):
  the sidecar is a proxy to the hub and nothing else.

The module holds *no* construction logic of its own beyond the bare database
accessor: what a service needs to be built correctly is knowledge that belongs
to the composition root that owns the wiring, not to the registry.
"""

from __future__ import annotations

import dataclasses
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from holdspeak.runtime.announce_scope import _announced, _origin

T = TypeVar("T")

class NoRuntimeError(RuntimeError):
    """No composition root is installed and none may be improvised here."""


@dataclass
class RuntimeServices:
    """One process's composed service layer.

    ``db``, ``observer`` and ``broadcast`` are the three things every caller
    needs. The named service fields are the hub's LIVE instances — the ones
    ``MeetingWebServer._create_app`` composes with wiring a bare constructor
    cannot reproduce. They are ``Optional`` because a bare composition (tests,
    a CLI command) holds none of them; a caller that
    finds ``None`` builds its own through :func:`service`.

    The field list was enumerated from ``holdspeak/web_server.py`` (the
    ``web_ctx = WebContext(...)`` block, ~:870-1047) intersected with what
    ``holdspeak/mcp`` and the primitive HTTP routes construct for themselves.
    ``web_context`` carries the whole hub context for the rare caller that
    needs a field not named here, so this list never has to grow just to
    unblock one route.
    """

    #: The one ``Database`` every caller in this process writes through. ``None``
    #: in a BARE composition, and that ``None`` is load-bearing: it means "this
    #: root shares no database handle; open the one your own accessor names".
    #: The ~40 MCP unit tests that monkeypatch ``<module>.get_database`` depend
    #: on that.
    db: Any = None
    observer: Any = None
    broadcast: Optional[Callable[[str, Any], None]] = None

    # --- desk primitives -------------------------------------------------
    # Composed by the hub with ``on_changed`` (HS-200-45 R4) so a write from
    # ANY caller — an HTTP route, MCP over stdio or HTTP, the iPad — puts one
    # ``desk_changed`` frame on the bus. Before this, only the browser that
    # made the write knew about it, because it refreshed itself.
    primitive_service: Optional[Any] = None
    workbench_service: Optional[Any] = None

    # --- the application-operation contract (PHILO-5-01) -----------------
    # ``holdspeak.operations.OperationRegistry`` bound to the live instances
    # above, once, by :func:`install_from_web_context`. HTTP routes reach it
    # through ``WebContext.operations``; MCP dispatch through this field. The
    # same object in both places is the identity fence.
    operations: Optional[Any] = None
    # PHILO-7-02: the kernel receipt readback (``kernel.receipt.read``).
    kernel_read_service: Optional[Any] = None

    # --- meetings --------------------------------------------------------
    # ``meeting_service`` carries ``bind_lifecycle`` (on_start / on_stop /
    # on_bookmark / on_update): live capture is impossible without it, which
    # is why ``meeting.start_capture`` used to fail with a soft refusal.
    meeting_service: Optional[Any] = None
    meeting_intel_service: Optional[Any] = None      # notify= -> the /ws bus
    meeting_aftercare_service: Optional[Any] = None  # notify= -> the /ws bus
    # PHILO-5-02 (gap A): the brief's producer clock (``WebContext.brief_clock``).
    monday_brief_service: Optional[Any] = None
    today_service: Optional[Any] = None

    # --- project rooms ---------------------------------------------------
    project_service: Optional[Any] = None          # delta_service= (mutual)
    project_delta_service: Optional[Any] = None    # collector + project
    project_update_service: Optional[Any] = None   # broker=
    project_steward_service: Optional[Any] = None  # collector/delta/update/door
    project_setup_service: Optional[Any] = None
    project_door_service: Optional[Any] = None
    project_evidence_collector: Optional[Any] = None
    watch_service: Optional[Any] = None            # gh watch kwargs
    connections_service: Optional[Any] = None
    connection_signin_service: Optional[Any] = None
    suggested_source_service: Optional[Any] = None  # PHILO-9-02: project_service=
    channel_service: Optional[Any] = None           # PHILO-10-01: the Send
    onboarding_service: Optional[Any] = None        # the Conductor K1: agent_hooks.install
    agent_hand_service: Optional[Any] = None        # Conductor K2: Hand to agent
    desk_window_service: Optional[Any] = None       # PHILO-16 16b: the desk's windows
    note_outcomes_service: Optional[Any] = None     # Betterment Q9: Find the tasks

    # --- operations ------------------------------------------------------
    cadence_service: Optional[Any] = None          # Config.load().cadence
    follow_through_service: Optional[Any] = None
    door_service: Optional[Any] = None
    actuator_service: Optional[Any] = None         # broadcast=
    mission_control_service: Optional[Any] = None
    reaction_service: Optional[Any] = None
    memory_service: Optional[Any] = None
    coder_service: Optional[Any] = None
    settings_service: Optional[Any] = None         # on_settings_applied=
    credential_service: Optional[Any] = None       # on_settings_applied=
    dictation_service: Optional[Any] = None        # journal_repository=
    people_service: Optional[Any] = None           # production People store

    # --- attention (HS-200-13, counsel P1-4) ----------------------------
    # The ONE durable last-known store the arrival route, the heartbeat and
    # the MCP sidecar replay from (``needs_you_aggregate.shared_last_known``).
    needs_you_last_known: Optional[Any] = None

    # --- inference -------------------------------------------------------
    inference_setup_service: Optional[Any] = None
    inference_acquisition_service: Optional[Any] = None
    model_library_service: Optional[Any] = None
    inference_assignment_service: Optional[Any] = None
    inference_capability_service: Optional[Any] = None

    # --- remaining hub boundaries ----------------------------------------
    projection_service: Optional[Any] = None
    authority_service: Optional[Any] = None
    sync_service: Optional[Any] = None
    gate_service: Optional[Any] = None
    setup_service: Optional[Any] = None
    delivery_service: Optional[Any] = None
    mesh_service: Optional[Any] = None
    profile_key_service: Optional[Any] = None

    # --- refinement ------------------------------------------------------
    refinement_coordinator: Optional[Any] = None   # host_kind="web"
    refinement_service: Optional[Any] = None

    # --- composed by the hub outside its WebContext ----------------------
    # The hub's Ask transport (hub_model=, broadcast=, rails_hydrator=) is
    # assembled by ``web/routes/primitives/ask.build_ask_service``; the plugin
    # job service is plain. Both are populated by :func:`install_from_web_context`
    # because families ask for them by name (counsel P1-3).
    ask_service: Optional[Any] = None
    plugin_job_service: Optional[Any] = None

    # --- providers -------------------------------------------------------
    github_provider: Optional[Any] = None          # self._gh_runner
    jira_provider: Optional[Any] = None            # self._acli_runner
    confluence_provider: Optional[Any] = None

    # --- escape hatch / provenance ---------------------------------------
    #: The hub's own ``WebContext``, when a hub installed this. ``None`` for a
    #: bare composition.
    web_context: Optional[Any] = None
    #: True when this is a bare composition, not a hub's. Callers that must
    #: behave differently outside a hub read this rather than guessing from a
    #: ``None`` field.
    bare_root: bool = False
    #: Free-form label for receipts and refusal messages.
    label: str = "hub"

    def emit_desk_changed(self, kind: str, obj_id: str, op: str) -> None:
        """Announce one changed desk object on the bus, if there is a bus.

        Inside a write (:func:`announce_scope`) the change is held: the write
        sends ONE ``desk_changed`` frame at its end, naming all it touched.
        Outside one (a worker thread, a conductor) the frame goes now.
        """
        change = (kind, obj_id, op, _origin())
        scope = _announced.get()
        if scope is not None and not scope.closed:
            scope.changes.append(change)
            scope.emitters.append(self)
            return
        self._send_desk_changed([change])

    def _send_desk_changed(self, changes: list) -> None:
        """One frame: the first change at the top level (the shape every
        listener already reads), and every change under ``changes``."""
        if changes:
            # Every producer's write comes through here.  Tell the memory
            # conductor WHAT changed, so the new item is in the index in
            # seconds and the pass reads only those sources
            # (MEMORY-DESIGN.md 3.1: speed, not correctness).
            try:
                from holdspeak import memory_conductor

                memory_conductor.wake([(change[0], change[1]) for change in changes])
            except Exception:  # pragma: no cover - a wake never fails a write
                pass
            # PERF-DOCK (2026-10-28): a write that is not only window placement
            # marks the cached Needs you dirty BEFORE the frame goes, so the
            # browser's plain read after the frame rebuilds it. The browser no
            # longer forces a rebuild (``?fresh=1``) on each frame.
            if self.db is not None and any(change[0] != "windows" for change in changes):
                try:
                    from holdspeak.services.needs_you_aggregate import mark_needs_you_dirty

                    mark_needs_you_dirty(self.db)
                except Exception:  # pragma: no cover - a marker never fails a write
                    pass
        if self.broadcast is None or not changes:
            return
        unique = list(dict.fromkeys(changes))
        kind, obj_id, op, origin = unique[0]
        try:
            self.broadcast(
                "desk_changed",
                {
                    "kind": kind, "id": obj_id, "op": op, "origin": origin,
                    "changes": [{"kind": k, "id": i, "op": o} for k, i, o, _ in unique],
                },
            )
        except Exception:  # pragma: no cover - a dead socket never fails a write
            pass


_lock = threading.Lock()
_installed: Optional[RuntimeServices] = None

#: Every service field a caller may ask :func:`service` for, by name.
SERVICE_FIELDS: frozenset[str] = frozenset(
    f.name for f in dataclasses.fields(RuntimeServices)
    if f.name not in {"db", "observer", "broadcast", "web_context", "bare_root", "label"}
)


def install(services: RuntimeServices) -> RuntimeServices:
    """Install *services* as this process's composition root."""
    global _installed
    with _lock:
        _installed = services
    return services


def uninstall() -> None:
    """Drop the installed root (process teardown; test isolation)."""
    global _installed
    with _lock:
        _installed = None


def installed() -> Optional[RuntimeServices]:
    """The installed root, or ``None`` — never raises, never improvises."""
    return _installed


def bare(db: Any = None, *, label: str = "bare") -> RuntimeServices:
    """A composition root that shares nothing — it opens NO database.

    Every field stays ``None`` (unless a caller passes an explicit *db*), so
    each caller falls back to its own accessor through :func:`db_or` /
    :func:`observer_or` / :func:`service`. Installing this root is therefore
    free of side effects: nothing is opened, nothing is written, no
    ``holdspeak.db`` is created.

    That is what makes it usable as the test root: it *permits* composition in
    this process without dictating which database handle the composition uses.
    """
    return RuntimeServices(db=db, observer=None, bare_root=True, label=label)


def no_runtime_message() -> str:
    """One sentence naming the situation and the remedy."""
    from holdspeak.db.core import DEFAULT_DB_PATH
    from holdspeak.runtime_lock import read_owner

    path = Path(DEFAULT_DB_PATH).expanduser()
    owner = read_owner(path)
    if owner:
        return (
            f"No composition root is installed in this process, and pid "
            f"{owner.get('pid')} already owns {path} on port {owner.get('port')}; "
            f"reach that hub over HTTP instead of opening the database twice."
        )
    return (
        f"No running HoldSpeak hub owns {path}; start `holdspeak web`, then retry."
    )


def current() -> RuntimeServices:
    """This process's composition root.

    In the hub this is the instance ``_create_app`` installed. Outside a hub
    this raises :class:`NoRuntimeError`, because improvising a second root over
    a database another process owns is exactly the multi-writer arrangement
    ``runtime_lock.py``'s C10 forbids.
    """
    root = _installed
    if root is not None:
        return root
    raise NoRuntimeError(no_runtime_message())


def db_or(fallback: Callable[[], Any]) -> Any:
    """The root's shared ``Database``, else *fallback*'s.

    *fallback* is the CALLING module's own ``get_database`` symbol. Reading it
    through the caller rather than importing it here is deliberate: it is the
    seam the MCP unit tests monkeypatch per module. When a hub installed the root there is one
    shared handle and *fallback* is never called — which is the whole point of
    the story: the hub and MCP stop being two writers.

    Calling this outside a hub raises
    :class:`NoRuntimeError` before any database is opened.
    """
    root = current()
    return root.db if root.db is not None else fallback()


def observer_or(fallback: Callable[[], Any]) -> Any:
    """The root's pipeline observer, else *fallback*'s."""
    root = current()
    return root.observer if root.observer is not None else fallback()


def broadcast() -> Optional[Callable[[str, Any], None]]:
    """The hub's bus, or ``None`` outside a hub."""
    return current().broadcast


def service(name: str, build: Callable[[], T]) -> T:
    """The hub's live instance of *name*, else a bare one from *build*.

    Falling back to *build* is lawful in exactly three situations, and in no
    others:

    1. **A bare composition** — a unit test on an isolated HOME. There is no hub, so there is no live
       instance to borrow and nothing to race.
    2. **A service the hub does not compose at all.** Several services are
       built per-request by their own HTTP routes too (they carry no callbacks
       and no runners), so a fresh instance over the same ``Database`` is
       behaviourally identical.
    3. **A partially-wired context** — a route test that builds a
       ``WebContext`` with only the fields it exercises.

    What is NOT lawful is the pre-HS-200-45 arrangement: building bare *while*
    a hub holds a wired instance, which is how an MCP write lost its broadcast
    and how ``meeting.start_capture`` lost its lifecycle callbacks.
    """
    root = current()
    if name not in SERVICE_FIELDS:
        # A programming error, surfaced where the tests run rather than
        # hidden behind a silent bare build in production (counsel P1-3).
        raise KeyError(
            f"RuntimeServices has no field {name!r}; a family asked the "
            "composition root for a service it does not carry"
        )
    instance = getattr(root, name, None)
    if instance is not None:
        return instance  # type: ignore[return-value]
    return build()


def notify_desk_changed(kind: str, obj_id: str, op: str) -> None:
    """Announce a desk write from a writer that has no ``on_changed`` of its own.

    For the few writers below the two primitive services -- the reaction and
    resourceful projections, the coder note materializer, the rails journal,
    the guardrail seeds -- that upsert notes or workbench items directly.
    A no-op outside a hub (no root, or a bare one): there is no bus.
    """
    root = _installed
    if root is None or root.broadcast is None:
        return
    root.emit_desk_changed(kind, obj_id, op)


def services_from_web_context(
    ctx: Any,
    *,
    db: Any = None,
    observer: Any = None,
) -> RuntimeServices:
    """Build a :class:`RuntimeServices` from a hub's ``WebContext``.

    One place maps the hub's context onto the registry, so the field list
    cannot drift between the two: every named field below is read off ``ctx``
    by the same name, except the four the hub composes outside the context
    constructor.
    """
    from holdspeak.db.core import get_database, get_observer

    from holdspeak.runtime.web_context_services import SERVICE_NAMES

    return RuntimeServices(
        db=db if db is not None else get_database(),
        observer=observer if observer is not None else get_observer(),
        broadcast=getattr(ctx, "broadcast", None),
        web_context=ctx,
        bare_root=False,
        label="hub",
        **{name: getattr(ctx, name, None) for name in SERVICE_NAMES},
    )


def _bare_onboarding() -> Any:
    from holdspeak.services.onboarding_service import OnboardingService

    return OnboardingService()


def install_from_web_context(
    ctx: Any,
    *,
    db: Any = None,
    observer: Any = None,
) -> RuntimeServices:
    """Compose a hub's root from its ``WebContext`` and install it.

    This is the WHOLE hub-side composition step, in one function, so that
    ``MeetingWebServer._create_app`` and the fences exercise the same code
    rather than two hand-kept copies of it:

    1. map the hub's live services onto a :class:`RuntimeServices`,
    2. compose the two desk-primitive services with ``on_changed`` bound to the
       root's ``desk_changed`` broadcast, and put them on both the context and
       the root, so the primitive HTTP routes and MCP dispatch resolve the SAME
       instance,
    3. put the loop's services (meetings, the summary, the clock-bearing brief,
       the Thought application service) on both the context and the root,
       composing the brief service here with the hub's producer clock,
    4. bind the application-operation contract (``holdspeak.operations``) to
       those same live instances and put it on both the context and the root,
    5. install it as this process's root.
    """
    from holdspeak.db.core import get_database, get_observer
    from holdspeak.services.primitive_service import PrimitiveService
    from holdspeak.services.workbench_service import WorkbenchService
    from holdspeak.services.setup_service import SetupService

    resolved_db = db if db is not None else get_database()
    resolved_observer = observer if observer is not None else get_observer()
    services = services_from_web_context(
        ctx, db=resolved_db, observer=resolved_observer
    )

    def _on_changed(kind: str, obj_id: str, op: str) -> None:
        services.emit_desk_changed(kind, obj_id, op)

    primitives = PrimitiveService(
        resolved_db, observer=resolved_observer, on_changed=_on_changed
    )
    workbenches = WorkbenchService(
        resolved_db, observer=resolved_observer, on_changed=_on_changed
    )
    services.primitive_service = primitives
    services.workbench_service = workbenches
    try:
        ctx.primitive_service = primitives
        ctx.workbench_service = workbenches
    except AttributeError:  # pragma: no cover - a non-dataclass stand-in
        pass

    # The two services families ask for that the hub composes OUTSIDE its
    # WebContext (counsel P1-3). Built by the hub's real builders, so an MCP
    # ``ask.run`` in the hub gets the Ask transport with hub_model=,
    # broadcast= and rails_hydrator= -- not a bare one.
    from holdspeak.services.plugin_job_service import PluginJobService
    from holdspeak.web.routes.primitives.ask import build_ask_service

    services.ask_service = build_ask_service(ctx)
    services.plugin_job_service = PluginJobService(resolved_db, observer=resolved_observer)

    # PHILO-5-02: the rest of the loop's services. The hub composes every one
    # of them itself (``MeetingWebServer._create_app``); the brief service is
    # composed HERE, once, with the hub's producer clock (gap A). A partially
    # wired context (a fence's stand-in) gets the same bare builds its routes
    # would make, put on BOTH the context and the root so the two still share
    # one instance.
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

    builders: dict[str, Callable[[], Any]] = {
        "meeting_service": lambda: MeetingService(resolved_db, observer=resolved_observer),
        "meeting_intel_service": lambda: MeetingIntelService(
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

    # PHILO-9-01: the Room's services. The hub composes every one of them
    # (``MeetingWebServer._create_app``, the mutual project/delta pair); a
    # partially wired context gets the same bare builds the MCP project family
    # makes off-hub, put on BOTH the context and the root.
    from holdspeak.runtime.room_composition import compose_room_services

    compose_room_services(services, ctx, resolved_db, resolved_observer)

    # PHILO-5-01/02: the contract binds to the instances composed above --
    # never to a fresh one -- so an HTTP route and an MCP call reach one object.
    from holdspeak import operations

    registry = operations.bind({name: getattr(services, name) for name in operations.BOUND_SERVICES})
    services.operations = registry
    try:
        ctx.operations = registry
    except AttributeError:  # pragma: no cover - a non-dataclass stand-in
        pass
    return install(services)


# ── the hub's service construction (bootstrap move, 2026-11-08) ─────────────
#
# ``MeetingWebServer._create_app`` built every service inline until this move;
# it now asks :func:`compose_hub` for the composition, mounts the routers with
# it and registers the lifespan. ``host`` is the web server: it supplies the
# runtime callbacks (``on_*``), the ``broadcast`` thunk, the bind and token,
# and the ``gh``/``acli`` runners. This module never imports
# ``holdspeak.web_server``; the host is passed in.


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


def compose_delivery(hub: HubComposition, *, auth_token: Optional[str]) -> HubComposition:
    """Build the delivery link, terminal targets and the hub command service.

    One shared NodeLinkState feeds both the node link and the terminal command
    claim leg: commands issued at the hub reach a remote node through the same
    authenticated long-poll. The terminal command service is the node router's
    command_source. ``_create_app`` calls this at the point it built them
    before, between the router mounts.
    """
    from holdspeak.delivery.node_link import NodeLinkState, NodeTokenStore
    from holdspeak.delivery.commands import HubCommandService, NodeCommandProcessor
    from holdspeak.delivery.terminal import TerminalTargetRegistry
    from holdspeak.db import get_database as _get_delivery_db
    from holdspeak.db.delivery_receipts import NodeReceiptLedger

    _delivery_link = NodeLinkState(
        NodeTokenStore(None), web_token=auth_token
    )
    _delivery_targets = TerminalTargetRegistry()
    hub.signin_targets["targets"] = _delivery_targets
    _delivery_live = hub.web_ctx.delivery_service.terminal_live_service(
        targets=_delivery_targets
    )
    from holdspeak.kernel.runtime import _service as _kernel_service

    _delivery_cmd = HubCommandService(
        repo=_get_delivery_db().delivery_receipts,
        processor=NodeCommandProcessor(
            node_id="local",
            targets=_delivery_targets,
            ledger=NodeReceiptLedger(None),
        ),
        local_node_id="local",
        kernel_broker=_kernel_service(),
    )
    _delivery_link.command_source = _delivery_cmd.claim_for_node

    hub.delivery_link = _delivery_link
    hub.delivery_targets = _delivery_targets
    hub.delivery_cmd = _delivery_cmd
    hub.delivery_live = _delivery_live
    return hub
