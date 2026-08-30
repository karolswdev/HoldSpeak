"""TTS route: browser default + kokoro-onnx optional extra (HS-154-01).

GET /api/tts/status  -> {installed, model_ready}
POST /api/tts        -> streaming WAV (404 without the extra)
POST /api/tts/download -> trigger model weights download (egress-badged, receipted)

The ``holdspeak[tts]`` extra is LAZY-IMPORTED: the base install never pays
for it. When absent every route answers 404 with a typed code, and the
client seam stays on the browser voice — no dead UI.
"""
from __future__ import annotations

import io
import struct
import time
from pathlib import Path
from typing import Any, Iterator

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from ...logging_config import get_logger
from ...services.errors import ServiceError
from ..context import WebContext
from ..runtime_support import error_500

log = get_logger("web.routes.tts")

# ---- lazy kokoro-onnx singleton ----

_kokoro_instance: Any = None
_kokoro_checked = False
_kokoro_available: bool | None = None


def _check_kokoro_available() -> bool:
    """Check whether kokoro-onnx is importable (cached after first probe)."""
    global _kokoro_available, _kokoro_checked
    if _kokoro_checked:
        return _kokoro_available is True
    _kokoro_checked = True
    try:
        import kokoro_onnx  # noqa: F401

        _kokoro_available = True
        return True
    except ImportError:
        _kokoro_available = False
        return False


def _reset_kokoro_state() -> None:
    """Reset lazy state (test seam only)."""
    global _kokoro_instance, _kokoro_checked, _kokoro_available
    _kokoro_instance = None
    _kokoro_checked = False
    _kokoro_available = None


def _model_weights_dir() -> Path:
    """Directory where kokoro-onnx model weights live."""
    from ...config import CONFIG_DIR

    return CONFIG_DIR / "tts"


def _model_ready() -> bool:
    """Check whether the model weights have been downloaded."""
    weights_dir = _model_weights_dir()
    # kokoro-onnx needs two files: the ONNX model and the voices binary
    model_file = weights_dir / "kokoro-v0_19.onnx"
    voices_file = weights_dir / "voices.bin"
    return model_file.exists() and voices_file.exists()


def _get_kokoro() -> Any:
    """Get or create the kokoro-onnx engine singleton.

    Returns None if the extra is absent or model not ready.
    """
    global _kokoro_instance
    if _kokoro_instance is not None:
        return _kokoro_instance
    if not _check_kokoro_available():
        return None
    if not _model_ready():
        return None
    try:
        import kokoro_onnx

        weights_dir = _model_weights_dir()
        _kokoro_instance = kokoro_onnx.Kokoro(
            str(weights_dir / "kokoro-v0_19.onnx"),
            str(weights_dir / "voices.bin"),
        )
        return _kokoro_instance
    except Exception:
        log.warning("kokoro-onnx engine failed to initialize", exc_info=True)
        return None


