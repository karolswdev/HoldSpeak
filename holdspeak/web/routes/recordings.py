"""Recordings transport (2026-10-28); the work is :mod:`holdspeak.recordings.service`.

GET  /api/recordings                    the rows, the usage, the link bases, the encoder
POST /api/recordings                    {width, height, voice, project_id?, view?}: start
POST /api/recordings/folder/open        open the recordings folder (Finder)
GET  /api/recordings/{id}               one row
POST /api/recordings/{id}/chunks        one chunk (the raw body), appended
POST /api/recordings/{id}/stop          end the capture; the encode starts
POST /api/recordings/{id}/retry         encode a failed one again
POST /api/recordings/{id}/share         a new share token
POST /api/recordings/{id}/unshare       Stop sharing
POST /api/recordings/{id}/park          move it to recordings/_parked/
GET  /api/recordings/{id}/video         the video (the desk's Play; owner token)
GET  /api/recordings/{id}/poster        the poster frame (owner token)
GET  /r/{id}/{token}/{name}             the shared link: no hub token; Range (Safari)

Every handler that touches the disk or a process runs in the threadpool.
"""
from __future__ import annotations

import subprocess
import sys
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ...recordings.service import RECORDINGS
from ...recordings.store import RecordingRefused
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.recordings")

_MEDIA = {"mp4": "video/mp4", "webm": "video/webm"}


def _refused(exc: RecordingRefused) -> JSONResponse:
    return JSONResponse({"error": exc.detail, "reason": exc.code}, status_code=exc.status)


def _port(request: Request) -> int | None:
    server = request.scope.get("server")
    if isinstance(server, (tuple, list)) and len(server) > 1 and server[1]:
        return int(server[1])
    return request.url.port


async def _json(request: Request) -> dict[str, Any]:
    try:
        body = await request.json()
    except Exception:
        return {}
    return body if isinstance(body, dict) else {}


def _open_folder(path: str) -> None:
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.run([opener, path], check=False, timeout=10,
                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wire_recordings(ctx: WebContext) -> None:
    RECORDINGS.configure(broadcast=lambda kind, data: (ctx.broadcast or (lambda *_: None))(kind, data))


def build_recordings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    wire_recordings(ctx)

    def act(fn: Any, *args: Any, status: int = 200, **kwargs: Any) -> Any:
        try:
            return JSONResponse(fn(*args, **kwargs), status_code=status)
        except RecordingRefused as exc:
            return _refused(exc)

    @router.get("/api/recordings")
    async def api_recordings(request: Request) -> Any:
        port = _port(request)

        def read() -> dict[str, Any]:
            RECORDINGS.remember_bases(port=port)
            return RECORDINGS.payload()

        try:
            return JSONResponse(await run_in_threadpool(read))
        except Exception as exc:
            return error_500(exc, log, "Failed to read recordings")

    @router.post("/api/recordings")
    async def api_recording_start(request: Request) -> Any:
        body = await _json(request)
        port = _port(request)

        def start() -> Any:
            RECORDINGS.remember_bases(port=port)
            return act(
                RECORDINGS.start,
                width=int(body.get("width") or 0), height=int(body.get("height") or 0),
                voice=bool(body.get("voice")), project_id=str(body.get("project_id") or ""),
                view=str(body.get("view") or ""), status=201,
            )

        return await run_in_threadpool(start)

    @router.post("/api/recordings/folder/open")
    async def api_recordings_open_folder() -> Any:
        def open_it() -> dict[str, Any]:
            root = RECORDINGS.store.root()
            root.mkdir(parents=True, exist_ok=True)
            _open_folder(str(root))
            return {"opened": True, "folder": str(root)}

        try:
            return JSONResponse(await run_in_threadpool(open_it))
        except Exception as exc:
            return error_500(exc, log, "Failed to open the recordings folder")

    @router.get("/api/recordings/{recording_id}")
    async def api_recording_get(recording_id: str) -> Any:
        return await run_in_threadpool(act, RECORDINGS.get, recording_id)

    @router.post("/api/recordings/{recording_id}/chunks")
    async def api_recording_chunk(recording_id: str, request: Request) -> Any:
        data = await request.body()
        return await run_in_threadpool(act, RECORDINGS.chunk, recording_id, data)

    @router.post("/api/recordings/{recording_id}/stop")
    async def api_recording_stop(recording_id: str) -> Any:
        return await run_in_threadpool(act, RECORDINGS.stop, recording_id)

    @router.post("/api/recordings/{recording_id}/retry")
    async def api_recording_retry(recording_id: str) -> Any:
        return await run_in_threadpool(act, RECORDINGS.retry, recording_id)

    @router.post("/api/recordings/{recording_id}/share")
    async def api_recording_share(recording_id: str) -> Any:
        return await run_in_threadpool(act, RECORDINGS.share, recording_id)

    @router.post("/api/recordings/{recording_id}/unshare")
    async def api_recording_unshare(recording_id: str) -> Any:
        return await run_in_threadpool(act, RECORDINGS.unshare, recording_id)

    @router.post("/api/recordings/{recording_id}/park")
    async def api_recording_park(recording_id: str) -> Any:
        return await run_in_threadpool(act, RECORDINGS.park, recording_id)

    def _video(recording_id: str) -> Any:
        rec = RECORDINGS.store.get(recording_id)
        if rec is None or rec.state != "ready":
            return Response(status_code=404)
        path = RECORDINGS.store.video_path(rec)
        if not path.is_file():
            return Response(status_code=404)
        return FileResponse(path, media_type=_MEDIA.get(rec.encoder, "video/mp4"))

    @router.get("/api/recordings/{recording_id}/video")
    async def api_recording_video(recording_id: str) -> Any:
        return await run_in_threadpool(_video, recording_id)

    @router.get("/api/recordings/{recording_id}/poster")
    async def api_recording_poster(recording_id: str) -> Any:
        def poster() -> Any:
            try:
                path = RECORDINGS.store.poster_path(recording_id)
            except RecordingRefused:
                return Response(status_code=404)
            return FileResponse(path, media_type="image/jpeg") if path.is_file() else Response(status_code=404)

        return await run_in_threadpool(poster)

    @router.get("/r/{recording_id}/{token}/{name}")
    async def shared_recording(recording_id: str, token: str, name: str) -> Any:
        """The link he opens on the phone: the share token is the only key."""

        def shared() -> Any:
            rec = RECORDINGS.store.by_share(recording_id, token)
            if rec is None or name != rec.video_name():
                return Response(status_code=404)
            path = RECORDINGS.store.video_path(rec)
            if not path.is_file():
                return Response(status_code=404)
            return FileResponse(
                path,
                media_type=_MEDIA.get(rec.encoder, "video/mp4"),
                headers={"Cache-Control": "private, max-age=3600"},
            )

        return await run_in_threadpool(shared)

    return router


__all__ = ["build_recordings_router", "wire_recordings"]
