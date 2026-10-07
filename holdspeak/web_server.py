"""Meeting web server for HoldSpeak.

Provides a per-meeting FastAPI server with HTTP endpoints and a WebSocket for
real-time updates.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import socket
import threading
import time
from pathlib import Path
from dataclasses import dataclass
from holdspeak.timestamps import aware, local_now
from typing import Any, Callable, Optional, TYPE_CHECKING

from .logging_config import get_logger
from .web.routes._mount import mount_router
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


#: The hub's fixed default port (owner ruling 2026-10-05, "strong defaults").
#: ``holdspeak doctor`` falls back to it (doctor.DEFAULT_URL), and bookmarks
#: and MCP clients keep working across boots.  When another process holds it,
#: the hub takes a free port and records it on the owner lock, where doctor
#: and ``holdspeak-mcp`` read it (mcp.server.discover_hub).
DEFAULT_WEB_PORT = 8765


def _bind_listen_socket(host: str, preferred: int) -> socket.socket:
    """Bind ``preferred`` on ``host``; when it is busy, bind a free port.

    The hub serves on the socket bound here, so no other process can take
    the port between this check and the listener (no check-then-bind race).
    SO_REUSEADDR matches uvicorn's own bind: a port left in TIME_WAIT by the
    last hub is free; a port another listener holds is busy.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, int(preferred)))
    except OSError:
        log.info("Port %s is busy; the hub takes a free port.", preferred)
        sock.bind((host, 0))
    sock.set_inheritable(True)
    return sock


def _coder_watch_step(
    snapshot: Optional[dict[str, str]], path: Path,
) -> tuple[dict[str, str], list[str], list[str]]:
    """One read of the coder watcher (Conductor K3).

    Returns ``(snapshot, transitions, entered)``. The snapshot maps each
    session to its wait episode (``coder_steering.wait_snapshot``), so a new
    wait after an answer is a transition even when both reads saw it
    blocked. ``snapshot=None`` is the first read: no frames, and every open
    wait is ``entered`` (the notify decision reconciles it against the
    persisted notified set). An absent registry is an empty baseline.
    """
    from . import agent_context, coder_steering

    sessions = agent_context.list_agent_sessions(state_path=path) if path.exists() else []
    current = coder_steering.wait_snapshot(sessions)
    if snapshot is None:
        return current, [], [key for key, wait in current.items() if wait]
    transitions = coder_steering.awaiting_transitions(snapshot, current)
    return current, transitions, [key for key in transitions if current.get(key)]


def _coder_awaiting_edge(keys: list[str]) -> Optional[dict]:
    """Conductor K3: coder sessions began to wait for the owner.

    Marks the needs-you aggregate dirty and runs the Heartbeat's notify
    decision now (Notify mode, quiet hours and the notified item set are its
    own). The block announces itself, so the faces get one ``desk_changed``
    frame and re-read Needs you. A failure is logged and never stops the
    coder watcher.
    """
    try:
        from .db import get_database, get_observer
        from .runtime.announce_scope import announce_writes
        from .services.heartbeat_service import HeartbeatService

        db = get_database()
        with announce_writes("coder", "awaiting", keys[0] if keys else "") as name:
            for key in keys[1:]:
                name(key)
            return HeartbeatService(db, observer=get_observer()).notify_coder_edge(
                session_key=",".join(keys),
            )
    except Exception as exc:
        log.warning(f"coder awaiting edge failed: {exc}")
        return None


