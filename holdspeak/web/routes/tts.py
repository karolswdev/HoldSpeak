"""TTS route: the hub's one voice is the Line's Pocket TTS (HS-154-01, 2026-11-07).

GET  /api/tts/status   -> {installed, model_ready, engine, voice}
POST /api/tts          -> streaming WAV (404 without the ``line`` extra)
POST /api/tts/download -> fetch the Line's TTS weights (egress-badged, receipted)

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
import time
from threading import Lock
from typing import Any, Iterator, Mapping, Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from ...logging_config import get_logger
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.tts")

ENGINE = "pocket"
#: The longest the download route waits for the Line's fetch job.
DOWNLOAD_WAIT_S = 30 * 60

# ---- the one engine per process ----

_engine: Any = None
_installed: Optional[bool] = None
_STATE_LOCK = Lock()


def _reset_state() -> None:
    """Forget the engine and the import probe (test seam only)."""
    global _engine, _installed
    with _STATE_LOCK:
        _engine = None
        _installed = None


def _line_installed() -> bool:
    """The ``line`` extra imports (``pocket_tts`` and ``torch``); cached."""
    global _installed
    with _STATE_LOCK:
        if _installed is None:
            try:
                import pocket_tts  # noqa: F401
                import torch  # noqa: F401

                _installed = True
            except ImportError:
                _installed = False
        return _installed


def _voice() -> str:
    from ...line.speech import TTS_VOICE

    return TTS_VOICE


def _tts_row() -> Optional[Mapping[str, Any]]:
    """The signed catalogue's TTS preset (the Line's voice weights)."""
    from ...line import models

    for row in models.presets():
        if row["role"] == "tts":
            return row
    return None


def _model_ready() -> bool:
    from ...line import models

    row = _tts_row()
    return row is not None and models.ready(row)


def _get_engine() -> Any:
    """The process's one Pocket engine; the first use loads it."""
    global _engine
    with _STATE_LOCK:
        if _engine is None:
            from ...line.speech import Pocket

            _engine = Pocket(voice=_voice())
        return _engine


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

    engine = _get_engine()
    yield _wav_header(RATE)
    for chunk in engine.stream(text):
        yield chunk.astype("<i2", copy=False).tobytes()


def _first_two(gen: Iterator[bytes]) -> tuple[Optional[bytes], Optional[bytes]]:
    """The header and the first audio chunk (loads the engine; off the loop)."""
    header = next(gen, None)
    first = next(gen, None) if header is not None else None
    return header, first


def _not_installed() -> JSONResponse:
    return JSONResponse(
        {"code": "tts_not_installed", "message": "Install the Line extra: pip install 'holdspeak[line]'"},
        status_code=404,
    )


def _not_ready() -> JSONResponse:
    return JSONResponse(
        {"code": "tts_model_not_ready", "message": "The voice model is not downloaded."},
        status_code=404,
    )


def build_tts_router(ctx: WebContext) -> APIRouter:
    """Build the TTS route family (HS-154-01)."""
    router = APIRouter()

    @router.get("/api/tts/status")
    def tts_status(request: Request) -> Any:
        """Report TTS availability: the Line extra installed + its TTS weights ready."""
        try:
            installed = _line_installed()
            ready = installed and _model_ready()
            return JSONResponse({
                "installed": installed,
                "model_ready": ready,
                "engine": ENGINE,
                "voice": _voice(),
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to read TTS status")

    @router.post("/api/tts")
    async def tts_speak(request: Request) -> Any:
        """Synthesize text to streaming WAV audio with the Line's Pocket engine.

        404 ``tts_not_installed`` without the ``line`` extra; 404
        ``tts_model_not_ready`` before the weights are fetched.
        """
        if not await run_in_threadpool(_line_installed):
            return _not_installed()
        if not await run_in_threadpool(_model_ready):
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
        if voice not in (None, "", _voice()):
            return JSONResponse(
                {"code": "tts_invalid_voice", "message": f"Voice {voice} is not available. Use {_voice()}."},
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

    @router.post("/api/tts/download")
    def tts_download(request: Request) -> Any:
        """Fetch the Line's TTS weights through ``line/models.py`` (egress-badged, receipted).

        Starts (or joins) the Line's fetch job for the TTS preset and waits
        for it; the 202 carries the receipt and the egress badge.
        """
        if not _line_installed():
            return _not_installed()
        try:
            from ...line import models

            row = _tts_row()
            if row is None:
                return JSONResponse(
                    {"code": "tts_no_preset", "message": "The catalogue has no voice model."},
                    status_code=404,
                )
            started = time.monotonic()
            models.start(row["id"])
            models.wait(row["id"], DOWNLOAD_WAIT_S)
            after = models.model_row(row)
            ready = models.ready(row)
            receipt = {
                "downloaded": ready,
                "elapsed_s": round(time.monotonic() - started, 2),
                "weights_dir": str(models.model_dir(row)),
                "total_bytes": int(row["source"]["download_bytes"]),
                "state": after.get("state"),
            }
            if after.get("reason"):
                receipt["reason"] = after["reason"]
            egress = {
                "host": models.HOST,
                "bytes_estimate": f"~{round(int(row['source']['download_bytes']) / 1_000_000)} MB",
                "purpose": f"Voice model weights ({row['label']})",
            }
            return JSONResponse({"receipt": receipt, "egress": egress}, status_code=202)
        except Exception as exc:
            return error_500(exc, log, "Failed to download the voice model")

    return router


__all__ = ["ENGINE", "build_tts_router"]
