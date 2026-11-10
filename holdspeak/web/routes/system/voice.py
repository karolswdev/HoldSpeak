"""Voice HTTP operations and the unchanged streaming dictation socket."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .... import operations
from ....services.errors import ServiceError
from ....speech_session import browser_mic_sessions
from ...context import WebContext
from ...operation_routes import operation_router
from .._mount import mount_router
from ..dictation._declared import registry_for, _answer
from .voice_stream import build_voice_stream_router
from .voice_support import _route_principal


def build_voice_router(ctx: WebContext) -> APIRouter:
    router = APIRouter()
    registry = registry_for(ctx)

    async def api_transcribe(request: Request) -> Any:
        principal = _route_principal(request)
        try:
            registry().authorize(principal, "dictation.transcribe")
            raw = await request.body()
            result = await registry().invoke(
                principal,
                "dictation.transcribe",
                {
                    "pipeline": request.query_params.get("pipeline", "").lower()
                    in ("true", "1"),
                    "mic_handle": str(
                        request.query_params.get("mic_session", "") or ""
                    ),
                },
                held={"raw": raw},
            )
            return result
        except ServiceError as exc:
            return JSONResponse(
                exc.context.get("body")
                or {"success": False, "error": exc.detail, "code": exc.code},
                status_code=int(exc.context.get("status") or 400),
            )

    names = {
        "dictation.wake.type",
        "dictation.mic.open",
        "dictation.mic.close",
        "dictation.transcribe",
        "dictation.preview.type",
        "dictation.preview.discard",
        "dictation.command.test",
    }
    mount_router(
        router,
        operation_router(
            [d for d in operations.DICTATION_OPERATIONS if d.name in names],
            registry,
            _answer,
            module=__name__,
            hand_written={"dictation.transcribe": lambda d: api_transcribe},
        ),
    )
    mount_router(
        router, build_voice_stream_router(ctx, sessions=lambda: browser_mic_sessions())
    )
    return router
