"""Declared hub voice operations; HTTP sends the service's WAV iterator.

The binary transport stays hand-written. TtsService validates text/voice,
checks the Line extra and weights, loads the one engine off the loop and
prepares the first audio chunk before HTTP sends a success header.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...services import tts_service as tts_engine
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router, _principal
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.tts")

def _refusal(exc: ServiceError) -> JSONResponse:
    return JSONResponse(exc.context.get("body") or {"code": exc.code, "message": exc.detail},
                        status_code=int(exc.context.get("status") or 400))


async def _answer(fn: Any, *, status: int = 200) -> Any:
    """The produced routes' envelope: a refusal keeps its typed code and message."""
    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except ServiceError as exc:
        return _refusal(exc)
    except Exception as exc:
        return error_500(exc, log, "Failed to run the voice verb")


def build_tts_router(ctx: WebContext) -> APIRouter:
    """Build the TTS route family (HS-154-01)."""
    router = APIRouter()

    async def tts_speak(request: Request) -> Any:
        principal = _principal(request)
        try:
            registry().authorize(principal, "tts.speak")
            body = await request.json()
        except ServiceError as exc:
            return _refusal(exc)
        except Exception:
            return JSONResponse({"code": "tts_invalid_request", "message": "Expected a JSON body with text."},
                                status_code=400)
        args = {key: body.get(key) for key in ("text", "voice")} if isinstance(body, dict) else {}
        try:
            gen = await run_in_threadpool(lambda: registry().invoke(principal, "tts.speak", args))
            return StreamingResponse(gen, media_type="audio/wav")
        except ServiceError as exc:
            return _refusal(exc)
        except operations.OperationRefused as exc:
            return JSONResponse({"code": exc.code, "message": exc.detail}, status_code=400)

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, tts_service=tts_engine.TtsService)

    mount_router(router, operation_router([d for d in operations.MEDIA_OPERATIONS if d.service == "tts_service"], registry, _answer,
                                          module=__name__, hand_written={"tts.speak": lambda d: tts_speak}))

    return router


__all__ = ["build_tts_router"]
