"""Server → device status push-back (HS-14-07).

The AIPI-Lite-class device's LCD shows what HoldSpeak says it's
doing: ``Listening...`` while the user holds the button,
``Thinking...`` while transcription runs, the transcript
snippet on completion, ``Recording 12:34`` during a meeting,
``Bookmark @ 47s`` after a long-press, and so on.

This module owns the cross-thread plumbing only.
:class:`DeviceStatusEmitter` is a thread-safe registry of
per-device sender callables. The WebSocket route
(:mod:`holdspeak.device_audio_ws`) registers a sender at handshake
acceptance time that puts each status onto an asyncio queue
served by the connection's writer task; the runtime's voice and
meeting paths call :meth:`DeviceStatusEmitter.send` /
:meth:`DeviceStatusEmitter.broadcast` from any thread.

Callers may include the placeholder ``{label}`` in the status
text; the emitter substitutes it with the device's registered
label (resolved via the supplied ``DeviceRegistry``).
"""

from __future__ import annotations

import threading
from typing import Callable, Iterable, Optional, Protocol

from .logging_config import get_logger

log = get_logger("device_status")

StatusSender = Callable[[str, int], None]


class _LabelLookup(Protocol):
    """Subset of ``DeviceRegistry`` we need to resolve ``{label}``."""

    def get(self, device_id: str): ...  # noqa: D401 - matches DeviceRegistry.get


class DeviceStatusEmitter:
    """Thread-safe registry of per-device status senders.

    The WebSocket handler registers a sender at handshake-accept
    time and unregisters on disconnect. Every send is fire-and-
    forget — failures (queue full, connection torn down) are
    logged but do not raise.
    """

    def __init__(self, *, label_lookup: Optional[_LabelLookup] = None) -> None:
        self._lock = threading.Lock()
        self._senders: dict[str, StatusSender] = {}
        self._label_lookup = label_lookup

    def register(self, device_id: str, sender: StatusSender) -> None:
        with self._lock:
            self._senders[device_id] = sender

    def unregister(self, device_id: str) -> None:
        with self._lock:
            self._senders.pop(device_id, None)

    def is_registered(self, device_id: str) -> bool:
        with self._lock:
            return device_id in self._senders

    def active_device_ids(self) -> list[str]:
        with self._lock:
            return list(self._senders.keys())

    def send(self, device_id: str, text: str, *, ttl_ms: int = 0) -> bool:
        """Send a status message to ``device_id``.

        Returns ``True`` when the message was handed to the
        connection's writer queue, ``False`` when no sender is
        registered for that device or the dispatch raised.
        """
        rendered = self._render(device_id, text)
        with self._lock:
            sender = self._senders.get(device_id)
        if sender is None:
            return False
        try:
            sender(rendered, int(ttl_ms))
            return True
        except Exception:
            log.exception(
                "device_status_send_failed",
                extra={"device_id": device_id},
            )
            return False

    def broadcast(
        self,
        device_ids: Iterable[str],
        text: str,
        *,
        ttl_ms: int = 0,
    ) -> int:
        """Send the same message to several devices.

        Returns the count of successful sends.
        """
        delivered = 0
        for device_id in device_ids:
            if self.send(device_id, text, ttl_ms=ttl_ms):
                delivered += 1
        return delivered

    def _render(self, device_id: str, text: str) -> str:
        if "{label}" not in text:
            return text
        label = device_id
        if self._label_lookup is not None:
            try:
                descriptor = self._label_lookup.get(device_id)
            except Exception:
                descriptor = None
            if descriptor is not None:
                resolved = getattr(descriptor, "label", None)
                if resolved:
                    label = str(resolved)
        return text.replace("{label}", label)


# HS-17-08: width budget for status text on the AIPI-Lite LCD's
# bottom row. Empirical (Montserrat 10 + the device's display).
LCD_TEXT_MAX_CHARS = 30


def truncate_for_lcd(text: str, max_len: int = LCD_TEXT_MAX_CHARS) -> str:
    """Truncate `text` to `max_len` chars + `…` if needed.

    Stable cross-call: ASCII fast-path, single-pass length check, no
    splitting. Used by per-segment / intel / action-item pushback so
    long meeting strings don't overflow the LCD's single line.
    """
    if text is None:
        return ""
    if len(text) <= max_len:
        return text
    if max_len <= 1:
        return "…"
    return text[: max_len - 1] + "…"


def push_segment_to_devices(
    emitter: "DeviceStatusEmitter",
    attached_ids: Iterable[str],
    segment,
    *,
    ttl_ms: int = 3000,
) -> int:
    """Push a finalized transcript segment to all attached devices.

    HS-17-08: turns the AIPI-Lite LCD into a live confirmation channel
    during meetings — every finalized utterance flashes briefly on
    the device. Returns the count of successful sends (matches
    `DeviceStatusEmitter.broadcast`'s contract). No-op + returns 0
    if `attached_ids` is empty.

    `segment` is duck-typed — we read `.speaker` (optional) and
    `.text`. Built so the caller doesn't have to think about
    TranscriptSegment vs. a future SegmentDict.
    """
    ids = [d for d in attached_ids if d]
    if not ids:
        return 0
    speaker = getattr(segment, "speaker", None) or "?"
    text = getattr(segment, "text", "") or ""
    payload = truncate_for_lcd(f"{speaker}: {text}")
    return emitter.broadcast(ids, payload, ttl_ms=ttl_ms)


__all__ = [
    "DeviceStatusEmitter",
    "StatusSender",
    "LCD_TEXT_MAX_CHARS",
    "truncate_for_lcd",
    "push_segment_to_devices",
]
