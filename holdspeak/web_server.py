"""Meeting web server for HoldSpeak.

Provides a per-meeting FastAPI server with HTTP endpoints and a WebSocket for
real-time updates.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import socket
import threading
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional, TYPE_CHECKING

from .logging_config import get_logger
from .web.runtime_support import _parse_iso_datetime

if TYPE_CHECKING:
    import numpy as np

    from .audio import AudioSource
    from .device_audio import DeviceRegistry
    from .device_status import DeviceStatusEmitter

log = get_logger("web_server")

try:
    import uvicorn
    from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse, Response
    from fastapi.staticfiles import StaticFiles
except Exception as e:  # pragma: no cover - optional dependency at runtime
    uvicorn = None  # type: ignore[assignment]
    FastAPI = None  # type: ignore[assignment]
    WebSocket = None  # type: ignore[assignment]
    WebSocketDisconnect = None  # type: ignore[assignment]
    HTMLResponse = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]
    Response = None  # type: ignore[assignment]
    _IMPORT_ERROR: Optional[Exception] = e
else:
    _IMPORT_ERROR = None


def _find_free_port(host: str) -> int:
    """Pick a free TCP port by binding to port 0."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def _format_duration(total_seconds: float) -> str:
    """Format duration as MM:SS or HH:MM:SS."""
    total_secs = max(0, int(total_seconds))
    hours, remainder = divmod(total_secs, 3600)
    mins, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


@dataclass(frozen=True)
class BroadcastMessage:
    type: str
    data: Any

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "data": self.data}


class WebSocketManager:
    """Tracks connected WebSocket clients and broadcasts messages."""

    def __init__(self) -> None:
        self._clients: set[Any] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: Any, *, subprotocol: Optional[str] = None) -> None:
        await websocket.accept(subprotocol=subprotocol)
        async with self._lock:
            self._clients.add(websocket)

    async def disconnect(self, websocket: Any) -> None:
        async with self._lock:
            self._clients.discard(websocket)

    async def broadcast(self, message: BroadcastMessage) -> None:
        payload = message.to_dict()
        async with self._lock:
            clients = list(self._clients)

        dead: list[Any] = []
        for websocket in clients:
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)

        if dead:
            async with self._lock:
                for websocket in dead:
                    self._clients.discard(websocket)

    async def close_all(self) -> None:
        async with self._lock:
            clients = list(self._clients)
            self._clients.clear()
        for websocket in clients:
            try:
                await websocket.close()
            except Exception:
                pass


@dataclass
class WebRuntimeCallbacks:
    """The behaviors + collaborators the web runtime injects into the server.

    HS-26-06: collapses what were ~30 individual ``MeetingWebServer`` constructor
    kwargs into one bundle. Field names match the historical kwargs, so callers
    read the same — they just wrap them in ``WebRuntimeCallbacks(...)``.
    ``MeetingWebServer.__init__`` now takes this plus only the scalar bind config
    (host / port / auth_token). The routes already read these via ``WebContext``;
    this bundle is the single seam through which the runtime supplies them.
    """

    on_bookmark: Callable[[str], Any]
    on_stop: Callable[[], Any]
    get_state: Callable[[], dict[str, Any]]
    on_start: Optional[Callable[[], Any]] = None
    on_meeting_stop: Optional[Callable[[], Any]] = None
    on_get_status: Optional[Callable[[], Any]] = None
    on_update_meeting: Optional[Callable[..., Any]] = None
    on_get_intent_controls: Optional[Callable[[], Any]] = None
    on_set_intent_profile: Optional[Callable[[str], Any]] = None
    on_set_intent_override: Optional[Callable[[Optional[list[str]]], Any]] = None
    on_route_preview: Optional[Callable[..., Any]] = None
    on_process_plugin_jobs: Optional[Callable[..., Any]] = None
    on_update_action_item: Optional[Callable[[str, str], Any]] = None
    on_update_action_item_review: Optional[Callable[[str, str], Any]] = None
    on_edit_action_item: Optional[Callable[..., Any]] = None
    on_set_title: Optional[Callable[[str], None]] = None
    on_set_tags: Optional[Callable[[list[str]], None]] = None
    on_settings_applied: Optional[Callable[[Any], None]] = None
    # HS-60: type a stored wake preview by its one-shot token; returns the
    # typed text, or None for an unknown/used token.
    on_wake_type: Optional[Callable[[str], Optional[str]]] = None
    # HS-75-01: hold-key preview commit/discard (the wake seam generalized).
    on_preview_type: Optional[Callable[[str], Optional[str]]] = None
    on_preview_discard: Optional[Callable[[str], bool]] = None
    # HS-78-01: speak-to-fill — browser audio in, the runtime's transcript out.
    # HS-131-09: `(audio, *, principal, mic_handle)` — the route supplies the
    # authenticated identity and the opaque interval handle.
    on_transcribe: Optional[Callable[..., str]] = None
    # HS-131-09: the admitted variant — returns a handle carrying the text, the
    # live provider admission, and the parent's close.
    on_transcribe_admitted: Optional[Callable[..., Any]] = None
    on_dictation_config_changed: Optional[Callable[[], None]] = None
    # HSM-13-04: deliver a companion-dictated answer (already pipeline-processed by the
    # route) into the waiting coder session via the SAME tmux/type path local dictation
    # uses. Deliver-on-command only; raises if undeliverable so the client sees an
    # honest failure rather than a false ack.
    on_remote_dictation: Optional[Callable[..., Any]] = None
    # HS-112-06: the runtime's one audio-floor arbiter (a `VoiceTypingSession`),
    # shared so the browser's open mic claims the SAME floor the hotkey, the
    # meeting recorder and the wake listener claim — one owner model, not two.
    voice_session: Optional[Any] = None
    project_detector: Optional[Any] = None
    device_registry: Optional["DeviceRegistry"] = None
    device_psk_provider: Optional[Callable[[], str]] = None
    on_device_audio_chunk: Optional[Callable[[str, "np.ndarray"], None]] = None
    on_device_voice_start: Optional[Callable[[str, "AudioSource"], bool]] = None
    on_device_voice_stop: Optional[
        Callable[[str, "AudioSource"], Optional["np.ndarray"]]
    ] = None
    on_device_voice_cancel: Optional[Callable[[str], None]] = None
    device_status_emitter: Optional["DeviceStatusEmitter"] = None
    on_device_event: Optional[Callable[[str, str, Optional[float]], None]] = None
    on_device_health: Optional[Callable[[Any], None]] = None
    on_device_query: Optional[
        Callable[[str, str, Optional[float]], Optional[dict[str, Any]]]
    ] = None


