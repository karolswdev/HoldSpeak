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

# WFS-CFG-001: global dictation blocks file. Tests monkeypatch this constant.
_GLOBAL_BLOCKS_PATH = Path.home() / ".config" / "holdspeak" / "blocks.yaml"

try:
    import uvicorn
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse, JSONResponse, Response
    from pydantic import BaseModel
except Exception as e:  # pragma: no cover - optional dependency at runtime
    uvicorn = None  # type: ignore[assignment]
    FastAPI = None  # type: ignore[assignment]
    WebSocket = None  # type: ignore[assignment]
    WebSocketDisconnect = None  # type: ignore[assignment]
    HTMLResponse = None  # type: ignore[assignment]
    JSONResponse = None  # type: ignore[assignment]
    Response = None  # type: ignore[assignment]
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


class _ActivitySettingsRequest(BaseModel):
    enabled: Optional[bool] = None
    retention_days: Optional[int] = None


class _ActivityDomainRuleRequest(BaseModel):
    domain: str
    action: str = "exclude"


class _ActivityProjectRuleRequest(BaseModel):
    project_id: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None
    match_type: Optional[str] = None
    pattern: Optional[str] = None
    entity_type: Optional[str] = None


def _model_fields_set(model: Any) -> set[str]:
    fields = getattr(model, "model_fields_set", None)
    if fields is not None:
        return set(fields)
    fields = getattr(model, "__fields_set__", None)
    if fields is not None:
        return set(fields)
    return set()


def _activity_project_rule_payload(rule: Any) -> dict[str, Any]:
    return {
        "id": rule.id,
        "project_id": rule.project_id,
        "project_name": rule.project_name,
        "name": rule.name,
        "enabled": rule.enabled,
        "priority": rule.priority,
        "match_type": rule.match_type,
        "pattern": rule.pattern,
        "entity_type": rule.entity_type,
        "created_at": rule.created_at.isoformat(),
        "updated_at": rule.updated_at.isoformat(),
    }


