"""Transcriber lifecycle state (HS-63-04).

Status reporting, lazy load, and background warm — verbatim moves out of
WebRuntime.
"""

from __future__ import annotations

import inspect
import threading
from typing import Any

from ..logging_config import get_logger
from ..transcribe import Transcriber

log = get_logger("web_runtime")


def _frozen_session_transcriber(runtime: Any, session: Any) -> Any:
    """Construct through frozen session evidence when the runtime owns that seam.

    Small embedders may provide a no-argument injected transcriber factory; that
    is a construction seam, not a permission to read Config after admission.
    """
    frozen = session.frozen_transcriber_arguments() or {}
    factory = runtime._ensure_transcriber_loaded
    parameters = inspect.signature(factory).parameters.values()
    accepts_keywords = any(item.kind is inspect.Parameter.VAR_KEYWORD for item in parameters)
    accepted = {item.name for item in parameters}
    return factory(**frozen) if accepts_keywords or set(frozen).issubset(accepted) else factory()


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
        deployment_revision_id: str | None = None,
    ) -> Transcriber:
        """Construct/reuse a transcriber for immutable routed construction.

        Legacy callers may still omit all arguments.  Every routed caller passes
        the exact deployment revision as well as backend/model/language; a loaded
        artifact without a matching durable preload receipt is replaced rather
        than silently borrowed under the new route.
        """
        selected_model = model_name if model_name is not None else self.config.model.name
        selected_backend = backend if backend is not None else self.config.model.backend
        selected_language = language if language is not None else getattr(self.config.model, "language", "auto")
        # HS-131-09: constructing a Transcriber loads no weights. The MLX load is
        # a model invocation, so it happens through admitted preload children.
        with self._transcriber_init_lock:
            reusable = self._loaded_transcriber_reusable(
                self.transcriber,
                deployment_revision_id=deployment_revision_id,
                backend=selected_backend,
                model_name=selected_model,
                language=selected_language,
            )
            if not reusable:
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

    def _loaded_transcriber_reusable(
        self,
        transcriber: Any,
        *,
        deployment_revision_id: str | None,
        backend: str,
        model_name: str,
        language: str | None,
    ) -> bool:
        if (
            transcriber is None
            or getattr(transcriber, "model_name", None) != model_name
            or getattr(transcriber, "backend", None) != backend
            or str(getattr(transcriber, "language", None) or "auto")
            != str(language or "auto")
        ):
            return False
        if not deployment_revision_id:
            return True
        # Route construction identity alone is insufficient: an MLX model loaded
        # for another deployment (or without a durable lifecycle receipt) must
        # not run under this route just because its display strings match.
        from ..kernel.runtime import _service
        from ..speech_session.transcription import _durable_preload_provenance_matches

        return _durable_preload_provenance_matches(
            _service(),
            getattr(getattr(transcriber, "_impl", None), "_holdspeak_preload_provenance", {}),
            deployment_revision_id=str(deployment_revision_id),
            engine=str(backend),
            model=str(model_name),
            language=str(language or "auto"),
        )

    def _warm_transcriber_in_background(self) -> None:
        if not self._transcription_warm_on_start_enabled():
            return

        def _warm() -> None:
            # Freeze SERVICE lifecycle authority before construction. The warm
            # never selects a model from mutable ModelConfig bytes. Admission is
            # an accelerator boundary: a kernel/bootstrap/planning failure must
            # defer to the first lawful transcription, never escape this thread.
            try:
                from ..speech_session import preload_service_admission

                admission = preload_service_admission()
                material = admission.frozen_preload_material()
                deployment_revision_id = str(admission.evidence["deployment_revision_id"])
            except Exception as exc:
                # Do not extend this catch into the admitted physical load below.
                # Capture remains available; its first lawful routed transcription
                # owns the actual lifecycle and can surface an in-flow failure.
                reason = str(getattr(exc, "reason", "") or getattr(exc, "code", "") or exc)
                log.info("local model preload deferred to first transcription: %s", reason)
                return
            with self.transcription_lock:
                try:
                    transcriber = self._ensure_transcriber_loaded(
                        model_name=str(material["model"]),
                        backend=str(material["engine"]),
                        language=str(material["language"]),
                        deployment_revision_id=deployment_revision_id,
                    )
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
