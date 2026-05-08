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
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Optional

import numpy as np

from .audio import AudioSource, _linear_resample_mono
from .logging_config import get_logger

log = get_logger("audio.remote")
registry_log = get_logger("audio.devices")

_INT16_SCALE = 32768.0


class RemoteAudioRecorderError(RuntimeError):
    """Raised when ``RemoteAudioRecorder`` is used incorrectly."""


class DeviceRegistryError(RuntimeError):
    """Base class for ``DeviceRegistry`` errors."""


class DuplicateLabelError(DeviceRegistryError):
    """Raised by :meth:`DeviceRegistry.register` when an active device already holds the requested label.

    The WebSocket handler in HS-14-04 maps this to a 409 Conflict on
    the ``/api/devices/audio`` handshake.
    """


@dataclass
class DeviceDescriptor:
    """Public-facing metadata for one registered remote audio device."""

    id: str
    label: str
    connected_at: datetime
    last_seen: datetime
    queue_depth: int = 0


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


class DeviceRegistry:
    """Thread-safe in-memory registry of remote audio devices.

    Each registered device gets a private :class:`RemoteAudioRecorder`;
    consumers fetch it through :meth:`recorder_for`. The registry's
    lifecycle is owned by the FastAPI app — it is created at runtime
    bootstrap and lives as long as the runtime does. Devices
    re-register on reconnect; nothing here is persisted across
    restarts.

    Label uniqueness is enforced because ``label`` surfaces verbatim
    as ``TranscriptSegment.speaker``; two devices both labeled
    ``"Karol"`` would yield ambiguous transcripts. A label freed by
    :meth:`unregister` may be reused immediately.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._descriptors: dict[str, DeviceDescriptor] = {}
        self._recorders: dict[str, RemoteAudioRecorder] = {}

    def register(self, device_id: str, label: str) -> DeviceDescriptor:
        """Register a device and create its backing recorder.

        Raises:
            ValueError: if ``device_id`` or ``label`` is empty / blank.
            DuplicateLabelError: if another *active* device already
                holds ``label``.

        Re-registering the same ``device_id`` is allowed only when
        the existing descriptor is gone (i.e. the device must
        unregister first). A second call with the same id raises
        ``DeviceRegistryError`` so that races are loud rather than
        silently overwriting an active recorder.
        """
        device_id = (device_id or "").strip()
        label = (label or "").strip()
        if not device_id:
            raise ValueError("device_id must be non-empty")
        if not label:
            raise ValueError("label must be non-empty")

        now = datetime.now()
        with self._lock:
            if device_id in self._descriptors:
                raise DeviceRegistryError(
                    f"device_id {device_id!r} is already registered; "
                    "unregister before registering again"
                )
            for existing in self._descriptors.values():
                if existing.label == label:
                    raise DuplicateLabelError(
                        f"label {label!r} is already in use by device "
                        f"{existing.id!r}"
                    )

            descriptor = DeviceDescriptor(
                id=device_id,
                label=label,
                connected_at=now,
                last_seen=now,
            )
            recorder = RemoteAudioRecorder()
            self._descriptors[device_id] = descriptor
            self._recorders[device_id] = recorder

        registry_log.info(
            "device_registered",
            extra={"device_id": device_id, "label": label},
        )
        return descriptor

    def unregister(self, device_id: str) -> None:
        """Drop the device and its recorder.

        Idempotent — calling on an unknown id logs at info and
        returns without raising.
        """
        with self._lock:
            descriptor = self._descriptors.pop(device_id, None)
            self._recorders.pop(device_id, None)

        if descriptor is None:
            registry_log.info(
                "device_unregister_unknown",
                extra={"device_id": device_id},
            )
            return

        registry_log.info(
            "device_unregistered",
            extra={"device_id": device_id, "label": descriptor.label},
        )

    def get(self, device_id: str) -> Optional[DeviceDescriptor]:
        with self._lock:
            descriptor = self._descriptors.get(device_id)
            if descriptor is None:
                return None
            return replace(descriptor)

    def active(self) -> list[DeviceDescriptor]:
        with self._lock:
            return [replace(d) for d in self._descriptors.values()]

    def touch(self, device_id: str) -> None:
        """Update ``last_seen`` for a registered device.

        No-op (logged at debug) for an unknown id so a racing tail
        message from a just-unregistered device does not blow up.
        """
        now = datetime.now()
        with self._lock:
            descriptor = self._descriptors.get(device_id)
            if descriptor is None:
                registry_log.debug(
                    "device_touch_unknown",
                    extra={"device_id": device_id},
                )
                return
            descriptor.last_seen = now

    def recorder_for(self, device_id: str) -> Optional[AudioSource]:
        """Return the device's :class:`RemoteAudioRecorder`, or ``None`` if unknown."""
        with self._lock:
            return self._recorders.get(device_id)


__all__ = [
    "DeviceDescriptor",
    "DeviceRegistry",
    "DeviceRegistryError",
    "DuplicateLabelError",
    "RemoteAudioRecorder",
    "RemoteAudioRecorderError",
]
