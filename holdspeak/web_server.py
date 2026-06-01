"""Meeting web server for HoldSpeak.

Provides a per-meeting FastAPI server with HTTP endpoints and a WebSocket for
real-time updates.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import re
import socket
import threading
from copy import deepcopy
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional, TYPE_CHECKING
from urllib.parse import urlparse

from .logging_config import get_logger

if TYPE_CHECKING:
    import numpy as np

    from .audio import AudioSource
    from .device_audio import DeviceRegistry
    from .device_status import DeviceStatusEmitter

log = get_logger("web_server")
_HTTP_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")

_DASHBOARD_HTML_PATH = (
    Path(__file__).resolve().parent / "static" / "_built" / "index.html"
)

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


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _meeting_active_from_state(state: dict[str, Any]) -> bool:
    if isinstance(state.get("meeting_active"), bool):
        return bool(state.get("meeting_active"))
    return bool(state.get("started_at")) and not bool(state.get("ended_at"))


def _meeting_summary_from_state(state: dict[str, Any]) -> Optional[dict[str, Any]]:
    if not _meeting_active_from_state(state):
        return None
    meeting_id = state.get("id")
    if not meeting_id:
        return None
    return {
        "id": meeting_id,
        "title": state.get("title"),
        "tags": state.get("tags") if isinstance(state.get("tags"), list) else [],
        "started_at": state.get("started_at"),
        "ended_at": state.get("ended_at"),
        "duration": state.get("duration"),
        "formatted_duration": state.get("formatted_duration"),
    }


def _normalize_runtime_status_payload(raw_payload: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    payload = dict(raw_payload)
    payload_state = payload.get("state")
    if not isinstance(payload_state, dict):
        payload_state = state
    meeting_active = (
        bool(payload.get("meeting_active"))
        if isinstance(payload.get("meeting_active"), bool)
        else _meeting_active_from_state(payload_state)
    )
    payload["status"] = payload.get("status") or "ok"
    payload["mode"] = payload.get("mode") or "web"
    payload["meeting_active"] = meeting_active
    payload["state"] = payload_state
    if "meeting_id" not in payload:
        payload["meeting_id"] = payload_state.get("id") if meeting_active else None
    if "meeting" not in payload:
        payload["meeting"] = _meeting_summary_from_state(payload_state)
    return payload


@dataclass(frozen=True)
class BroadcastMessage:
    type: str
    data: Any

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "data": self.data}


class _UnknownDeviceError(LookupError):
    """Raised by ``on_start`` when a requested device id is not registered.

    The route maps this to a 404 with the offending ``device_id``
    surfaced in the JSON body so the caller can correct its
    request without polling the registry.
    """

    def __init__(self, device_id: str) -> None:
        super().__init__(f"Unknown device id: {device_id!r}")
        self.device_id = device_id


def _meeting_callback_payload(result: Any) -> Any:
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except Exception:
            return None
    if isinstance(result, dict):
        return result
    return None


def _validate_cloud_base_url(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("intel_cloud_base_url must start with http:// or https://")
    return raw


def _merge_dict(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(dst.get(key), dict):
            _merge_dict(dst[key], value)
        else:
            dst[key] = value
    return dst


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


class MeetingWebServer:
    """FastAPI-based web dashboard server for a meeting."""

    def __init__(
        self,
        *,
        on_bookmark: Callable[[str], Any],
        on_stop: Callable[[], Any],
        get_state: Callable[[], dict[str, Any]],
        on_start: Optional[Callable[[], Any]] = None,
        on_meeting_stop: Optional[Callable[[], Any]] = None,
        on_get_status: Optional[Callable[[], Any]] = None,
        on_update_meeting: Optional[Callable[..., Any]] = None,
        on_get_intent_controls: Optional[Callable[[], Any]] = None,
        on_set_intent_profile: Optional[Callable[[str], Any]] = None,
        on_set_intent_override: Optional[Callable[[Optional[list[str]]], Any]] = None,
        on_route_preview: Optional[Callable[..., Any]] = None,
        on_process_plugin_jobs: Optional[Callable[..., Any]] = None,
        on_update_action_item: Optional[Callable[[str, str], Any]] = None,
        on_update_action_item_review: Optional[Callable[[str, str], Any]] = None,
        on_edit_action_item: Optional[Callable[..., Any]] = None,
        on_set_title: Optional[Callable[[str], None]] = None,
        on_set_tags: Optional[Callable[[list[str]], None]] = None,
        on_settings_applied: Optional[Callable[[Any], None]] = None,
        on_dictation_config_changed: Optional[Callable[[], None]] = None,
        project_detector: Optional[Any] = None,
        device_registry: Optional["DeviceRegistry"] = None,
        device_psk_provider: Optional[Callable[[], str]] = None,
        on_device_audio_chunk: Optional[Callable[[str, "np.ndarray"], None]] = None,
        on_device_voice_start: Optional[Callable[[str, "AudioSource"], bool]] = None,
        on_device_voice_stop: Optional[
            Callable[[str, "AudioSource"], Optional["np.ndarray"]]
        ] = None,
        on_device_voice_cancel: Optional[Callable[[str], None]] = None,
        device_status_emitter: Optional["DeviceStatusEmitter"] = None,
        on_device_event: Optional[Callable[[str, str, Optional[float]], None]] = None,
        on_device_health: Optional[Callable[[Any], None]] = None,
        on_device_query: Optional[Callable[[str, str, Optional[float]], Optional[dict[str, Any]]]] = None,
        host: str = "127.0.0.1",
        port: Optional[int] = None,
        auth_token: str = "",
    ) -> None:
        if _IMPORT_ERROR is not None:
            raise RuntimeError(
                "MeetingWebServer requires FastAPI + uvicorn. "
                "Install dependencies: `pip install fastapi uvicorn`."
            ) from _IMPORT_ERROR

        self.on_bookmark = on_bookmark
        self.on_stop = on_stop
        self.on_meeting_stop = on_meeting_stop
        self.get_state = get_state
        self.on_start = on_start
        self.on_get_status = on_get_status
        self.on_update_meeting = on_update_meeting
        self.on_get_intent_controls = on_get_intent_controls
        self.on_set_intent_profile = on_set_intent_profile
        self.on_set_intent_override = on_set_intent_override
        self.on_route_preview = on_route_preview
        self.on_process_plugin_jobs = on_process_plugin_jobs
        self.on_update_action_item = on_update_action_item
        self.on_update_action_item_review = on_update_action_item_review
        self.on_edit_action_item = on_edit_action_item
        self.on_set_title = on_set_title
        self.on_set_tags = on_set_tags
        self.on_settings_applied = on_settings_applied
        self.on_dictation_config_changed = on_dictation_config_changed
        self._project_detector = project_detector
        if device_registry is None:
            from .device_audio import DeviceRegistry as _DeviceRegistry
            device_registry = _DeviceRegistry()
        self.device_registry: "DeviceRegistry" = device_registry
        if device_psk_provider is None:
            from .config import Config as _Config
            from .device_audio import ensure_device_psk as _ensure_device_psk

            def _default_psk_provider() -> str:
                return _ensure_device_psk(_Config.load())

            device_psk_provider = _default_psk_provider
        self.device_psk_provider: Callable[[], str] = device_psk_provider
        self.on_device_audio_chunk: Optional[Callable[[str, "np.ndarray"], None]] = (
            on_device_audio_chunk
        )
        self.on_device_voice_start: Optional[
            Callable[[str, "AudioSource"], bool]
        ] = on_device_voice_start
        self.on_device_voice_stop: Optional[
            Callable[[str, "AudioSource"], Optional["np.ndarray"]]
        ] = on_device_voice_stop
        self.on_device_voice_cancel: Optional[Callable[[str], None]] = on_device_voice_cancel
        if device_status_emitter is None:
            from .device_status import DeviceStatusEmitter as _DeviceStatusEmitter
            device_status_emitter = _DeviceStatusEmitter(label_lookup=device_registry)
        self.device_status_emitter: "DeviceStatusEmitter" = device_status_emitter
        self.on_device_event: Optional[Callable[[str, str, Optional[float]], None]] = (
            on_device_event
        )
        self.on_device_health = on_device_health
        self.on_device_query = on_device_query
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
        # closing over `self`. HS-26-01 piloted /health + /api/state; HS-26-02
        # added meeting / speaker / intel; HS-26-03 dictation / agent-hook /
        # intent; HS-26-04 activity / connector / plugin-job.
        from .web.context import WebContext
        from .web.routes import (
            build_activity_router,
            build_core_router,
            build_dictation_router,
            build_meetings_router,
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
        )
        app.include_router(build_core_router(web_ctx))
        app.include_router(build_meetings_router(web_ctx))
        app.include_router(build_dictation_router(web_ctx))
        app.include_router(build_activity_router(web_ctx))

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

        @app.get("/")
        async def dashboard() -> Any:
            try:
                html = _DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read runtime index: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8' />"
                    "<title>HoldSpeak</title></head>"
                    "<body><h1>HoldSpeak Runtime</h1>"
                    "<p>Runtime UI missing — run "
                    "<code>cd web && npm run build</code>.</p>"
                    "</body></html>"
                )
            return HTMLResponse(html)

        @app.get("/api/devices/health")
        async def api_devices_health() -> Any:
            from .meeting_session import _device_descriptor_to_dict

            devices = [
                _device_descriptor_to_dict(descriptor)
                for descriptor in self.device_registry.active()
            ]
            return JSONResponse({"devices": devices})

        @app.get("/api/runtime/status")
        async def api_runtime_status() -> Any:
            try:
                state = self.get_state() or {}
            except Exception as e:
                log.error(f"get_state failed: {e}")
                state = {}

            if self.on_get_status is not None:
                try:
                    raw_payload = self.on_get_status()
                except Exception as e:
                    log.error(f"on_get_status failed: {e}")
                    return JSONResponse({"success": False, "error": str(e)}, status_code=500)
                if isinstance(raw_payload, dict):
                    return JSONResponse(_normalize_runtime_status_payload(raw_payload, state))
                return JSONResponse({"status": "ok", "runtime_status": raw_payload})

            return JSONResponse(_normalize_runtime_status_payload({}, state))

        @app.get("/api/companion/status")
        async def api_companion_status() -> Any:
            """Return one debug snapshot for the AIPI agent companion loop."""
            from .agent_context import (
                get_recent_awaiting_agent_session,
                list_recent_awaiting_agent_sessions,
            )
            from .agent_device import AGENT_QUERY_NAMES, build_agent_identity_payload
            from .config import Config
            from .meeting_session import _device_descriptor_to_dict

            try:
                state = self.get_state() or {}
            except Exception as e:
                log.error(f"get_state failed: {e}")
                state = {}

            runtime_error: str | None = None
            if self.on_get_status is not None:
                try:
                    raw_payload = self.on_get_status()
                    if isinstance(raw_payload, dict):
                        runtime_payload = _normalize_runtime_status_payload(raw_payload, state)
                    else:
                        runtime_payload = _normalize_runtime_status_payload(
                            {"runtime_status": raw_payload},
                            state,
                        )
                except Exception as e:
                    log.error(f"on_get_status failed: {e}")
                    runtime_error = str(e)
                    runtime_payload = _normalize_runtime_status_payload({}, state)
            else:
                runtime_payload = _normalize_runtime_status_payload({}, state)

            devices = [
                _device_descriptor_to_dict(descriptor)
                for descriptor in self.device_registry.active()
            ]
            device_connected = bool(devices)

            agent_error: str | None = None
            try:
                session = get_recent_awaiting_agent_session(max_age_seconds=120)
                agent_sessions = list_recent_awaiting_agent_sessions(
                    max_age_seconds=120,
                    limit=8,
                )
            except Exception as e:
                log.error(f"agent companion status failed: {e}")
                agent_error = str(e)
                session = None
                agent_sessions = []
            agent_waiting = bool(session and session.awaiting_response)
            tmux_reply_available = bool(
                session
                and session.awaiting_response
                and getattr(session, "tmux_pane", None)
            )

            dictation_error: str | None = None
            try:
                dictation_cfg = Config.load().dictation
                pipeline_enabled = bool(dictation_cfg.pipeline.enabled)
                pipeline_stages = list(dictation_cfg.pipeline.stages)
                target_profile_override = dictation_cfg.pipeline.target_profile_override
                runtime_backend = dictation_cfg.runtime.backend
            except Exception as e:
                log.error(f"dictation config load failed: {e}")
                dictation_error = str(e)
                pipeline_enabled = False
                pipeline_stages = []
                target_profile_override = None
                runtime_backend = None

            text_injection_known = "text_injection_enabled" in runtime_payload
            text_injection_enabled = (
                bool(runtime_payload.get("text_injection_enabled"))
                if text_injection_known
                else None
            )
            agent_identity = build_agent_identity_payload(
                session,
                text_injection_enabled=text_injection_enabled,
            )
            if session is not None and not any(
                item.agent == session.agent and item.session_id == session.session_id
                for item in agent_sessions
            ):
                agent_sessions.insert(0, session)
            selected_agent_key = (
                (session.agent, session.session_id) if session is not None else None
            )
            agent_session_items = []
            selected_index: int | None = None
            for index, item in enumerate(agent_sessions):
                item_key = (item.agent, item.session_id)
                selected = item_key == selected_agent_key
                if selected:
                    selected_index = index
                agent_session_items.append(
                    {
                        "index": index,
                        "selected": selected,
                        "session": item.to_dict(),
                        "identity": build_agent_identity_payload(
                            item,
                            text_injection_enabled=text_injection_enabled,
                        ),
                    }
                )

            blockers: list[str] = []
            if not device_connected:
                blockers.append("no_device_connected")
            if not agent_waiting:
                blockers.append("no_agent_waiting")
            if not pipeline_enabled:
                blockers.append("dictation_pipeline_disabled")
            if text_injection_enabled is False and not tmux_reply_available:
                blockers.append("text_injection_unavailable")
            elif text_injection_enabled is None and not tmux_reply_available:
                blockers.append("text_injection_status_unknown")
            if agent_error:
                blockers.append("agent_status_unavailable")
            if dictation_error:
                blockers.append("dictation_config_unavailable")
            if runtime_error:
                blockers.append("runtime_status_unavailable")

            return JSONResponse(
                {
                    "status": "ok",
                    "ready_for_agent_reply": not blockers,
                    "blockers": blockers,
                    "checks": {
                        "device_connected": device_connected,
                        "agent_waiting": agent_waiting,
                        "dictation_pipeline_enabled": pipeline_enabled,
                        "text_injection_enabled": text_injection_enabled,
                        "tmux_reply_available": tmux_reply_available,
                        "target_confidence": (
                            agent_identity["target_confidence"] if agent_identity else None
                        ),
                    },
                    "devices": {
                        "connected": device_connected,
                        "count": len(devices),
                        "items": devices,
                        "query_names": sorted(AGENT_QUERY_NAMES),
                    },
                    "agent": {
                        "awaiting_response": agent_waiting,
                        "session": session.to_dict() if session else None,
                        "identity": agent_identity,
                        "sessions": {
                            "count": len(agent_session_items),
                            "selected_index": selected_index,
                            "items": agent_session_items,
                        },
                        "max_age_seconds": 120,
                        "error": agent_error,
                    },
                    "dictation": {
                        "pipeline_enabled": pipeline_enabled,
                        "stages": pipeline_stages,
                        "target_profile_override": target_profile_override,
                        "runtime_backend": runtime_backend,
                        "error": dictation_error,
                    },
                    "runtime": {
                        "status": runtime_payload.get("status"),
                        "mode": runtime_payload.get("mode"),
                        "meeting_active": runtime_payload.get("meeting_active"),
                        "meeting_id": runtime_payload.get("meeting_id"),
                        "voice_state": runtime_payload.get("voice_state"),
                        "text_injection_enabled": text_injection_enabled,
                        "text_injection_error": runtime_payload.get("text_injection_error"),
                        "tmux_reply_available": tmux_reply_available,
                        "target_transport": (
                            agent_identity["target_transport"] if agent_identity else None
                        ),
                        "error": runtime_error,
                    },
                    "companion": {
                        "query_names": sorted(AGENT_QUERY_NAMES),
                        "voice_reply_max_age_seconds": 120,
                    },
                }
            )

        # === History browsing routes (database-backed) ===

        @app.get("/history")
        async def history_dashboard() -> Any:
            """Serve the history dashboard (HS-10-08: now read from the
            Astro-built _built/history/index.html). The /settings route
            still points here because settings live as a tab inside
            the history page."""
            history_path = (
                Path(__file__).resolve().parent
                / "static"
                / "_built"
                / "history"
                / "index.html"
            )
            try:
                html = history_path.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read built history page: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8' />"
                    "<title>HoldSpeak History</title></head>"
                    "<body><h1>HoldSpeak History</h1>"
                    "<p>History UI not built. Run <code>npm run build</code> "
                    "in <code>web/</code>.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/settings")
        async def settings_dashboard() -> Any:
            """Serve web settings UI (currently integrated with history dashboard)."""
            return await history_dashboard()

        @app.get("/activity")
        async def activity_dashboard() -> Any:
            """Serve the local activity intelligence dashboard (HS-10-07:
            now read from the Astro-built _built/activity/index.html)."""
            page = (
                Path(__file__).resolve().parent
                / "static"
                / "_built"
                / "activity"
                / "index.html"
            )
            try:
                html = page.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read activity.html: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8'/>"
                    "<title>HoldSpeak Activity</title></head>"
                    "<body><h1>Local Activity</h1><p>Page unavailable.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/dictation")
        async def dictation_dashboard() -> Any:
            """Serve the dictation block-config UI (HS-10-09: now read
            from the Astro-built _built/dictation/index.html)."""
            page = (
                Path(__file__).resolve().parent
                / "static"
                / "_built"
                / "dictation"
                / "index.html"
            )
            try:
                html = page.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read built dictation page: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8'/>"
                    "<title>HoldSpeak Dictation</title></head>"
                    "<body><h1>HoldSpeak Dictation</h1>"
                    "<p>Dictation UI not built. Run <code>npm run build</code> "
                    "in <code>web/</code>.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/companion")
        async def companion_dashboard() -> Any:
            """Serve the AI PI companion surface (HS-24-01)."""
            page = (
                Path(__file__).resolve().parent
                / "static"
                / "_built"
                / "companion"
                / "index.html"
            )
            try:
                html = page.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read built companion page: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8'/>"
                    "<title>HoldSpeak Companion</title></head>"
                    "<body><h1>AI PI Companion</h1>"
                    "<p>Companion UI not built. Run <code>npm run build</code> "
                    "in <code>web/</code>.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/docs/dictation-runtime")
        async def dictation_runtime_docs() -> Any:
            """Serve local dictation runtime setup guidance (HS-10-09:
            now read from _built/docs/dictation-runtime/index.html)."""
            page = (
                Path(__file__).resolve().parent
                / "static"
                / "_built"
                / "docs"
                / "dictation-runtime"
                / "index.html"
            )
            try:
                html = page.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read built dictation-runtime docs: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8'/>"
                    "<title>Dictation Runtime Setup</title></head>"
                    "<body><h1>Dictation Runtime Setup</h1>"
                    "<p>Page unavailable.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/api/projects/{project_id}/briefings")
        async def api_list_project_briefings(
            project_id: str,
            limit: int = 50,
        ) -> Any:
            """HS-13-09: per-project meeting_context timeline.

            Returns every meeting_context briefing whose
            `value.project_id` matches, ordered newest first.
            The /history Projects-tab panel walks this for the
            cross-meeting narrative.
            """
            from .db import get_database

            try:
                clean_limit = max(1, min(int(limit), 200))
            except (TypeError, ValueError):
                clean_limit = 50
            try:
                db = get_database()
                if db.get_project(project_id) is None:
                    return JSONResponse(
                        {"error": f"Unknown project: {project_id}"},
                        status_code=404,
                    )
                annotations = db.list_activity_annotations(
                    source_connector_id="meeting_context",
                    annotation_type="meeting_context_briefing",
                    limit=max(clean_limit * 4, 100),
                )
                rows = []
                for ann in annotations:
                    if not isinstance(ann.value, dict):
                        continue
                    if ann.value.get("project_id") != project_id:
                        continue
                    rows.append(
                        {
                            "id": ann.id,
                            "title": ann.title,
                            "value": ann.value,
                            "created_at": ann.created_at.isoformat(),
                            "updated_at": ann.updated_at.isoformat(),
                        }
                    )
                    if len(rows) >= clean_limit:
                        break
                return JSONResponse(
                    {"project_id": project_id, "briefings": rows}
                )
            except Exception as e:
                log.error(f"Failed to list project briefings: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/settings")
        async def api_get_settings() -> Any:
            try:
                from .config import Config
                from .plugins.dictation.runtime_counters import get_counters, get_session_status

                config = Config.load()
                payload = config.to_dict()
                # WFS-CFG-004: surface runtime counters + session-disabled state
                # alongside the persisted config. Read-only — clients should
                # not echo this back on PUT.
                payload["_runtime_status"] = {
                    "counters": get_counters(),
                    "session": get_session_status(),
                }
                return JSONResponse(payload)
            except Exception as e:
                log.error(f"Failed to load settings: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.put("/api/settings")
        async def api_update_settings(payload: dict[str, Any]) -> Any:
            """Persist app settings from web UI."""
            try:
                from .config import (
                    Config,
                    DeviceConfig,
                    DictationConfig,
                    DictationConfigError,
                    DictationPipelineConfig,
                    HotkeyConfig,
                    KEY_DISPLAY,
                    KEY_MAP,
                    LLMRuntimeConfig,
                    MeetingConfig,
                    ModelConfig,
                    UIConfig,
                )

                current = Config.load()
                merged = deepcopy(current.to_dict())
                _merge_dict(merged, payload or {})

                hotkey_data = merged.get("hotkey", {})
                model_data = merged.get("model", {})
                ui_data = merged.get("ui", {})
                meeting_data = merged.get("meeting", {})
                device_data = merged.get("device", {})

                hotkey_key = str(hotkey_data.get("key", current.hotkey.key))
                if hotkey_key not in KEY_MAP:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid hotkey key: {hotkey_key}"},
                        status_code=400,
                    )
                hotkey_data["key"] = hotkey_key
                hotkey_data["display"] = KEY_DISPLAY.get(hotkey_key, hotkey_key)

                model_name = str(model_data.get("name", current.model.name))
                if model_name not in {"tiny", "base", "small", "medium", "large"}:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid model name: {model_name}"},
                        status_code=400,
                    )
                model_data["name"] = model_name
                model_data["warm_on_start"] = bool(
                    model_data.get("warm_on_start", current.model.warm_on_start)
                )

                # --- UIConfig validation ---
                theme = str(ui_data.get("theme", current.ui.theme)).strip().lower()
                if theme not in {"dark", "light", "dracula", "monokai"}:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid theme: {theme}"},
                        status_code=400,
                    )
                ui_data["theme"] = theme

                history_lines = int(ui_data.get("history_lines", current.ui.history_lines))
                if not (1 <= history_lines <= 100):
                    return JSONResponse(
                        {"success": False, "error": "history_lines must be between 1 and 100"},
                        status_code=400,
                    )
                ui_data["history_lines"] = history_lines
                ui_data["show_audio_meter"] = bool(
                    ui_data.get("show_audio_meter", current.ui.show_audio_meter)
                )

                # --- Optional string / bool fields in MeetingConfig ---
                meeting_data["mic_device"] = (
                    str(meeting_data.get("mic_device") or "").strip() or None
                )
                meeting_data["system_audio_device"] = (
                    str(meeting_data.get("system_audio_device") or "").strip() or None
                )
                meeting_data["auto_export"] = bool(
                    meeting_data.get("auto_export", current.meeting.auto_export)
                )
                meeting_data["intel_summary_model"] = (
                    str(meeting_data.get("intel_summary_model") or "").strip() or None
                )
                meeting_data["intel_cloud_reasoning_effort"] = (
                    str(meeting_data.get("intel_cloud_reasoning_effort") or "").strip() or None
                )

                export_format = str(meeting_data.get("export_format", current.meeting.export_format))
                if export_format not in {"txt", "markdown", "json", "srt"}:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid export format: {export_format}"},
                        status_code=400,
                    )
                meeting_data["export_format"] = export_format

                intel_provider = str(meeting_data.get("intel_provider", current.meeting.intel_provider)).lower()
                if intel_provider not in {"local", "cloud", "auto"}:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid intel provider: {intel_provider}"},
                        status_code=400,
                    )
                meeting_data["intel_provider"] = intel_provider

                from .plugins.router import available_profiles

                meeting_data["mir_enabled"] = bool(
                    meeting_data.get("mir_enabled", current.meeting.mir_enabled)
                )
                mir_profile = str(
                    meeting_data.get("mir_profile", current.meeting.mir_profile)
                ).strip().lower()
                if mir_profile not in set(available_profiles()):
                    return JSONResponse(
                        {"success": False, "error": f"Invalid mir profile: {mir_profile}"},
                        status_code=400,
                    )
                meeting_data["mir_profile"] = mir_profile

                poll_seconds = int(meeting_data.get("intel_queue_poll_seconds", current.meeting.intel_queue_poll_seconds))
                if poll_seconds < 5:
                    return JSONResponse(
                        {"success": False, "error": "intel_queue_poll_seconds must be at least 5"},
                        status_code=400,
                    )
                meeting_data["intel_queue_poll_seconds"] = poll_seconds

                retry_base_seconds = int(
                    meeting_data.get("intel_retry_base_seconds", current.meeting.intel_retry_base_seconds)
                )
                if retry_base_seconds < 1:
                    return JSONResponse(
                        {"success": False, "error": "intel_retry_base_seconds must be at least 1"},
                        status_code=400,
                    )
                meeting_data["intel_retry_base_seconds"] = retry_base_seconds

                retry_max_seconds = int(
                    meeting_data.get("intel_retry_max_seconds", current.meeting.intel_retry_max_seconds)
                )
                if retry_max_seconds < retry_base_seconds:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "intel_retry_max_seconds must be >= intel_retry_base_seconds",
                        },
                        status_code=400,
                    )
                meeting_data["intel_retry_max_seconds"] = retry_max_seconds

                retry_max_attempts = int(
                    meeting_data.get("intel_retry_max_attempts", current.meeting.intel_retry_max_attempts)
                )
                if retry_max_attempts < 1:
                    return JSONResponse(
                        {"success": False, "error": "intel_retry_max_attempts must be at least 1"},
                        status_code=400,
                    )
                meeting_data["intel_retry_max_attempts"] = retry_max_attempts

                failure_alert_percent = float(
                    meeting_data.get(
                        "intel_retry_failure_alert_percent",
                        current.meeting.intel_retry_failure_alert_percent,
                    )
                )
                if not (0.0 <= failure_alert_percent <= 100.0):
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "intel_retry_failure_alert_percent must be between 0 and 100",
                        },
                        status_code=400,
                    )
                meeting_data["intel_retry_failure_alert_percent"] = failure_alert_percent

                failure_hysteresis_minutes = float(
                    meeting_data.get(
                        "intel_retry_failure_hysteresis_minutes",
                        current.meeting.intel_retry_failure_hysteresis_minutes,
                    )
                )
                if failure_hysteresis_minutes < 0.0:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "intel_retry_failure_hysteresis_minutes must be >= 0",
                        },
                        status_code=400,
                    )
                meeting_data["intel_retry_failure_hysteresis_minutes"] = failure_hysteresis_minutes

                webhook_url = str(
                    meeting_data.get(
                        "intel_retry_failure_webhook_url",
                        current.meeting.intel_retry_failure_webhook_url or "",
                    )
                    or ""
                ).strip()
                if webhook_url:
                    parsed_webhook = urlparse(webhook_url)
                    if parsed_webhook.scheme not in {"http", "https"} or not parsed_webhook.netloc:
                        return JSONResponse(
                            {
                                "success": False,
                                "error": "intel_retry_failure_webhook_url must be a valid http(s) URL",
                            },
                            status_code=400,
                        )
                meeting_data["intel_retry_failure_webhook_url"] = webhook_url or None
                webhook_header_name = str(
                    meeting_data.get(
                        "intel_retry_failure_webhook_header_name",
                        current.meeting.intel_retry_failure_webhook_header_name or "",
                    )
                    or ""
                ).strip()
                webhook_header_value = str(
                    meeting_data.get(
                        "intel_retry_failure_webhook_header_value",
                        current.meeting.intel_retry_failure_webhook_header_value or "",
                    )
                    or ""
                ).strip()
                if bool(webhook_header_name) != bool(webhook_header_value):
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "intel_retry_failure_webhook_header_name and intel_retry_failure_webhook_header_value must both be set or both be empty",
                        },
                        status_code=400,
                    )
                if webhook_header_name and not _HTTP_HEADER_NAME_RE.match(webhook_header_name):
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "intel_retry_failure_webhook_header_name must contain only letters, digits, and hyphens",
                        },
                        status_code=400,
                    )
                meeting_data["intel_retry_failure_webhook_header_name"] = webhook_header_name or None
                meeting_data["intel_retry_failure_webhook_header_value"] = webhook_header_value or None

                similarity = float(meeting_data.get("similarity_threshold", current.meeting.similarity_threshold))
                if not (0.0 <= similarity <= 1.0):
                    return JSONResponse(
                        {"success": False, "error": "similarity_threshold must be between 0.0 and 1.0"},
                        status_code=400,
                    )
                meeting_data["similarity_threshold"] = similarity

                try:
                    meeting_data["intel_cloud_base_url"] = _validate_cloud_base_url(
                        meeting_data.get("intel_cloud_base_url")
                    )
                except ValueError as e:
                    return JSONResponse({"success": False, "error": str(e)}, status_code=400)

                meeting_data["intel_cloud_api_key_env"] = str(
                    meeting_data.get("intel_cloud_api_key_env", current.meeting.intel_cloud_api_key_env)
                ).strip() or "OPENAI_API_KEY"
                meeting_data["intel_cloud_model"] = str(
                    meeting_data.get("intel_cloud_model", current.meeting.intel_cloud_model)
                ).strip() or "gpt-5-mini"

                # WFS-CFG-004: validate the dictation slice (preserves
                # current values when payload omits them; merged already
                # carries `current.to_dict()["dictation"]` as the base).
                # Drops the read-only `_runtime_status` enrichment if the
                # client echoed it back.
                merged.pop("_runtime_status", None)
                dictation_data = merged.get("dictation", {}) or {}
                pipeline_data = dictation_data.get("pipeline", {}) or {}
                runtime_data = dictation_data.get("runtime", {}) or {}

                pipeline_data["enabled"] = bool(pipeline_data.get(
                    "enabled", current.dictation.pipeline.enabled
                ))
                raw_stages = pipeline_data.get("stages", current.dictation.pipeline.stages)
                if not isinstance(raw_stages, list) or not all(
                    isinstance(stage, str) for stage in raw_stages
                ):
                    return JSONResponse(
                        {"success": False, "error": "dictation.pipeline.stages must be a list of strings"},
                        status_code=400,
                    )
                pipeline_data["stages"] = list(raw_stages)
                try:
                    max_lat = int(pipeline_data.get(
                        "max_total_latency_ms",
                        current.dictation.pipeline.max_total_latency_ms,
                    ))
                except (TypeError, ValueError):
                    return JSONResponse(
                        {"success": False, "error": "dictation.pipeline.max_total_latency_ms must be an integer"},
                        status_code=400,
                    )
                if max_lat <= 0:
                    return JSONResponse(
                        {"success": False, "error": "dictation.pipeline.max_total_latency_ms must be > 0"},
                        status_code=400,
                    )
                pipeline_data["max_total_latency_ms"] = max_lat
                target_override = str(pipeline_data.get(
                    "target_profile_override",
                    current.dictation.pipeline.target_profile_override,
                )).strip().lower() or "auto"
                allowed_target_overrides = {
                    "auto",
                    "claude_code",
                    "codex_cli",
                    "terminal_shell",
                    "browser",
                    "editor",
                    "chat",
                }
                if target_override not in allowed_target_overrides:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": (
                                "dictation.pipeline.target_profile_override must be one of: "
                                + ", ".join(sorted(allowed_target_overrides))
                            ),
                        },
                        status_code=400,
                    )
                pipeline_data["target_profile_override"] = target_override

                backend = str(runtime_data.get(
                    "backend", current.dictation.runtime.backend
                )).strip().lower()
                if backend not in {"auto", "mlx", "llama_cpp", "openai_compatible"}:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid dictation backend: {backend!r}"},
                        status_code=400,
                    )
                runtime_data["backend"] = backend
                runtime_data["mlx_model"] = str(runtime_data.get(
                    "mlx_model", current.dictation.runtime.mlx_model
                )).strip() or current.dictation.runtime.mlx_model
                runtime_data["llama_cpp_model_path"] = str(runtime_data.get(
                    "llama_cpp_model_path", current.dictation.runtime.llama_cpp_model_path
                )).strip() or current.dictation.runtime.llama_cpp_model_path
                runtime_data["openai_compatible_model"] = str(runtime_data.get(
                    "openai_compatible_model", current.dictation.runtime.openai_compatible_model
                )).strip() or current.dictation.runtime.openai_compatible_model
                runtime_data["openai_compatible_base_url"] = str(runtime_data.get(
                    "openai_compatible_base_url", current.dictation.runtime.openai_compatible_base_url
                )).strip() or current.dictation.runtime.openai_compatible_base_url
                try:
                    _validate_cloud_base_url(runtime_data["openai_compatible_base_url"])
                except ValueError:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "dictation.runtime.openai_compatible_base_url must start with http:// or https://",
                        },
                        status_code=400,
                    )
                runtime_data["openai_compatible_api_key_env"] = str(runtime_data.get(
                    "openai_compatible_api_key_env",
                    current.dictation.runtime.openai_compatible_api_key_env,
                )).strip()
                try:
                    timeout_seconds = float(runtime_data.get(
                        "openai_compatible_timeout_seconds",
                        current.dictation.runtime.openai_compatible_timeout_seconds,
                    ))
                except (TypeError, ValueError):
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "dictation.runtime.openai_compatible_timeout_seconds must be a number",
                        },
                        status_code=400,
                    )
                if timeout_seconds <= 0:
                    return JSONResponse(
                        {
                            "success": False,
                            "error": "dictation.runtime.openai_compatible_timeout_seconds must be > 0",
                        },
                        status_code=400,
                    )
                runtime_data["openai_compatible_timeout_seconds"] = timeout_seconds
                runtime_data["warm_on_start"] = bool(runtime_data.get(
                    "warm_on_start", current.dictation.runtime.warm_on_start
                ))

                try:
                    dictation_cfg = DictationConfig(
                        pipeline=DictationPipelineConfig(**pipeline_data),
                        runtime=LLMRuntimeConfig(**runtime_data),
                    )
                except DictationConfigError as exc:
                    return JSONResponse(
                        {"success": False, "error": str(exc)},
                        status_code=400,
                    )
                except TypeError as exc:
                    return JSONResponse(
                        {"success": False, "error": f"Invalid dictation field: {exc}"},
                        status_code=400,
                    )

                updated = Config(
                    hotkey=HotkeyConfig(**hotkey_data),
                    model=ModelConfig(**model_data),
                    ui=UIConfig(**ui_data),
                    meeting=MeetingConfig(**meeting_data),
                    dictation=dictation_cfg,
                    device=DeviceConfig(**device_data),
                )
                updated.save()

                if self.on_settings_applied is not None:
                    try:
                        self.on_settings_applied(updated)
                    except Exception as e:
                        log.error(f"on_settings_applied failed: {e}")

                return JSONResponse({"success": True, "settings": updated.to_dict()})
            except Exception as e:
                log.error(f"Failed to update settings: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        # ── Project knowledge-base endpoints ──────────────────────────────

        @app.get("/api/projects")
        async def api_list_projects(include_archived: bool = False) -> Any:
            try:
                from .db import get_database
                db = get_database()
                projects = db.list_projects(include_archived=include_archived)
                return JSONResponse({
                    "projects": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "keywords": p.keywords,
                            "team_members": p.team_members,
                            "context": p.context,
                            "detection_threshold": p.detection_threshold,
                            "is_archived": p.is_archived,
                            "meeting_count": p.meeting_count,
                            "created_at": p.created_at.isoformat(),
                            "updated_at": p.updated_at.isoformat(),
                        }
                        for p in projects
                    ]
                })
            except Exception as e:
                log.error(f"Failed to list projects: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/projects")
        async def api_create_project(payload: dict[str, Any]) -> Any:
            try:
                import uuid
                from .db import get_database
                db = get_database()
                name = str(payload.get("name") or "").strip()
                if not name:
                    return JSONResponse(
                        {"success": False, "error": "Project name is required"},
                        status_code=400,
                    )
                project_id = f"proj-{uuid.uuid4().hex[:12]}"
                keywords = payload.get("keywords") or []
                if isinstance(keywords, str):
                    keywords = [k.strip() for k in keywords.split(",") if k.strip()]
                team_members = payload.get("team_members") or []
                if isinstance(team_members, str):
                    team_members = [m.strip() for m in team_members.split(",") if m.strip()]
                threshold = float(payload.get("detection_threshold", 0.4))
                if not (0.0 <= threshold <= 1.0):
                    return JSONResponse(
                        {"success": False, "error": "detection_threshold must be between 0 and 1"},
                        status_code=400,
                    )
                db.create_project(
                    project_id=project_id,
                    name=name,
                    description=str(payload.get("description") or ""),
                    keywords=keywords,
                    team_members=team_members,
                    context=payload.get("context") or {},
                    detection_threshold=threshold,
                )
                # Reload detector
                if self._project_detector is not None:
                    self._project_detector.reload_projects(
                        db.get_all_projects_for_detector()
                    )
                project = db.get_project(project_id)
                return JSONResponse({
                    "success": True,
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "description": project.description,
                        "keywords": project.keywords,
                        "team_members": project.team_members,
                        "context": project.context,
                        "detection_threshold": project.detection_threshold,
                        "is_archived": project.is_archived,
                        "meeting_count": project.meeting_count,
                        "created_at": project.created_at.isoformat(),
                        "updated_at": project.updated_at.isoformat(),
                    } if project else None,
                })
            except Exception as e:
                log.error(f"Failed to create project: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.get("/api/projects/{project_id}")
        async def api_get_project(project_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                project = db.get_project(project_id)
                if not project:
                    return JSONResponse({"error": "Project not found"}, status_code=404)
                return JSONResponse({
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "keywords": project.keywords,
                    "team_members": project.team_members,
                    "context": project.context,
                    "detection_threshold": project.detection_threshold,
                    "is_archived": project.is_archived,
                    "meeting_count": project.meeting_count,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                })
            except Exception as e:
                log.error(f"Failed to get project: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.patch("/api/projects/{project_id}")
        async def api_update_project(project_id: str, payload: dict[str, Any]) -> Any:
            try:
                from .db import get_database
                db = get_database()
                existing = db.get_project(project_id)
                if not existing:
                    return JSONResponse(
                        {"success": False, "error": "Project not found"},
                        status_code=404,
                    )
                update_fields: dict[str, Any] = {}
                if "name" in payload:
                    name = str(payload["name"]).strip()
                    if not name:
                        return JSONResponse(
                            {"success": False, "error": "Project name cannot be empty"},
                            status_code=400,
                        )
                    update_fields["name"] = name
                if "description" in payload:
                    update_fields["description"] = str(payload["description"] or "")
                if "keywords" in payload:
                    kw = payload["keywords"]
                    if isinstance(kw, str):
                        kw = [k.strip() for k in kw.split(",") if k.strip()]
                    update_fields["keywords"] = kw
                if "team_members" in payload:
                    tm = payload["team_members"]
                    if isinstance(tm, str):
                        tm = [m.strip() for m in tm.split(",") if m.strip()]
                    update_fields["team_members"] = tm
                if "context" in payload:
                    update_fields["context"] = payload["context"] or {}
                if "detection_threshold" in payload:
                    threshold = float(payload["detection_threshold"])
                    if not (0.0 <= threshold <= 1.0):
                        return JSONResponse(
                            {"success": False, "error": "detection_threshold must be between 0 and 1"},
                            status_code=400,
                        )
                    update_fields["detection_threshold"] = threshold
                if update_fields:
                    db.update_project(project_id, **update_fields)
                # Reload detector
                if self._project_detector is not None:
                    self._project_detector.reload_projects(
                        db.get_all_projects_for_detector()
                    )
                updated = db.get_project(project_id)
                return JSONResponse({
                    "success": True,
                    "project": {
                        "id": updated.id,
                        "name": updated.name,
                        "description": updated.description,
                        "keywords": updated.keywords,
                        "team_members": updated.team_members,
                        "context": updated.context,
                        "detection_threshold": updated.detection_threshold,
                        "is_archived": updated.is_archived,
                        "meeting_count": updated.meeting_count,
                        "created_at": updated.created_at.isoformat(),
                        "updated_at": updated.updated_at.isoformat(),
                    } if updated else None,
                })
            except Exception as e:
                log.error(f"Failed to update project: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.delete("/api/projects/{project_id}")
        async def api_archive_project(project_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                existing = db.get_project(project_id)
                if not existing:
                    return JSONResponse(
                        {"success": False, "error": "Project not found"},
                        status_code=404,
                    )
                db.update_project(project_id, is_archived=True)
                if self._project_detector is not None:
                    self._project_detector.reload_projects(
                        db.get_all_projects_for_detector()
                    )
                return JSONResponse({"success": True})
            except Exception as e:
                log.error(f"Failed to archive project: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.get("/api/projects/{project_id}/meetings")
        async def api_project_meetings(
            project_id: str, limit: int = 50, offset: int = 0
        ) -> Any:
            try:
                from .db import get_database
                db = get_database()
                meetings = db.get_project_meetings(project_id, limit=limit, offset=offset)
                return JSONResponse({"meetings": meetings})
            except Exception as e:
                log.error(f"Failed to get project meetings: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/projects/{project_id}/meetings/{meeting_id}")
        async def api_associate_meeting(project_id: str, meeting_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                db.associate_meeting_project(
                    meeting_id=meeting_id,
                    project_id=project_id,
                    source="manual",
                    confidence=1.0,
                )
                return JSONResponse({"success": True})
            except Exception as e:
                log.error(f"Failed to associate meeting: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.delete("/api/projects/{project_id}/meetings/{meeting_id}")
        async def api_disassociate_meeting(project_id: str, meeting_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                db.disassociate_meeting_project(
                    meeting_id=meeting_id,
                    project_id=project_id,
                )
                return JSONResponse({"success": True})
            except Exception as e:
                log.error(f"Failed to disassociate meeting: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.get("/api/meetings/{meeting_id}/projects")
        async def api_meeting_projects(meeting_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                projects = db.get_meeting_projects(meeting_id)
                return JSONResponse({"projects": projects})
            except Exception as e:
                log.error(f"Failed to get meeting projects: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/projects/{project_id}/summary")
        async def api_project_summary(project_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                summary = db.get_project_summary(project_id)
                return JSONResponse(summary)
            except Exception as e:
                log.error(f"Failed to get project summary: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/projects/{project_id}/action-items")
        async def api_project_action_items(project_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                items = db.get_project_action_items(project_id)
                return JSONResponse({
                    "action_items": [
                        {
                            "id": ai.id,
                            "task": ai.task,
                            "owner": ai.owner,
                            "due": ai.due,
                            "status": ai.status,
                            "review_state": ai.review_state,
                            "source_timestamp": ai.source_timestamp,
                            "meeting_id": ai.meeting_id,
                            "meeting_title": ai.meeting_title,
                            "meeting_date": ai.meeting_date.isoformat(),
                            "created_at": ai.created_at.isoformat(),
                            "completed_at": ai.completed_at.isoformat() if ai.completed_at else None,
                            "reviewed_at": ai.reviewed_at.isoformat() if ai.reviewed_at else None,
                        }
                        for ai in items
                    ]
                })
            except Exception as e:
                log.error(f"Failed to get project action items: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/projects/{project_id}/artifacts")
        async def api_project_artifacts(project_id: str) -> Any:
            try:
                from .db import get_database
                db = get_database()
                artifacts = db.get_project_artifacts(project_id)
                return JSONResponse({
                    "artifacts": [
                        {
                            "id": a.id,
                            "meeting_id": a.meeting_id,
                            "artifact_type": a.artifact_type,
                            "title": a.title,
                            "body_markdown": a.body_markdown,
                            "confidence": a.confidence,
                            "status": a.status,
                            "plugin_id": a.plugin_id,
                            "created_at": a.created_at.isoformat(),
                        }
                        for a in artifacts
                    ]
                })
            except Exception as e:
                log.error(f"Failed to get project artifacts: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket) -> None:
            log.info(f"WebSocket connection attempt from {websocket.client}")
            try:
                await self._ws.connect(websocket)
                log.info("WebSocket connected successfully")
            except Exception as e:
                log.error(f"WebSocket connect failed: {e}", exc_info=True)
                return

            try:
                # Optional initial state push via REST endpoint; for WS we at
                # least emit current duration immediately if available.
                duration = self._current_formatted_duration()
                if duration is not None:
                    await websocket.send_json({"type": "duration", "data": duration})

                while True:
                    # Keep connection alive; ignore client messages for now.
                    message = await websocket.receive_text()
                    if message == "ping":
                        await websocket.send_text("pong")
                    elif message.startswith("{"):
                        # Accept JSON no-op messages without error.
                        try:
                            json.loads(message)
                        except Exception:
                            pass
            except WebSocketDisconnect:
                pass
            except Exception as e:
                log.debug(f"WebSocket error: {e}")
            finally:
                await self._ws.disconnect(websocket)

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
