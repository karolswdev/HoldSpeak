"""Local transcription using a Whisper backend.

`Transcriber` loads a Whisper model and converts microphone audio (mono,
float32, 16 kHz) into text.

HS-131-09: local Whisper is a model invocation like any other. Every nonempty
dispatch requires a live admitted session (a
:class:`~holdspeak.speech_session.transcription.TranscriptionAdmission`) and runs
as ONE ``holdspeak.whisper-transcribe@1`` child with a terminal receipt; the MLX
model load is its own ``holdspeak.whisper-preload@1`` SIBLING child, completed
before it. Audio is dispatch-only: the kernel sees its SHA-256 and safe counts,
never the samples. Empty/invalid audio creates no child at all.
"""

from __future__ import annotations

import importlib
import importlib.util
import platform
import sys
import threading
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol

import numpy as np

from .errors import TranscriptionError as _TranscriptionErrorBase
from .logging_config import get_logger

log = get_logger("transcribe")


class TranscriberError(_TranscriptionErrorBase):
    """Raised when model loading or transcription fails."""

    code: str = "TRANSCRIBER_ERROR"


class TranscriberTimeoutError(TranscriberError):
    """Raised when transcription exceeds the configured timeout (HS-25-05).

    A subclass of TranscriberError so existing transcription error handling
    (notify + return to idle) catches it without special-casing.
    """

    code: str = "TRANSCRIBER_TIMEOUT_ERROR"


class _TranscriberImpl(Protocol):
    device: str
    compute_type: str

    def transcribe(self, audio_array: np.ndarray) -> str: ...

    def ensure_loaded(self, admission: object) -> None: ...


def _is_darwin_arm64() -> bool:
    return sys.platform == "darwin" and platform.machine() == "arm64"