def _wav_header(sample_rate: int, num_samples: int, channels: int = 1, bits: int = 16) -> bytes:
    """Build a minimal WAV header for raw PCM data."""
    byte_rate = sample_rate * channels * (bits // 8)
    block_align = channels * (bits // 8)
    data_size = num_samples * block_align
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits,
        b"data",
        data_size,
    )
    return header


def _synthesize_wav(text: str, voice: str = "af_heart", speed: float = 1.0) -> Iterator[bytes]:
    """Generate WAV bytes from text using the kokoro engine.

    Yields the WAV header first, then PCM data chunks.
    """
    engine = _get_kokoro()
    if engine is None:
        return

    try:
        import numpy as np

        samples, sample_rate = engine.create(text, voice=voice, speed=speed)
        # Normalize to int16
        if samples.dtype != np.int16:
            peak = max(abs(samples.min()), abs(samples.max())) or 1.0
            samples = (samples / peak * 32767).astype(np.int16)
        num_samples = len(samples)
        yield _wav_header(sample_rate, num_samples)
        # Stream in chunks of ~4096 samples
        chunk_size = 4096
        for i in range(0, num_samples, chunk_size):
            yield samples[i : i + chunk_size].tobytes()
    except Exception:
        log.warning("TTS synthesis failed", exc_info=True)
        return


# ---- the 404 for absent extra ----

_NOT_INSTALLED = JSONResponse(
    {"code": "tts_not_installed", "message": "Install the TTS extra: pip install 'holdspeak[tts]'"},
    status_code=404,
)


def build_tts_router(ctx: WebContext) -> APIRouter:
    """Build the TTS route family (HS-154-01)."""
    router = APIRouter()

    @router.get("/api/tts/status")
    async def tts_status(request: Request) -> Any:
        """Report TTS availability: extra installed + model weights ready."""
        try:
            installed = _check_kokoro_available()
            ready = installed and _model_ready()
            return JSONResponse({
                "installed": installed,
                "model_ready": ready,
            })
        except Exception as exc:
            return error_500(exc, log, "Failed to read TTS status")

    @router.post("/api/tts")
    async def tts_speak(request: Request) -> Any:
        """Synthesize text to streaming WAV audio.

        404 when the kokoro-onnx extra is absent.
        """
        if not _check_kokoro_available():
            return _NOT_INSTALLED
        if not _model_ready():
            return JSONResponse(
                {"code": "tts_model_not_ready", "message": "TTS model weights not downloaded."},
                status_code=503,
            )
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
        voice = body.get("voice", "af_heart") if isinstance(body, dict) else "af_heart"
        speed = body.get("speed", 1.0) if isinstance(body, dict) else 1.0

        return StreamingResponse(
            _synthesize_wav(text, voice=voice, speed=speed),
            media_type="audio/wav",
        )

    @router.post("/api/tts/download")
    async def tts_download(request: Request) -> Any:
        """Download kokoro-onnx model weights (egress-badged, receipted).

        Follows the Model Library download pattern: POST triggers the
        download, 202 carries the receipt. The egress badge names the
        host and an approximate size.
        """
        if not _check_kokoro_available():
            return _NOT_INSTALLED
        try:
            weights_dir = _model_weights_dir()
            weights_dir.mkdir(parents=True, exist_ok=True)

            # kokoro-onnx's own download mechanism
            import kokoro_onnx

            started = time.monotonic()
            model_path = weights_dir / "kokoro-v0_19.onnx"
            voices_path = weights_dir / "voices.bin"

            # Use kokoro-onnx's download helper if available, else
            # the library downloads on first Kokoro() instantiation.
            if hasattr(kokoro_onnx, "download"):
                kokoro_onnx.download(str(weights_dir))
            else:
                # Instantiate to trigger download — the constructor
                # downloads if files are absent.
                try:
                    kokoro_onnx.Kokoro(str(model_path), str(voices_path))
                except FileNotFoundError:
                    # Model files not bundled and no download helper.
                    # The owner must manually place the weights.
                    return JSONResponse(
                        {
                            "code": "tts_download_manual",
                            "message": "Place kokoro-v0_19.onnx and voices.bin in the TTS weights directory.",
                            "weights_dir": str(weights_dir),
                        },
                        status_code=422,
                    )

            elapsed = time.monotonic() - started
            ready = _model_ready()

            # Reset the singleton so it picks up new weights
            global _kokoro_instance
            _kokoro_instance = None

            receipt = {
                "downloaded": ready,
                "elapsed_s": round(elapsed, 2),
                "weights_dir": str(weights_dir),
            }
            egress = {
                "host": "huggingface.co",
                "bytes_estimate": "~90 MB",
                "purpose": "TTS model weights (kokoro-onnx)",
            }
            return JSONResponse(
                {
                    "receipt": receipt,
                    "egress": egress,
                },
                status_code=202,
            )
        except Exception as exc:
            return error_500(exc, log, "Failed to download TTS model")

    return router


__all__ = ["build_tts_router"]
