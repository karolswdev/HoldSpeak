"""HS-60-01: the wake-word engine seam.

A small, fully injectable listener loop around an openWakeWord detector.
The seam exists so every behavior (detection thresholds, the refractory
cooldown, pause/resume, shutdown) is unit-testable **without the optional
engine installed**: CI carries no `[wakeword]` extra, so the real detector
hides behind lazy imports and `wake_word_available()`.

The safety posture this module serves (the Phase-60 conditions): the wake
word *arms*, it never types; what happens after a detection belongs to the
runtime (HS-60-02), which keeps the default action a preview. Detection and
everything downstream run locally; the only network moment in the whole
feature is the explicit one-time model download in
:func:`download_wake_models`.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional, Protocol

import numpy as np

from .logging_config import get_logger

log = get_logger("wake_word")

#: openWakeWord's native hop: 80 ms of 16 kHz mono int16.
FRAME_SAMPLES = 1280
SAMPLE_RATE = 16000


class WakeDetector(Protocol):
    """One frame in, one score out. `reset()` clears streaming state."""

    def predict(self, frame: np.ndarray) -> float: ...

    def reset(self) -> None: ...


#: A frame source: returns the next int16 frame, or None when the source is
#: closed (which ends the listener loop). Blocking is fine; the loop owns a
#: daemon thread.
FrameSource = Callable[[], Optional[np.ndarray]]


class WakeWordListener:
    """The detection loop: frames → scores → a debounced on_detect.

    - ``threshold``: a frame score at/above it is a detection.
    - ``refractory_seconds``: after a detection (or a resume) no further
      detection fires until the cooldown passes — openWakeWord scores stay
      hot for several frames after a hit, and arming twice is a bug.
    - ``pause()/resume()``: while paused, frames are still drained (the
      audio source must not back up) but never scored; resume resets the
      detector's streaming state so stale audio cannot fire.
    """

    def __init__(
        self,
        *,
        detector: WakeDetector,
        frames: FrameSource,
        on_detect: Callable[[float], None],
        threshold: float = 0.5,
        refractory_seconds: float = 2.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._detector = detector
        self._frames = frames
        self._on_detect = on_detect
        self.threshold = float(threshold)
        self.refractory_seconds = float(refractory_seconds)
        self._clock = clock
        self._paused = threading.Event()
        self._stopped = threading.Event()
        self._last_fire: float = float("-inf")
        self._thread: Optional[threading.Thread] = None

    # ── lifecycle ────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self.run, name="HoldSpeakWakeWord", daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        self._stopped.set()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
        self._thread = None

    def pause(self) -> None:
        """Idempotent: hold-to-talk and meeting capture call this freely."""
        self._paused.set()

    def resume(self) -> None:
        """Idempotent. Stale buffered audio must never fire a detection."""
        if not self._paused.is_set():
            return
        try:
            self._detector.reset()
        except Exception:  # pragma: no cover - a detector without state
            pass
        # A fresh cooldown on resume: the first frames after a stream gap
        # are the likeliest to glitch.
        self._last_fire = self._clock()
        self._paused.clear()

    @property
    def paused(self) -> bool:
        return self._paused.is_set()

    # ── the loop ─────────────────────────────────────────────────────────

    def run(self) -> None:
        """The blocking loop (run by `start()`'s thread; callable inline in tests)."""
        while not self._stopped.is_set():
            frame = self._frames()
            if frame is None:
                break
            if self._paused.is_set():
                continue  # drained, never scored
            try:
                score = float(self._detector.predict(np.asarray(frame)))
            except Exception as exc:  # pragma: no cover - engine hiccup
                log.debug(f"wake detector predict failed: {exc}")
                continue
            if score < self.threshold:
                continue
            now = self._clock()
            if now - self._last_fire < self.refractory_seconds:
                continue
            self._last_fire = now
            try:
                self._detector.reset()
            except Exception:  # pragma: no cover
                pass
            try:
                self._on_detect(score)
            except Exception as exc:  # pragma: no cover - observer safety
                log.debug(f"wake on_detect raised: {exc}")


class ArmedCapture:
    """The post-detection state machine, fed one int16 frame at a time.

    Frame-count time (one frame = 80 ms), no wall clock: wait for speech
    onset inside the armed window; capture until sustained silence or the
    utterance cap; then `result()` yields float32 audio for the normal
    pipeline, or None when the window expired with nothing spoken (the
    silent disarm). Pure and injectable: HS-60-02's runtime drives it from
    the live stream; tests drive it from arrays.
    """

    def __init__(
        self,
        *,
        window_seconds: float = 8.0,
        max_utterance_seconds: float = 15.0,
        silence_seconds: float = 1.2,
        speech_rms: float = 350.0,
    ) -> None:
        frame_s = FRAME_SAMPLES / SAMPLE_RATE
        self._window_frames = max(1, int(window_seconds / frame_s))
        self._max_frames = max(1, int(max_utterance_seconds / frame_s))
        self._silence_frames = max(1, int(silence_seconds / frame_s))
        self.speech_rms = float(speech_rms)
        self._waiting = 0
        self._silent_run = 0
        self._captured: list[np.ndarray] = []
        self.state = "waiting"  # waiting | capturing | captured | expired

    @staticmethod
    def _rms(frame: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(frame.astype(np.float64)))))

    def feed(self, frame: np.ndarray) -> str:
        """Feed one frame; returns the state after consuming it."""
        if self.state in ("captured", "expired"):
            return self.state
        frame = np.asarray(frame)
        loud = self._rms(frame) >= self.speech_rms
        if self.state == "waiting":
            self._waiting += 1
            if loud:
                self.state = "capturing"
                self._captured.append(frame)
            elif self._waiting >= self._window_frames:
                self.state = "expired"
            return self.state
        # capturing
        self._captured.append(frame)
        self._silent_run = 0 if loud else self._silent_run + 1
        if self._silent_run >= self._silence_frames or len(self._captured) >= self._max_frames:
            self.state = "captured"
        return self.state

    def result(self) -> Optional[np.ndarray]:
        """float32 [-1, 1] audio when captured; None otherwise."""
        if self.state != "captured" or not self._captured:
            return None
        audio = np.concatenate(self._captured).astype(np.float32) / 32768.0
        return audio


