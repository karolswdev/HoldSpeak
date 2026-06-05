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

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
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
    on_dictation_config_changed: Optional[Callable[[], None]] = None
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
        from .plugins.dictation.corrections import CorrectionStore

        self.dictation_corrections = CorrectionStore()
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
        self.on_dictation_config_changed = callbacks.on_dictation_config_changed
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
        self.auth_token = auth_token
        self._configured_port = port

        self.port: Optional[int] = None
        self._server: Optional[Any] = None
        self._thread: Optional[threading.Thread] = None
        self._started = threading.Event()

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._ws = WebSocketManager()
        self._duration_task: Optional[asyncio.Task[None]] = None

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
        return self.url

    def stop(self) -> None:
        """Stop the server gracefully."""
        if self._server is None:
            return

        log.info("Stopping meeting web server")
        self._server.should_exit = True

        if self._thread is not None:
            self._thread.join(timeout=10.0)

        self._server = None
        self._thread = None
        self._loop = None
        self._duration_task = None
        self._started.clear()

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

        # HS-25-02: token gate, enforced ONLY when bound off-loopback. Loopback
        # binds stay fully open (the long-standing "localhost is trusted" model).
        # The device-audio WebSocket keeps its own PSK handshake and is exempt;
        # /health stays open for liveness probes.
        _auth_exempt_paths = {"/health", "/api/devices/audio"}

        @app.middleware("http")
        async def _web_auth_gate(request: Request, call_next: Any) -> Any:
            if not web_auth.is_loopback_host(self.host):
                path = request.url.path
                # Static assets carry no secrets and the browser must load them
                # to even render a token prompt, so they stay open off-loopback.
                is_static = path.startswith("/_built")
                if path not in _auth_exempt_paths and not is_static:
                    token = web_auth.extract_request_token(
                        authorization=request.headers.get("authorization"),
                        header_token=request.headers.get("x-holdspeak-token"),
                        query_token=request.query_params.get("token"),
                    )
                    if not web_auth.verify_web_token(token, self.auth_token):
                        return JSONResponse(
                            {"success": False, "error": "Unauthorized"},
                            status_code=401,
                        )
            return await call_next(request)

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
        from .web.routes import (
            build_activity_router,
            build_core_router,
            build_dictation_router,
            build_meetings_router,
            build_pages_router,
            build_projects_router,
            build_system_router,
        )

        web_ctx = WebContext(
            get_state=self.get_state,
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
            on_get_intent_controls=self.on_get_intent_controls,
            on_set_intent_profile=self.on_set_intent_profile,
            on_set_intent_override=self.on_set_intent_override,
            on_route_preview=self.on_route_preview,
            on_dictation_config_changed=self.on_dictation_config_changed,
            on_process_plugin_jobs=self.on_process_plugin_jobs,
            device_registry=self.device_registry,
            project_detector=self._project_detector,
            ws=self._ws,
            on_get_status=self.on_get_status,
            on_settings_applied=self.on_settings_applied,
            current_formatted_duration=self._current_formatted_duration,
            corrections=self.dictation_corrections,
        )
        app.include_router(build_core_router(web_ctx))
        app.include_router(build_meetings_router(web_ctx))
        app.include_router(build_dictation_router(web_ctx))
        app.include_router(build_activity_router(web_ctx))
        app.include_router(build_pages_router(web_ctx))
        app.include_router(build_system_router(web_ctx))
        app.include_router(build_projects_router(web_ctx))

        @app.on_event("startup")
        async def _startup() -> None:
            self._loop = asyncio.get_running_loop()
            self._duration_task = asyncio.create_task(self._duration_loop())
            self._started.set()
            log.debug("Meeting web server startup complete")

        @app.on_event("shutdown")
        async def _shutdown() -> None:
            if self._duration_task is not None:
                self._duration_task.cancel()
                try:
                    await self._duration_task
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    log.debug(f"Duration task error during shutdown: {e}")
            await self._ws.close_all()
            log.debug("Meeting web server shutdown complete")

        # HS-10-01: serve the Astro-built design-system output. The web/
        # source builds into static/_built/; legacy hand-authored pages
        # remain at static/*.html and are served by the explicit handlers
        # below until each route's rebuild story migrates it.
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
