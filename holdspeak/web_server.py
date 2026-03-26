"""Meeting web server for HoldSpeak.

Provides a per-meeting FastAPI server with HTTP endpoints and a WebSocket for
real-time updates.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import socket
import threading
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from .logging_config import get_logger

log = get_logger("web_server")

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


class _UpdateMeetingRequest(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None


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
        on_update_action_item: Optional[Callable[[str, str], Any]] = None,
        on_set_title: Optional[Callable[[str], None]] = None,
        on_set_tags: Optional[Callable[[list[str]], None]] = None,
        host: str = "127.0.0.1",
    ) -> None:
        if _IMPORT_ERROR is not None:
            raise RuntimeError(
                "MeetingWebServer requires FastAPI + uvicorn. "
                "Install dependencies: `pip install fastapi uvicorn`."
            ) from _IMPORT_ERROR

        self.on_bookmark = on_bookmark
        self.on_stop = on_stop
        self.get_state = get_state
        self.on_update_action_item = on_update_action_item
        self.on_set_title = on_set_title
        self.on_set_tags = on_set_tags
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

        @app.post("/api/stop")
        async def api_stop(_: Optional[_StopRequest] = None) -> Any:
            try:
                result = self.on_stop()
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

        @app.patch("/api/meeting")
        async def api_update_meeting(payload: _UpdateMeetingRequest) -> Any:
            """Update meeting title and/or tags."""
            try:
                if payload.title is not None and self.on_set_title is not None:
                    self.on_set_title(payload.title)
                if payload.tags is not None and self.on_set_tags is not None:
                    self.on_set_tags(payload.tags)
                return JSONResponse({"success": True})
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
                            "meeting_id": item.meeting_id,
                            "meeting_title": item.meeting_title,
                            "meeting_date": item.meeting_date.isoformat(),
                            "created_at": item.created_at.isoformat(),
                            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
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
            item_id: str, payload: _ActionItemUpdateRequest
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
                return JSONResponse({"success": True})
            except Exception as e:
                log.error(f"Failed to update action item: {e}")
                return JSONResponse(
                    {"success": False, "error": str(e)}, status_code=500
                )

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
