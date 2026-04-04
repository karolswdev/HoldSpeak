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
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .logging_config import get_logger

log = get_logger("web_server")
_HTTP_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]+$")

_DASHBOARD_HTML_PATH = Path(__file__).resolve().parent / "static" / "dashboard.html"

try:
    import uvicorn
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel
except Exception as e:  # pragma: no cover - optional dependency at runtime
    uvicorn = None  # type: ignore[assignment]
    FastAPI = None  # type: ignore[assignment]
    WebSocket = None  # type: ignore[assignment]
    WebSocketDisconnect = None  # type: ignore[assignment]
    HTMLResponse = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]
    BaseModel = object  # type: ignore[assignment]
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


class _BookmarkRequest(BaseModel):
    label: str = ""


class _StopRequest(BaseModel):
    reason: Optional[str] = None


class _ActionItemUpdateRequest(BaseModel):
    status: str  # "done", "pending", or "dismissed"


class _ActionItemReviewRequest(BaseModel):
    review_state: str  # "pending" or "accepted"


class _ActionItemEditRequest(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None


class _UpdateMeetingRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None


class _IntentProfileRequest(BaseModel):
    profile: str


class _IntentOverrideRequest(BaseModel):
    intents: Optional[list[str]] = None


class _IntentPreviewRequest(BaseModel):
    profile: Optional[str] = None
    threshold: Optional[float] = None
    intent_scores: Optional[dict[str, float]] = None
    override_intents: Optional[list[str]] = None
    previous_intents: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    transcript: Optional[str] = None


class _GlobalActionItemUpdateRequest(BaseModel):
    status: str


class _GlobalActionItemReviewRequest(BaseModel):
    review_state: str


class _GlobalActionItemEditRequest(BaseModel):
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None


class _SpeakerUpdateRequest(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None


class _IntelProcessRequest(BaseModel):
    max_jobs: Optional[int] = None
    mode: Optional[str] = None


class _PluginJobProcessRequest(BaseModel):
    max_jobs: Optional[int] = None
    mode: Optional[str] = None


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
        project_detector: Optional[Any] = None,
        host: str = "127.0.0.1",
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
        self._project_detector = project_detector
        self.host = host

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

        self.port = _find_free_port(self.host)
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
        app = FastAPI()

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

        @app.get("/")
        async def dashboard() -> Any:
            try:
                html = _DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read dashboard.html: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8' />"
                    "<title>HoldSpeak</title></head>"
                    "<body><h1>HoldSpeak Dashboard</h1>"
                    "<p>Dashboard UI missing.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/health")
        async def health() -> Any:
            return JSONResponse({"status": "ok"})

        @app.get("/api/state")
        async def api_state() -> Any:
            try:
                state = self.get_state() or {}
            except Exception as e:
                log.error(f"get_state failed: {e}")
                state = {}
            return JSONResponse(state)

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

        @app.get("/api/intents/control")
        async def api_get_intent_controls() -> Any:
            if self.on_get_intent_controls is None:
                return JSONResponse(
                    {
                        "enabled": False,
                        "profile": "balanced",
                        "available_profiles": [],
                        "supported_intents": [],
                        "override_intents": [],
                    }
                )
            try:
                payload = self.on_get_intent_controls()
            except Exception as e:
                log.error(f"on_get_intent_controls failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            return JSONResponse(payload if isinstance(payload, dict) else {"controls": payload})

        @app.put("/api/intents/profile")
        async def api_set_intent_profile(payload: _IntentProfileRequest) -> Any:
            if self.on_set_intent_profile is None:
                return JSONResponse(
                    {"success": False, "error": "Intent profile updates not supported"},
                    status_code=501,
                )
            try:
                result = self.on_set_intent_profile(payload.profile)
            except Exception as e:
                log.error(f"on_set_intent_profile failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            if isinstance(result, dict):
                self.broadcast("intent_controls_updated", result)
            return JSONResponse({"success": True, "controls": result})

        @app.put("/api/intents/override")
        async def api_set_intent_override(payload: _IntentOverrideRequest) -> Any:
            if self.on_set_intent_override is None:
                return JSONResponse(
                    {"success": False, "error": "Intent override updates not supported"},
                    status_code=501,
                )
            try:
                result = self.on_set_intent_override(payload.intents)
            except Exception as e:
                log.error(f"on_set_intent_override failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            if isinstance(result, dict):
                self.broadcast("intent_controls_updated", result)
            return JSONResponse({"success": True, "controls": result})

        @app.post("/api/intents/preview")
        async def api_preview_intent_route(payload: Optional[_IntentPreviewRequest] = None) -> Any:
            if self.on_route_preview is None:
                return JSONResponse(
                    {"success": False, "error": "Intent route preview not supported"},
                    status_code=501,
                )
            try:
                result = self.on_route_preview(
                    profile=payload.profile if payload is not None else None,
                    threshold=payload.threshold if payload is not None else None,
                    intent_scores=payload.intent_scores if payload is not None else None,
                    override_intents=payload.override_intents if payload is not None else None,
                    previous_intents=payload.previous_intents if payload is not None else None,
                    tags=payload.tags if payload is not None else None,
                    transcript=payload.transcript if payload is not None else None,
                )
            except Exception as e:
                log.error(f"on_route_preview failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)
            return JSONResponse({"success": True, "route": result})

        @app.post("/api/bookmark")
        async def api_bookmark(payload: Optional[_BookmarkRequest] = None) -> Any:
            try:
                label = payload.label if payload is not None else ""
                result = self.on_bookmark(label)
            except Exception as e:
                log.error(f"on_bookmark failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            bookmark_data: Any = None
            if hasattr(result, "to_dict"):
                try:
                    bookmark_data = result.to_dict()
                except Exception:
                    bookmark_data = None
            elif isinstance(result, dict):
                bookmark_data = result

            if bookmark_data is not None:
                self.broadcast("bookmark", bookmark_data)

            return JSONResponse({"success": True})

        async def _handle_stop_request(callback: Callable[[], Any]) -> Any:
            try:
                result = callback()
            except Exception as e:
                log.error(f"on_stop failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            stopped_data: Any = None
            if hasattr(result, "to_dict"):
                try:
                    stopped_data = result.to_dict()
                except Exception:
                    stopped_data = None
            elif isinstance(result, dict):
                stopped_data = result
            else:
                stopped_data = {"status": "stopped"}

            self.broadcast("stopped", stopped_data)
            return JSONResponse({"success": True})

        @app.post("/api/meeting/start")
        async def api_meeting_start() -> Any:
            if self.on_start is None:
                return JSONResponse(
                    {"success": False, "error": "Meeting start control not supported"},
                    status_code=501,
                )

            try:
                result = self.on_start()
            except Exception as e:
                log.error(f"on_start failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            meeting_data: Any = None
            if hasattr(result, "to_dict"):
                try:
                    meeting_data = result.to_dict()
                except Exception:
                    meeting_data = None
            elif isinstance(result, dict):
                meeting_data = result

            if meeting_data is not None:
                self.broadcast("meeting_started", meeting_data)
            return JSONResponse({"success": True, "meeting": meeting_data})

        @app.post("/api/meeting/stop")
        async def api_meeting_stop(_: Optional[_StopRequest] = None) -> Any:
            callback = self.on_meeting_stop or self.on_stop
            return await _handle_stop_request(callback)

        @app.post("/api/stop")
        async def api_stop(_: Optional[_StopRequest] = None) -> Any:
            # Backward-compatible alias.
            return await _handle_stop_request(self.on_stop)

        @app.patch("/api/action-items/{item_id}")
        async def api_update_action_item(
            item_id: str, payload: _ActionItemUpdateRequest
        ) -> Any:
            if self.on_update_action_item is None:
                return JSONResponse(
                    {"success": False, "error": "Action item updates not supported"},
                    status_code=501,
                )

            status = payload.status
            if status not in ("done", "pending", "dismissed"):
                return JSONResponse(
                    {"success": False, "error": f"Invalid status: {status}"},
                    status_code=400,
                )

            try:
                result = self.on_update_action_item(item_id, status)
            except Exception as e:
                log.error(f"on_update_action_item failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            if result is None:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )

            # Broadcast the update to all connected clients
            self.broadcast("action_item_updated", result)

            return JSONResponse({"success": True, "action_item": result})

        @app.patch("/api/action-items/{item_id}/review")
        async def api_update_action_item_review(
            item_id: str, payload: _ActionItemReviewRequest
        ) -> Any:
            if self.on_update_action_item_review is None:
                return JSONResponse(
                    {"success": False, "error": "Action item review updates not supported"},
                    status_code=501,
                )

            review_state = str(payload.review_state or "").strip().lower()
            if review_state not in ("pending", "accepted"):
                return JSONResponse(
                    {"success": False, "error": f"Invalid review_state: {review_state}"},
                    status_code=400,
                )

            try:
                result = self.on_update_action_item_review(item_id, review_state)
            except Exception as e:
                log.error(f"on_update_action_item_review failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            if result is None:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )

            self.broadcast("action_item_updated", result)
            return JSONResponse({"success": True, "action_item": result})

        @app.patch("/api/action-items/{item_id}/edit")
        async def api_edit_action_item(
            item_id: str, payload: _ActionItemEditRequest
        ) -> Any:
            if self.on_edit_action_item is None:
                return JSONResponse(
                    {"success": False, "error": "Action item edits not supported"},
                    status_code=501,
                )

            task = str(payload.task or "").strip()
            if not task:
                return JSONResponse(
                    {"success": False, "error": "Action item task cannot be empty"},
                    status_code=400,
                )

            try:
                result = self.on_edit_action_item(
                    item_id,
                    task=task,
                    owner=payload.owner,
                    due=payload.due,
                )
            except Exception as e:
                log.error(f"on_edit_action_item failed: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

            if result is None:
                return JSONResponse(
                    {"success": False, "error": "Action item not found"},
                    status_code=404,
                )

            self.broadcast("action_item_updated", result)
            return JSONResponse({"success": True, "action_item": result})

        @app.patch("/api/meeting")
        async def api_update_meeting(payload: _UpdateMeetingRequest) -> Any:
            """Update meeting title and/or tags."""
            try:
                meeting_data: Optional[dict[str, Any]] = None
                if self.on_update_meeting is not None:
                    result = self.on_update_meeting(title=payload.title, tags=payload.tags)
                    if hasattr(result, "to_dict"):
                        try:
                            meeting_data = result.to_dict()
                        except Exception:
                            meeting_data = None
                    elif isinstance(result, dict):
                        meeting_data = result
                else:
                    if payload.title is not None and self.on_set_title is not None:
                        self.on_set_title(payload.title)
                    if payload.tags is not None and self.on_set_tags is not None:
                        self.on_set_tags(payload.tags)
                    try:
                        meeting_data = self.get_state() or {}
                    except Exception:
                        meeting_data = None

                if isinstance(meeting_data, dict):
                    self.broadcast(
                        "meeting_updated",
                        {
                            "title": meeting_data.get("title"),
                            "tags": meeting_data.get("tags") if isinstance(meeting_data.get("tags"), list) else [],
                        },
                    )
                return JSONResponse({"success": True, "meeting": meeting_data})
            except Exception as e:
                log.error(f"Failed to update meeting: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)}, status_code=500
                )

        # === History browsing routes (database-backed) ===

        @app.get("/history")
        async def history_dashboard() -> Any:
            """Serve the history dashboard HTML."""
            history_path = Path(__file__).resolve().parent / "static" / "history.html"
            try:
                html = history_path.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read history.html: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8' />"
                    "<title>Meeting History</title></head>"
                    "<body><h1>Meeting History</h1>"
                    "<p>History UI not available.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/settings")
        async def settings_dashboard() -> Any:
            """Serve web settings UI (currently integrated with history dashboard)."""
            return await history_dashboard()

        @app.get("/api/settings")
        async def api_get_settings() -> Any:
            try:
                from .config import Config
                config = Config.load()
                return JSONResponse(config.to_dict())
            except Exception as e:
                log.error(f"Failed to load settings: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.put("/api/settings")
        async def api_update_settings(payload: dict[str, Any]) -> Any:
            """Persist app settings from web UI."""
            try:
                from .config import Config, HotkeyConfig, ModelConfig, UIConfig, MeetingConfig, KEY_MAP, KEY_DISPLAY

                current = Config.load()
                merged = deepcopy(current.to_dict())
                _merge_dict(merged, payload or {})

                hotkey_data = merged.get("hotkey", {})
                model_data = merged.get("model", {})
                ui_data = merged.get("ui", {})
                meeting_data = merged.get("meeting", {})

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

                updated = Config(
                    hotkey=HotkeyConfig(**hotkey_data),
                    model=ModelConfig(**model_data),
                    ui=UIConfig(**ui_data),
                    meeting=MeetingConfig(**meeting_data),
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

        @app.get("/api/meetings")
        async def api_list_meetings(
            limit: int = 50,
            offset: int = 0,
            search: Optional[str] = None,
        ) -> Any:
            """List meetings from database."""
            try:
                from .db import get_database
                db = get_database()

                if search:
                    # Search transcripts
                    results = db.search_transcripts(search, limit=limit)
                    # Group by meeting
                    meeting_ids = list(dict.fromkeys([r[0] for r in results]))
                    meetings = [db.get_meeting(mid) for mid in meeting_ids[:limit]]
                    meetings = [m for m in meetings if m is not None]
                    return JSONResponse({
                        "meetings": [m.to_dict() for m in meetings],
                        "total": len(meetings),
                    })

                meetings = db.list_meetings(limit=limit, offset=offset)
                return JSONResponse({
                    "meetings": [
                        {
                            "id": m.id,
                            "started_at": m.started_at.isoformat(),
                            "ended_at": m.ended_at.isoformat() if m.ended_at else None,
                            "title": m.title,
                            "duration_seconds": m.duration_seconds,
                            "segment_count": m.segment_count,
                            "action_item_count": m.action_item_count,
                            "tags": m.tags,
                            "intel_status": m.intel_status,
                            "intel_status_detail": m.intel_status_detail,
                        }
                        for m in meetings
                    ],
                    "total": db.get_meeting_count(),
                })
            except Exception as e:
                log.error(f"Failed to list meetings: {e}")
                return JSONResponse(
                    {"error": str(e)}, status_code=500
                )

        @app.get("/api/speakers")
        async def api_list_speakers() -> Any:
            """List known speakers with aggregate stats."""
            try:
                from .db import get_database

                db = get_database()
                speakers = db.get_all_speakers()
                payload: list[dict[str, Any]] = []
                for speaker in speakers:
                    stats = db.get_speaker_stats(speaker.id)
                    payload.append(
                        {
                            "id": speaker.id,
                            "name": speaker.name,
                            "avatar": speaker.avatar,
                            "sample_count": speaker.sample_count,
                            "total_segments": stats.get("total_segments", 0),
                            "total_speaking_time": stats.get("total_speaking_time", 0.0),
                            "meeting_count": stats.get("meeting_count", 0),
                            "first_seen": stats["first_seen"].isoformat() if stats.get("first_seen") else None,
                            "last_seen": stats["last_seen"].isoformat() if stats.get("last_seen") else None,
                        }
                    )

                payload.sort(key=lambda s: (s.get("last_seen") or "", s.get("sample_count") or 0), reverse=True)
                return JSONResponse({"speakers": payload, "total": len(payload)})
            except Exception as e:
                log.error(f"Failed to list speakers: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/speakers/{speaker_id}")
        async def api_get_speaker(speaker_id: str, limit: int = 500) -> Any:
            """Get speaker profile, stats, and related segments grouped by meeting."""
            try:
                from .db import get_database

                db = get_database()
                speaker = db.get_speaker(speaker_id)
                if speaker is None:
                    return JSONResponse({"error": "Speaker not found"}, status_code=404)

                stats = db.get_speaker_stats(speaker_id)
                groups = db.get_speaker_segments(speaker_id, limit=limit)
                for group in groups:
                    if isinstance(group.get("meeting_date"), datetime):
                        group["meeting_date"] = group["meeting_date"].isoformat()

                return JSONResponse(
                    {
                        "speaker": {
                            "id": speaker.id,
                            "name": speaker.name,
                            "avatar": speaker.avatar,
                            "sample_count": speaker.sample_count,
                        },
                        "stats": {
                            "total_segments": stats.get("total_segments", 0),
                            "total_speaking_time": stats.get("total_speaking_time", 0.0),
                            "meeting_count": stats.get("meeting_count", 0),
                            "first_seen": stats["first_seen"].isoformat() if stats.get("first_seen") else None,
                            "last_seen": stats["last_seen"].isoformat() if stats.get("last_seen") else None,
                        },
                        "meetings": groups,
                    }
                )
            except Exception as e:
                log.error(f"Failed to get speaker: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.patch("/api/speakers/{speaker_id}")
        async def api_update_speaker(speaker_id: str, payload: _SpeakerUpdateRequest) -> Any:
            """Rename speaker and/or update avatar."""
            try:
                from .db import get_database

                db = get_database()
                updated = False

                if payload.name is not None:
                    name = payload.name.strip()
                    if not name:
                        return JSONResponse({"success": False, "error": "Speaker name cannot be empty"}, status_code=400)
                    updated = db.update_speaker_name(speaker_id, name) or updated

                if payload.avatar is not None:
                    avatar = payload.avatar.strip()
                    if not avatar:
                        return JSONResponse({"success": False, "error": "Speaker avatar cannot be empty"}, status_code=400)
                    updated = db.update_speaker_avatar(speaker_id, avatar) or updated

                if not updated:
                    return JSONResponse({"success": False, "error": "Speaker not found"}, status_code=404)

                speaker = db.get_speaker(speaker_id)
                if speaker is None:
                    return JSONResponse({"success": False, "error": "Speaker not found"}, status_code=404)

                return JSONResponse(
                    {
                        "success": True,
                        "speaker": {
                            "id": speaker.id,
                            "name": speaker.name,
                            "avatar": speaker.avatar,
                            "sample_count": speaker.sample_count,
                        },
                    }
                )
            except Exception as e:
                log.error(f"Failed to update speaker: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.get("/api/meetings/{meeting_id}")
        async def api_get_meeting(meeting_id: str) -> Any:
            """Get meeting details from database."""
            try:
                from .db import get_database
                db = get_database()
                meeting = db.get_meeting(meeting_id)
                if meeting is None:
                    return JSONResponse(
                        {"error": "Meeting not found"}, status_code=404
                    )
                return JSONResponse(meeting.to_dict())
            except Exception as e:
                log.error(f"Failed to get meeting: {e}")
                return JSONResponse(
                    {"error": str(e)}, status_code=500
                )

        @app.get("/api/meetings/{meeting_id}/intent-timeline")
        async def api_get_meeting_intent_timeline(
            meeting_id: str,
            limit: int = 200,
        ) -> Any:
            """Get persisted MIR intent timeline for one meeting."""
            try:
                from .db import get_database
                from .intent_timeline import detect_intent_transitions

                db = get_database()
                meeting = db.get_meeting(meeting_id)
                if meeting is None:
                    return JSONResponse(
                        {"error": "Meeting not found"},
                        status_code=404,
                    )

                windows = db.list_intent_windows(meeting_id, limit=limit)
                transitions = detect_intent_transitions(
                    [(window.window_id, list(window.active_intents)) for window in windows]
                )
                return JSONResponse(
                    {
                        "meeting_id": meeting_id,
                        "windows": [
                            {
                                "meeting_id": window.meeting_id,
                                "window_id": window.window_id,
                                "start_seconds": window.start_seconds,
                                "end_seconds": window.end_seconds,
                                "transcript_hash": window.transcript_hash,
                                "transcript_excerpt": window.transcript_excerpt,
                                "profile": window.profile,
                                "threshold": window.threshold,
                                "active_intents": window.active_intents,
                                "intent_scores": window.intent_scores,
                                "override_intents": window.override_intents,
                                "tags": window.tags,
                                "metadata": window.metadata,
                                "created_at": window.created_at.isoformat(),
                                "updated_at": window.updated_at.isoformat(),
                            }
                            for window in windows
                        ],
                        "transitions": transitions,
                    }
                )
            except Exception as e:
                log.error(f"Failed to load meeting intent timeline: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/meetings/{meeting_id}/plugin-runs")
        async def api_get_meeting_plugin_runs(
            meeting_id: str,
            limit: int = 500,
            window_id: Optional[str] = None,
        ) -> Any:
            """Get persisted MIR plugin-run history for one meeting."""
            try:
                from .db import get_database

                db = get_database()
                meeting = db.get_meeting(meeting_id)
                if meeting is None:
                    return JSONResponse(
                        {"error": "Meeting not found"},
                        status_code=404,
                    )

                runs = db.list_plugin_runs(meeting_id, window_id=window_id, limit=limit)
                return JSONResponse(
                    {
                        "meeting_id": meeting_id,
                        "window_id": window_id,
                        "runs": [
                            {
                                "id": run.id,
                                "meeting_id": run.meeting_id,
                                "window_id": run.window_id,
                                "plugin_id": run.plugin_id,
                                "plugin_version": run.plugin_version,
                                "status": run.status,
                                "idempotency_key": run.idempotency_key,
                                "duration_ms": run.duration_ms,
                                "output": run.output,
                                "error": run.error,
                                "deduped": run.deduped,
                                "created_at": run.created_at.isoformat(),
                                "updated_at": run.updated_at.isoformat(),
                            }
                            for run in runs
                        ],
                    }
                )
            except Exception as e:
                log.error(f"Failed to load meeting plugin runs: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/meetings/{meeting_id}/artifacts")
        async def api_get_meeting_artifacts(
            meeting_id: str,
            limit: int = 200,
        ) -> Any:
            """Get synthesized artifacts and lineage for one meeting."""
            try:
                from .db import get_database

                db = get_database()
                meeting = db.get_meeting(meeting_id)
                if meeting is None:
                    return JSONResponse(
                        {"error": "Meeting not found"},
                        status_code=404,
                    )

                artifacts = db.list_artifacts(meeting_id, limit=limit)
                return JSONResponse(
                    {
                        "meeting_id": meeting_id,
                        "artifacts": [
                            {
                                "id": artifact.id,
                                "meeting_id": artifact.meeting_id,
                                "artifact_type": artifact.artifact_type,
                                "title": artifact.title,
                                "body_markdown": artifact.body_markdown,
                                "structured_json": artifact.structured_json,
                                "confidence": artifact.confidence,
                                "status": artifact.status,
                                "plugin_id": artifact.plugin_id,
                                "plugin_version": artifact.plugin_version,
                                "sources": artifact.sources,
                                "created_at": artifact.created_at.isoformat(),
                                "updated_at": artifact.updated_at.isoformat(),
                            }
                            for artifact in artifacts
                        ],
                    }
                )
            except Exception as e:
                log.error(f"Failed to load meeting artifacts: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/plugin-jobs")
        async def api_list_plugin_jobs(
            status: str = "all",
            meeting_id: Optional[str] = None,
            limit: int = 200,
        ) -> Any:
            """List deferred MIR plugin-run queue jobs."""
            try:
                from .db import get_database

                db = get_database()
                jobs = db.list_plugin_run_jobs(status=status, meeting_id=meeting_id, limit=limit)
                now = datetime.now()
                return JSONResponse(
                    {
                        "jobs": [
                            {
                                "id": job.id,
                                "meeting_id": job.meeting_id,
                                "window_id": job.window_id,
                                "plugin_id": job.plugin_id,
                                "plugin_version": job.plugin_version,
                                "transcript_hash": job.transcript_hash,
                                "idempotency_key": job.idempotency_key,
                                "status": job.status,
                                "requested_at": job.requested_at.isoformat(),
                                "updated_at": job.updated_at.isoformat(),
                                "attempts": job.attempts,
                                "last_error": job.last_error,
                                "retry_scheduled": (
                                    job.status == "queued"
                                    and bool(job.last_error)
                                    and job.requested_at > now
                                ),
                                "next_retry_at": (
                                    job.requested_at.isoformat()
                                    if (
                                        job.status == "queued"
                                        and bool(job.last_error)
                                        and job.requested_at > now
                                    )
                                    else None
                                ),
                            }
                            for job in jobs
                        ]
                    }
                )
            except Exception as e:
                log.error(f"Failed to list deferred plugin jobs: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/plugin-jobs/summary")
        async def api_plugin_jobs_summary() -> Any:
            """Return aggregate telemetry for deferred MIR plugin-run queue."""
            try:
                from .db import get_database

                db = get_database()
                summary = db.get_plugin_run_job_summary()
                return JSONResponse(
                    {
                        "total_jobs": summary.total_jobs,
                        "queued_jobs": summary.queued_jobs,
                        "running_jobs": summary.running_jobs,
                        "failed_jobs": summary.failed_jobs,
                        "queued_due_jobs": summary.queued_due_jobs,
                        "scheduled_retry_jobs": summary.scheduled_retry_jobs,
                        "next_retry_at": (
                            summary.next_retry_at.isoformat() if summary.next_retry_at else None
                        ),
                    }
                )
            except Exception as e:
                log.error(f"Failed to load deferred plugin-job summary: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/plugin-jobs/process")
        async def api_process_plugin_jobs(payload: Optional[_PluginJobProcessRequest] = None) -> Any:
            """Process deferred plugin-run queue jobs now."""
            if self.on_process_plugin_jobs is None:
                return JSONResponse(
                    {"success": False, "error": "Deferred plugin queue processing not supported"},
                    status_code=501,
                )
            max_jobs = payload.max_jobs if payload is not None else None
            if max_jobs is not None and int(max_jobs) <= 0:
                return JSONResponse(
                    {"success": False, "error": "max_jobs must be greater than 0"},
                    status_code=400,
                )
            mode = (payload.mode if payload is not None else None) or "respect_backoff"
            normalized_mode = str(mode).strip().lower()
            if normalized_mode not in {"respect_backoff", "retry_now"}:
                return JSONResponse(
                    {"success": False, "error": "mode must be respect_backoff or retry_now"},
                    status_code=400,
                )
            include_scheduled = normalized_mode == "retry_now"
            try:
                result = self.on_process_plugin_jobs(
                    max_jobs=max_jobs,
                    include_scheduled=include_scheduled,
                )
                payload_data = dict(result) if isinstance(result, dict) else {"processed": int(result)}
                payload_data["mode"] = normalized_mode
                payload_data["success"] = True
                self.broadcast("plugin_jobs_processed", payload_data)
                return JSONResponse(payload_data)
            except Exception as e:
                log.error(f"Failed to process deferred plugin jobs: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.post("/api/plugin-jobs/{job_id}/retry-now")
        async def api_retry_plugin_job_now(job_id: int) -> Any:
            """Reschedule one deferred MIR plugin-run job for immediate retry."""
            try:
                from .db import get_database

                db = get_database()
                job = db.get_plugin_run_job(job_id) if hasattr(db, "get_plugin_run_job") else None
                if job is None:
                    return JSONResponse({"success": False, "error": "Plugin job not found"}, status_code=404)
                if str(job.status).strip().lower() == "running":
                    return JSONResponse(
                        {"success": False, "error": "Cannot retry a running plugin job"},
                        status_code=409,
                    )

                db.retry_plugin_run_job(
                    int(job_id),
                    error="Manual retry requested from web UI.",
                    retry_at=datetime.now(),
                )
                updated = db.get_plugin_run_job(job_id) if hasattr(db, "get_plugin_run_job") else None
                return JSONResponse(
                    {
                        "success": True,
                        "job": (
                            {
                                "id": updated.id,
                                "meeting_id": updated.meeting_id,
                                "window_id": updated.window_id,
                                "plugin_id": updated.plugin_id,
                                "plugin_version": updated.plugin_version,
                                "status": updated.status,
                                "requested_at": updated.requested_at.isoformat(),
                                "updated_at": updated.updated_at.isoformat(),
                                "attempts": updated.attempts,
                                "last_error": updated.last_error,
                            }
                            if updated is not None
                            else None
                        ),
                    }
                )
            except Exception as e:
                log.error(f"Failed to retry deferred plugin job {job_id}: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.post("/api/plugin-jobs/{job_id}/cancel")
        async def api_cancel_plugin_job(job_id: int) -> Any:
            """Cancel one deferred MIR plugin-run job."""
            try:
                from .db import get_database

                db = get_database()
                job = db.get_plugin_run_job(job_id) if hasattr(db, "get_plugin_run_job") else None
                if job is None:
                    return JSONResponse({"success": False, "error": "Plugin job not found"}, status_code=404)
                if str(job.status).strip().lower() == "running":
                    return JSONResponse(
                        {"success": False, "error": "Cannot cancel a running plugin job"},
                        status_code=409,
                    )
                db.complete_plugin_run_job(job_id)
                return JSONResponse({"success": True})
            except Exception as e:
                log.error(f"Failed to cancel deferred plugin job {job_id}: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.get("/api/all-action-items")
        async def api_list_all_action_items(
            include_completed: bool = False,
            owner: Optional[str] = None,
            meeting_id: Optional[str] = None,
        ) -> Any:
            """List action items across all meetings from database."""
            try:
                from .db import get_database
                db = get_database()
                items = db.list_action_items(
                    include_completed=include_completed,
                    owner=owner,
                    meeting_id=meeting_id,
                )
                return JSONResponse({
                    "action_items": [
                        {
                            "id": item.id,
                            "task": item.task,
                            "owner": item.owner,
                            "due": item.due,
                            "status": item.status,
                            "review_state": item.review_state,
                            "meeting_id": item.meeting_id,
                            "meeting_title": item.meeting_title,
                            "meeting_date": item.meeting_date.isoformat(),
                            "created_at": item.created_at.isoformat(),
                            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                        }
                        for item in items
                    ]
                })
            except Exception as e:
                log.error(f"Failed to list action items: {e}")
                return JSONResponse(
                    {"error": str(e)}, status_code=500
                )

        @app.patch("/api/all-action-items/{item_id}")
        async def api_update_global_action_item(
            item_id: str, payload: _GlobalActionItemUpdateRequest
        ) -> Any:
            """Update action item status in database."""
            status = payload.status
            if status not in ("done", "pending", "dismissed"):
                return JSONResponse(
                    {"success": False, "error": f"Invalid status: {status}"},
                    status_code=400,
                )

            try:
                from .db import get_database
                db = get_database()
                success = db.update_action_item_status(item_id, status)
                if not success:
                    return JSONResponse(
                        {"success": False, "error": "Action item not found"},
                        status_code=404,
                    )
                updated = db.get_action_item(item_id) if hasattr(db, "get_action_item") else None
                return JSONResponse(
                    {
                        "success": True,
                        "action_item": (
                            {
                                "id": updated.id,
                                "task": updated.task,
                                "owner": updated.owner,
                                "due": updated.due,
                                "status": updated.status,
                                "review_state": updated.review_state,
                                "meeting_id": updated.meeting_id,
                                "meeting_title": updated.meeting_title,
                                "meeting_date": updated.meeting_date.isoformat(),
                                "created_at": updated.created_at.isoformat(),
                                "completed_at": (
                                    updated.completed_at.isoformat()
                                    if updated.completed_at
                                    else None
                                ),
                                "reviewed_at": (
                                    updated.reviewed_at.isoformat()
                                    if updated.reviewed_at
                                    else None
                                ),
                            }
                            if updated is not None
                            else None
                        ),
                    }
                )
            except Exception as e:
                log.error(f"Failed to update action item: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)}, status_code=500
                )

        @app.patch("/api/all-action-items/{item_id}/review")
        async def api_review_global_action_item(
            item_id: str, payload: _GlobalActionItemReviewRequest
        ) -> Any:
            """Update action item review state."""
            review_state = str(payload.review_state or "").strip().lower()
            if review_state not in ("pending", "accepted"):
                return JSONResponse(
                    {"success": False, "error": f"Invalid review_state: {review_state}"},
                    status_code=400,
                )

            try:
                from .db import get_database
                db = get_database()
                success = db.update_action_item_review_state(item_id, review_state)
                if not success:
                    return JSONResponse(
                        {"success": False, "error": "Action item not found"},
                        status_code=404,
                    )
                updated = db.get_action_item(item_id) if hasattr(db, "get_action_item") else None
                return JSONResponse(
                    {
                        "success": True,
                        "action_item": (
                            {
                                "id": updated.id,
                                "task": updated.task,
                                "owner": updated.owner,
                                "due": updated.due,
                                "status": updated.status,
                                "review_state": updated.review_state,
                                "meeting_id": updated.meeting_id,
                                "meeting_title": updated.meeting_title,
                                "meeting_date": updated.meeting_date.isoformat(),
                                "created_at": updated.created_at.isoformat(),
                                "completed_at": (
                                    updated.completed_at.isoformat()
                                    if updated.completed_at
                                    else None
                                ),
                                "reviewed_at": (
                                    updated.reviewed_at.isoformat()
                                    if updated.reviewed_at
                                    else None
                                ),
                            }
                            if updated is not None
                            else None
                        ),
                    }
                )
            except Exception as e:
                log.error(f"Failed to update action item review state: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.patch("/api/all-action-items/{item_id}/edit")
        async def api_edit_global_action_item(
            item_id: str, payload: _GlobalActionItemEditRequest
        ) -> Any:
            """Edit action item details and auto-accept the item."""
            task = str(payload.task or "").strip()
            if not task:
                return JSONResponse(
                    {"success": False, "error": "Action item task cannot be empty"},
                    status_code=400,
                )

            owner = payload.owner
            due = payload.due
            try:
                from .db import get_database
                db = get_database()
                success = db.edit_action_item(
                    item_id,
                    task=task,
                    owner=owner,
                    due=due,
                )
                if not success:
                    return JSONResponse(
                        {"success": False, "error": "Action item not found"},
                        status_code=404,
                    )
                updated = db.get_action_item(item_id) if hasattr(db, "get_action_item") else None
                return JSONResponse(
                    {
                        "success": True,
                        "action_item": (
                            {
                                "id": updated.id,
                                "task": updated.task,
                                "owner": updated.owner,
                                "due": updated.due,
                                "status": updated.status,
                                "review_state": updated.review_state,
                                "meeting_id": updated.meeting_id,
                                "meeting_title": updated.meeting_title,
                                "meeting_date": updated.meeting_date.isoformat(),
                                "created_at": updated.created_at.isoformat(),
                                "completed_at": (
                                    updated.completed_at.isoformat()
                                    if updated.completed_at
                                    else None
                                ),
                                "reviewed_at": (
                                    updated.reviewed_at.isoformat()
                                    if updated.reviewed_at
                                    else None
                                ),
                            }
                            if updated is not None
                            else None
                        ),
                    }
                )
            except ValueError as e:
                return JSONResponse({"success": False, "error": str(e)}, status_code=400)
            except Exception as e:
                log.error(f"Failed to edit action item: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.get("/api/intel/jobs")
        async def api_list_intel_jobs(
            status: str = "all",
            limit: int = 20,
            history_limit: int = 5,
        ) -> Any:
            """List deferred intelligence jobs."""
            try:
                from .db import get_database
                from .config import Config

                db = get_database()
                jobs = db.list_intel_jobs(status=status, limit=limit)
                retry_max_attempts = max(1, int(Config.load().meeting.intel_retry_max_attempts))
                now = datetime.now()
                bounded_history_limit = max(1, min(int(history_limit), 20))
                return JSONResponse(
                    {
                        "jobs": [
                            {
                                "meeting_id": job.meeting_id,
                                "status": job.status,
                                "transcript_hash": job.transcript_hash,
                                "requested_at": job.requested_at.isoformat(),
                                "updated_at": job.updated_at.isoformat(),
                                "attempts": job.attempts,
                                "last_error": job.last_error,
                                "meeting_title": job.meeting_title,
                                "started_at": job.started_at.isoformat() if job.started_at else None,
                                "intel_status_detail": job.intel_status_detail,
                                "retry_scheduled": (
                                    job.status == "queued"
                                    and bool(job.last_error)
                                    and job.requested_at > now
                                ),
                                "next_retry_at": (
                                    job.requested_at.isoformat()
                                    if (
                                        job.status == "queued"
                                        and bool(job.last_error)
                                        and job.requested_at > now
                                    )
                                    else None
                                ),
                                "retries_remaining": max(0, retry_max_attempts - int(job.attempts)),
                                "retry_max_attempts": retry_max_attempts,
                                "retry_history": [
                                    {
                                        "attempt": event.attempt,
                                        "outcome": event.outcome,
                                        "error": event.error,
                                        "retry_at": event.retry_at.isoformat() if event.retry_at else None,
                                        "created_at": event.created_at.isoformat(),
                                    }
                                    for event in db.list_intel_job_attempts(
                                        job.meeting_id,
                                        limit=bounded_history_limit,
                                    )
                                ],
                            }
                            for job in jobs
                        ]
                    }
                )
            except Exception as e:
                log.error(f"Failed to list intel jobs: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/intel/summary")
        async def api_intel_queue_summary() -> Any:
            """Return aggregate deferred-intel queue telemetry."""
            try:
                from .db import get_database

                db = get_database()
                summary = db.get_intel_queue_summary()
                return JSONResponse(
                    {
                        "total_jobs": summary.total_jobs,
                        "queued_jobs": summary.queued_jobs,
                        "running_jobs": summary.running_jobs,
                        "failed_jobs": summary.failed_jobs,
                        "queued_due_jobs": summary.queued_due_jobs,
                        "scheduled_retry_jobs": summary.scheduled_retry_jobs,
                        "next_retry_at": (
                            summary.next_retry_at.isoformat() if summary.next_retry_at else None
                        ),
                    }
                )
            except Exception as e:
                log.error(f"Failed to load intel queue summary: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/intel/process")
        async def api_process_intel_jobs(payload: Optional[_IntelProcessRequest] = None) -> Any:
            """Process queued deferred-intel jobs now."""
            try:
                from .config import Config
                from .intel_queue import drain_intel_queue

                cfg = Config.load().meeting
                max_jobs = payload.max_jobs if payload is not None else None
                mode = (payload.mode if payload is not None else None) or "respect_backoff"
                normalized_mode = str(mode).strip().lower()
                if normalized_mode not in {"respect_backoff", "retry_now"}:
                    return JSONResponse(
                        {"success": False, "error": "mode must be respect_backoff or retry_now"},
                        status_code=400,
                    )
                include_scheduled = normalized_mode == "retry_now"
                processed = drain_intel_queue(
                    cfg.intel_realtime_model,
                    provider=cfg.intel_provider,
                    cloud_model=cfg.intel_cloud_model,
                    cloud_api_key_env=cfg.intel_cloud_api_key_env,
                    cloud_base_url=cfg.intel_cloud_base_url,
                    cloud_reasoning_effort=cfg.intel_cloud_reasoning_effort,
                    cloud_store=cfg.intel_cloud_store,
                    retry_base_seconds=cfg.intel_retry_base_seconds,
                    retry_max_seconds=cfg.intel_retry_max_seconds,
                    retry_max_attempts=cfg.intel_retry_max_attempts,
                    include_scheduled=include_scheduled,
                    max_jobs=max_jobs,
                )
                return JSONResponse(
                    {
                        "success": True,
                        "processed": processed,
                        "mode": normalized_mode,
                    }
                )
            except Exception as e:
                log.error(f"Failed to process intel jobs: {e}")
                return JSONResponse({"success": False, "error": str(e)}, status_code=500)

        @app.post("/api/intel/retry/{meeting_id}")
        async def api_retry_intel_job(meeting_id: str) -> Any:
            """Requeue deferred intelligence for a specific meeting."""
            try:
                from .db import get_database

                db = get_database()
                ok = db.requeue_intel_job(meeting_id, reason="Manual retry requested from web UI.")
                if not ok:
                    return JSONResponse({"success": False, "error": "Meeting not found or transcript is empty"}, status_code=404)
                return JSONResponse({"success": True})
            except Exception as e:
                log.error(f"Failed to retry intel job: {e}")
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
