"""The hub's one voice: status, model download and streaming speech.

The Line extra and its Pocket engine are loaded lazily. HTTP and declared
operations use this same state; no route builds its own engine.
"""
from __future__ import annotations

import time
import struct
from threading import Lock
from typing import Any, Mapping, Optional

from holdspeak.services.errors import ServiceError

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
    from ..line.speech import TTS_VOICE

    return TTS_VOICE


def _tts_row() -> Optional[Mapping[str, Any]]:
    """The signed catalogue's TTS preset (the Line's voice weights)."""
    from ..line import models

    for row in models.presets():
        if row["role"] == "tts":
            return row
    return None


def _model_ready() -> bool:
    from ..line import models

    row = _tts_row()
    return row is not None and models.ready(row)


def _get_engine() -> Any:
    """The process's one Pocket engine; the first use loads it."""
    global _engine
    with _STATE_LOCK:
        if _engine is None:
            from ..line.speech import Pocket

            _engine = Pocket(voice=_voice())
        return _engine


def _refused(code: str, message: str, status: int = 404) -> ServiceError:
    return ServiceError(code, message, context={"status": status, "body": {"code": code, "message": message}})


def not_installed() -> ServiceError:
    return _refused("tts_not_installed", "Install the Line extra: pip install 'holdspeak[line]'")


def not_ready() -> ServiceError:
    return _refused("tts_model_not_ready", "The voice model is not downloaded.")


class TtsService:
    """``tts.status`` and ``tts.download``: the Line's TTS weights, read and fetched."""

    def speak(self, text: Any, voice: Any = None) -> Any:
        """Prepare a WAV iterator and its first PCM chunk before sending HTTP headers."""
        if not _line_installed():
            raise not_installed()
        if not _model_ready():
            raise not_ready()
        if not text or not isinstance(text, str):
            raise _refused("tts_invalid_request", "text is required.", 400)
        if voice not in (None, "", _voice()):
            raise _refused("tts_invalid_voice", f"Voice {voice} is not available. Use {_voice()}.", 400)
        from ..line.audio import RATE

        def synthesize():
            header = struct.pack("<4sI4s4sIHHIIHH4sI", b"RIFF", 0xFFFFFFFF, b"WAVE", b"fmt ",
                                 16, 1, 1, RATE, RATE * 2, 2, 16, b"data", 0xFFFFFFFF - 36)
            yield header
            for chunk in _get_engine().stream(text):
                yield chunk.astype("<i2", copy=False).tobytes()

        gen = synthesize()
        try:
            header = next(gen, None)
            first = next(gen, None) if header is not None else None
        except Exception as exc:
            raise _refused("tts_synthesis_failed", "The voice engine returned no audio.", 500) from exc
        if header is None or first is None:
            raise _refused("tts_synthesis_failed", "The voice engine returned no audio.", 500)

        def chain():
            yield header
            yield first
            yield from gen

        return chain()

    def status(self) -> dict[str, Any]:
        """The Line extra installed, its TTS weights ready, the engine and the voice."""
        installed = _line_installed()
        return {"installed": installed, "model_ready": installed and _model_ready(), "engine": ENGINE,
                "voice": _voice()}

    def download(self) -> dict[str, Any]:
        """Start (or join) the Line's fetch job for the TTS preset and wait for it: the receipt and the egress."""
        if not _line_installed():
            raise not_installed()
        from ..line import models

        row = _tts_row()
        if row is None:
            raise _refused("tts_no_preset", "The catalogue has no voice model.")
        started = time.monotonic()
        models.start(row["id"])
        models.wait(row["id"], DOWNLOAD_WAIT_S)
        after = models.model_row(row)
        receipt = {
            "downloaded": models.ready(row),
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
        return {"receipt": receipt, "egress": egress}


__all__ = ["ENGINE", "TtsService", "not_installed", "not_ready"]
