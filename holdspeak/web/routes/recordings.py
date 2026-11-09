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

The JSON verbs are produced from ``holdspeak/media_operations.py`` (2026-11-09,
one contract); the chunk (a raw body), the video, the poster and the shared link
(file answers) stay hand-written here. Every handler that touches the disk or a
process runs in the threadpool.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...recordings import service as recordings
from ...recordings.store import RecordingRefused
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.recordings")

_MEDIA = {"mp4": "video/mp4", "webm": "video/webm"}


def _refused(exc: RecordingRefused) -> JSONResponse:
    return JSONResponse({"error": exc.detail, "reason": exc.code}, status_code=exc.status)


def _port(request: Request) -> int | None:
    server = request.scope.get("server")
    if isinstance(server, (tuple, list)) and len(server) > 1 and server[1]:
        return int(server[1])
    return request.url.port


async def _answer(fn: Any, *, status: int = 200) -> Any:
    """The produced routes' envelope: a refusal keeps ``{error, reason}`` and its status."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return JSONResponse(exc.context.get("body") or {"error": exc.detail, "reason": exc.code},
                            status_code=int(exc.context.get("status") or 400))
    except Exception as exc:
        return error_500(exc, log, "Failed to run the recording verb")


def _remember(request: Request) -> None:
    """The two link bases come from the port this request reached (list and start)."""
    recordings.RECORDINGS.remember_bases(port=_port(request))


def wire_recordings(ctx: WebContext) -> None:
    recordings.RECORDINGS.configure(broadcast=lambda kind, data: (ctx.broadcast or (lambda *_: None))(kind, data))


def build_recordings_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    wire_recordings(ctx)

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, recordings_service=lambda: operations.LIVE_RECORDINGS_SERVICE)

    def produced(*names: str) -> APIRouter:
        by_name = {d.name: d for d in operations.MEDIA_OPERATIONS}
        return operation_router([by_name[name] for name in names], registry, _answer, module=__name__)

    # The list and start read the link bases from the request's port first.
    mount_router(router, produced("recordings.list", "recordings.start"), dependencies=[Depends(_remember)])
    mount_router(router, produced("recordings.open_folder", "recordings.get"))

    @router.post("/api/recordings/{recording_id}/chunks")
    async def api_recording_chunk(recording_id: str, request: Request) -> Any:
        data = await request.body()

        def append() -> Any:
            try:
                return JSONResponse(recordings.RECORDINGS.chunk(recording_id, data))
            except RecordingRefused as exc:
                return _refused(exc)

        return await run_in_threadpool(append)

    mount_router(router, produced("recordings.stop", "recordings.retry", "recordings.share", "recordings.unshare",
                                  "recordings.park"))

    def _video(recording_id: str) -> Any:
        rec = recordings.RECORDINGS.store.get(recording_id)
        if rec is None or rec.state != "ready":
            return Response(status_code=404)
        path = recordings.RECORDINGS.store.video_path(rec)
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
                path = recordings.RECORDINGS.store.poster_path(recording_id)
            except RecordingRefused:
                return Response(status_code=404)
            return FileResponse(path, media_type="image/jpeg") if path.is_file() else Response(status_code=404)

        return await run_in_threadpool(poster)

    @router.get("/r/{recording_id}/{token}/{name}")
    async def shared_recording(recording_id: str, token: str, name: str) -> Any:
        """The link he opens on the phone: the share token is the only key."""

        def shared() -> Any:
            rec = recordings.RECORDINGS.store.by_share(recording_id, token)
            if rec is None or name != rec.video_name():
                return Response(status_code=404)
            path = recordings.RECORDINGS.store.video_path(rec)
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
