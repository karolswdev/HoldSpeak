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

import hmac
import secrets
import threading
from collections import deque
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional, TYPE_CHECKING

import numpy as np
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from .audio import AudioSource, _linear_resample_mono
from .logging_config import get_logger

if TYPE_CHECKING:
    from .config import Config

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
        device_id: Optional[str] = None,
    ) -> None:
        if sample_rate <= 0 or wire_sample_rate <= 0:
            raise ValueError("sample rates must be positive")
        if max_buffer_seconds <= 0:
            raise ValueError("max_buffer_seconds must be positive")

        self.sample_rate = int(sample_rate)
        self.wire_sample_rate = int(wire_sample_rate)
        self.max_buffer_seconds = float(max_buffer_seconds)
        self.device_id = device_id

        self._lock = threading.Lock()
        self._frames: deque[np.ndarray] = deque()
        self._buffered_samples: int = 0
        self._recording = False

    @property
    def is_recording(self) -> bool:
        with self._lock:
            return self._recording

    @property
    def buffered_bytes(self) -> int:
        """Current pushed-buffer depth in bytes (int16 LE = 2 bytes/sample)."""
        with self._lock:
            return self._buffered_samples * 2

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

        return self._frames_to_audio(frames, wire_rate, target_rate)

    def drain(self) -> np.ndarray:
        """Return all currently-buffered audio without stopping the recording.

        The internal buffer is cleared after the snapshot, so subsequent
        ``push()`` calls accumulate fresh audio. Used by the meeting
        path (HS-14-06) to incrementally consume audio while the
        recording stays open.

        Returns an empty float32 array when no audio is buffered or
        the recorder is not currently recording.
        """
        with self._lock:
            if not self._recording:
                return np.empty((0,), dtype=np.float32)
            frames = list(self._frames)
            self._frames.clear()
            self._buffered_samples = 0
            wire_rate = self.wire_sample_rate
            target_rate = self.sample_rate

        return self._frames_to_audio(frames, wire_rate, target_rate)

    @staticmethod
    def _frames_to_audio(
        frames: list[np.ndarray],
        wire_rate: int,
        target_rate: int,
    ) -> np.ndarray:
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
            # Single warning per overflow burst (the loop drains in
            # one shot before logging) — not one per dropped frame.
            message = (
                "device.queue.overflow"
                if self.device_id is not None
                else "remote_audio_buffer_overflow"
            )
            log.warning(
                message,
                extra={
                    "device_id": self.device_id,
                    "dropped_samples": dropped_samples,
                    "dropped_bytes": dropped_samples * 2,
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
            recorder = RemoteAudioRecorder(device_id=device_id)
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
        """Return a snapshot of every registered device.

        ``queue_depth`` is refreshed from the live recorder's
        current pushed-buffer depth on each call so callers
        (``/api/runtime/status`` in HS-14-07) get an accurate
        view without having to manually tick the registry.
        """
        with self._lock:
            snapshot: list[DeviceDescriptor] = []
            for descriptor in self._descriptors.values():
                recorder = self._recorders.get(descriptor.id)
                depth = recorder.buffered_bytes if recorder is not None else 0
                snapshot.append(replace(descriptor, queue_depth=depth))
            return snapshot

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


# ---------------------------------------------------------------------------
# Device handshake protocol (HS-14-03)
# ---------------------------------------------------------------------------
#
# A device opens the audio ingest WebSocket, sends a single JSON
# ``DeviceHandshake`` frame as its first message, and only then is
# allowed to push binary PCM. The route (HS-14-04) maps the
# exceptions raised here onto WebSocket close codes from the 4xxx
# application range; constants live here so the route does not
# duplicate them.

DEVICE_HANDSHAKE_VERSION = 1

WS_CLOSE_INVALID_HANDSHAKE = 4001
WS_CLOSE_PSK_MISMATCH = 4003
WS_CLOSE_DUPLICATE_LABEL = 4009


class HandshakeError(DeviceRegistryError):
    """Base class for handshake-time auth/protocol errors."""

    code: int = WS_CLOSE_INVALID_HANDSHAKE


class InvalidHandshakeError(HandshakeError):
    """Raised when the handshake payload is missing fields, malformed, or has unknown extras."""

    code: int = WS_CLOSE_INVALID_HANDSHAKE


class PskMismatchError(HandshakeError):
    """Raised when the device's PSK does not match the configured value."""

    code: int = WS_CLOSE_PSK_MISMATCH


# ``DuplicateLabelError`` is raised by ``DeviceRegistry.register`` and
# carries no ``code`` of its own. The route maps it to
# ``WS_CLOSE_DUPLICATE_LABEL`` (4009) at the call site.


class DeviceHandshake(BaseModel):
    """First-message handshake the device sends on the audio ingest WebSocket.

    Strict by design — unknown fields are rejected. The PSK is *not*
    compared here; route-level code calls :func:`verify_psk` with
    the configured value.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    type: Literal["hello"]
    device_id: str
    label: str
    psk: str
    version: int

    @field_validator("device_id", "label", "psk")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("must not be empty")
        return value


def parse_handshake(payload: Any) -> DeviceHandshake:
    """Validate and parse a handshake payload (a decoded JSON object).

    Raises:
        InvalidHandshakeError: if the payload is not a mapping, is
            missing required fields, has unknown fields, or contains
            invalid types.
    """
    if not isinstance(payload, dict):
        raise InvalidHandshakeError(
            f"handshake payload must be a JSON object, got {type(payload).__name__}"
        )
    try:
        return DeviceHandshake.model_validate(payload)
    except ValidationError as exc:
        raise InvalidHandshakeError(str(exc)) from exc


def verify_psk(provided: str, expected: str) -> bool:
    """Constant-time comparison between the device-supplied PSK and the configured one.

    Returns ``False`` (without invoking ``hmac.compare_digest``) when
    either input is empty so a freshly-installed instance with no
    PSK on disk cannot be authenticated by sending an empty string.
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(
        provided.encode("utf-8"), expected.encode("utf-8")
    )


# ---------------------------------------------------------------------------
# PSK lifecycle helpers
# ---------------------------------------------------------------------------


def generate_device_psk() -> str:
    """Return a fresh, cryptographically random URL-safe base64 PSK (32 chars)."""
    # token_urlsafe(24) yields ~32 chars (no padding). Comfortably
    # above the ≥24 char floor in the spec; the underlying entropy
    # is 24 bytes (192 bits).
    return secrets.token_urlsafe(24)


def ensure_device_psk(
    config: "Config",
    *,
    save_path: Optional[Path] = None,
) -> str:
    """Return the device PSK, generating + persisting it on first use.

    Mutates ``config.device.psk`` and saves the config file when the
    PSK was empty. A non-empty PSK is returned unchanged without
    touching disk.
    """
    if config.device.psk:
        return config.device.psk
    config.device.psk = generate_device_psk()
    config.save(save_path)
    return config.device.psk


def rotate_device_psk(
    config: "Config",
    *,
    save_path: Optional[Path] = None,
) -> str:
    """Generate a fresh PSK, persist it, and return it.

    Currently-connected devices stay connected for their lifetime —
    revocation lands when HS-14-04 wires the route and re-auths on
    every reconnect.
    """
    config.device.psk = generate_device_psk()
    config.save(save_path)
    return config.device.psk


__all__ = [
    "DEVICE_HANDSHAKE_VERSION",
    "DeviceDescriptor",
    "DeviceHandshake",
    "DeviceRegistry",
    "DeviceRegistryError",
    "DuplicateLabelError",
    "HandshakeError",
    "InvalidHandshakeError",
    "PskMismatchError",
    "RemoteAudioRecorder",
    "RemoteAudioRecorderError",
    "WS_CLOSE_DUPLICATE_LABEL",
    "WS_CLOSE_INVALID_HANDSHAKE",
    "WS_CLOSE_PSK_MISMATCH",
    "ensure_device_psk",
    "generate_device_psk",
    "parse_handshake",
    "rotate_device_psk",
    "verify_psk",
]
