"""Transcriber lifecycle state (HS-63-04).

Status reporting, lazy load, and background warm — verbatim moves out of
WebRuntime.
"""

from __future__ import annotations

import threading

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

    def _ensure_transcriber_loaded(
        self,
        *,
        model_name: str | None = None,
        backend: str | None = None,
        language: str | None = None,
    ) -> Transcriber:
        """Construct/reuse a transcriber for explicit, immutable parameters.

        Runtime warmup leaves arguments absent and uses Config.  A Meeting passes
        its frozen deployment evidence, so Config cannot change physical model
        selection between admission and execution.
        """
        selected_model = model_name if model_name is not None else self.config.model.name
        selected_backend = backend if backend is not None else self.config.model.backend
        selected_language = language if language is not None else getattr(self.config.model, "language", "auto")
        # HS-131-09: constructing a Transcriber loads no weights. The MLX load is
        # a model invocation, so it happens through admitted preload children.
        with self._transcriber_init_lock:
            if (
                self.transcriber is None
                or getattr(self.transcriber, "model_name", None) != selected_model
                or getattr(self.transcriber, "backend", None) != selected_backend
                or str(getattr(self.transcriber, "language", None) or "auto")
                != str(selected_language or "auto")
            ):
                self._set_transcription_status("loading")
                try:
                    self.transcriber = Transcriber(
                        model_name=selected_model,
                        backend=selected_backend,
                        language=selected_language,
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
                    transcriber = self._ensure_transcriber_loaded()
                except Exception as exc:
                    self._set_transcription_status("error", error=f"{type(exc).__name__}: {exc}")
                    with self.state_lock:
                        self.runtime_status["last_error"] = f"Transcription warmup failed: {exc}"
                    log.error(f"Transcription warmup failed: {exc}", exc_info=True)
                    return
                # HS-131-09 (Sol Amendment 4): a PRE-session warm has no session
                # to parent it, so it runs only under the owner's explicit
                # `model.local_model_preload_authority`. Blank/absent DEFERS the
                # load to the first admitted session — it never dispatches MLX
                # on authority inferred from this process.
                from ..speech_session import SpeechSessionRefused, preload_service_admission

                try:
                    admission = preload_service_admission(config_snapshot=self.config)
                except SpeechSessionRefused as exc:
                    # The refusal carries the revision the owner must set in
                    # `model.local_model_preload_authority` to authorize a warm for
                    # THIS model configuration; it is a hash, never secret material.
                    log.info(
                        "local model preload deferred to the first admitted session: "
                        "%s (set model.local_model_preload_authority=%s to authorize)",
                        exc.reason,
                        getattr(exc, "detail", "") or "<unknown>",
                    )
                    return
                try:
                    transcriber.warm(admission)
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
