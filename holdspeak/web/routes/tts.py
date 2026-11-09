"""TTS route: the hub's one voice is the Line's Pocket TTS (HS-154-01, 2026-11-07).

POST /api/tts          -> streaming WAV (404 without the ``line`` extra); hand-written
GET  /api/tts/status   -> produced from ``tts.status`` (``holdspeak/media_operations.py``)
POST /api/tts/download -> produced from ``tts.download`` (egress-badged, receipted)

The engine, its state and the two declared verbs live in
``holdspeak/services/tts_service.py`` (2026-11-09).

The desk and a call speak with the same engine and the same weights:
``holdspeak/line/speech.py`` (``Pocket``, Kyutai Pocket TTS, MIT code,
CC-BY-4.0 weights) and the signed catalogue's TTS preset, fetched by
``holdspeak/line/models.py``. The ``line`` extra is LAZY-IMPORTED: the
base install never pays for it. When it is absent every route answers 404
with a typed code, and the client seam (``web/src/lib/tts.ts``) stays on
the browser voice.

NOTE: Pocket has no speed control. ``speed`` in the request body is
accepted and ignored.
"""
from __future__ import annotations

import struct
from typing import Any, Iterator, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from ... import operations
from ...logging_config import get_logger
from ...services import tts_service as tts_engine
from ...services.errors import ServiceError
from ..context import WebContext
from ..operation_routes import operation_router
from ..runtime_support import error_500
from ._mount import mount_router

log = get_logger("web.routes.tts")

def _wav_header(sample_rate: int, channels: int = 1, bits: int = 16) -> bytes:
    """A WAV header for a stream of unknown length (the sizes are the maximum)."""
    byte_rate = sample_rate * channels * (bits // 8)
    block_align = channels * (bits // 8)
    return struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 0xFFFFFFFF, b"WAVE", b"fmt ", 16, 1, channels,
        sample_rate, byte_rate, block_align, bits, b"data", 0xFFFFFFFF - 36,
    )


def _synthesize_wav(text: str) -> Iterator[bytes]:
    """The WAV header, then the engine's 16-bit PCM chunks as they are made."""
    from ...line.audio import RATE

    engine = tts_engine._get_engine()
    yield _wav_header(RATE)
    for chunk in engine.stream(text):
        yield chunk.astype("<i2", copy=False).tobytes()


def _first_two(gen: Iterator[bytes]) -> tuple[Optional[bytes], Optional[bytes]]:
    """The header and the first audio chunk (loads the engine; off the loop)."""
    header = next(gen, None)
    first = next(gen, None) if header is not None else None
    return header, first


def _not_installed() -> JSONResponse:
    return _refusal(tts_engine.not_installed())


def _not_ready() -> JSONResponse:
    return _refusal(tts_engine.not_ready())


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

    @router.post("/api/tts")
    async def tts_speak(request: Request) -> Any:
        """Synthesize text to streaming WAV audio with the Line's Pocket engine.

        404 ``tts_not_installed`` without the ``line`` extra; 404
        ``tts_model_not_ready`` before the weights are fetched.
        """
        if not await run_in_threadpool(tts_engine._line_installed):
            return _not_installed()
        if not await run_in_threadpool(tts_engine._model_ready):
            return _not_ready()
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"code": "tts_invalid_request", "message": "Expected a JSON body with text."},
                status_code=400,
            )
        text = body.get("text", "") if isinstance(body, dict) else ""
        if not text or not isinstance(text, str):
            return JSONResponse(
                {"code": "tts_invalid_request", "message": "text is required."},
                status_code=400,
            )
        voice = body.get("voice") if isinstance(body, dict) else None
        if voice not in (None, "", tts_engine._voice()):
            return JSONResponse(
                {"code": "tts_invalid_voice", "message": f"Voice {voice} is not available. Use {tts_engine._voice()}."},
                status_code=400,
            )

        gen = _synthesize_wav(text)
        try:
            # Load the engine and make the first chunk off the event loop, so
            # a failure answers 500 before the 200 is sent.
            header, first = await run_in_threadpool(_first_two, gen)
        except Exception:
            log.warning("TTS synthesis failed", exc_info=True)
            header, first = None, None
        if header is None or first is None:
            return JSONResponse(
                {"code": "tts_synthesis_failed", "message": "The voice engine returned no audio."},
                status_code=500,
            )

        def _chain() -> Iterator[bytes]:
            yield header
            yield first
            yield from gen

        # Starlette iterates a sync generator in its thread pool.
        return StreamingResponse(_chain(), media_type="audio/wav")

    def registry() -> operations.OperationRegistry:
        return operations.for_context(ctx, tts_service=tts_engine.TtsService)

    by_name = {d.name: d for d in operations.MEDIA_OPERATIONS}
    mount_router(router, operation_router([by_name["tts.status"], by_name["tts.download"]], registry, _answer,
                                          module=__name__))

    return router


__all__ = ["build_tts_router"]