def _module_available(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


def _resolve_backend(backend: str) -> str:
    backend = backend.strip().lower()
    if backend not in {"auto", "mlx", "faster-whisper"}:
        raise TranscriberError("backend must be one of: auto|mlx|faster-whisper")

    if backend == "mlx":
        if not _is_darwin_arm64():
            raise TranscriberError("backend 'mlx' is only supported on macOS arm64")
        if not (_module_available("mlx") and _module_available("mlx_whisper")):
            raise TranscriberError(
                "mlx-whisper is not installed. Install dependencies first (macOS arm64 only)."
            )
        return "mlx"

    if backend == "faster-whisper":
        if not _module_available("faster_whisper"):
            raise TranscriberError(
                "faster-whisper is not installed. On Linux, install it with: "
                "uv pip install -e '.[linux]'"
            )
        return "faster-whisper"

    # auto
    if _is_darwin_arm64() and (_module_available("mlx") and _module_available("mlx_whisper")):
        return "mlx"
    if _module_available("faster_whisper"):
        return "faster-whisper"
    raise TranscriberError(
        "No supported transcription backend is installed. On Linux, install: "
        "uv pip install -e '.[linux]'"
    )


def _model_repo_candidates(model_name: str) -> list[str]:
    name = model_name.strip()
    if not name:
        return []

    if Path(name).exists():
        return [name]

    if "/" in name:
        return [name]

    key = name.lower()
    if key in {"tiny", "base", "small", "medium"}:
        return [
            f"mlx-community/whisper-{key}-mlx",
            f"mlx-community/whisper-{key}",
        ]

    if key == "large":
        return [
            "mlx-community/whisper-large-v3-mlx",
            "mlx-community/whisper-large-v2-mlx",
            "mlx-community/whisper-large-v3",
            "mlx-community/whisper-large-v2",
        ]

    return [name]


class _MlxTranscriber:
    """Transcribe audio locally using mlx-whisper (macOS arm64 only)."""

    def __init__(
        self,
        *,
        model_name: str = "base",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None:
        """Initialize the Whisper model.

        Args:
            model_name: Whisper model name (defaults to "base").
            device: Unused (kept for backwards compatibility with faster-whisper).
            compute_type: Unused (kept for backwards compatibility with faster-whisper).
            language: A Whisper language code to pin transcription to, or
                None for Whisper's own per-utterance auto-detection (HS-59).
        """

        self.language = language
        # HS-60-06 (a real latent crash, reproduced): MLX streams are bound to
        # the thread that created them — loading the model on one thread and
        # transcribing from another raises an UNCAUGHT C++ exception
        # ("There is no Stream(gpu, 1) in current thread") that terminates
        # the whole process. Pin ALL MLX work (the load below and every
        # transcribe) to one dedicated thread, so callers may live anywhere
        # (the hotkey thread, the wake listener, a route worker).
        import concurrent.futures

        self._mlx_thread = concurrent.futures.ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="HoldSpeakMlx"
        )
        log.info(f"Initializing Transcriber with model_name='{model_name}'")

        try:
            mx = importlib.import_module("mlx.core")
            mlx_whisper = importlib.import_module("mlx_whisper")
        except Exception as exc:  # pragma: no cover
            raise TranscriberError(
                "mlx-whisper is not available. Install dependencies first (macOS arm64 only)."
            ) from exc

        _ = device
        _ = compute_type

        self.model_name = model_name
        self._path_or_hf_repo = None
        self._mx = mx
        self._mlx_whisper = mlx_whisper

        candidates = _model_repo_candidates(model_name)
        log.debug(f"Model candidates for '{model_name}': {candidates}")
        if not candidates:
            raise TranscriberError("model_name must be non-empty")
        # HS-131-09: constructing this loads NOTHING. Loading MLX weights is a
        # model invocation, so it happens in `ensure_loaded` under an admitted
        # preload child — never as an unreceipted constructor side effect.
        self._candidates = tuple(candidates)

        self.device = "mlx"
        self.compute_type = "float16"
        log.info(f"Transcriber constructed (unloaded): candidates={self._candidates}")

    @property
    def loaded(self) -> bool:
        return self._path_or_hf_repo is not None

    def ensure_loaded(self, admission: Any) -> None:
        """Load the weights through admitted sibling preload work.

        Historic speech sessions receipt each physical candidate attempt. A
        bundle-backed Meeting deliberately collapses that private candidate walk
        into one frozen, P=1 lifecycle child; its candidates and strategies were
        already frozen at Meeting admission.
        """
        reusable = getattr(admission, "loaded_artifact_reusable", None)
        if self._path_or_hf_repo is not None:
            # A loaded MLX instance is not ambient proof.  It can serve another
            # frozen route only when that route's exact deployment revision and
            # durable successful preload receipt both cross-bind it.
            if callable(reusable) and reusable(self):
                return
            self._path_or_hf_repo = None
        if bool(getattr(admission, "single_preload_sequence", False)):
            frozen = getattr(admission, "frozen_preload_material", lambda: {})()
            material = dict(frozen)
            if (
                material.get("engine") != "mlx"
                or str(material.get("model") or "") != self.model_name
                or str(material.get("language") or "auto") != str(self.language or "auto")
            ):
                raise TranscriberError("frozen MLX preload construction is missing")
            candidates = tuple(str(item) for item in material["candidate_ids"])
            strategies = tuple(str(item) for item in material["strategy_sequence"])
            outcome, _ = admission.preload_sequence(
                material=material,
                run=lambda cancellation: self._load_candidate_sequence(
                    candidates=candidates,
                    strategies=strategies,
                    cancellation=cancellation,
                ),
            )
            if outcome.outcome == "succeeded":
                return
            raise TranscriberError(
                f"Failed to load Whisper model '{self.model_name}' via mlx-whisper "
                f"(preload {outcome.outcome})."
            )
        attempt, last = 0, ""
        for repo in self._candidates:
            material = {
                "model_repo": repo,
                "engine": "mlx",
                "model": self.model_name,
                "language": self.language or "auto",
            }
            for stage, run in (
                ("model-holder", lambda repo=repo: self._model_holder_get(repo)),
                ("silent-audio", lambda repo=repo: self._silent_audio_load(repo)),
            ):
                attempt += 1
                outcome, _ = admission.preload_child(
                    stage=stage, material=material, run=run, attempt_ordinal=attempt
                )
                if outcome.outcome == "succeeded":
                    log.info(f"MLX model loaded from {repo} via {stage}")
                    self._path_or_hf_repo = repo
                    return
                last = f"{stage}:{outcome.outcome}"
                log.warning(f"MLX preload {stage} for {repo} ended {outcome.outcome}")
        raise TranscriberError(
            f"Failed to load Whisper model '{self.model_name}' via mlx-whisper "
            f"(last preload {last or 'not attempted'})."
        )

    def _load_candidate_sequence(
        self,
        *,
        candidates: tuple[str, ...],
        strategies: tuple[str, ...],
        cancellation: Any = None,
    ) -> str:
        """Walk exactly the admitted MLX lifecycle sequence, once.

        The candidates, stages, and terminal stop rules were frozen before the
        lifecycle operation was admitted.  This adapter neither re-reads its
        mutable candidate field nor invents a fallback stage.
        """
        from .kernel.model import KernelRefused
        from .kernel.provider_signals import ProviderIndeterminate

        physical = {
            "model-holder": self._model_holder_get,
            "silent-audio": self._silent_audio_load,
        }
        last = ""
        for repo in candidates:
            for stage in strategies:
                if cancellation is not None and cancellation.is_set():
                    raise KernelRefused("speech_preload_cancelled")
                run = physical.get(stage)
                if run is None:
                    raise TranscriberError("frozen MLX preload stage is invalid")
                try:
                    run(repo)
                except (KernelRefused, ProviderIndeterminate):
                    # These dispositions are terminal.  In particular an unknown
                    # native physical result may never advance to another stage.
                    raise
                except Exception as exc:
                    if cancellation is not None and cancellation.is_set():
                        raise KernelRefused("speech_preload_cancelled") from exc
                    last = f"{stage}:{type(exc).__name__}"
                    log.warning("MLX preload %s for %s failed: %s", stage, repo, type(exc).__name__)
                    # Only a known caught no-generation failure advances.
                    continue
                if cancellation is not None and cancellation.is_set():
                    raise KernelRefused("speech_preload_cancelled")
                self._path_or_hf_repo = repo
                log.info("MLX model loaded from %s via %s", repo, stage)
                return stage
        raise TranscriberError(
            f"Failed to load Whisper model '{self.model_name}' via mlx-whisper "
            f"(last preload {last or 'not attempted'})."
        )

    def _model_holder_get(self, path_or_hf_repo: str) -> str:
        """The explicit no-decode load hook, on the pinned MLX thread."""
        def _run() -> str:
            from mlx_whisper.transcribe import ModelHolder  # type: ignore

            ModelHolder.get_model(path_or_hf_repo, self._mx.float16)
            return "model-holder"

        return str(self._mlx_thread.submit(_run).result())

    def _silent_audio_load(self, path_or_hf_repo: str) -> str:
        """The fallback: one tiny silent transcription forces the weight load."""
        def _run() -> str:
            silent = np.zeros(1600, dtype=np.float32)  # ~0.1s at 16 kHz
            warm_kwargs = {"language": self.language} if self.language else {"language": "en"}
            self._mlx_whisper.transcribe(  # type: ignore[union-attr]
                silent,
                path_or_hf_repo=path_or_hf_repo,
                verbose=None,
                **warm_kwargs,
            )
            return "silent-audio"

        return str(self._mlx_thread.submit(_run).result())

    def transcribe(self, audio_array: np.ndarray) -> str:
        """Transcribe an in-memory audio array.

        Args:
            audio_array: Numpy array of mono audio. Prefer float32 at 16 kHz.

        Returns:
            Transcribed text (may be empty).

        Raises:
            TranscriberError: If transcription fails.
            ValueError: If the provided audio has an invalid shape.
        """

        audio = np.asarray(audio_array)
        if audio.ndim == 2:
            # Common shape from some pipelines: (n_samples, 1)
            if audio.shape[1] != 1:
                raise ValueError("audio_array must be mono (shape (n,) or (n, 1))")
            audio = audio[:, 0]
        elif audio.ndim != 1:
            raise ValueError("audio_array must be mono (shape (n,) or (n, 1))")

        if audio.size == 0:
            return ""
        if self._path_or_hf_repo is None:
            raise TranscriberError("the MLX model is not loaded; preload was never admitted")

        audio = np.ascontiguousarray(audio, dtype=np.float32)
        log.debug(f"Transcribing {len(audio)} samples ({len(audio)/16000:.2f}s)")

        def _run() -> str:
            # HS-59: pass `language` only when pinned — the auto-detect call
            # stays byte-identical to the pre-knob behavior.
            extra = {"language": self.language} if self.language else {}
            result = self._mlx_whisper.transcribe(  # type: ignore[union-attr]
                audio,
                path_or_hf_repo=self._path_or_hf_repo,
                verbose=None,
                **extra,
            )
            if isinstance(result, dict):
                return str(result.get("text", "")).strip()
            return str(getattr(result, "text", result)).strip()

        try:
            # Always on the pinned MLX thread (HS-60-06): MLX streams are
            # thread-bound, and a cross-thread call is a process-fatal C++
            # exception, not a Python error.
            text = self._mlx_thread.submit(_run).result()
            log.info(f"Transcription result: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            return text
        except Exception as exc:
            log.error(f"Transcription failed: {exc}", exc_info=True)
            raise TranscriberError(f"Transcription failed: {exc}") from exc


class _FasterWhisperTranscriber:
    """Transcribe audio locally using faster-whisper."""

    def __init__(
        self,
        *,
        model_name: str = "base",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None:
        self.language = language
        try:
            faster_whisper = importlib.import_module("faster_whisper")
        except Exception as exc:  # pragma: no cover
            raise TranscriberError(
                "faster-whisper is not installed. On Linux, install it with: "
                "uv pip install -e '.[linux]'"
            ) from exc

        self.model_name = model_name
        self.device = device or "cpu"
        self.compute_type = compute_type or "int8"

        try:
            self._model = faster_whisper.WhisperModel(
                model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
        except Exception as exc:
            raise TranscriberError(f"Failed to load faster-whisper model '{model_name}': {exc}") from exc

    @property
    def loaded(self) -> bool:
        return True

    def ensure_loaded(self, admission: Any) -> None:
        """Faster-whisper loads in its constructor (Phase-D Amendment 11).

        That ratified local-only, constructor-inseparable exception occurs after
        the parent and frozen speech route exist, but it neither dispatches nor
        receipts lifecycle work here. Only MLX has the separable admitted load.
        """
        return None

    def transcribe(self, audio_array: np.ndarray) -> str:
        audio = np.asarray(audio_array)
        if audio.ndim == 2:
            if audio.shape[1] != 1:
                raise ValueError("audio_array must be mono (shape (n,) or (n, 1))")
            audio = audio[:, 0]
        elif audio.ndim != 1:
            raise ValueError("audio_array must be mono (shape (n,) or (n, 1))")

        if audio.size == 0:
            return ""

        audio = np.ascontiguousarray(audio, dtype=np.float32)

        try:
            # HS-59: pass `language` only when pinned — auto stays byte-identical.
            extra = {"language": self.language} if self.language else {}
            segments, _info = self._model.transcribe(audio, vad_filter=False, **extra)
            parts: list[str] = []
            for seg in segments:
                text = str(getattr(seg, "text", "")).strip()
                if text:
                    parts.append(text)
            return " ".join(parts).strip()
        except Exception as exc:
            raise TranscriberError(f"Transcription failed: {exc}") from exc


class Transcriber:
    """Transcribe audio locally using the selected backend."""

    def __init__(
        self,
        *,
        model_name: str = "base",
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        backend: str = "auto",
        timeout_seconds: float = 0.0,
        language: Optional[str] = None,
    ) -> None:
        from .languages import normalize_language

        resolved = _resolve_backend(backend)
        self.backend = resolved
        # HS-25-05: hard ceiling so a hung model can't freeze the pipeline
        # forever. <= 0 disables the timeout (calls run inline, as before).
        self.timeout_seconds = float(timeout_seconds)
        # HS-59: "auto"/""/None all mean Whisper's own detection — the
        # backends then receive no language at all (byte-identical calls).
        self.language = normalize_language(language)

        if resolved == "mlx":
            self._impl: _TranscriberImpl = _MlxTranscriber(
                model_name=model_name,
                device=device,
                compute_type=compute_type,
                language=self.language,
            )
        else:
            self._impl = _FasterWhisperTranscriber(
                model_name=model_name,
                device=device,
                compute_type=compute_type,
                language=self.language,
            )

        self.model_name = model_name
        self.device = self._impl.device
        self.compute_type = self._impl.compute_type

    def warm(self, admission: Any) -> None:
        """Load the local weights through one admitted frozen lifecycle route."""
        self._impl.ensure_loaded(admission)
        recorder = getattr(admission, "record_loaded_artifact", None)
        receipt = getattr(admission, "last_preload_receipt", None)
        if callable(recorder) and isinstance(receipt, Mapping):
            recorder(self._impl, receipt)

    @property
    def loaded(self) -> bool:
        return bool(getattr(self._impl, "loaded", True))

    def transcribe(
        self,
        audio_array: np.ndarray,
        *,
        admission: Any = None,
        capability: str = "whisper-transcribe",
    ) -> str:
        """Transcribe under ONE admitted invocation child (HS-131-09).

        ``admission`` is the live session's
        :class:`~holdspeak.speech_session.transcription.TranscriptionAdmission`
        (a ``dictation.session``, ``wake.session``, or the existing
        ``meeting.session``). Empty or invalid audio creates no child at all;
        nonempty audio with no live admission is a named refusal raised BEFORE
        any MLX/faster-whisper call.
        """
        from .speech_session.plan import (
            TRANSCRIPTION_CONTEXT_REQUIRED,
            SpeechSessionRefused,
        )
        from .speech_session.transcription import audio_sha256

        audio = np.asarray(audio_array)
        if audio.ndim == 2:
            if audio.shape[1] != 1:
                raise ValueError("audio_array must be mono (shape (n,) or (n, 1))")
            audio = audio[:, 0]
        elif audio.ndim != 1:
            raise ValueError("audio_array must be mono (shape (n,) or (n, 1))")
        if audio.size == 0:
            # Mechanical: no model runs, so no child and no receipt exist.
            return ""
        if admission is None:
            raise SpeechSessionRefused(TRANSCRIPTION_CONTEXT_REQUIRED, capability)

        audio = np.ascontiguousarray(audio, dtype=np.float32)
        digest = audio_sha256(audio)
        # The preload lifecycle completes before the routed transcription child.
        self.warm(admission)
        errors: list[BaseException] = []

        def _dispatch() -> str:
            try:
                return self._timed_transcribe(audio)
            except BaseException as exc:  # noqa: BLE001 - re-raised for the child
                errors.append(exc)
                raise

        outcome, text = admission.transcribe_child(
            material={
                "audio_sha256": digest,
                "sample_count": int(audio.size),
                "sample_rate": 16000,
                "backend": self.backend,
                "model": self.model_name,
                "device": self.device,
                "compute_type": self.compute_type,
                "language": self.language or "auto",
                "timeout_seconds": float(self.timeout_seconds),
            },
            run=_dispatch,
            seed=digest,
        )
        if outcome.outcome != "succeeded":
            if errors:
                raise errors[0]
            raise TranscriberError(f"Transcription was not admitted: {outcome.outcome}")
        return str(text or "")

    def _timed_transcribe(self, audio_array: np.ndarray) -> str:
        if self.timeout_seconds <= 0:
            return self._impl.transcribe(audio_array)

        # Run the (possibly native, uninterruptible) backend on a daemon worker
        # and bound the wait. On timeout we abandon the worker — it cannot be
        # force-killed, but as a daemon it won't block process exit, and the
        # caller's locks release as this raises. Best-effort by design.
        outcome: dict[str, object] = {}

        def _run() -> None:
            try:
                outcome["text"] = self._impl.transcribe(audio_array)
            except BaseException as exc:  # noqa: BLE001 - propagated to caller
                outcome["error"] = exc

        worker = threading.Thread(
            target=_run, name="HoldSpeakTranscribeTimeout", daemon=True
        )
        worker.start()
        worker.join(self.timeout_seconds)

        if worker.is_alive():
            raise TranscriberTimeoutError(
                f"Transcription exceeded {self.timeout_seconds:.0f}s and was "
                "abandoned (the model may be hung). The next utterance will retry."
            )
        if "error" in outcome:
            raise outcome["error"]  # type: ignore[misc]
        return str(outcome.get("text", ""))