class MeetingWebServer:
    """FastAPI-based web dashboard server for a meeting."""

    def __init__(
        self,
        callbacks: "WebRuntimeCallbacks",
        *,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        auth_token: str = "",
        dictation_corrections_repository: Optional[Any] = None,
        dictation_journal_repository: Optional[Any] = None,
    ) -> None:
        if _IMPORT_ERROR is not None:
            raise RuntimeError(
                "MeetingWebServer requires FastAPI + uvicorn. "
                "Install dependencies: `pip install fastapi uvicorn`."
            ) from _IMPORT_ERROR

        # HS-26-06: explode the bundle onto attributes so the rest of the class
        # (and `_create_app`'s WebContext build) reads `self.on_*` unchanged.
        self._callbacks = callbacks
        # HS-39-02: one session-scoped dictation correction store, shared by the
        # dictation routes (record/read) and the live runtime (consult).
        # HS-40-02: when the live runtime injects a repository the store is
        # DB-backed (loads recent on construction, writes through on record);
        # with none (the default — every test that builds a bare server) it's
        # the Phase-39 in-process ring, byte-identical and touching no DB.
        from .plugins.dictation.corrections import CorrectionStore

        self.dictation_corrections = CorrectionStore(
            repository=dictation_corrections_repository
        )
        # HS-39-05: one session-scoped dictation telemetry store, fed via the
        # pipeline `on_run` hook from the dry-run + live paths.
        from .plugins.dictation.telemetry_store import DictationTelemetryStore

        self.dictation_telemetry = DictationTelemetryStore()
        # HS-45-01: one session-scoped dictation journal recorder, fed at the
        # same post-run seam telemetry uses from the dry-run + live paths. When
        # the live runtime injects a repository the recorder is durable; with
        # none (the default — every bare server / test) it is a no-op and
        # dictation stays byte-identical (no DB touched).
        from .plugins.dictation.journal import DictationJournalRecorder

        self.dictation_journal = DictationJournalRecorder(
            repository=dictation_journal_repository
        )
        self.on_bookmark = callbacks.on_bookmark
        self.on_stop = callbacks.on_stop
        self.on_meeting_stop = callbacks.on_meeting_stop
        self.get_state = callbacks.get_state
        self.on_start = callbacks.on_start
        self.on_get_status = callbacks.on_get_status
        self.on_update_meeting = callbacks.on_update_meeting
        self.on_get_intent_controls = callbacks.on_get_intent_controls
        self.on_set_intent_profile = callbacks.on_set_intent_profile
        self.on_set_intent_override = callbacks.on_set_intent_override
        self.on_route_preview = callbacks.on_route_preview
        self.on_process_plugin_jobs = callbacks.on_process_plugin_jobs
        self.on_update_action_item = callbacks.on_update_action_item
        self.on_update_action_item_review = callbacks.on_update_action_item_review
        self.on_edit_action_item = callbacks.on_edit_action_item
        self.on_set_title = callbacks.on_set_title
        self.on_set_tags = callbacks.on_set_tags
        self.on_settings_applied = callbacks.on_settings_applied
        self.on_wake_type = callbacks.on_wake_type
        self.on_preview_type = callbacks.on_preview_type
        self.on_preview_discard = callbacks.on_preview_discard
        self.on_transcribe = callbacks.on_transcribe
        self.on_transcribe_admitted = callbacks.on_transcribe_admitted
        self.on_dictation_config_changed = callbacks.on_dictation_config_changed
        self.on_remote_dictation = callbacks.on_remote_dictation
        # HS-112-06: the shared audio-floor arbiter (None on a bare server).
        self.voice_session = callbacks.voice_session
        self._project_detector = callbacks.project_detector
        device_registry = callbacks.device_registry
        if device_registry is None:
            from .device_audio import DeviceRegistry as _DeviceRegistry
            device_registry = _DeviceRegistry()
        self.device_registry: "DeviceRegistry" = device_registry
        device_psk_provider = callbacks.device_psk_provider
        if device_psk_provider is None:
            from .config import Config as _Config
            from .device_audio import ensure_device_psk as _ensure_device_psk

            def _default_psk_provider() -> str:
                return _ensure_device_psk(_Config.load())

            device_psk_provider = _default_psk_provider
        self.device_psk_provider: Callable[[], str] = device_psk_provider
        self.on_device_audio_chunk: Optional[Callable[[str, "np.ndarray"], None]] = (
            callbacks.on_device_audio_chunk
        )
        self.on_device_voice_start: Optional[
            Callable[[str, "AudioSource"], bool]
        ] = callbacks.on_device_voice_start
        self.on_device_voice_stop: Optional[
            Callable[[str, "AudioSource"], Optional["np.ndarray"]]
        ] = callbacks.on_device_voice_stop
        self.on_device_voice_cancel: Optional[Callable[[str], None]] = callbacks.on_device_voice_cancel
        device_status_emitter = callbacks.device_status_emitter
        if device_status_emitter is None:
            from .device_status import DeviceStatusEmitter as _DeviceStatusEmitter
            device_status_emitter = _DeviceStatusEmitter(label_lookup=device_registry)
        self.device_status_emitter: "DeviceStatusEmitter" = device_status_emitter
        self.on_device_event: Optional[Callable[[str, str, Optional[float]], None]] = (
            callbacks.on_device_event
        )
        self.on_device_health = callbacks.on_device_health
        self.on_device_query = callbacks.on_device_query
        self.host = host
        from . import web_auth

        # Every runtime has an owner credential, including loopback and bare
        # in-process servers.  The full runtime persists its configured token;
        # a directly-constructed server gets an ephemeral one.
        self.auth_token = auth_token or (
            web_auth.generate_web_token() if web_auth.is_loopback_host(host) else ""
        )
        self._configured_port = port

        self.port: Optional[int] = None
        self._server: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._started = threading.Event()
        # HSM-15-10: LAN discovery advertiser, created at start() once the port
        # is bound, only off-loopback. Best-effort (never blocks/crashes start).
        self._mesh_advertiser: Optional[Any] = None

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = WebSocketManager()
        self._duration_task: Optional[asyncio.Task[None]] = None
        self._coder_frames_task: Optional[asyncio.Task[None]] = None
        self._rails_observer_task: Optional[asyncio.Task[None]] = None
        self._kernel_liveness_task: Optional[asyncio.Task[None]] = None

        self.app = self._create_app()

    @property
    def url(self) -> Optional[str]:
        if self.port is None:
            return None
        return f"http://{self.host}:{self.port}"

    def start(self) -> str:
        """Start the server in a background thread and return its URL."""
        if self._thread is not None and self._thread.is_alive():
            if self.url is None:
                raise RuntimeError("Server thread is running but URL is unknown")
            return self.url

        # HS-25-02: refuse to expose an unauthenticated runtime off-loopback.
        from . import web_auth

        blocked, reason = web_auth.nonloopback_bind_blocked(self.host, self.auth_token)
        if blocked:
            raise RuntimeError(reason)
        if not web_auth.is_loopback_host(self.host):
            log.warning(
                "Binding non-loopback host %r: the web runtime is reachable beyond "
                "this machine and requires the auth token on every request.",
                self.host,
            )

        self.port = self._configured_port or _find_free_port(self.host)
        from .principals import agent_credentials

        agent_credentials.set_hub_url(f"http://{self.host}:{self.port}")
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_config=None,
            access_log=False,
            lifespan="on",
        )
        self._server = uvicorn.Server(config)
        self._started.clear()

        self._thread = threading.Thread(
            target=self._run_server,
            name=f"MeetingWebServer:{self.port}",
            daemon=True,
        )
        self._thread.start()

        if not self._started.wait(timeout=5.0):
            raise RuntimeError("Timed out waiting for web server startup")

        if self.url is None:
            raise RuntimeError("Server started but URL is unknown")

        log.info(f"Meeting web server started: {self.url}")

        # HSM-15-10: advertise on the LAN once bound (off-loopback only). Wholly
        # best-effort — a failure here logs a warning and never affects the
        # already-running server.
        self._start_mesh_advertising()

        return self.url

    def stop(self) -> None:
        """Stop the server gracefully."""
        if self._server is None:
            return

        log.info("Stopping meeting web server")
        # HSM-15-10: unregister the LAN advertisement before tearing down.
        self._stop_mesh_advertising()
        self._server.should_exit = True

        if self._thread is not None:
            self._thread.join(timeout=10.0)

        self._server = None
        self._thread = None
        self._loop = None
        self._duration_task = None
        self._started.clear()

    def _start_mesh_advertising(self) -> None:
        """Advertise this server on the LAN (HSM-15-10), best-effort.

        Off-loopback binds only; any failure (zeroconf missing, registration
        error) is logged inside the advertiser and never propagates here.
        """
        from . import web_auth

        if web_auth.is_loopback_host(self.host) or self.port is None:
            return
        try:
            from . import __version__
            from .config import Config
            from .mesh import MeshAdvertiser, resolve_device_name

            try:
                configured_name = Config.load().mesh.device_name
            except Exception:
                configured_name = ""
            advertiser = MeshAdvertiser(
                device_name=resolve_device_name(configured_name),
                host=self.host,
                port=self.port,
                version=__version__,
                requires_token=True,  # off-loopback always requires the token
            )
            advertiser.start()
            self._mesh_advertiser = advertiser
        except Exception as e:  # pragma: no cover - defensive; advertiser self-guards
            log.warning(f"Mesh advertising could not start: {e}")

    def _stop_mesh_advertising(self) -> None:
        advertiser = self._mesh_advertiser
        self._mesh_advertiser = None
        if advertiser is None:
            return
        try:
            advertiser.stop()
        except Exception as e:  # pragma: no cover - defensive
            log.debug(f"Mesh advertising stop failed: {e}")

    def broadcast(self, message_type: str, data: Any) -> None:
        """Broadcast an update to all connected WebSocket clients."""
        loop = self._loop
        if loop is None or loop.is_closed():
            log.debug(f"Broadcast skipped - no event loop (type={message_type})")
            return

        log.debug(f"Broadcasting {message_type} to WebSocket clients")
        message = BroadcastMessage(type=message_type, data=data)
        future = asyncio.run_coroutine_threadsafe(self._ws.broadcast(message), loop)

        def _log_result(f: "concurrent.futures.Future[None]") -> None:
            try:
                f.result()
            except Exception as e:
                log.debug(f"WebSocket broadcast failed: {e}")

        future.add_done_callback(_log_result)

    def _run_server(self) -> None:
        assert self._server is not None
        try:
            self._server.run()
        except Exception as e:
            log.error(f"Web server failed: {e}")
            self._started.set()

    def _create_app(self) -> Any:
        from . import web_auth

        app = FastAPI()
        app.state.device_registry = self.device_registry

        # HS-106-02: network location is never request authority.  Every API
        # request gets a typed principal at the edge; the centralized route-right
        # table refuses missing rights before route code runs.  Static shell files
        # and the existing health/pairing entrances remain public.
        from .principals import (
            Principal,
            PrincipalKind,
            UNAUTHENTICATED,
            agent_credentials,
            derive_owner,
            refusal,
            required_right,
        )

        app.state.agent_credentials = agent_credentials
        app.state.owner_token = self.auth_token

        @app.middleware("http")
        async def _web_auth_gate(request: Request, call_next: Any) -> Any:
            token = web_auth.extract_request_token(
                authorization=request.headers.get("authorization"),
                header_token=request.headers.get("x-holdspeak-token"),
                query_token=request.query_params.get("token"),
            )
            principal = derive_owner(token, self.auth_token)
            if principal is None:
                principal = agent_credentials.derive(token)
            credential = None
            if principal is None:
                node_token = request.headers.get("x-holdspeak-node-token")
                node_store = getattr(request.app.state, "node_token_store", None)
                # HS-131-16: the whole authenticated snapshot, not only the opaque
                # id. The mesh relay legs are authorized against the node's NAME
                # and its exact credential generation, and neither may be read
                # from the request body.
                snapshot = node_store.identify(node_token) if node_store else None
                if snapshot is not None and snapshot.node_id:
                    principal = Principal(PrincipalKind.NODE, snapshot.node_id)
                    credential = snapshot
            principal = principal or UNAUTHENTICATED
            request.state.principal = principal
            request.state.node_credential = credential

            right = required_right(request.method, request.url.path)
            if right is not None and not principal.permits(right):
                status = 401 if principal.kind is PrincipalKind.NONE else 403
                return JSONResponse(refusal(principal, right), status_code=status)
            return await call_next(request)

        # HS-117-11: unified domain-error handler. HoldSpeakError subclasses
        # produce a structured JSON response instead of a raw 500.
        from .errors import HoldSpeakError, error_response

        @app.exception_handler(HoldSpeakError)
        async def _holdspeak_error_handler(
            request: Request, exc: HoldSpeakError
        ) -> JSONResponse:
            log.warning("domain error on %s %s: %s", request.method, request.url.path, exc)
            return JSONResponse(error_response(exc), status_code=400)

        from .device_audio_ws import register_device_audio_routes

        register_device_audio_routes(
            app,
            device_registry=self.device_registry,
            get_psk=self.device_psk_provider,
            on_chunk=self.on_device_audio_chunk,
            on_voice_start=self.on_device_voice_start,
            on_voice_stop=self.on_device_voice_stop,
            on_voice_cancel=self.on_device_voice_cancel,
            status_emitter=self.device_status_emitter,
            on_event=self.on_device_event,
            on_device_health=self.on_device_health,
            on_device_query=self.on_device_query,
        )

        # Phase 26: route modules read from a shared WebContext instead of
        # closing over `self`. HS-26-01..05 migrated every domain off this
        # factory; what remains here is app assembly + lifespan + the
        # device-audio WS (its own PSK handshake). `_create_app` is now a thin
        # assembler.
        from .web.context import WebContext
        from .services.authority_service import AuthorityService
        from .services.credential_service import CredentialService
        from .services.delivery_service import DeliveryService
        from .services.cadence_service import CadenceService
        from .services.coder_service import CoderService
        from .services.dictation_service import DictationService
        from .services.sync_service import SyncService
        from .services.actuator_service import ActuatorProposalService
        from .config import Config
        from .services.gate_service import GateService
        from .services.follow_through_service import FollowThroughService
        from .services.memory_service import MemoryService
        from .services.mesh_service import MeshService
        from .services.mission_control_service import MissionControlService
        from .services.project_service import ProjectService
        from .services.projection_service import ProjectionService
        from .services.settings_service import SettingsService
        from .services.setup_service import SetupService
        from .services.inference_setup_service import InferenceSetupApplicationService
        from .services.inference_acquisition_service import InferenceAcquisitionApplicationService
        from .services.model_library_service import ModelLibraryApplicationService
        from .services.inference_assignment_service import InferenceAssignmentService
        from .services.inference_capability_service import InferenceCapabilityApplicationService
        from .services.profile_key_service import ProfileKeyService
        from .db import get_database, get_observer
        from .web.routes import (
            build_activity_router,
            build_automations_router,
            build_authority_router,
            build_cadence_router,
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
            build_follow_through_router,
            build_people_router,
            build_desk_actuators_router,
            build_desk_seed_router,
            build_meeting_import_router,
            build_meetings_router,
            build_memory_router,
            build_model_library_router,
            build_inference_assignments_router,
            build_monday_brief_router,
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
        )

        from .services.meeting_aftercare_service import MeetingAftercareService
        from .services.meeting_intel_service import MeetingIntelService
        from .services.meeting_service import MeetingService
        from .services.people_service import PeopleService, UnavailablePeopleStore
        from .people import production_people_store
        from .services.reaction_service import ReactionService
        from .services.refinement_coordinator import RefinementCoordinator
        from .services.refinement_application_service import RefinementApplicationService

        from .delivery.node_link import NodeTokenStore as _MeshNodeTokenStore

        def _mesh_token_store() -> Any:
            return _MeshNodeTokenStore(None)

        obs = get_observer()
        meeting_service = MeetingService(get_database(), observer=obs)
        notify = lambda message_type, data: self.broadcast(message_type, data)
        meeting_intel_service = MeetingIntelService(get_database(), notify=notify, observer=obs)
        meeting_aftercare_service = MeetingAftercareService(get_database(), notify=notify, observer=obs)
        refinement_coordinator = RefinementCoordinator(get_database(), host_kind="web")
        refinement_service = RefinementApplicationService(
            get_database(), coordinator=refinement_coordinator
        )
        self.refinement_coordinator = refinement_coordinator

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
            if self.on_update_meeting is not None:
                return self.on_update_meeting(title=title, tags=tags)
            if title is not None and self.on_set_title is not None:
                self.on_set_title(title)
            if tags is not None and self.on_set_tags is not None:
                self.on_set_tags(tags)
            return self.get_state() or {}

        meeting_service.bind_lifecycle(
            on_start=self.on_start,
            # HS-132-01: the meeting verb binds the no-fallback stop. The
            # runtime-fallback `on_stop` sets `runtime_stop_event` when no
            # meeting is live, so binding it here let a stop press with a stale
            # orb exit the hub main loop and still answer success. Mirrors the
            # partial-context composition in web/routes/meetings/live.py.
            on_stop=self.on_meeting_stop or self.on_stop,
            on_bookmark=self.on_bookmark,
            # Bound only when a runtime actually owns the live meeting's
            # metadata; otherwise the archive path in
            # `MeetingService.update_meeting` stays in charge, unchanged.
            on_update=(
                _update_meeting
                if (
                    self.on_update_meeting is not None
                    or self.on_set_title is not None
                    or self.on_set_tags is not None
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
        from .kernel.runtime import _configure

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
        web_ctx = WebContext(
            get_state=self.get_state,
            meeting_service=meeting_service,
            meeting_service_factory=lambda: MeetingService(get_database(), observer=obs),
            meeting_intel_service=meeting_intel_service,
            meeting_intel_service_factory=lambda: MeetingIntelService(get_database(), notify=notify, observer=obs),
            meeting_aftercare_service=meeting_aftercare_service,
            meeting_aftercare_service_factory=lambda: MeetingAftercareService(get_database(), notify=notify, observer=obs),
            # Late-bind broadcast: the prior inline handlers called
            # `self.broadcast(...)`, which resolves the attribute at call time
            # (tests reassign `server.broadcast` to spy on it). A thunk keeps
            # that dynamic dispatch instead of freezing the bound method.
            broadcast=lambda message_type, data: self.broadcast(message_type, data),
            on_bookmark=self.on_bookmark,
            on_start=self.on_start,
            on_stop=self.on_stop,
            on_meeting_stop=self.on_meeting_stop,
            on_update_action_item=self.on_update_action_item,
            on_update_action_item_review=self.on_update_action_item_review,
            on_edit_action_item=self.on_edit_action_item,
            on_update_meeting=self.on_update_meeting,
            on_set_title=self.on_set_title,
            on_set_tags=self.on_set_tags,
            project_service=ProjectService(get_database(), observer=obs),
            projection_service=ProjectionService(get_database(), observer=obs),
            authority_service=AuthorityService(get_database(), observer=obs),
            credential_service=CredentialService(
                get_database(), on_settings_applied=self.on_settings_applied, observer=obs
            ),
            cadence_service=CadenceService(get_database(), Config.load().cadence, observer=obs),
            follow_through_service=FollowThroughService(get_database(), observer=obs, people_projection=people_service),
            people_service=people_service,
            sync_service=SyncService(get_database(), observer=obs),
            gate_service=GateService(get_database(), observer=obs),
            setup_service=SetupService(get_database(), observer=obs),
            inference_setup_service=inference_setup_service,
            inference_acquisition_service=inference_acquisition_service,
            model_library_service=model_library_service,
            inference_assignment_service=inference_assignment_service,
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
            memory_service=MemoryService(get_database(), observer=obs),
            mission_control_service=MissionControlService(get_database(), observer=obs),
            reaction_service=ReactionService(get_database(), observer=obs),
            refinement_coordinator=refinement_coordinator,
            refinement_service=refinement_service,
            settings_service=SettingsService(
                get_database(), on_settings_applied=self.on_settings_applied, observer=obs
            ),
            profile_key_service=ProfileKeyService(get_database()),
            on_get_intent_controls=self.on_get_intent_controls,
            on_set_intent_profile=self.on_set_intent_profile,
            on_set_intent_override=self.on_set_intent_override,
            on_route_preview=self.on_route_preview,
            on_dictation_config_changed=self.on_dictation_config_changed,
            on_remote_dictation=self.on_remote_dictation,
            coder_service=CoderService(get_database(), observer=obs),
            dictation_service=DictationService(
                get_database(), observer=obs,
                journal_repository=getattr(self.dictation_journal, "repository", None),
                journal_available=self.dictation_journal is not None,
            ),
            on_process_plugin_jobs=self.on_process_plugin_jobs,
            device_registry=self.device_registry,
            project_detector=self._project_detector,
            ws=self._ws,
            on_get_status=self.on_get_status,
            on_settings_applied=self.on_settings_applied,
            on_wake_type=self.on_wake_type,
            on_preview_type=self.on_preview_type,
            on_preview_discard=self.on_preview_discard,
            on_transcribe=self.on_transcribe,
            on_transcribe_admitted=self.on_transcribe_admitted,
            current_formatted_duration=self._current_formatted_duration,
            corrections=self.dictation_corrections,
            telemetry=self.dictation_telemetry,
            journal=self.dictation_journal,
            voice_session=self.voice_session,
            # HSM-15-10: a server bound off-loopback requires the auth token; the
            # mesh identify endpoint surfaces that to an unpaired companion.
            mesh_requires_token=not web_auth.is_loopback_host(self.host),
            web_host=self.host,
            web_auth_token=self.auth_token,
        )
        from .web.routes.actuator_shared import DeskActuatorLifecycle
        web_ctx.actuator_service = ActuatorProposalService(
            get_database(), config_provider=lambda: Config.load(path=__import__("holdspeak.config", fromlist=["CONFIG_FILE"]).CONFIG_FILE),
            broadcast=lambda message_type, data: self.broadcast(message_type, data),
            lifecycle=DeskActuatorLifecycle(web_ctx, get_database()),
        )
        app.include_router(build_core_router(web_ctx))
        app.include_router(build_authority_router(web_ctx))
        app.include_router(build_cadence_router(web_ctx))
        app.include_router(build_follow_through_router(web_ctx))
        app.include_router(build_people_router(web_ctx))
        app.include_router(build_automations_router(web_ctx))
        app.include_router(build_decision_records_router(web_ctx))
        app.include_router(build_decisions_router(web_ctx))
        app.include_router(build_memory_router(web_ctx))
        app.include_router(build_model_library_router(web_ctx))
        app.include_router(build_inference_assignments_router(web_ctx))
        app.include_router(build_monday_brief_router(web_ctx))
        app.include_router(build_meetings_router(web_ctx))
        app.include_router(build_desk_actuators_router(web_ctx))
        app.include_router(build_desk_seed_router(web_ctx))
        app.include_router(build_meeting_import_router(web_ctx))
        app.include_router(build_mesh_router(web_ctx))
        app.include_router(build_missioncontrol_router(web_ctx))
        app.include_router(build_delivery_router(web_ctx))
        app.include_router(build_delivery_attempts_router(web_ctx))
        app.include_router(build_delivery_dossiers_router(web_ctx))
        app.include_router(build_delivery_prs_router(web_ctx))
        app.include_router(build_repositories_router(web_ctx))
        # One shared NodeLinkState feeds both the node link and the terminal
        # command claim leg: commands issued at the hub reach a remote node
        # through the same authenticated long-poll. The terminal command
        # service is the node router's command_source.
        from .delivery.node_link import NodeLinkState, NodeTokenStore
        from .delivery.commands import HubCommandService, NodeCommandProcessor
        from .delivery.terminal import TerminalTargetRegistry
        from .db import get_database as _get_delivery_db
        from .db.delivery_receipts import NodeReceiptLedger

        _delivery_link = NodeLinkState(
            NodeTokenStore(None), web_token=self.auth_token
        )
        app.state.node_token_store = _delivery_link.token_store
        _delivery_targets = TerminalTargetRegistry()
        from .kernel.runtime import _service as _kernel_service

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
        app.include_router(
            build_delivery_node_router(
                web_ctx, link=_delivery_link, web_token=self.auth_token
            )
        )
        app.include_router(
            build_delivery_terminal_router(
                web_ctx,
                service=_delivery_cmd,
                targets=_delivery_targets,
                link=_delivery_link,
            )
        )
        # The factory shares the terminal command service and target
        # registry so a launch issues its worktree.create/spawn envelopes
        # and pins the spawned pane's immutable target on the same spine.
        app.include_router(
            build_delivery_factory_router(
                web_ctx, commands=_delivery_cmd, targets=_delivery_targets
            )
        )
        app.include_router(build_dictation_router(web_ctx))
        app.include_router(build_activity_router(web_ctx))
        app.include_router(build_pages_router(web_ctx))
        app.include_router(
            build_system_router(
                web_ctx, commands=_delivery_cmd, targets=_delivery_targets
            )
        )
        app.include_router(build_projects_router(web_ctx))
        app.include_router(build_roadmaps_router(web_ctx))
        app.include_router(build_primitives_router(web_ctx))
        app.include_router(build_projections_router(web_ctx))
        app.include_router(build_constitutional_router())
        app.include_router(build_scheduled_recordings_router(web_ctx))
        app.include_router(build_setup_router(web_ctx))
        app.include_router(build_sync_router(web_ctx))

        @app.on_event("startup")
        async def _startup() -> None:
            # HS-104-02 restart honesty: revalidate-or-expire, never resume.
            try:
                from .web.routes.system.gate_routes import invalidate_held_on_startup

                invalidate_held_on_startup(web_ctx.gate_service)
            except Exception as e:
                log.error(f"gate startup invalidation failed: {e}")
            try:
                from .web.routes.primitives.invocations import recover_inference_on_startup

                recover_inference_on_startup()
            except Exception as e:
                log.error(f"inference startup recovery failed: {e}")
            self._loop = asyncio.get_running_loop()
            self._duration_task = asyncio.create_task(self._duration_loop())
            self._coder_frames_task = asyncio.create_task(self._coder_frames_loop())
            self._rails_observer_task = asyncio.create_task(self._rails_observer_loop())
            await asyncio.to_thread(_kernel_service().reap_and_recover_projections)
            try:
                await refinement_coordinator.start()
            except Exception as e:
                log.error(f"refinement coordinator startup recovery failed: {e}")
            self._kernel_liveness_task = asyncio.create_task(
                self._kernel_liveness_loop()
            )
            try:
                from .skills_library import seed_skills_if_empty
                seeded = seed_skills_if_empty()
                if seeded:
                    log.info(f"Seeded {seeded} built-in skills")
            except Exception as e:
                log.debug(f"skill seeding skipped: {e}")
            try:
                from .workbench_conductor import start_conductor, set_broadcast
                set_broadcast(lambda t, d: self.broadcast(t, d))
                start_conductor()
            except Exception as e:
                log.error(f"workbench conductor startup failed: {e}")
            try:
                from .scheduled_recording_conductor import (
                    start_scheduled_recording_conductor,
                    set_broadcast as sr_set_broadcast,
                )
                sr_set_broadcast(lambda t, d: self.broadcast(t, d))
                start_scheduled_recording_conductor(
                    voice_floor_fn=lambda: self.voice_session.active_owner
                    if hasattr(self, "voice_session")
                    else None,
                    start_meeting_fn=lambda principal, title: (
                        setattr(callbacks, "pending_title", title) or  # type: ignore[func-returns-value]
                        callbacks._start_meeting(principal=principal)
                    )
                    if hasattr(callbacks, "_start_meeting")
                    else None,
                    stop_meeting_fn=lambda: callbacks._stop_active_meeting(
                        allow_runtime_fallback=False
                    )
                    if hasattr(callbacks, "_stop_active_meeting")
                    else None,
                )
            except Exception as e:
                log.error(f"scheduled recording conductor startup failed: {e}")
            self._started.set()
            log.debug("Meeting web server startup complete")

        @app.on_event("shutdown")
        async def _shutdown() -> None:
            await refinement_coordinator.shutdown()
            for task in (
                self._duration_task,
                self._coder_frames_task,
                self._rails_observer_task,
                self._kernel_liveness_task,
            ):
                if task is None:
                    continue
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    log.debug(f"Background task error during shutdown: {e}")
            await self._ws.close_all()
            log.debug("Meeting web server shutdown complete")

        # HS-91-09: serve the one Vite/React build. Explicit browser routes
        # return its index shell; this mount owns hashed assets and public art.
        _BUILT_DIR = Path(__file__).resolve().parent / "static" / "_built"
        if _BUILT_DIR.is_dir():
            app.mount(
                "/_built",
                StaticFiles(directory=str(_BUILT_DIR), html=True),
                name="built",
            )

        return app

    def _current_formatted_duration(self) -> Optional[str]:
        try:
            state = self.get_state() or {}
        except Exception:
            return None

        duration = state.get("duration")
        if isinstance(duration, (int, float)):
            return _format_duration(float(duration))

        formatted_duration = state.get("formatted_duration")
        if isinstance(formatted_duration, str) and formatted_duration:
            return formatted_duration

        started_at = _parse_iso_datetime(state.get("started_at"))
        if started_at is None:
            return None

        ended_at = _parse_iso_datetime(state.get("ended_at"))
        end = ended_at or datetime.now()
        return _format_duration((end - started_at).total_seconds())

    async def _duration_loop(self) -> None:
        """Broadcast duration updates every second."""
        last: Optional[str] = None
        while True:
            await asyncio.sleep(1.0)
            duration = self._current_formatted_duration()
            if duration is None:
                continue
            if duration != last:
                await self._ws.broadcast(BroadcastMessage(type="duration", data=duration))
                last = duration

    async def _kernel_liveness_loop(self) -> None:
        """Terminalize work whose claimed executor stopped reporting."""
        from .kernel.runtime import _service as _kernel_service

        while True:
            await asyncio.sleep(1.0)
            try:
                await asyncio.to_thread(_kernel_service().reap_and_recover_projections)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.debug(f"kernel liveness loop error: {exc}")

    async def _coder_frames_loop(self) -> None:
        """THE registry watcher (HS-87-01): a `scope:"coder"` frame per
        awaiting-response transition, so closed surfaces stay current
        without polling. The registry file's mtime gates the read (a
        stat every 2 s, the JSON only when the hooks actually wrote);
        the first observation is a baseline, never a broadcast."""
        from . import agent_context, coder_steering

        last_mtime: Optional[float] = None
        snapshot: Optional[dict[str, bool]] = None
        while True:
            await asyncio.sleep(2.0)
            try:
                path = agent_context.AGENT_CONTEXT_FILE
                mtime = path.stat().st_mtime if path.exists() else None
                if mtime == last_mtime:
                    continue
                last_mtime = mtime
                sessions = await asyncio.to_thread(agent_context.list_agent_sessions)
                current = coder_steering.awaiting_snapshot(sessions)
                if snapshot is not None:
                    for key in coder_steering.awaiting_transitions(snapshot, current):
                        await self._ws.broadcast(
                            BroadcastMessage(
                                type="intel_status",
                                data={
                                    "state": "ready",
                                    "scope": "coder",
                                    "capability": {
                                        "kind": "coder",
                                        "id": key,
                                        "name": key.split(":", 1)[0],
                                    },
                                },
                            )
                        )
                snapshot = current
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.debug(f"coder frames loop error: {e}")

    async def _rails_observer_loop(self) -> None:
        """The ambient dw observer (HS-88-03) — OFF BY DEFAULT. When
        enabled, tail the rails' events, and each NEW batch becomes a
        journal note summarized by a local RuntimeProfile model (off the
        event loop). Read-only: the only write is the journal. The flag
        is re-read each tick so it can be turned on without a restart;
        when off the loop just sleeps."""
        from . import rails_observer
        from .config import Config
        from .missioncontrol_bridge import events_payload, load_project_map
        from .principals import Principal, PrincipalKind, derive_owner

        # An ambient observer is not an owner. Its single kernel capability is
        # admission of the receipt-gated journal summary invocation.
        observer_principal = Principal(
            PrincipalKind.SERVICE,
            "rails-observer",
            frozenset(
                {
                    ("rails.observer-batch", 1),
                    ("inference.invoke", 1),
                    ("inference.cancel", 1),
                }
            ),
            "rails-observer:journal-only",
        )
        seen: set[str] = set()
        primed = False
        while True:
            await asyncio.sleep(5.0)
            try:
                cfg = Config.load().rails_observer
                if not cfg.enabled:
                    continue
                principal = derive_owner(self.auth_token, self.auth_token)
                if principal is None:
                    raise RuntimeError("rails observer owner principal unavailable")
                payload = await asyncio.to_thread(
                    events_payload,
                    load_project_map(),
                    cfg.tail,
                    principal=principal,
                )
                events: list[dict] = []
                for repo in payload.get("repos", []):
                    if repo.get("status") == "live":
                        for e in repo.get("events", []) or []:
                            events.append({**e, "repo": repo.get("name", "")})
                # HS-88-04: fold in events pushed by remote nodes (live
                # ones only; a stale node's stream is dropped, never faked).
                events += rails_observer.drain_remote_events()
                fresh, seen = rails_observer.new_events(events, seen)
                if not primed:
                    # First observation is a baseline — journal only what
                    # happens AFTER the observer wakes (the HS-86-03 rule).
                    primed = True
                    continue
                if not fresh:
                    continue
                from .db import get_database
                from .kernel.runtime import _service
                # The enabled/tail controls are observer mechanics.  Its route
                # and provenance are frozen from the Rails assignment bundle;
                # never feed the retained migration-era profile pointer into a
                # recurring execution tick.
                summarizer = rails_observer.build_profile_summarizer(
                    db=get_database(),
                    broker=_service(),
                    principal=observer_principal,
                )
                batch = await asyncio.to_thread(
                    rails_observer.summarize_batch, fresh, summarize_fn=summarizer
                )
                from .db import get_database

                await asyncio.to_thread(
                    rails_observer.record_journal_entry,
                    get_database(),
                    batch,
                    title="Rails journal",
                )
                await self._ws.broadcast(
                    BroadcastMessage(
                        type="intel_status",
                        data={
                            "state": "ready",
                            "scope": "rails-journal",
                            "capability": {"kind": "rails-journal", "id": "journal", "name": "rails"},
                        },
                    )
                )
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.debug(f"rails observer loop error: {e}")
