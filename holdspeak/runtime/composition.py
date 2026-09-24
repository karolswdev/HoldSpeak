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

    # --- meetings --------------------------------------------------------
    # ``meeting_service`` carries ``bind_lifecycle`` (on_start / on_stop /
    # on_bookmark / on_update): live capture is impossible without it, which
    # is why ``meeting.start_capture`` used to fail with a soft refusal.
    meeting_service: Optional[Any] = None
    meeting_intel_service: Optional[Any] = None      # notify= -> the /ws bus
    meeting_aftercare_service: Optional[Any] = None  # notify= -> the /ws bus
    # PHILO-5-02 (gap A): the brief's producer clock (``WebContext.brief_clock``).
    monday_brief_service: Optional[Any] = None

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
        """Put one ``desk_changed`` frame on the bus, if there is a bus."""
        if self.broadcast is None:
            return
        origin = "hub"
        try:
            from holdspeak.services.observer import _caller_identity

            origin = _caller_identity.get("") or "hub"
        except Exception:  # pragma: no cover - the bus must not break a write
            pass
        try:
            self.broadcast(
                "desk_changed",
                {"kind": kind, "id": obj_id, "op": op, "origin": origin},
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

    names = (
        "primitive_service",
        "workbench_service",
        "meeting_service",
        "meeting_intel_service",
        "meeting_aftercare_service",
        "monday_brief_service",
        "project_service",
        "project_delta_service",
        "project_update_service",
        "project_steward_service",
        "project_setup_service",
        "project_door_service",
        "project_evidence_collector",
        "watch_service",
        "connections_service",
        "inference_setup_service",
        "inference_acquisition_service",
        "model_library_service",
        "inference_assignment_service",
        "inference_capability_service",
        "projection_service",
        "authority_service",
        "sync_service",
        "gate_service",
        "setup_service",
        "delivery_service",
        "mesh_service",
        "profile_key_service",
        "cadence_service",
        "follow_through_service",
        "door_service",
        "actuator_service",
        "mission_control_service",
        "reaction_service",
        "memory_service",
        "coder_service",
        "settings_service",
        "credential_service",
        "dictation_service",
        "people_service",
        "needs_you_last_known",
        "refinement_coordinator",
        "refinement_service",
        "github_provider",
        "jira_provider",
        "confluence_provider",
    )
    return RuntimeServices(
        db=db if db is not None else get_database(),
        observer=observer if observer is not None else get_observer(),
        broadcast=getattr(ctx, "broadcast", None),
        web_context=ctx,
        bare_root=False,
        label="hub",
        **{name: getattr(ctx, name, None) for name in names},
    )


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