# ── the real engine, strictly optional ──────────────────────────────────────


def wake_word_available() -> bool:
    """True when the optional engine imports (`pip install 'holdspeak[wakeword]'`)."""
    try:
        import openwakeword  # noqa: F401
    except Exception:
        return False
    return True


def download_wake_models(model: str = "hey_jarvis") -> None:
    """Fetch the detection models (THE one network moment of the feature).

    Downloads ~7 MB (the named wake model plus openWakeWord's shared
    melspectrogram/embedding/VAD models) from the openWakeWord GitHub
    releases into the package's resource cache. Explicit and one-time; the
    settings UI and the docs state it plainly.
    """
    from openwakeword.utils import download_models

    download_models(model_names=[model])


class OpenWakeWordDetector:
    """The real detector: openWakeWord over ONNX, one model, one score."""

    def __init__(self, model: str = "hey_jarvis") -> None:
        from openwakeword.model import Model

        self._name = model
        self._model = Model(wakeword_models=[model], inference_framework="onnx")
        # Warm the inference path on the CONSTRUCTION thread: onnxruntime's
        # first run initializes its thread pool and kernels, and doing that
        # lazily on the listener's daemon thread proved fragile in the full
        # runtime cocktail (uvicorn + Metal resident). One silent frame here
        # makes every later predict a plain steady-state call.
        self._model.predict(np.zeros(FRAME_SAMPLES, dtype=np.int16))
        self._model.reset()

    def predict(self, frame: np.ndarray) -> float:
        frame = np.asarray(frame)
        if frame.dtype != np.int16:
            # The recorder side works in float32 [-1, 1]; convert once here.
            frame = np.clip(frame, -1.0, 1.0)
            frame = (frame * 32767.0).astype(np.int16)
        scores = self._model.predict(frame)
        if self._name in scores:
            return float(scores[self._name])
        return float(max(scores.values(), default=0.0))

    def reset(self) -> None:
        self._model.reset()


__all__ = [
    "ArmedCapture",
    "FRAME_SAMPLES",
    "SAMPLE_RATE",
    "FrameSource",
    "OpenWakeWordDetector",
    "WakeDetector",
    "WakeWordListener",
    "download_wake_models",
    "wake_word_available",
]
