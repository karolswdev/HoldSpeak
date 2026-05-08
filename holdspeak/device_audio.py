"""Remote audio source: PCM frames pushed in over the wire.

``RemoteAudioRecorder`` is the AIPI-Lite-side counterpart to
:class:`holdspeak.audio.AudioRecorder`. Where ``AudioRecorder``
opens a local PortAudio stream, ``RemoteAudioRecorder`` accepts
pushed PCM frames via :meth:`RemoteAudioRecorder.push` (called by
the ``/api/devices/audio`` WebSocket route in HS-14-04) and returns
the same mono float32 16 kHz ndarray on ``stop_recording()``.

Wire contract (set by phase 14): 16 kHz mono int16 little-endian.
A non-default ``wire_sample_rate`` is supported as a defensive
fallback — if a future device emits a different rate the recorder
resamples on stop. The bridge is expected to do rate-matching on
its side, so the resample path stays a safety net.

Backpressure here is intentionally minimal — a bounded ring of
pushed frames with drop-oldest on overflow, plus a logged
warning. The richer policy (per-device queues, observability
counters, ``/api/runtime/status`` integration) lands in HS-14-04.
"""

from __future__ import annotations

import threading
from collections import deque

import numpy as np

from .audio import AudioSource, _linear_resample_mono
from .logging_config import get_logger

log = get_logger("audio.remote")

_INT16_SCALE = 32768.0


class RemoteAudioRecorderError(RuntimeError):
    """Raised when ``RemoteAudioRecorder`` is used incorrectly."""


class RemoteAudioRecorder:
    """An :class:`AudioSource` that consumes PCM frames pushed by a remote device."""

    def __init__(
        self,
        *,
        sample_rate: int = 16_000,
        wire_sample_rate: int = 16_000,
        max_buffer_seconds: float = 2.0,
    ) -> None:
        if sample_rate <= 0 or wire_sample_rate <= 0:
            raise ValueError("sample rates must be positive")
        if max_buffer_seconds <= 0:
            raise ValueError("max_buffer_seconds must be positive")

        self.sample_rate = int(sample_rate)
        self.wire_sample_rate = int(wire_sample_rate)
        self.max_buffer_seconds = float(max_buffer_seconds)

        self._lock = threading.Lock()
        self._frames: deque[np.ndarray] = deque()
        self._buffered_samples: int = 0
        self._recording = False

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    def start_recording(self) -> None:
        with self._lock:
            if self._recording:
                raise RemoteAudioRecorderError("Recording already started")
            self._recording = True
            self._frames.clear()
            self._buffered_samples = 0

    def push(self, pcm_bytes: bytes) -> None:
        """Append a frame of int16 LE PCM to the pushed-audio buffer.

        Bytes pushed before ``start_recording()`` or after
        ``stop_recording()`` are silently dropped — the WebSocket
        route may race the device's stop signal and we don't want
        to blow up the connection over a tail frame. An odd
        trailing byte (incomplete sample) is also dropped.
        """
        if not pcm_bytes:
            return

        usable = len(pcm_bytes) - (len(pcm_bytes) % 2)
        if usable <= 0:
            return

        samples = np.frombuffer(pcm_bytes[:usable], dtype="<i2").astype(np.float32)
        samples /= _INT16_SCALE

        with self._lock:
            if not self._recording:
                return
            self._frames.append(samples)
            self._buffered_samples += int(samples.size)
            self._enforce_buffer_cap_locked()

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the captured audio.

        Returns:
            Mono float32 numpy array at ``self.sample_rate`` (16 kHz).

        Raises:
            RemoteAudioRecorderError: If recording was not started.
        """
        with self._lock:
            if not self._recording:
                raise RemoteAudioRecorderError("Recording not started")
            self._recording = False
            frames = list(self._frames)
            self._frames.clear()
            self._buffered_samples = 0
            wire_rate = self.wire_sample_rate
            target_rate = self.sample_rate

        if not frames:
            return np.empty((0,), dtype=np.float32)

        audio = np.concatenate(frames).astype(np.float32, copy=False)
        if wire_rate != target_rate:
            audio = _linear_resample_mono(audio, wire_rate, target_rate)
        return audio

    def _enforce_buffer_cap_locked(self) -> None:
        cap_samples = max(1, int(round(self.max_buffer_seconds * self.wire_sample_rate)))
        if self._buffered_samples <= cap_samples:
            return

        dropped_samples = 0
        while self._buffered_samples > cap_samples and self._frames:
            oldest = self._frames.popleft()
            self._buffered_samples -= int(oldest.size)
            dropped_samples += int(oldest.size)

        if dropped_samples:
            log.warning(
                "remote_audio_buffer_overflow",
                extra={
                    "dropped_samples": dropped_samples,
                    "cap_samples": cap_samples,
                    "buffered_samples": self._buffered_samples,
                    "max_buffer_seconds": self.max_buffer_seconds,
                    "wire_sample_rate": self.wire_sample_rate,
                },
            )


__all__ = [
    "RemoteAudioRecorder",
    "RemoteAudioRecorderError",
]
