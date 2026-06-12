"""Transcriber lifecycle state (HS-63-04).

Status reporting, lazy load, and background warm — verbatim moves out of
WebRuntime.
"""

from __future__ import annotations

import threading

import numpy as np

from ..logging_config import get_logger
from ..transcribe import Transcriber

log = get_logger("web_runtime")

# HS-32-03: the owner string a meeting uses to hold the shared
# ``VoiceTypingSession`` audio floor. One arbiter for hotkey / device /
# meeting capture; while a meeting holds this, hotkey/device ``begin()``
# is rejected, and a meeting can't start while either holds the floor.
_MEETING_AUDIO_OWNER = "meeting"



log = get_logger("web_runtime")


class TranscriberStateMixin:
    def _transcription_warm_on_start_enabled(self) -> bool:
        return bool(getattr(self.config.model, "warm_on_start", True))

    def _set_transcription_status(self, status: str, *, error: str = "") -> None:
        with self.state_lock:
            self.runtime_status["transcription_model"] = self.config.model.name
            self.runtime_status["transcription_warm_on_start"] = self._transcription_warm_on_start_enabled()
            self.runtime_status["transcription_status"] = status
            self.runtime_status["transcription_error"] = error
        if status == "warming":
            self._set_runtime_activity(
                "processing",
                source="runtime",
                label="Warming model",
                detail=f"Preparing transcription model {self.config.model.name}.",
                last_event="transcription_warming",
                last_error="",
            )
        elif status == "loading":
            self._set_runtime_activity(
                "processing",
                source="runtime",
                label="Loading model",
                detail=f"Loading transcription model {self.config.model.name}.",
                last_event="transcription_loading",
                last_error="",
            )
        elif status == "error":
            self._set_runtime_activity(
                "error",
                source="runtime",
                detail="Transcription model unavailable.",
                last_event="transcription_status_error",
                last_error=error,
            )

    def _ensure_transcriber_loaded(self) -> Transcriber:
        # HS-63-06: the check-and-construct is serialized — see the
        # _transcriber_init_lock comment in web_runtime.__init__ for the
        # process-fatal MLX consequence of letting two instances exist.
        with self._transcriber_init_lock:
            if self.transcriber is None or getattr(self.transcriber, "model_name", None) != self.config.model.name:
                self._set_transcription_status("loading")
                try:
                    self.transcriber = Transcriber(
                        model_name=self.config.model.name,
                        backend=self.config.model.backend,
                        language=getattr(self.config.model, "language", "auto"),
                    )
                except Exception as exc:
                    self._set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                    raise
        self._set_transcription_status("loaded")
        return self.transcriber

    def _warm_transcriber_in_background(self) -> None:
        if not self._transcription_warm_on_start_enabled():
            return

        def _warm() -> None:
            with self.transcription_lock:
                try:
                    self._ensure_transcriber_loaded()
                except Exception as exc:
                    self._set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                    with self.state_lock:
                        self.runtime_status["last_error"] = f"Transcription warmup failed: {exc}"
                    log.error(f"Transcription warmup failed: {exc}", exc_info=True)

        self._set_transcription_status("warming")
        threading.Thread(
            target=_warm,
            name="HoldSpeakTranscriptionWarmup",
            daemon=True,
        ).start()