def _activity_record_payload(record: Any) -> dict[str, Any]:
    return {
        "id": record.id,
        "source_browser": record.source_browser,
        "source_profile": record.source_profile,
        "url": record.url,
        "title": record.title,
        "domain": record.domain,
        "visit_count": record.visit_count,
        "first_seen_at": record.first_seen_at.isoformat() if record.first_seen_at else None,
        "last_seen_at": record.last_seen_at.isoformat() if record.last_seen_at else None,
        "entity_type": record.entity_type,
        "entity_id": record.entity_id,
        "project_id": record.project_id,
    }


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
        self.on_dictation_config_changed = on_dictation_config_changed
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

        @app.get("/activity")
        async def activity_dashboard() -> Any:
            """Serve the local activity intelligence dashboard."""
            page = Path(__file__).resolve().parent / "static" / "activity.html"
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
            """Serve the dictation block-config UI (HS-4-02)."""
            page = Path(__file__).resolve().parent / "static" / "dictation.html"
            try:
                html = page.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read dictation.html: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8'/>"
                    "<title>HoldSpeak Dictation</title></head>"
                    "<body><h1>Dictation</h1><p>Page unavailable.</p></body></html>"
                )
            return HTMLResponse(html)

        @app.get("/docs/dictation-runtime")
        async def dictation_runtime_docs() -> Any:
            """Serve local dictation runtime setup guidance."""
            page = Path(__file__).resolve().parent / "static" / "dictation-runtime-setup.html"
            try:
                html = page.read_text(encoding="utf-8")
            except Exception as e:
                log.error(f"Failed to read dictation-runtime-setup.html: {e}")
                html = (
                    "<!doctype html><html><head><meta charset='utf-8'/>"
                    "<title>Dictation Runtime Setup</title></head>"
                    "<body><h1>Dictation Runtime Setup</h1>"
                    "<p>Page unavailable.</p></body></html>"
                )
            return HTMLResponse(html)

        # === Local activity intelligence routes ===

        def _activity_status_payload() -> dict[str, Any]:
            from .activity_history import discover_browser_history_sources
            from .db import get_database

            db = get_database()
            settings = db.get_activity_privacy_settings()
            rules = db.list_activity_domain_rules()
            checkpoints = db.list_activity_import_checkpoints()
            checkpoint_payload = [
                {
                    "source_browser": checkpoint.source_browser,
                    "source_profile": checkpoint.source_profile,
                    "source_path_hash": checkpoint.source_path_hash,
                    "last_visit_raw": checkpoint.last_visit_raw,
                    "last_imported_at": checkpoint.last_imported_at.isoformat() if checkpoint.last_imported_at else None,
                    "last_error": checkpoint.last_error,
                    "enabled": checkpoint.enabled,
                }
                for checkpoint in checkpoints
            ]
            discovered = [
                {
                    "source_browser": source.source_browser,
                    "source_profile": source.source_profile,
                    "source_path_hash": source.source_path_hash,
                    "readable": source.path.is_file(),
                    "enabled": bool(source.enabled and settings["enabled"]),
                }
                for source in discover_browser_history_sources()
            ]
            return {
                "settings": settings,
                "sources": discovered,
                "checkpoints": checkpoint_payload,
                "domain_rules": rules,
                "record_count": len(db.list_activity_records(limit=5000)),
            }

        @app.get("/api/activity/status")
        async def api_activity_status() -> Any:
            try:
                return JSONResponse(_activity_status_payload())
            except Exception as e:
                log.error(f"Failed to read activity status: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/activity/records")
        async def api_activity_records(
            project_id: Optional[str] = None,
            domain: Optional[str] = None,
            entity_type: Optional[str] = None,
            limit: int = 100,
        ) -> Any:
            try:
                from .activity_context import build_activity_context
                from .db import get_database

                db = get_database()
                bundle = build_activity_context(
                    db=db,
                    project_id=project_id,
                    limit=limit,
                    refresh=False,
                ).to_dict()
                records = bundle["records"]
                if domain:
                    clean_domain = domain.strip().lower()
                    records = [record for record in records if record.get("domain") == clean_domain]
                if entity_type:
                    clean_type = entity_type.strip().lower()
                    records = [record for record in records if record.get("entity_type") == clean_type]
                bundle["records"] = records
                return JSONResponse(bundle)
            except Exception as e:
                log.error(f"Failed to read activity records: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/activity/refresh")
        async def api_activity_refresh() -> Any:
            try:
                from .activity_history import import_browser_history
                from .db import get_database

                db = get_database()
                results = import_browser_history(db=db)
                return JSONResponse(
                    {
                        "results": [
                            {
                                "source_browser": result.source_browser,
                                "source_profile": result.source_profile,
                                "source_path_hash": result.source_path_hash,
                                "imported_count": result.imported_count,
                                "checkpoint_raw": result.checkpoint_raw,
                                "enabled": result.enabled,
                                "error": result.error,
                            }
                            for result in results
                        ],
                        "status": _activity_status_payload(),
                    }
                )
            except Exception as e:
                log.error(f"Failed to refresh activity: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.put("/api/activity/settings")
        async def api_activity_settings(payload: _ActivitySettingsRequest) -> Any:
            try:
                from .db import get_database

                db = get_database()
                settings = db.update_activity_privacy_settings(
                    enabled=payload.enabled,
                    retention_days=payload.retention_days,
                )
                return JSONResponse({"settings": settings, "status": _activity_status_payload()})
            except Exception as e:
                log.error(f"Failed to update activity settings: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/activity/domains")
        async def api_activity_domain_rule(payload: _ActivityDomainRuleRequest) -> Any:
            try:
                from .db import get_database

                db = get_database()
                rule = db.upsert_activity_domain_rule(
                    domain=payload.domain,
                    action=payload.action,
                )
                return JSONResponse({"rule": rule, "status": _activity_status_payload()})
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            except Exception as e:
                log.error(f"Failed to update activity domain rule: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.delete("/api/activity/domains/{domain}")
        async def api_delete_activity_domain_rule(domain: str) -> Any:
            try:
                from .db import get_database

                db = get_database()
                deleted = db.delete_activity_domain_rule(domain)
                return JSONResponse({"deleted": deleted, "status": _activity_status_payload()})
            except Exception as e:
                log.error(f"Failed to delete activity domain rule: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.get("/api/activity/project-rules")
        async def api_activity_project_rules(include_disabled: bool = True) -> Any:
            try:
                from .db import get_database

                db = get_database()
                rules = db.list_activity_project_rules(include_disabled=include_disabled)
                return JSONResponse({"rules": [_activity_project_rule_payload(rule) for rule in rules]})
            except Exception as e:
                log.error(f"Failed to list activity project rules: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/activity/project-rules")
        async def api_create_activity_project_rule(payload: _ActivityProjectRuleRequest) -> Any:
            try:
                from .db import get_database

                db = get_database()
                rule = db.create_activity_project_rule(
                    project_id=payload.project_id or "",
                    name=payload.name or "",
                    match_type=payload.match_type or "",
                    pattern=payload.pattern or "",
                    entity_type=payload.entity_type,
                    priority=payload.priority if payload.priority is not None else 100,
                    enabled=True if payload.enabled is None else payload.enabled,
                )
                return JSONResponse({"rule": _activity_project_rule_payload(rule)})
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            except Exception as e:
                log.error(f"Failed to create activity project rule: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.put("/api/activity/project-rules/{rule_id}")
        async def api_update_activity_project_rule(
            rule_id: str,
            payload: _ActivityProjectRuleRequest,
        ) -> Any:
            try:
                from .db import get_database

                db = get_database()
                fields: dict[str, Any] = {}
                present = _model_fields_set(payload)
                for key in (
                    "project_id",
                    "name",
                    "enabled",
                    "priority",
                    "match_type",
                    "pattern",
                    "entity_type",
                ):
                    if key in present:
                        fields[key] = getattr(payload, key)
                rule = db.update_activity_project_rule(rule_id, **fields)
                if rule is None:
                    return JSONResponse({"error": "activity project rule not found"}, status_code=404)
                return JSONResponse({"rule": _activity_project_rule_payload(rule)})
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            except Exception as e:
                log.error(f"Failed to update activity project rule: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.delete("/api/activity/project-rules/{rule_id}")
        async def api_delete_activity_project_rule(rule_id: str) -> Any:
            try:
                from .db import get_database

                db = get_database()
                return JSONResponse({"deleted": db.delete_activity_project_rule(rule_id)})
            except Exception as e:
                log.error(f"Failed to delete activity project rule: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/activity/project-rules/preview")
        async def api_preview_activity_project_rule(payload: _ActivityProjectRuleRequest) -> Any:
            try:
                from .db import get_database

                db = get_database()
                matches = db.preview_activity_project_rule(
                    project_id=payload.project_id or "",
                    match_type=payload.match_type or "",
                    pattern=payload.pattern or "",
                    entity_type=payload.entity_type,
                    limit=50,
                )
                return JSONResponse(
                    {
                        "count": len(matches),
                        "matches": [_activity_record_payload(record) for record in matches],
                    }
                )
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=400)
            except Exception as e:
                log.error(f"Failed to preview activity project rule: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.post("/api/activity/project-rules/apply")
        async def api_apply_activity_project_rules(limit: Optional[int] = None) -> Any:
            try:
                from .db import get_database

                db = get_database()
                updated = db.apply_activity_project_rules(limit=limit)
                return JSONResponse({"updated": updated})
            except Exception as e:
                log.error(f"Failed to apply activity project rules: {e}")
                return JSONResponse({"error": str(e)}, status_code=500)

        @app.delete("/api/activity/records")
        async def api_delete_activity_records(
            domain: Optional[str] = None,
            project_id: Optional[str] = None,
        ) -> Any:
            try:
                from .db import get_database

                db = get_database()
                deleted = db.delete_activity_records(domain=domain, project_id=project_id)
                return JSONResponse({"deleted": deleted, "status": _activity_status_payload()})
            except Exception as e:
                log.error(f"Failed to delete activity records: {e}")
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

                backend = str(runtime_data.get(
                    "backend", current.dictation.runtime.backend
                )).strip().lower()
                if backend not in {"auto", "mlx", "llama_cpp"}:
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

        @app.get("/api/meetings/{meeting_id}/export")
        async def api_export_meeting(
            meeting_id: str,
            format: str = "markdown",
        ) -> Any:
            """Render a saved meeting handoff export."""
            export_format = str(format or "").strip().lower()
            if export_format == "md":
                export_format = "markdown"
            if export_format not in {"markdown", "json"}:
                return JSONResponse(
                    {"error": f"Invalid export format: {format}"},
                    status_code=400,
                )

            try:
                from .db import get_database
                from .meeting_exports import render_meeting_export

                db = get_database()
                meeting = db.get_meeting(meeting_id)
                if meeting is None:
                    return JSONResponse(
                        {"error": "Meeting not found"}, status_code=404
                    )

                artifacts = db.list_artifacts(meeting_id, limit=200)
                content = render_meeting_export(
                    meeting,
                    export_format,  # type: ignore[arg-type]
                    artifacts=artifacts,
                )
                extension = "md" if export_format == "markdown" else "json"
                media_type = (
                    "text/markdown; charset=utf-8"
                    if export_format == "markdown"
                    else "application/json; charset=utf-8"
                )
                filename = f"holdspeak-meeting-{meeting_id}.{extension}"
                return Response(
                    content=content,
                    media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
                )
            except Exception as e:
                log.error(f"Failed to export meeting: {e}")
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
                            "source_timestamp": item.source_timestamp,
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
                                "source_timestamp": updated.source_timestamp,
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
                                "source_timestamp": updated.source_timestamp,
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
                                "source_timestamp": updated.source_timestamp,
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

        # ── Dictation block-config endpoints (WFS-CFG-001 + WFS-CFG-002) ──

        def _resolve_project_context(project_root: Optional[str] = None) -> dict[str, Any]:
            """Return detected/manual project context for dictation project APIs."""
            from .plugins.dictation.project_root import detect_project_for_cwd

            if project_root is None or not str(project_root).strip():
                ctx = detect_project_for_cwd()
                if ctx is None:
                    raise ValueError("no project detected for current working directory")
                return dict(ctx)

            root = Path(str(project_root)).expanduser().resolve()
            if not root.exists() or not root.is_dir():
                raise ValueError(f"project_root must be an existing directory: {root}")

            ctx = detect_project_for_cwd(root)
            if ctx is not None:
                return dict(ctx)
            return {"name": root.name, "root": str(root), "anchor": "manual"}

        def _resolve_blocks_target(
            scope: str,
            project_root: Optional[str] = None,
        ) -> tuple[Path, Optional[dict[str, Any]]]:
            """Return `(path, project_ctx)` for the requested scope.

            Raises `ValueError` with a user-facing message on bad input.
            """
            from . import web_server as _self_module

            if scope == "global":
                return _self_module._GLOBAL_BLOCKS_PATH, None
            if scope == "project":
                ctx = _resolve_project_context(project_root)
                return Path(ctx["root"]) / ".holdspeak" / "blocks.yaml", dict(ctx)
            raise ValueError(f"scope must be 'global' or 'project', got {scope!r}")

        @app.get("/api/dictation/project-context")
        async def api_dictation_project_context(project_root: Optional[str] = None) -> Any:
            """Validate and describe the active/manual dictation project root."""
            try:
                project = _resolve_project_context(project_root)
            except ValueError as exc:
                return JSONResponse({"error": str(exc)}, status_code=400 if project_root else 404)
            root = Path(project["root"])
            return JSONResponse(
                {
                    "project": project,
                    "paths": {
                        "blocks": str(root / ".holdspeak" / "blocks.yaml"),
                        "project_kb": str(root / ".holdspeak" / "project.yaml"),
                    },
                }
            )

        def _read_blocks_document(path: Path) -> tuple[dict[str, Any], bool]:
            """Read `path` as a raw YAML mapping; return empty default if missing."""
            import yaml

            if not path.exists():
                return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, False
            raw = path.read_text(encoding="utf-8")
            data = yaml.safe_load(raw)
            if data is None:
                return {"version": 1, "default_match_confidence": 0.6, "blocks": []}, True
            if not isinstance(data, dict):
                raise ValueError(
                    f"{path}: top-level YAML must be a mapping, got {type(data).__name__}"
                )
            data.setdefault("version", 1)
            data.setdefault("default_match_confidence", 0.6)
            data.setdefault("blocks", [])
            return data, True

        _STARTER_BLOCK_TEMPLATES: tuple[dict[str, Any], ...] = (
            {
                "id": "ai_prompt_context",
                "title": "AI prompt context",
                "description": "Append the selected project name and clear instruction context to AI-assistant prompts.",
                "sample_utterance": "help me design the settings panel",
                "requires_project": True,
                "block": {
                    "id": "ai_prompt_context",
                    "description": "User is dictating a prompt for an AI assistant and wants project context attached.",
                    "match": {
                        "examples": [
                            "Claude help me write a function for this project",
                            "build a prompt for the settings panel",
                            "ask the assistant to debug this module",
                        ],
                        "negative_examples": ["remind me to buy milk"],
                        "threshold": 0.7,
                    },
                    "inject": {
                        "mode": "append",
                        "template": "\n\nProject: {project.name}\nUse the selected project's constraints and local context when answering.",
                    },
                },
            },
            {
                "id": "action_item",
                "title": "Action item",
                "description": "Turn short task dictation into a consistent action-item line.",
                "sample_utterance": "follow up with Sam about the launch checklist",
                "requires_project": False,
                "block": {
                    "id": "action_item",
                    "description": "User is capturing a task or follow-up item.",
                    "match": {
                        "examples": [
                            "follow up with Sam about the launch checklist",
                            "remember to review the pull request",
                            "make a task to update the docs",
                        ],
                        "negative_examples": ["write a paragraph about the architecture"],
                        "threshold": 0.7,
                    },
                    "inject": {
                        "mode": "replace",
                        "template": "Action item: {raw_text}",
                    },
                },
            },
            {
                "id": "concise_note",
                "title": "Concise note",
                "description": "Format quick thoughts as a clean note that is easy to scan later.",
                "sample_utterance": "the retry worker should surface its next scheduled run",
                "requires_project": False,
                "block": {
                    "id": "concise_note",
                    "description": "User is dictating a concise note or implementation observation.",
                    "match": {
                        "examples": [
                            "note that the retry worker needs a status line",
                            "capture this implementation idea",
                            "write down this design concern",
                        ],
                        "negative_examples": ["send an email to Alex"],
                        "threshold": 0.7,
                    },
                    "inject": {
                        "mode": "replace",
                        "template": "Note: {raw_text}",
                    },
                },
            },
            {
                "id": "code_review_focus",
                "title": "Code review focus",
                "description": "Append a review rubric for correctness, edge cases, and tests.",
                "sample_utterance": "review the queue processing change",
                "requires_project": False,
                "block": {
                    "id": "code_review_focus",
                    "description": "User is dictating a code-review request.",
                    "match": {
                        "examples": [
                            "review the queue processing change",
                            "look over this implementation for bugs",
                            "check this diff for edge cases",
                        ],
                        "negative_examples": ["start a meeting recording"],
                        "threshold": 0.7,
                    },
                    "inject": {
                        "mode": "append",
                        "template": "\n\nReview focus: correctness, edge cases, regressions, and missing tests.",
                    },
                },
            },
        )
        _STARTER_PROJECT_KB: dict[str, Any] = {
            "stack": None,
            "task_focus": None,
            "constraints": None,
        }

        def _starter_template(template_id: str) -> Optional[dict[str, Any]]:
            for template in _STARTER_BLOCK_TEMPLATES:
                if template["id"] == template_id:
                    return deepcopy(template)
            return None

        def _serialize_intent(intent: Any) -> Optional[dict[str, Any]]:
            if intent is None:
                return None
            return {
                "matched": bool(getattr(intent, "matched", False)),
                "block_id": getattr(intent, "block_id", None),
                "confidence": float(getattr(intent, "confidence", 0.0)),
                "raw_label": getattr(intent, "raw_label", None),
                "extras": dict(getattr(intent, "extras", {}) or {}),
            }

        def _serialize_stage_result(result: Any) -> dict[str, Any]:
            return {
                "stage_id": str(getattr(result, "stage_id", "")),
                "elapsed_ms": float(getattr(result, "elapsed_ms", 0.0)),
                "intent": _serialize_intent(getattr(result, "intent", None)),
                "warnings": list(getattr(result, "warnings", []) or []),
                "metadata": dict(getattr(result, "metadata", {}) or {}),
                "text": str(getattr(result, "text", "")),
            }

        def _run_dictation_dry_run_text(
            text: str,
            project_root_override: Optional[str],
        ) -> dict[str, Any]:
            """Execute the browser dry-run path for already-validated text."""
            from .config import Config
            from .plugins.dictation.assembly import build_pipeline
            from .plugins.dictation.contracts import Utterance

            cfg = Config.load().dictation
            try:
                project = _resolve_project_context(project_root_override)
            except ValueError:
                if project_root_override:
                    raise
                project = None
            project_root = Path(project["root"]) if project else None

            if not cfg.pipeline.enabled:
                return {
                    "project": dict(project) if project else None,
                    "runtime_status": "disabled",
                    "runtime_detail": "dictation pipeline disabled (opt-in)",
                    "blocks_count": 0,
                    "stages": [],
                    "final_text": text,
                    "total_elapsed_ms": 0.0,
                    "warnings": ["dictation pipeline disabled"],
                }

            result = build_pipeline(
                cfg,
                project_root=project_root,
                global_blocks_path=_GLOBAL_BLOCKS_PATH,
            )
            run = result.pipeline.run(
                Utterance(
                    raw_text=text,
                    audio_duration_s=0.0,
                    transcribed_at=datetime.now(),
                    project=project,
                )
            )
            return {
                "project": dict(project) if project else None,
                "runtime_status": result.runtime_status,
                "runtime_detail": result.runtime_detail,
                "blocks_count": len(result.blocks.blocks),
                "stages": [_serialize_stage_result(sr) for sr in run.stage_results],
                "final_text": run.final_text,
                "total_elapsed_ms": float(run.total_elapsed_ms),
                "warnings": list(run.warnings),
            }

        def _unique_block_id(base_id: str, document: dict[str, Any]) -> str:
            existing = {
                b.get("id")
                for b in document.get("blocks", [])
                if isinstance(b, dict)
            }
            if base_id not in existing:
                return base_id
            index = 2
            while f"{base_id}_{index}" in existing:
                index += 1
            return f"{base_id}_{index}"

        def _block_summary(path: Path) -> dict[str, Any]:
            from .plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

            if not path.exists():
                return {
                    "path": str(path),
                    "exists": False,
                    "valid": True,
                    "count": 0,
                    "error": None,
                }
            try:
                loaded = load_blocks_yaml(path)
            except BlockConfigError as exc:
                return {
                    "path": str(path),
                    "exists": True,
                    "valid": False,
                    "count": 0,
                    "error": str(exc),
                }
            return {
                "path": str(path),
                "exists": True,
                "valid": True,
                "count": len(loaded.blocks),
                "error": None,
            }

        @app.get("/api/dictation/block-templates")
        async def api_dictation_block_templates() -> Any:
            return JSONResponse(
                {
                    "templates": [
                        {
                            "id": template["id"],
                            "title": template["title"],
                            "description": template["description"],
                            "sample_utterance": template["sample_utterance"],
                            "requires_project": template["requires_project"],
                            "block": deepcopy(template["block"]),
                        }
                        for template in _STARTER_BLOCK_TEMPLATES
                    ]
                }
            )

        def _runtime_readiness(cfg: Any) -> dict[str, Any]:
            from .plugins.dictation import runtime as runtime_module
            from .plugins.dictation.runtime_counters import get_counters, get_session_status

            if not cfg.pipeline.enabled:
                return {
                    "status": "disabled",
                    "requested_backend": cfg.runtime.backend,
                    "resolved_backend": None,
                    "detail": "dictation pipeline disabled",
                    "model_path": None,
                    "model_exists": False,
                    "counters": get_counters(),
                    "session": get_session_status(),
                }

            try:
                resolved_backend, reason = runtime_module.resolve_backend(cfg.runtime.backend)
            except runtime_module.RuntimeUnavailableError as exc:
                from .plugins.dictation.guidance import runtime_guidance

                return {
                    "status": "unavailable",
                    "requested_backend": cfg.runtime.backend,
                    "resolved_backend": None,
                    "detail": str(exc),
                    "model_path": None,
                    "model_exists": False,
                    "guidance": runtime_guidance(
                        kind="unavailable",
                        requested_backend=cfg.runtime.backend,
                    ),
                    "counters": get_counters(),
                    "session": get_session_status(),
                }

            model_path = Path(
                cfg.runtime.mlx_model
                if resolved_backend == "mlx"
                else cfg.runtime.llama_cpp_model_path
            ).expanduser()
            model_exists = model_path.exists()
            guidance = None
            if not model_exists:
                from .plugins.dictation.guidance import runtime_guidance

                guidance = runtime_guidance(
                    kind="missing_model",
                    requested_backend=cfg.runtime.backend,
                    resolved_backend=resolved_backend,
                    model_path=model_path,
                )
            return {
                "status": "available" if model_exists else "missing_model",
                "requested_backend": cfg.runtime.backend,
                "resolved_backend": resolved_backend,
                "detail": reason if model_exists else f"model file missing at {model_path}",
                "model_path": str(model_path),
                "model_exists": model_exists,
                "guidance": guidance,
                "counters": get_counters(),
                "session": get_session_status(),
            }

        @app.get("/api/dictation/readiness")
        async def api_dictation_readiness(project_root: Optional[str] = None) -> Any:
            """Return one browser-facing readiness snapshot for dictation setup."""
            from .config import Config
            from .plugins.dictation.project_kb import ProjectKBError, kb_path_for, read_project_kb

            cfg = Config.load().dictation
            warnings: list[dict[str, Any]] = []

            project: Optional[dict[str, Any]]
            project_error: Optional[str] = None
            try:
                project = _resolve_project_context(project_root)
            except ValueError as exc:
                if project_root:
                    return JSONResponse({"error": str(exc)}, status_code=400)
                project = None
                project_error = str(exc)

            global_path, _ = _resolve_blocks_target("global")
            global_blocks = _block_summary(global_path)

            project_blocks: Optional[dict[str, Any]] = None
            project_root_path: Optional[Path] = None
            if project is not None:
                project_root_path = Path(project["root"])
                project_blocks = _block_summary(project_root_path / ".holdspeak" / "blocks.yaml")

            resolved_blocks = (
                project_blocks
                if project_blocks is not None and project_blocks["exists"]
                else global_blocks
            )
            resolved_scope = (
                "project"
                if project_blocks is not None and project_blocks["exists"]
                else "global"
            )

            kb_payload: dict[str, Any] = {
                "path": None,
                "exists": False,
                "valid": True,
                "keys": [],
                "error": None,
            }
            if project_root_path is not None:
                kb_path = kb_path_for(project_root_path)
                kb_payload["path"] = str(kb_path)
                kb_payload["exists"] = kb_path.exists()
                try:
                    kb = read_project_kb(project_root_path)
                    kb_payload["keys"] = sorted((kb or {}).keys())
                except ProjectKBError as exc:
                    kb_payload["valid"] = False
                    kb_payload["error"] = str(exc)

            runtime_payload = _runtime_readiness(cfg)

            if not cfg.pipeline.enabled:
                warnings.append({
                    "code": "pipeline_disabled",
                    "message": "Dictation pipeline is disabled.",
                    "action": "Enable the dictation pipeline from Runtime.",
                    "section": "runtime",
                    "runtime_action": "enable_pipeline",
                })
            if project is None:
                warnings.append({
                    "code": "no_project",
                    "message": project_error or "No project root detected.",
                    "action": "Set a project root override or launch holdspeak from a project directory.",
                    "section": "readiness",
                })
            if not resolved_blocks["exists"] or int(resolved_blocks["count"]) == 0:
                warnings.append({
                    "code": "no_blocks",
                    "message": "No dictation blocks are loaded for the selected project.",
                    "action": "Create the Action item starter and run its sample.",
                    "section": "blocks",
                    "template_id": "action_item",
                    "template_action": "create_dry_run",
                    "template_scope": "project" if project is not None else "global",
                })
            if not global_blocks["valid"] or (project_blocks is not None and not project_blocks["valid"]):
                warnings.append({
                    "code": "invalid_blocks",
                    "message": "A blocks.yaml file is invalid.",
                    "action": "Open Blocks and fix the validation error.",
                    "section": "blocks",
                })
            if project is not None and not kb_payload["exists"]:
                warnings.append({
                    "code": "missing_project_kb",
                    "message": "Project KB file is missing.",
                    "action": "Create a starter Project KB file.",
                    "section": "kb",
                    "kb_action": "create_starter",
                })
            if not kb_payload["valid"]:
                warnings.append({
                    "code": "invalid_project_kb",
                    "message": "Project KB file is invalid.",
                    "action": "Open Project KB and fix the validation error.",
                    "section": "kb",
                })
            if runtime_payload["status"] == "unavailable":
                warnings.append({
                    "code": "runtime_unavailable",
                    "message": runtime_payload["detail"],
                    "action": "Install the selected runtime extra or change backend.",
                    "section": "runtime",
                    "guidance": runtime_payload.get("guidance"),
                })
            elif runtime_payload["status"] == "missing_model":
                warnings.append({
                    "code": "runtime_model_missing",
                    "message": runtime_payload["detail"],
                    "action": "Download the model or update the runtime model path.",
                    "section": "runtime",
                    "guidance": runtime_payload.get("guidance"),
                })

            ready = (
                cfg.pipeline.enabled
                and project is not None
                and bool(resolved_blocks["valid"])
                and int(resolved_blocks["count"]) > 0
                and bool(kb_payload["valid"])
                and runtime_payload["status"] == "available"
            )

            return JSONResponse(
                {
                    "ready": ready,
                    "project": project,
                    "config": {
                        "pipeline_enabled": cfg.pipeline.enabled,
                        "max_total_latency_ms": cfg.pipeline.max_total_latency_ms,
                        "backend": cfg.runtime.backend,
                    },
                    "blocks": {
                        "global": global_blocks,
                        "project": project_blocks,
                        "resolved_scope": resolved_scope,
                        "resolved": resolved_blocks,
                    },
                    "project_kb": kb_payload,
                    "runtime": runtime_payload,
                    "warnings": warnings,
                }
            )

        @app.get("/api/dictation/blocks")
        async def api_dictation_blocks_list(
            scope: str = "global",
            project_root: Optional[str] = None,
        ) -> Any:
            from .plugins.dictation.blocks import BlockConfigError, load_blocks_yaml

            try:
                path, project = _resolve_blocks_target(scope, project_root)
            except ValueError as exc:
                status = 404 if "no project detected" in str(exc) else 400
                return JSONResponse({"error": str(exc)}, status_code=status)
            try:
                document, exists = _read_blocks_document(path)
                if exists:
                    load_blocks_yaml(path)  # validate, surface errors to UI
            except BlockConfigError as exc:
                return JSONResponse(
                    {"error": str(exc), "scope": scope, "path": str(path)},
                    status_code=422,
                )
            except Exception as exc:
                log.error(f"Failed to read blocks document: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)
            return JSONResponse(
                {
                    "scope": scope,
                    "path": str(path),
                    "exists": exists,
                    "project": project,
                    "document": document,
                }
            )

        @app.post("/api/dictation/blocks")
        async def api_dictation_blocks_create(
            payload: dict[str, Any],
            scope: str = "global",
            project_root: Optional[str] = None,
        ) -> Any:
            from .plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

            block = payload.get("block") if isinstance(payload, dict) else None
            if not isinstance(block, dict):
                return JSONResponse(
                    {"error": "request body must be {'block': {...}}"},
                    status_code=400,
                )
            try:
                path, _project = _resolve_blocks_target(scope, project_root)
            except ValueError as exc:
                status = 404 if "no project detected" in str(exc) else 400
                return JSONResponse({"error": str(exc)}, status_code=status)

            try:
                document, _exists = _read_blocks_document(path)
            except Exception as exc:
                log.error(f"Failed to read blocks document: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)

            new_id = block.get("id")
            existing_ids = {b.get("id") for b in document["blocks"] if isinstance(b, dict)}
            if new_id in existing_ids:
                return JSONResponse(
                    {"error": f"block id {new_id!r} already exists"},
                    status_code=409,
                )
            document["blocks"].append(block)
            try:
                save_blocks_yaml(path, document)
            except BlockConfigError as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            return JSONResponse(
                {"scope": scope, "path": str(path), "document": document},
                status_code=201,
            )

        @app.post("/api/dictation/blocks/from-template")
        async def api_dictation_blocks_create_from_template(
            payload: dict[str, Any],
            scope: str = "global",
            project_root: Optional[str] = None,
        ) -> Any:
            from .plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

            template_id = payload.get("template_id") if isinstance(payload, dict) else None
            if not isinstance(template_id, str) or not template_id.strip():
                return JSONResponse(
                    {"error": "request body must include template_id"},
                    status_code=400,
                )
            template = _starter_template(template_id.strip())
            if template is None:
                return JSONResponse(
                    {"error": f"unknown starter template {template_id!r}"},
                    status_code=404,
                )
            run_dry_run = bool(payload.get("dry_run", False))
            if "dry_run" in payload and not isinstance(payload.get("dry_run"), bool):
                return JSONResponse(
                    {"error": "dry_run must be a boolean when provided"},
                    status_code=400,
                )
            try:
                path, project = _resolve_blocks_target(scope, project_root)
            except ValueError as exc:
                status = 404 if "no project detected" in str(exc) else 400
                return JSONResponse({"error": str(exc)}, status_code=status)
            if run_dry_run and project_root:
                try:
                    _resolve_project_context(project_root)
                except ValueError as exc:
                    return JSONResponse({"error": str(exc)}, status_code=400)

            requested_block_id = payload.get("block_id") if isinstance(payload, dict) else None
            if requested_block_id is not None and not isinstance(requested_block_id, str):
                return JSONResponse(
                    {"error": "block_id must be a string when provided"},
                    status_code=400,
                )
            try:
                document, _exists = _read_blocks_document(path)
            except Exception as exc:
                log.error(f"Failed to read blocks document: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)

            block = deepcopy(template["block"])
            base_id = (requested_block_id or block["id"]).strip()
            if not base_id:
                return JSONResponse({"error": "block_id cannot be empty"}, status_code=400)
            block["id"] = _unique_block_id(base_id, document)
            document["blocks"].append(block)
            try:
                save_blocks_yaml(path, document)
            except BlockConfigError as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            response_payload = {
                "scope": scope,
                "path": str(path),
                "project": project,
                "template": {
                    "id": template["id"],
                    "title": template["title"],
                    "sample_utterance": template["sample_utterance"],
                },
                "block": block,
                "document": document,
            }
            if run_dry_run:
                try:
                    dry_run = _run_dictation_dry_run_text(
                        str(template["sample_utterance"]),
                        project_root,
                    )
                except ValueError as exc:
                    return JSONResponse({"error": str(exc)}, status_code=400)
                except Exception as exc:
                    log.error(f"Template dry-run failed: {exc}")
                    return JSONResponse({"error": str(exc)}, status_code=500)
                dry_run["created_block_id"] = block["id"]
                dry_run["template_id"] = template["id"]
                dry_run["template_title"] = template["title"]
                dry_run["sample_utterance"] = template["sample_utterance"]
                response_payload["dry_run"] = dry_run
            return JSONResponse(response_payload, status_code=201)

        @app.put("/api/dictation/blocks/{block_id}")
        async def api_dictation_blocks_update(
            block_id: str,
            payload: dict[str, Any],
            scope: str = "global",
            project_root: Optional[str] = None,
        ) -> Any:
            from .plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

            block = payload.get("block") if isinstance(payload, dict) else None
            if not isinstance(block, dict):
                return JSONResponse(
                    {"error": "request body must be {'block': {...}}"},
                    status_code=400,
                )
            try:
                path, _project = _resolve_blocks_target(scope, project_root)
            except ValueError as exc:
                status = 404 if "no project detected" in str(exc) else 400
                return JSONResponse({"error": str(exc)}, status_code=status)
            if not path.exists():
                return JSONResponse(
                    {"error": f"no blocks file at {path}"},
                    status_code=404,
                )
            try:
                document, _exists = _read_blocks_document(path)
            except Exception as exc:
                log.error(f"Failed to read blocks document: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)

            blocks = document["blocks"]
            target_idx = next(
                (i for i, b in enumerate(blocks) if isinstance(b, dict) and b.get("id") == block_id),
                None,
            )
            if target_idx is None:
                return JSONResponse(
                    {"error": f"unknown block id {block_id!r}"},
                    status_code=404,
                )
            new_id = block.get("id", block_id)
            if new_id != block_id and any(
                isinstance(b, dict) and b.get("id") == new_id for b in blocks
            ):
                return JSONResponse(
                    {"error": f"block id {new_id!r} already exists"},
                    status_code=409,
                )
            blocks[target_idx] = block
            try:
                save_blocks_yaml(path, document)
            except BlockConfigError as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            return JSONResponse(
                {"scope": scope, "path": str(path), "document": document}
            )

        @app.delete("/api/dictation/blocks/{block_id}")
        async def api_dictation_blocks_delete(
            block_id: str,
            scope: str = "global",
            project_root: Optional[str] = None,
        ) -> Any:
            from .plugins.dictation.blocks import BlockConfigError, save_blocks_yaml

            try:
                path, _project = _resolve_blocks_target(scope, project_root)
            except ValueError as exc:
                status = 404 if "no project detected" in str(exc) else 400
                return JSONResponse({"error": str(exc)}, status_code=status)
            if not path.exists():
                return JSONResponse(
                    {"error": f"no blocks file at {path}"},
                    status_code=404,
                )
            try:
                document, _exists = _read_blocks_document(path)
            except Exception as exc:
                log.error(f"Failed to read blocks document: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)
            blocks = document["blocks"]
            kept = [b for b in blocks if not (isinstance(b, dict) and b.get("id") == block_id)]
            if len(kept) == len(blocks):
                return JSONResponse(
                    {"error": f"unknown block id {block_id!r}"},
                    status_code=404,
                )
            document["blocks"] = kept
            try:
                save_blocks_yaml(path, document)
            except BlockConfigError as exc:
                # save_blocks_yaml requires at least one block; an empty list is
                # rejected by `_build_match`/`blocks` shape rules. Surface the
                # 422 to the caller — they should DELETE-then-recreate or use
                # a "deactivate" toggle (out of scope for v1).
                return JSONResponse({"error": str(exc)}, status_code=422)
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            return JSONResponse(
                {"scope": scope, "path": str(path), "document": document}
            )

        # ── Project KB endpoints (WFS-CFG-003) ─────────────────────────────

        @app.get("/api/dictation/project-kb")
        async def api_dictation_project_kb_get(project_root: Optional[str] = None) -> Any:
            from .plugins.dictation.project_kb import ProjectKBError, read_project_kb

            try:
                ctx = _resolve_project_context(project_root)
            except ValueError as exc:
                if project_root:
                    return JSONResponse({"error": str(exc)}, status_code=400)
                return JSONResponse({
                    "detected": None,
                    "kb": None,
                    "kb_path": None,
                    "message": f"no project root detected from cwd={Path.cwd()}",
                })
            root = Path(ctx["root"])
            try:
                kb = read_project_kb(root)
            except ProjectKBError as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
            return JSONResponse({
                "detected": dict(ctx),
                "kb": kb,
                "kb_path": str(root / ".holdspeak" / "project.yaml"),
            })

        @app.put("/api/dictation/project-kb")
        async def api_dictation_project_kb_put(
            payload: dict[str, Any],
            project_root: Optional[str] = None,
        ) -> Any:
            from .plugins.dictation.project_kb import (
                ProjectKBError,
                kb_path_for,
                read_project_kb,
                write_project_kb,
            )

            kb = payload.get("kb") if isinstance(payload, dict) else None
            if not isinstance(kb, dict):
                return JSONResponse(
                    {"error": "request body must be {'kb': {<key>: <value>, ...}}"},
                    status_code=400,
                )
            try:
                ctx = _resolve_project_context(project_root)
            except ValueError as exc:
                return JSONResponse(
                    {"error": str(exc)},
                    status_code=400 if project_root else 404,
                )
            root = Path(ctx["root"])
            try:
                write_project_kb(root, kb)
            except ProjectKBError as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            try:
                fresh_kb = read_project_kb(root)
            except ProjectKBError as exc:
                return JSONResponse({"error": str(exc)}, status_code=500)
            # Re-detect so the caller sees the upgraded anchor signal
            # when this PUT just created `<root>/.holdspeak/`.
            redetected = _resolve_project_context(project_root) if project_root else ctx
            return JSONResponse({
                "detected": dict(redetected),
                "kb": fresh_kb,
                "kb_path": str(kb_path_for(root)),
            })

        @app.post("/api/dictation/project-kb/starter")
        async def api_dictation_project_kb_starter(project_root: Optional[str] = None) -> Any:
            from .plugins.dictation.project_kb import (
                ProjectKBError,
                kb_path_for,
                read_project_kb,
                write_project_kb,
            )

            try:
                ctx = _resolve_project_context(project_root)
            except ValueError as exc:
                return JSONResponse(
                    {"error": str(exc)},
                    status_code=400 if project_root else 404,
                )
            root = Path(ctx["root"])
            path = kb_path_for(root)
            if path.exists():
                return JSONResponse(
                    {"error": f"project KB already exists at {path}"},
                    status_code=409,
                )
            try:
                write_project_kb(root, _STARTER_PROJECT_KB)
            except ProjectKBError as exc:
                return JSONResponse({"error": str(exc)}, status_code=422)
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            try:
                fresh_kb = read_project_kb(root)
            except ProjectKBError as exc:
                return JSONResponse({"error": str(exc)}, status_code=500)
            redetected = _resolve_project_context(project_root) if project_root else ctx
            return JSONResponse(
                {
                    "detected": dict(redetected),
                    "kb": fresh_kb,
                    "kb_path": str(path),
                    "starter": True,
                },
                status_code=201,
            )

        @app.delete("/api/dictation/project-kb")
        async def api_dictation_project_kb_delete(project_root: Optional[str] = None) -> Any:
            from .plugins.dictation.project_kb import delete_project_kb

            try:
                ctx = _resolve_project_context(project_root)
            except ValueError as exc:
                return JSONResponse(
                    {"error": str(exc)},
                    status_code=400 if project_root else 404,
                )
            root = Path(ctx["root"])
            removed = delete_project_kb(root)
            if not removed:
                return JSONResponse(
                    {"error": f"no project.yaml at {root / '.holdspeak' / 'project.yaml'}"},
                    status_code=404,
                )
            if self.on_dictation_config_changed is not None:
                try:
                    self.on_dictation_config_changed()
                except Exception as exc:
                    log.error(f"on_dictation_config_changed failed: {exc}")
            return JSONResponse({"detected": dict(ctx), "kb": None, "kb_path": None})

        # ── Dictation dry-run endpoint (WFS-CFG-005) ───────────────────────

        @app.post("/api/dictation/dry-run")
        async def api_dictation_dry_run(payload: dict[str, Any]) -> Any:
            utterance = payload.get("utterance") if isinstance(payload, dict) else None
            if not isinstance(utterance, str):
                return JSONResponse(
                    {
                        "error": "utterance must be a string",
                        "detail": {"utterance": "required string"},
                    },
                    status_code=400,
                )
            text = utterance.strip()
            if not text:
                return JSONResponse(
                    {
                        "error": "utterance must not be empty",
                        "detail": {"utterance": "must not be empty"},
                    },
                    status_code=400,
                )
            project_root_override = payload.get("project_root") if isinstance(payload, dict) else None
            if project_root_override is not None and not isinstance(project_root_override, str):
                return JSONResponse(
                    {
                        "error": "project_root must be a string when provided",
                        "detail": {"project_root": "optional string path"},
                    },
                    status_code=400,
                )

            try:
                return JSONResponse(_run_dictation_dry_run_text(text, project_root_override))
            except ValueError as exc:
                return JSONResponse({"error": str(exc)}, status_code=400)
            except Exception as exc:
                log.error(f"Dictation dry-run failed: {exc}")
                return JSONResponse({"error": str(exc)}, status_code=500)

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
