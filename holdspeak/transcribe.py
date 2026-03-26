"""Local transcription using a Whisper backend.

`Transcriber` loads a Whisper model and converts microphone audio (mono,
float32, 16 kHz) into text.
"""

from __future__ import annotations

import importlib
import importlib.util
import platform
import sys
from pathlib import Path
from typing import Optional, Protocol

import numpy as np

from .logging_config import get_logger

log = get_logger("transcribe")


class TranscriberError(RuntimeError):
    """Raised when model loading or transcription fails."""


class _TranscriberImpl(Protocol):
    device: str
    compute_type: str

    def transcribe(self, audio_array: np.ndarray) -> str: ...


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
    ) -> None:
        """Initialize the Whisper model.

        Args:
            model_name: Whisper model name (defaults to "base").
            device: Unused (kept for backwards compatibility with faster-whisper).
            compute_type: Unused (kept for backwards compatibility with faster-whisper).
        """

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

        last_error: Optional[BaseException] = None
        for repo in candidates:
            log.info(f"Attempting to load model from: {repo}")
            try:
                self._preload_model(repo)
            except Exception as exc:
                log.warning(f"Failed to load from {repo}: {exc}")
                last_error = exc
                continue
            else:
                log.info(f"Successfully loaded model from: {repo}")
                self._path_or_hf_repo = repo
                break

        if self._path_or_hf_repo is None:
            suffix = f" Last error: {last_error}" if last_error else ""
            log.error(f"All model candidates failed for '{model_name}'{suffix}")
            raise TranscriberError(
                f"Failed to load Whisper model '{model_name}' via mlx-whisper.{suffix}"
            ) from last_error

        self.device = "mlx"
        self.compute_type = "float16"
        log.info(f"Transcriber ready: model={self._path_or_hf_repo}, device={self.device}")

    def _preload_model(self, path_or_hf_repo: str) -> None:
        log.debug(f"_preload_model called with: {path_or_hf_repo}")

        # Prefer preloading without decoding, if the internal hook exists.
        try:
            log.debug("Trying ModelHolder.get_model approach...")
            from mlx_whisper.transcribe import ModelHolder  # type: ignore

            ModelHolder.get_model(path_or_hf_repo, self._mx.float16)
            log.debug("ModelHolder.get_model succeeded")
            return
        except Exception as e:
            log.debug(f"ModelHolder approach failed: {e}, trying fallback...")

        # Fallback: run a tiny, silent transcription to force weight download/load.
        log.debug("Using silent transcription fallback to load model...")
        silent = np.zeros(1600, dtype=np.float32)  # ~0.1s at 16 kHz
        self._mlx_whisper.transcribe(  # type: ignore[union-attr]
            silent,
            path_or_hf_repo=path_or_hf_repo,
            verbose=None,
            language="en",
        )
        log.debug("Fallback transcription completed - model loaded")

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

        audio = np.ascontiguousarray(audio, dtype=np.float32)
        log.debug(f"Transcribing {len(audio)} samples ({len(audio)/16000:.2f}s)")

        try:
            result = self._mlx_whisper.transcribe(  # type: ignore[union-attr]
                audio,
                path_or_hf_repo=self._path_or_hf_repo,
                verbose=None,
            )
            if isinstance(result, dict):
                text = str(result.get("text", "")).strip()
            else:
                text = str(getattr(result, "text", result)).strip()
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
    ) -> None:
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
            segments, _info = self._model.transcribe(audio, vad_filter=False)
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
    ) -> None:
        resolved = _resolve_backend(backend)
        self.backend = resolved

        if resolved == "mlx":
            self._impl: _TranscriberImpl = _MlxTranscriber(
                model_name=model_name,
                device=device,
                compute_type=compute_type,
            )
        else:
            self._impl = _FasterWhisperTranscriber(
                model_name=model_name,
                device=device,
                compute_type=compute_type,
            )

        self.model_name = model_name
        self.device = self._impl.device
        self.compute_type = self._impl.compute_type

    def transcribe(self, audio_array: np.ndarray) -> str:
        return self._impl.transcribe(audio_array)