def _coder_answer_triage(keys: list[str]) -> list[str]:
    """Conductor K5: the waits that began, split by Control mode. Returns
    the keys to notify now; a HoldSpeak-launched agent's wait in YOLO is
    answered or escalated in the background (the responder notifies a REAL
    one itself), and in Normal a draft follows the notification. Fails
    toward notifying every key."""
    try:
        from .db import get_database
        from .services.agent_responder import default_agent_responder

        responder = default_agent_responder(get_database(), notify=_coder_awaiting_edge)
        split = responder.triage(keys)
        responder.start(split["decide"])
        return list(split["notify"])
    except Exception as exc:
        log.warning(f"coder answer triage failed: {exc}")
        return list(keys)


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
        preferred_port: Optional[int] = None,
        auth_token: str = "",
        dictation_corrections_repository: Optional[Any] = None,
        dictation_journal_repository: Optional[Any] = None,
        gh_runner: Optional[Any] = None,
        acli_runner: Optional[Any] = None,
        brief_clock: Optional[Any] = None,
    ) -> None:
        if _IMPORT_ERROR is not None:
            raise RuntimeError(
                "MeetingWebServer requires FastAPI + uvicorn. "
                "Install dependencies: `pip install fastapi uvicorn`."
            ) from _IMPORT_ERROR

        # HS-26-06: explode the bundle onto attributes so the rest of the class
        # (and `_create_app`'s WebContext build) reads `self.on_*` unchanged.
        self._callbacks = callbacks
        # HS-161-06: test-only fixture runner seam for e2e glass tests.
        # Default off; when non-None, injected into GitHubProviderAdapter
        # and WatchService snapshot_fetcher so the booted hub uses canned
        # responses instead of real subprocess calls.
        self._gh_runner = gh_runner
        self._acli_runner = acli_runner
        # PHILO-3-03: test-only producer clock for the brief (None = the wall
        # clock). The graph-walk rig's hub passes one to reach the next
        # producer-day; production never does.
        self._brief_clock = brief_clock
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

        # HS-176-02: the recorder also pushes one `dictation.journal.entry`
        # frame per stored row over the existing runtime bus. `self.broadcast`
        # resolves its event loop at call time and no-ops without one, so
        # binding it here is safe before the server starts.
        self.dictation_journal = DictationJournalRecorder(
            repository=dictation_journal_repository,
            broadcast=self.broadcast,
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
        # A port to try first when none is configured (the live hub passes
        # DEFAULT_WEB_PORT); taken when free, else a free port.  Bare servers
        # (tests) pass none and keep binding a free port.
        self._preferred_port = preferred_port
        self._listen_sockets: Optional[list[socket.socket]] = None

        self.port: Optional[int] = None
        self._server: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._started = threading.Event()
        self._startup_error: Optional[BaseException] = None
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

    def _gh_watch_service_kwargs(self) -> dict[str, Any]:
        """HS-161-06 / HS-166-03 rider-a: extra kwargs for WatchService.
        Uses default_snapshot_fetcher so gh AND jira share the same
        injection shape.  HS-166-04: pass the composed Jira adapter
        (with runner) so test/evaluate on a Jira Watch reaches the
        fixture runner, not a lazy db-only adapter."""
        from .db import get_database
        from .services.jira_provider import JiraProviderAdapter
        from .services.watch_sources import default_snapshot_fetcher
        jira = JiraProviderAdapter(
            db=get_database(), runner=self._acli_runner,
        ) if self._acli_runner else None
        fetcher = default_snapshot_fetcher(
            github_runner=self._gh_runner,
            jira_adapter=jira,
        )
        return {"snapshot_fetcher": fetcher}

    def _build_confluence_adapter(self) -> Any:
        """HS-174-07: build the Confluence adapter if acli runner is available."""
        if not self._acli_runner:
            return None
        try:
            from .db import get_database
            from .services.confluence_provider import ConfluenceProviderAdapter
            return ConfluenceProviderAdapter(
                db=get_database(), runner=self._acli_runner,
            )
        except Exception:
            return None

    @property
    def url(self) -> Optional[str]:
        if self.port is None:
            return None
        return f"http://{self.host}:{self.port}"

    def start(self) -> str:
        """Start the server in a background thread and return its URL."""
        if self._thread is not None and self._thread.is_alive():
            if self._server is None or not getattr(self._server, "started", False):
                raise RuntimeError("Web server startup is already in progress")
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

        self._listen_sockets = None
        if self._configured_port:
            self.port = self._configured_port
        elif self._preferred_port:
            listen = _bind_listen_socket(self.host, self._preferred_port)
            self._listen_sockets = [listen]
            self.port = int(listen.getsockname()[1])
        else:
            self.port = _find_free_port(self.host)
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
        self._startup_error = None
        self._started.clear()

        self._thread = threading.Thread(
            target=self._run_server,
            name=f"MeetingWebServer:{self.port}",
            daemon=True,
        )
        self._thread.start()

        # The lifespan handler sets ``_started`` before Uvicorn creates its
        # listening socket. Keep one deadline for both phases: callers must
        # never receive a URL that can immediately refuse a connection.
        deadline = time.monotonic() + 5.0
        while True:
            running_server = self._server
            startup_error = self._startup_error
            if startup_error is not None:
                self._fail_startup("Web server failed during startup", startup_error)
            if running_server is None:
                self._fail_startup("Web server failed during startup")
            if getattr(running_server, "started", False):
                break
            if getattr(running_server, "should_exit", False):
                self._fail_startup("Web server exited during startup")
            if self._thread is None or not self._thread.is_alive():
                self._fail_startup("Web server stopped during startup")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                phase = "listener" if self._started.is_set() else "startup"
                self._fail_startup(f"Timed out waiting for web server {phase}")
            time.sleep(min(0.01, remaining))

        if self.url is None:
            raise RuntimeError("Server started but URL is unknown")

        log.info(f"Meeting web server started: {self.url}")

        # HSM-15-10: advertise on the LAN once bound (off-loopback only). Wholly
        # best-effort — a failure here logs a warning and never affects the
        # already-running server.
        self._start_mesh_advertising()

        return self.url

    def _fail_startup(
        self, message: str, cause: Optional[BaseException] = None
    ) -> None:
        """Stop a failed startup and raise without publishing a dead URL."""
        server = self._server
        thread = self._thread
        if server is not None:
            server.should_exit = True
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        if thread is None or not thread.is_alive():
            self._server = None
            self._thread = None
            self._loop = None
            self.port = None
            for sock in self._listen_sockets or ():
                try:
                    sock.close()
                except OSError:
                    pass
            self._listen_sockets = None
        self._started.clear()
        if cause is not None:
            raise RuntimeError(message) from cause
        raise RuntimeError(message)

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

    def _conductor_start_meeting(
        self, principal, title, calendar_event_id=None
    ):
        """The scheduled-recording fire → the SAME start contract the routes
        use (HS-151-06; see the wiring comment at the conductor startup).

        The pending title/calendar seam (HS-147-04) lives on the RUNTIME
        (web_runtime.py:176-177), reachable as the bound ``on_start``
        method's owner. A harness callbacks bundle without ``on_start``
        lawfully no-ops — never raises.
        """
        on_start = getattr(self._callbacks, "on_start", None)
        if not callable(on_start):
            return None
        owner = getattr(on_start, "__self__", None)
        if owner is not None and hasattr(owner, "pending_title"):
            owner.pending_title = title
            owner.pending_calendar_event_id = calendar_event_id or None
        try:
            return on_start(principal=principal)
        except TypeError:
            # The contract's minimal shape is zero-arg (WebRuntimeCallbacks
            # declares Callable[[], Any]); mirror the routes' fallback.
            return on_start()

    def _memory_live_check(self) -> str:
        """For the memory conductor: a reason to wait while a meeting
        records, else "".  The meeting session lives on the runtime, the
        owner of the bound ``on_start`` (as in ``_conductor_start_meeting``)."""
        owner = getattr(getattr(self._callbacks, "on_start", None), "__self__", None)
        active = getattr(owner, "_active_meeting_session", None)
        if callable(active) and active() is not None:
            return "a meeting is recording"
        return ""

    def _conductor_stop_meeting(self):
        """Deadline auto-stop → ``on_meeting_stop`` (the fallback-free stop,
        meeting_glue.py:509-510). Missing on a harness bundle → no-op."""
        on_meeting_stop = getattr(self._callbacks, "on_meeting_stop", None)
        if not callable(on_meeting_stop):
            return None
        return on_meeting_stop()

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
            if self._listen_sockets:
                self._server.run(sockets=self._listen_sockets)
            else:
                self._server.run()
        except BaseException as e:
            self._startup_error = e
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

        async def _launch_cut_response(response: Any) -> Any:
            import json as _json

            from starlette.responses import Response as _Response

            from .services.conductor_launch import cut_value

            body = b"".join([chunk async for chunk in response.body_iterator])
            headers = {k: v for k, v in response.headers.items() if k.lower() != "content-length"}
            media = str(response.headers.get("content-type") or "")
            if body and "json" in media:
                try:
                    body = _json.dumps(cut_value(_json.loads(body)), default=str).encode()
                except ValueError:
                    body = str(cut_value(body.decode("utf-8", "replace")) or "").encode()
            elif body and media.startswith("text/"):
                body = str(cut_value(body.decode("utf-8", "replace")) or "").encode()
            return _Response(content=body, status_code=response.status_code, headers=headers,
                             media_type=response.media_type)

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
            response = await call_next(request)
            from .services.conductor_launch import launch_id_of

            if launch_id_of(principal) is None:
                return response
            # Conductor K6 (Astra round 2 on #903): EVERY HTTP answer a
            # launched agent receives passes the People cut, in one place.
            return await _launch_cut_response(response)

        # Every HTTP write sends one desk_changed frame (the root for routes
        # that do not go through OperationRegistry.invoke).
        from .web import announce as _announce

        _announce.install(app)

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
        from .services.door_service import DoorService
        from .services.refinement_thought_service import RefinementThoughtService
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
        from .services.connections_service import ConnectionsService
        from .db import get_database, get_observer
        from .web.routes import (
            build_activity_router,
            build_automations_router,
            build_authority_router,
            build_cadence_router,
            build_calendar_events_router,
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
            build_front_door_router,
            build_follow_through_router,
            build_proposal_router,
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

        from .services.meeting_aftercare_service import MeetingAftercareService
        from .services.meeting_intel_service import MeetingIntelService
        from .services.meeting_service import MeetingService
        from .services.people_service import PeopleService, UnavailablePeopleStore
        from .people import production_people_store
        from .services.reaction_service import ReactionService
        from .services.watch_service import WatchService
        from .services.github_provider import GitHubProviderAdapter
        from .services.jira_provider import JiraProviderAdapter
        from .services.project_door_service import ProjectDoorService
        from .services.project_setup_service import ProjectSetupService
        from .services.project_evidence_collector import ProjectEvidenceCollector
        from .services.project_delta_service import ProjectDeltaService
        from .services.project_update_service import ProjectUpdateService
        from .services.preparation_brief_service import PreparationBriefService
        from .services.project_steward_service import ProjectStewardService
        from .services.refinement_coordinator import RefinementCoordinator
        from .services.refinement_application_service import RefinementApplicationService

        from .delivery.node_link import NodeTokenStore as _MeshNodeTokenStore

        def _mesh_token_store() -> Any:
            return _MeshNodeTokenStore(None)

        obs = get_observer()
        # HS-200-45 R4: the services the hub holds that write BELOW the two
        # primitive services (reaction projections, coder-materialized notes)
        # get the same desk_changed callback. Late-bound through the root the
        # block below installs.
        from .runtime.composition import notify_desk_changed as _composition_notify
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
        # Meaning search: the one step that gets the local embedding model,
        # assigns it to ``memory.embed`` and wakes the memory conductor.
        from .services.meaning_search_service import MeaningSearchService

        memory_service = MemoryService(get_database(), observer=obs)
        memory_service.meaning = MeaningSearchService(
            get_database(),
            assignment_service=inference_assignment_service,
            broker_provider=lambda: broker,
        )
        # Owner ruling 2026-10-05: a LOCAL engine becomes "Default for AI
        # work" by itself; a network or cloud engine waits for the owner.
        from .services.inference_default_service import InferenceDefaultService

        inference_default_service = InferenceDefaultService(
            get_database(),
            assignment_service=inference_assignment_service,
            model_library_service=model_library_service,
            meaning_search=memory_service.meaning,
        )
        # "Set up local AI": only an explicit owner call starts its download.
        from .services.local_ai_setup_service import LocalAISetupService

        local_ai_setup_service = LocalAISetupService(
            get_database(),
            meaning_search=memory_service.meaning,
            broker_provider=lambda: broker,
        )
        # HS-160-05: extract the delta service so the project_service can
        # use it for the room() review section (mutual composition).
        _project_delta_service = ProjectDeltaService(
            get_database(),
            collector=ProjectEvidenceCollector(get_database()),
        )
        web_ctx = WebContext(
            get_state=self.get_state,
            meeting_service=meeting_service,
            meeting_service_factory=lambda: MeetingService(get_database(), observer=obs),
            meeting_intel_service=meeting_intel_service,
            # PHILO-5-02 (gap C): no summary factory. The HTTP summary routes
            # and MCP reach the ONE instance above; a factory beside it made a
            # second, so the two transports never shared object identity.
            meeting_aftercare_service=meeting_aftercare_service,
            meeting_aftercare_service_factory=lambda: MeetingAftercareService(get_database(), notify=notify, observer=obs),
            brief_clock=self._brief_clock,
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
            project_service=(_project_service := ProjectService(
                get_database(), observer=obs,
                delta_service=_project_delta_service,
            )),
            projection_service=ProjectionService(get_database(), observer=obs),
            authority_service=AuthorityService(get_database(), observer=obs),
            credential_service=CredentialService(
                get_database(), on_settings_applied=self.on_settings_applied, observer=obs
            ),
            cadence_service=CadenceService(get_database(), Config.load().cadence, observer=obs),
            follow_through_service=follow_through_service,
            door_service=door_service,
            people_service=people_service,
            sync_service=SyncService(get_database(), observer=obs),
            gate_service=GateService(get_database(), observer=obs),
            setup_service=SetupService(get_database(), observer=obs),
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
                on_changed=lambda kind, obj_id, op: _composition_notify(kind, obj_id, op),
            ),
            watch_service=WatchService(
                get_database(), observer=obs,
                **self._gh_watch_service_kwargs(),
            ),
            github_provider=GitHubProviderAdapter(
                db=get_database(), runner=self._gh_runner,
            ),
            jira_provider=JiraProviderAdapter(
                db=get_database(), runner=self._acli_runner,
            ),
            # HS-174-07 declared this field "construction only here" and then
            # never constructed it; the MCP `provider.confluence.*` family
            # built a bare adapter in the hub as a result. Same shape as the
            # Jira adapter above (counsel P1-3, caught by the asked-names fence).
            confluence_provider=(
                self._build_confluence_adapter()
                or __import__(
                    "holdspeak.services.confluence_provider", fromlist=["ConfluenceProviderAdapter"]
                ).ConfluenceProviderAdapter(db=get_database(), runner=self._acli_runner)
            ),
            connections_service=ConnectionsService(
                github_adapter=GitHubProviderAdapter(
                    db=get_database(), runner=self._gh_runner,
                ),
                jira_adapter=JiraProviderAdapter(
                    db=get_database(), runner=self._acli_runner,
                ),
                # PHILO-9-02 (B1): the Confluence row and its real Recheck
                # probe need the adapter; the bare builder returns None
                # unless a test injects a runner, so fall back as :1004 does.
                confluence_adapter=(
                    self._build_confluence_adapter()
                    or __import__(
                        "holdspeak.services.confluence_provider", fromlist=["ConfluenceProviderAdapter"]
                    ).ConfluenceProviderAdapter(db=get_database(), runner=self._acli_runner)
                ),
                config_loader=Config.load,
                inference_assignment_service=inference_assignment_service,
            ),
            project_setup_service=ProjectSetupService(
                get_database(),
                project_service=ProjectService(get_database(), observer=obs),
                watch_service=WatchService(
                    get_database(), observer=obs,
                    **self._gh_watch_service_kwargs(),
                ),
                github_adapter=GitHubProviderAdapter(
                    db=get_database(), runner=self._gh_runner,
                ),
                jira_adapter=JiraProviderAdapter(
                    db=get_database(), runner=self._acli_runner,
                ),
                connections_service=ConnectionsService(
                    github_adapter=GitHubProviderAdapter(
                        db=get_database(), runner=self._gh_runner,
                    ),
                    jira_adapter=JiraProviderAdapter(
                        db=get_database(), runner=self._acli_runner,
                    ),
                    config_loader=Config.load,
                    inference_assignment_service=inference_assignment_service,
                ),
            ),
            project_door_service=ProjectDoorService(
                project_service=ProjectService(get_database(), observer=obs),
                watch_service=WatchService(
                    get_database(), observer=obs,
                    **self._gh_watch_service_kwargs(),
                ),
                gh_runner=self._gh_runner,
                jira_adapter=JiraProviderAdapter(
                    db=get_database(), runner=self._acli_runner,
                ),
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
                get_database(), on_settings_applied=self.on_settings_applied, observer=obs
            ),
            profile_key_service=ProfileKeyService(get_database()),
            on_get_intent_controls=self.on_get_intent_controls,
            on_set_intent_profile=self.on_set_intent_profile,
            on_set_intent_override=self.on_set_intent_override,
            on_route_preview=self.on_route_preview,
            on_dictation_config_changed=self.on_dictation_config_changed,
            on_remote_dictation=self.on_remote_dictation,
            coder_service=CoderService(
                get_database(), observer=obs,
                on_changed=lambda kind, obj_id, op: _composition_notify(kind, obj_id, op),
            ),
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
        # HS-166-05: wire the project_service into the delta service
        # (mutual composition: delta needs project for create_item in
        # decide_proposal, project needs delta for room review section).
        _project_delta_service.attach_project_service(_project_service)
        # Owner ruling 2026-10-05: the onboarding backends compose the
        # settings and connections services above (detect + "Use it").
        from .services.onboarding_service import OnboardingService

        web_ctx.onboarding_service = OnboardingService(
            settings_service=web_ctx.settings_service,
            connections_service=web_ctx.connections_service,
            jira_provider=web_ctx.jira_provider,
            confluence_provider=web_ctx.confluence_provider,
        )

        # HS-200-45 R1/R4: ONE composition root. The desk-primitive services are
        # composed HERE, once, with the ``on_changed`` hook bound to the bus --
        # and then installed so every caller (the primitive HTTP routes, MCP
        # over /api/mcp, MCP over stdio proxied to this hub) writes through the
        # same instance. Before this, MCP dispatch and each HTTP route built
        # their own bare copy, so a write from anywhere but the acting browser
        # reached no open desk.
        from .runtime import composition as _composition

        _runtime_services = _composition.install_from_web_context(
            web_ctx, db=get_database(), observer=obs
        )

        # Conductor R2: the hub's agent credentials, their targets and launch
        # ownership survive a restart. After the composition is installed:
        # the revoke hook first (a credential that expired while the hub was
        # down ends its grants on load), then the reload, then every LIVE
        # launch grant left with no live credential is ended.
        from .services.conductor_launch import install_revoke_hook, reconcile_launch_grants

        install_revoke_hook()
        agent_credentials.attach(get_database(), follow_hub=True)
        try:
            reconcile_launch_grants(get_database())
        except Exception:  # a start never fails on the sweep; it runs again next start
            log.warning("launch grant reconcile failed", exc_info=True)

        from .web.routes.actuator_shared import DeskActuatorLifecycle
        web_ctx.actuator_service = ActuatorProposalService(
            get_database(), config_provider=lambda: Config.load(path=__import__("holdspeak.config", fromlist=["CONFIG_FILE"]).CONFIG_FILE),
            broadcast=lambda message_type, data: self.broadcast(message_type, data),
            lifecycle=DeskActuatorLifecycle(web_ctx, get_database()),
        )
        _runtime_services.actuator_service = web_ctx.actuator_service
        mount_router(app, build_core_router(web_ctx))
        mount_router(app, build_authority_router(web_ctx))
        mount_router(app, build_cadence_router(web_ctx))
        mount_router(app, build_calendar_events_router(web_ctx))
        mount_router(app, build_calendar_snapshot_router(web_ctx))
        mount_router(app, build_calendar_sources_router(web_ctx))
        mount_router(app, build_follow_through_router(web_ctx))
        mount_router(app, build_proposal_router(web_ctx))
        mount_router(app, build_door_router(web_ctx))
        mount_router(app, build_concierge_router(web_ctx))
        mount_router(app, build_front_door_router(web_ctx))
        mount_router(app, build_people_router(web_ctx))
        mount_router(app, build_automations_router(web_ctx))
        mount_router(app, build_decision_records_router(web_ctx))
        mount_router(app, build_decisions_router(web_ctx))
        mount_router(app, build_memory_router(web_ctx))
        mount_router(app, build_model_library_router(web_ctx))
        mount_router(app, build_inference_assignments_router(web_ctx))
        mount_router(app, build_monday_brief_router(web_ctx))
        mount_router(app, build_meetings_router(web_ctx))
        mount_router(app, build_desk_actuators_router(web_ctx))
        mount_router(app, build_desk_seed_router(web_ctx))
        mount_router(app, build_meeting_import_router(web_ctx))
        mount_router(app, build_mesh_router(web_ctx))
        mount_router(app, build_missioncontrol_router(web_ctx))
        mount_router(app, build_delivery_router(web_ctx))
        mount_router(app, build_delivery_attempts_router(web_ctx))
        mount_router(app, build_delivery_dossiers_router(web_ctx))
        mount_router(app, build_delivery_prs_router(web_ctx))
        from .web.routes.agent_hand import build_agent_hand_router

        mount_router(app, build_agent_hand_router(web_ctx))  # Conductor K2: Hand to agent
        mount_router(app, build_repositories_router(web_ctx))
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
        mount_router(app, 
            build_delivery_node_router(
                web_ctx, link=_delivery_link, web_token=self.auth_token
            )
        )
        mount_router(app, 
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
        mount_router(app, 
            build_delivery_factory_router(
                web_ctx, commands=_delivery_cmd, targets=_delivery_targets
            )
        )
        mount_router(app, build_dictation_router(web_ctx))
        mount_router(app, build_activity_router(web_ctx))
        mount_router(app, build_pages_router(web_ctx))
        mount_router(app, 
            build_system_router(
                web_ctx, commands=_delivery_cmd, targets=_delivery_targets
            )
        )
        mount_router(app, build_projects_router(web_ctx))
        mount_router(app, build_roadmaps_router(web_ctx))
        mount_router(app, build_primitives_router(web_ctx))
        mount_router(app, build_projections_router(web_ctx))
        mount_router(app, build_constitutional_router())
        mount_router(app, build_scheduled_recordings_router(web_ctx))
        mount_router(app, build_setup_router(web_ctx))
        from .web.routes.onboarding import build_onboarding_router

        mount_router(app, build_onboarding_router(web_ctx))
        mount_router(app, build_sync_router(web_ctx))
        mount_router(app, build_threads_router(web_ctx))
        mount_router(app, build_tts_router(web_ctx))
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
            # PHILO-7-02 (T6): a desk write left admitting/awaiting_decision by a
            # dead process ends indeterminate with its receipt (never resumed).
            try:
                from .kernel.desk_broker import recover_on_startup as recover_desk_on_startup

                recovered_desk = recover_desk_on_startup(_kernel_service())
                if recovered_desk:
                    log.info(f"desk: {recovered_desk} interrupted desk write(s) ended indeterminate")
            except Exception as e:
                log.error(f"desk startup recovery failed: {e}")
            self._loop = asyncio.get_running_loop()
            # MCP tool bodies run their coroutines on this loop (mcp/aio.py).
            from .mcp import aio as _mcp_aio

            _mcp_aio.set_hub_loop(self._loop)
            self._duration_task = asyncio.create_task(self._duration_loop())
            self._coder_frames_task = asyncio.create_task(self._coder_frames_loop())
            self._rails_observer_task = asyncio.create_task(self._rails_observer_loop())
            await asyncio.to_thread(_kernel_service().reap_and_recover_projections)
            try:
                await refinement_coordinator.start()
            except Exception as e:
                log.error(f"refinement coordinator startup recovery failed: {e}")
            # HS-200-41: settle asks whose dispatching process is gone. After
            # the coordinator starts, so that a lease a live refinement_hosts
            # row still backs reads as work in flight and never as
            # abandonment. Reconcile from proof only — this dispatches nothing.
            try:
                lost = await asyncio.to_thread(
                    _project_service.recover_ask_tasks_on_startup
                )
                if lost:
                    log.info(f"Settled {len(lost)} unfinished ask(s) whose host was lost")
            except Exception as e:
                log.error(f"ask task startup recovery failed: {e}")
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
            # HS-163-02 STW-009 + PHILO-9-02 (the steward beat, section 3):
            # settle abandoned steward work on the hub's COMPOSED service,
            # before the conductor starts: every Room operation left
            # non-terminal ends indeterminate with its receipt (children
            # first) and its run row interrupted in the same transaction; a
            # legacy run with no operation is interrupted as before.
            try:
                recovered = web_ctx.project_steward_service.recover_admitted_on_startup()
                if any(recovered.values()):
                    log.info(f"Steward recovery: {recovered}")
            except Exception as e:
                log.error(f"steward startup recovery failed: {e}")
            try:
                from .workbench_conductor import (
                    start_conductor,
                    set_broadcast,
                    set_scheduler_services,
                )
                set_broadcast(lambda t, d: self.broadcast(t, d))
                set_scheduler_services(
                    web_ctx.watch_service,
                    web_ctx.project_steward_service,
                )
                start_conductor()
            except Exception as e:
                log.error(f"workbench conductor startup failed: {e}")
            try:
                from .scheduled_recording_conductor import (
                    start_scheduled_recording_conductor,
                    set_broadcast as sr_set_broadcast,
                )
                sr_set_broadcast(lambda t, d: self.broadcast(t, d))
                # HS-151-06 (the attended leg's catch): this wiring was born
                # broken in HS-136-01 and no production fire ever succeeded —
                # the lambdas referenced an out-of-scope `callbacks` name AND
                # probed runtime-private method names (`_start_meeting`) that
                # the WebRuntimeCallbacks contract never carries; the
                # `if hasattr(...)` guards parsed INSIDE the lambda bodies
                # (conditional-expression precedence), so boot never raised
                # and every fire died or silently no-opped. Every prior walk
                # wired its own harness callbacks and never exercised this
                # path. The conductor now speaks the SAME contract the routes
                # do: `on_start(principal=...)` with the pending-title/
                # calendar seam set on the bound method's owner (the
                # runtime), and `on_meeting_stop()` which IS the
                # fallback-free stop (meeting_glue.py:509-510).
                start_scheduled_recording_conductor(
                    voice_floor_fn=lambda: self.voice_session.active_owner
                    if hasattr(self, "voice_session")
                    else None,
                    start_meeting_fn=self._conductor_start_meeting,
                    stop_meeting_fn=self._conductor_stop_meeting,
                )
            except Exception as e:
                log.error(f"scheduled recording conductor startup failed: {e}")
            try:
                from .calendar_ingest_conductor import start_calendar_ingest_conductor

                start_calendar_ingest_conductor()
            except Exception as e:
                log.error(f"calendar ingest conductor startup failed: {e}")
            # HS-200-42: the fourth conductor. Until this line nothing in the
            # running product drained `intel_jobs` (audit 2026-09-13 §3.1):
            # a stopped meeting enqueued a row and it sat there. It refuses
            # to start when this process does not own the database, so the
            # HOLDSPEAK_ALLOW_UNOWNED_DB hub keeps its "scheduled work OFF"
            # promise.
            try:
                from .intel_queue_conductor import start_intel_queue_conductor

                start_intel_queue_conductor(
                    broadcast=lambda t, d: self.broadcast(t, d)
                )
            except Exception as e:
                log.error(f"intel queue conductor startup failed: {e}")
            # The memory conductor (MEMORY-DESIGN.md §3): sweeps the source
            # tables into the chunk index and embeds through memory.embed.
            try:
                from .memory_conductor import set_live_check, start_memory_conductor

                # Extraction yields to a live meeting (MEMORY-DESIGN.md §9).
                set_live_check(self._memory_live_check)
                start_memory_conductor()
            except Exception as e:
                log.error(f"memory conductor startup failed: {e}")
            # Owner ruling 2026-10-05 ("strong defaults, batteries included"):
            # a LOCAL engine becomes "Default for AI work" by itself; network
            # and cloud engines become proposals.  Background thread: the
            # loopback scan never delays the listener.  Only the hub that owns
            # the database writes a default.
            try:
                from .intel_queue_conductor import owns_database

                if web_ctx.inference_default_service is not None and owns_database():
                    web_ctx.inference_default_service.kick("boot")
            except Exception as e:
                log.error(f"batteries default startup failed: {e}")
            # The defaults watcher: an engine started after boot is found by a
            # light loopback re-scan, and the meetings saved before any
            # engine existed are summarised once one does.  Owner-only.
            try:
                from .defaults_conductor import start_defaults_conductor

                start_defaults_conductor(
                    defaults_service=web_ctx.inference_default_service,
                )
            except Exception as e:
                log.error(f"defaults watcher startup failed: {e}")
            self._started.set()
            log.debug("Meeting web server startup complete")

        @app.on_event("shutdown")
        async def _shutdown() -> None:
            # HS-200-03: EVERY conductor this lifespan started is stopped here.
            # Only the calendar one was, so the workbench and scheduled-recording
            # conductors (started at the two `startup` sites above) outlived the
            # app that started them: on an in-process restart they kept ticking
            # against a database nobody owned any more, and in a test process
            # they survived every subsequent app and called `get_database()` on
            # a 60-second timer for the rest of the run. That is the thread whose
            # tick produced the CI-only web-activity failures.
            for name, stop in (
                ("calendar ingest", "calendar_ingest_conductor.stop_calendar_ingest_conductor"),
                ("workbench", "workbench_conductor.stop_conductor"),
                ("scheduled recording", "scheduled_recording_conductor.stop_scheduled_recording_conductor"),
                ("intel queue", "intel_queue_conductor.stop_intel_queue_conductor"),
                ("memory", "memory_conductor.stop_memory_conductor"),
                ("defaults", "defaults_conductor.stop_defaults_conductor"),
            ):
                module_name, _, attribute = stop.partition(".")
                try:
                    import importlib

                    module = importlib.import_module(f".{module_name}", __package__)
                    getattr(module, attribute)()
                except Exception as e:
                    log.error(f"{name} conductor shutdown failed: {e}")
            from .mcp import aio as _mcp_aio

            _mcp_aio.set_hub_loop(None)
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
        end = aware(ended_at) if ended_at else local_now()
        return _format_duration((end - aware(started_at)).total_seconds())

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
        blocked-state transition, so closed surfaces stay current without
        polling. The registry file's mtime gates the read (a stat every 2 s,
        the JSON only when the hooks actually wrote).

        Conductor K3: the first observation reconciles instead of being
        dropped. An absent registry is an EMPTY baseline (the first agent to
        block is a transition); waits already open at start run the notify
        decision, and the Heartbeat's persisted notified set keeps a wait it
        already notified silent after a restart."""
        from . import agent_context

        unseen = object()
        last_mtime: Any = unseen
        snapshot: Optional[dict[str, str]] = None
        while True:
            try:
                path = agent_context.AGENT_CONTEXT_FILE
                mtime = path.stat().st_mtime if path.exists() else None
                if mtime != last_mtime:
                    last_mtime = mtime
                    snapshot, transitions, entered = await asyncio.to_thread(
                        _coder_watch_step, snapshot, path,
                    )
                    for key in transitions:
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
                    if entered:
                        # After the frames: the decision builds the full
                        # needs-you answer, and the frames must not wait on it.
                        # Conductor K5: a launched agent's wait may be
                        # answered by Control mode first (never blocks here).
                        notify_now = await asyncio.to_thread(_coder_answer_triage, entered)
                        if notify_now:
                            await asyncio.to_thread(_coder_awaiting_edge, notify_now)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                log.debug(f"coder frames loop error: {e}")
            await asyncio.sleep(2.0)

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
